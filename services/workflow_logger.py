"""
Workflow Logging Service

Provides comprehensive logging for LLM workflow executions with detailed
observability, token tracking, and cost analysis.

This service captures:
- Complete workflow execution (start to finish)
- Individual node/step execution details
- All prompts and responses
- Token usage and costs
- Execution timing
- Error tracking
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from contextlib import contextmanager

from models import db, WorkflowLog, WorkflowNodeLog

logger = logging.getLogger(__name__)

# OpenAI Pricing (as of 2024-01-15)
# https://openai.com/pricing
PRICING = {
    'gpt-4o': {
        'prompt': 0.0025 / 1000,      # $2.50 per 1M tokens
        'completion': 0.010 / 1000     # $10.00 per 1M tokens
    },
    'gpt-4o-mini': {
        'prompt': 0.000150 / 1000,    # $0.150 per 1M tokens
        'completion': 0.000600 / 1000  # $0.600 per 1M tokens
    },
    'gpt-4-turbo': {
        'prompt': 0.010 / 1000,       # $10.00 per 1M tokens
        'completion': 0.030 / 1000     # $30.00 per 1M tokens
    },
    'gpt-4': {
        'prompt': 0.030 / 1000,       # $30.00 per 1M tokens
        'completion': 0.060 / 1000     # $60.00 per 1M tokens
    },
    'gpt-3.5-turbo': {
        'prompt': 0.0005 / 1000,      # $0.50 per 1M tokens
        'completion': 0.0015 / 1000    # $1.50 per 1M tokens
    }
}


def calculate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculate the cost of an LLM API call based on token usage.

    Args:
        model_name: Name of the model (e.g., "gpt-4o-mini")
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens

    Returns:
        Cost in USD (rounded to 6 decimal places)
    """
    if model_name not in PRICING:
        logger.warning(f"Unknown model for pricing: {model_name}. Using gpt-4o-mini as fallback.")
        model_name = 'gpt-4o-mini'

    pricing = PRICING[model_name]
    cost = (prompt_tokens * pricing['prompt']) + (completion_tokens * pricing['completion'])
    return round(cost, 6)


class WorkflowLogger:
    """
    Context manager for logging LLM workflow executions.

    Usage:
        async with WorkflowLogger("image_prompt_chain", task_id=123, persona_id=456) as wf_logger:
            wf_logger.set_input({"person_data": {...}, "num_images": 4})

            # Log node executions
            node_logger = wf_logger.start_node("generate_idea", order=0)
            node_logger.log_llm_call(
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=200,
                system_prompt="...",
                user_prompt="...",
                response="...",
                usage={"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200}
            )

            # Workflow auto-completes on exit
    """

    def __init__(
        self,
        workflow_name: str,
        task_id: Optional[int] = None,
        persona_id: Optional[int] = None,
        auto_commit: bool = True
    ):
        """
        Initialize workflow logger.

        Args:
            workflow_name: Name of the workflow (e.g., "image_prompt_chain")
            task_id: Optional GenerationTask.id for context
            persona_id: Optional GenerationResult.id for context
            auto_commit: Auto-commit database changes (default: True)
        """
        self.workflow_name = workflow_name
        self.task_id = task_id
        self.persona_id = persona_id
        self.auto_commit = auto_commit

        self.workflow_run_id = str(uuid.uuid4())
        self.workflow_log: Optional[WorkflowLog] = None
        self.started_at: Optional[datetime] = None

        # Track node order
        self.node_counter = 0

    async def __aenter__(self):
        """Start workflow logging (async context manager)."""
        return self.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Complete workflow logging (async context manager)."""
        if exc_type:
            # Workflow failed with exception
            self.complete(
                status='failed',
                error_message=f"{exc_type.__name__}: {str(exc_val)}"
            )
        else:
            # Workflow succeeded
            self.complete(status='completed')
        return False  # Don't suppress exceptions

    def __enter__(self):
        """Start workflow logging (sync context manager)."""
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Complete workflow logging (sync context manager)."""
        if exc_type:
            # Workflow failed with exception
            self.complete(
                status='failed',
                error_message=f"{exc_type.__name__}: {str(exc_val)}"
            )
        else:
            # Workflow succeeded
            self.complete(status='completed')
        return False  # Don't suppress exceptions

    def start(self) -> 'WorkflowLogger':
        """
        Start workflow logging.

        Returns:
            Self for chaining
        """
        self.started_at = datetime.utcnow()

        # Create workflow log record
        self.workflow_log = WorkflowLog(
            workflow_run_id=self.workflow_run_id,
            workflow_name=self.workflow_name,
            task_id=self.task_id,
            persona_id=self.persona_id,
            status='running',
            started_at=self.started_at
        )

        db.session.add(self.workflow_log)

        if self.auto_commit:
            db.session.commit()

        logger.info(f"[Workflow {self.workflow_run_id[:8]}] Started: {self.workflow_name}")
        return self

    def set_input(self, input_data: Dict[str, Any]) -> None:
        """
        Set workflow input data.

        Args:
            input_data: Dictionary of input parameters
        """
        if not self.workflow_log:
            raise RuntimeError("Workflow not started. Call start() first.")

        self.workflow_log.input_data = input_data

        if self.auto_commit:
            db.session.commit()

    def set_output(self, output_data: Dict[str, Any]) -> None:
        """
        Set workflow output data.

        Args:
            output_data: Dictionary of output results
        """
        if not self.workflow_log:
            raise RuntimeError("Workflow not started. Call start() first.")

        self.workflow_log.output_data = output_data

        if self.auto_commit:
            db.session.commit()

    def complete(self, status: str = 'completed', error_message: Optional[str] = None) -> None:
        """
        Complete workflow logging.

        Args:
            status: Final status ('completed' or 'failed')
            error_message: Error message if status is 'failed'
        """
        if not self.workflow_log:
            logger.warning(f"[Workflow {self.workflow_run_id[:8]}] Cannot complete - not started")
            return

        completed_at = datetime.utcnow()
        execution_time_ms = int((completed_at - self.started_at).total_seconds() * 1000)

        # Calculate total tokens and cost from all nodes
        total_tokens = 0
        total_cost = 0.0

        for node in self.workflow_log.nodes:
            if node.total_tokens:
                total_tokens += node.total_tokens
            if node.cost:
                total_cost += node.cost

        # Update workflow log
        self.workflow_log.status = status
        self.workflow_log.completed_at = completed_at
        self.workflow_log.execution_time_ms = execution_time_ms
        self.workflow_log.total_tokens = total_tokens if total_tokens > 0 else None
        self.workflow_log.total_cost = round(total_cost, 6) if total_cost > 0 else None
        self.workflow_log.error_message = error_message

        if self.auto_commit:
            db.session.commit()

        logger.info(
            f"[Workflow {self.workflow_run_id[:8]}] {status.upper()}: "
            f"{execution_time_ms}ms, {total_tokens} tokens, ${total_cost:.6f}"
        )

    def start_node(
        self,
        node_name: str,
        order: Optional[int] = None,
        input_data: Optional[Dict[str, Any]] = None
    ) -> 'NodeLogger':
        """
        Start logging a workflow node.

        Args:
            node_name: Name of the node (e.g., "generate_idea")
            order: Node execution order (auto-increments if not provided)
            input_data: Optional input data for this node

        Returns:
            NodeLogger instance for logging node execution
        """
        if not self.workflow_log:
            raise RuntimeError("Workflow not started. Call start() first.")

        if order is None:
            order = self.node_counter
            self.node_counter += 1

        return NodeLogger(
            workflow_log=self.workflow_log,
            node_name=node_name,
            node_order=order,
            input_data=input_data,
            auto_commit=self.auto_commit
        )


