-- Migration: Add Workflow Logging Tables
-- Date: 2024-02-24
-- Description: Add workflow_logs and workflow_node_logs tables for LLM workflow observability

-- Create workflow_logs table
CREATE TABLE IF NOT EXISTS workflow_logs (
    id SERIAL PRIMARY KEY,
    workflow_run_id VARCHAR(36) UNIQUE NOT NULL,
    workflow_name VARCHAR(100) NOT NULL,
    task_id INTEGER REFERENCES generation_tasks(id) ON DELETE SET NULL,
    persona_id INTEGER REFERENCES generation_results(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    input_data JSONB,
    output_data JSONB,
    total_tokens INTEGER,
    total_cost FLOAT,
    execution_time_ms INTEGER,
    error_message TEXT,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for workflow_logs
CREATE INDEX IF NOT EXISTS idx_workflow_logs_workflow_run_id ON workflow_logs(workflow_run_id);
CREATE INDEX IF NOT EXISTS idx_workflow_logs_workflow_name ON workflow_logs(workflow_name);
CREATE INDEX IF NOT EXISTS idx_workflow_logs_task_id ON workflow_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_workflow_logs_persona_id ON workflow_logs(persona_id);
CREATE INDEX IF NOT EXISTS idx_workflow_logs_status ON workflow_logs(status);
CREATE INDEX IF NOT EXISTS idx_workflow_logs_started_at ON workflow_logs(started_at DESC);

-- Create workflow_node_logs table
CREATE TABLE IF NOT EXISTS workflow_node_logs (
    id SERIAL PRIMARY KEY,
    workflow_log_id INTEGER NOT NULL REFERENCES workflow_logs(id) ON DELETE CASCADE,
    node_name VARCHAR(100) NOT NULL,
    node_order INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    model_name VARCHAR(100),
    temperature FLOAT,
    max_tokens INTEGER,
    system_prompt TEXT,
    user_prompt TEXT,
    input_data JSONB,
    output_data JSONB,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    cost FLOAT,
    execution_time_ms INTEGER,
    error_message TEXT,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for workflow_node_logs
CREATE INDEX IF NOT EXISTS idx_workflow_node_logs_workflow_log_id ON workflow_node_logs(workflow_log_id);
CREATE INDEX IF NOT EXISTS idx_workflow_node_logs_node_name ON workflow_node_logs(node_name);
CREATE INDEX IF NOT EXISTS idx_workflow_node_logs_node_order ON workflow_node_logs(workflow_log_id, node_order);

-- Add comments for documentation
COMMENT ON TABLE workflow_logs IS 'Stores LLM workflow execution logs for observability and cost analysis';
COMMENT ON TABLE workflow_node_logs IS 'Stores individual node execution logs within LLM workflows';

COMMENT ON COLUMN workflow_logs.workflow_run_id IS 'Unique UUID for this workflow execution';
COMMENT ON COLUMN workflow_logs.workflow_name IS 'Name of the workflow (e.g., image_prompt_chain)';
COMMENT ON COLUMN workflow_logs.task_id IS 'Optional reference to generation_tasks.id';
COMMENT ON COLUMN workflow_logs.persona_id IS 'Optional reference to generation_results.id';
COMMENT ON COLUMN workflow_logs.input_data IS 'JSONB containing workflow input parameters';
COMMENT ON COLUMN workflow_logs.output_data IS 'JSONB containing workflow output/results';
COMMENT ON COLUMN workflow_logs.total_tokens IS 'Total tokens used across all nodes';
COMMENT ON COLUMN workflow_logs.total_cost IS 'Total cost in USD across all nodes';

COMMENT ON COLUMN workflow_node_logs.workflow_log_id IS 'Reference to parent workflow_logs.id';
COMMENT ON COLUMN workflow_node_logs.node_name IS 'Name of the node (e.g., generate_idea)';
COMMENT ON COLUMN workflow_node_logs.node_order IS 'Execution order of this node (0-indexed)';
COMMENT ON COLUMN workflow_node_logs.system_prompt IS 'System prompt sent to LLM';
COMMENT ON COLUMN workflow_node_logs.user_prompt IS 'User prompt sent to LLM';
COMMENT ON COLUMN workflow_node_logs.prompt_tokens IS 'Number of prompt tokens used';
COMMENT ON COLUMN workflow_node_logs.completion_tokens IS 'Number of completion tokens generated';
COMMENT ON COLUMN workflow_node_logs.cost IS 'Cost in USD for this node execution';