class NodeLogger:
    """
    Logger for individual workflow node execution.

    Usage:
        node_logger = workflow_logger.start_node("generate_idea", order=0)
        node_logger.log_llm_call(...)
        node_logger.complete(output_data={"idea": "..."})
    """

    def __init__(
        self,
        workflow_log: WorkflowLog,
        node_name: str,
        node_order: int,
        input_data: Optional[Dict[str, Any]] = None,
        auto_commit: bool = True
    ):
        """
        Initialize node logger.

        Args:
            workflow_log: Parent WorkflowLog instance
            node_name: Name of the node
            node_order: Execution order (0-indexed)
            input_data: Optional input data
            auto_commit: Auto-commit database changes
        """
        self.workflow_log = workflow_log
        self.node_name = node_name
        self.node_order = node_order
        self.auto_commit = auto_commit

        self.started_at = datetime.utcnow()

        # Create node log record
        self.node_log = WorkflowNodeLog(
            workflow_log_id=workflow_log.id,
            node_name=node_name,
            node_order=node_order,
            status='running',
            input_data=input_data,
            started_at=self.started_at
        )

        db.session.add(self.node_log)

        if self.auto_commit:
            db.session.commit()

    def log_llm_call(
        self,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: str,
        user_prompt: str,
        response: str,
        usage: Dict[str, int]
    ) -> None:
        """
        Log LLM API call details.

        Args:
            model: Model name (e.g., "gpt-4o-mini")
            temperature: Temperature setting
            max_tokens: Max tokens setting
            system_prompt: System prompt sent
            user_prompt: User prompt sent
            response: LLM response received
            usage: Usage dict with prompt_tokens, completion_tokens, total_tokens
        """
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get('total_tokens', 0)

        # Calculate cost
        cost = calculate_cost(model, prompt_tokens, completion_tokens)

        # Update node log
        self.node_log.model_name = model
        self.node_log.temperature = temperature
        self.node_log.max_tokens = max_tokens
        self.node_log.system_prompt = system_prompt
        self.node_log.user_prompt = user_prompt
        self.node_log.output_data = {'response': response}
        self.node_log.prompt_tokens = prompt_tokens
        self.node_log.completion_tokens = completion_tokens
        self.node_log.total_tokens = total_tokens
        self.node_log.cost = cost

        if self.auto_commit:
            db.session.commit()

    def complete(
        self,
        status: str = 'completed',
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Complete node logging.

        Args:
            status: Final status ('completed' or 'failed')
            output_data: Output data from node execution
            error_message: Error message if status is 'failed'
        """
        completed_at = datetime.utcnow()
        execution_time_ms = int((completed_at - self.started_at).total_seconds() * 1000)

        self.node_log.status = status
        self.node_log.completed_at = completed_at
        self.node_log.execution_time_ms = execution_time_ms
        self.node_log.error_message = error_message

        if output_data:
            self.node_log.output_data = output_data

        if self.auto_commit:
            db.session.commit()


# Convenience function for creating workflow loggers
def create_workflow_logger(
    workflow_name: str,
    task_id: Optional[int] = None,
    persona_id: Optional[int] = None,
    auto_commit: bool = True
) -> WorkflowLogger:
    """
    Create a new workflow logger.

    Args:
        workflow_name: Name of the workflow
        task_id: Optional task ID for context
        persona_id: Optional persona ID for context
        auto_commit: Auto-commit database changes

    Returns:
        WorkflowLogger instance
    """
    return WorkflowLogger(
        workflow_name=workflow_name,
        task_id=task_id,
        persona_id=persona_id,
        auto_commit=auto_commit
    )
