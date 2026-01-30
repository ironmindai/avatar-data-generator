#!/usr/bin/env python3
"""
Avatar Data Generator - Task Processor Worker
STEP 1: DATA GENERATION ONLY

This module provides task processing functions for avatar generation:
1. Fetching pending tasks from the database with row-level locking
2. Calling Flowise API to generate persona data (names, bios)
3. Storing results in generation_results table
4. Updating task status to 'data-generated'

IMPORTANT: This worker handles ONLY the data generation step.
The image generation step will be implemented separately in a future version.

Status Flow:
    pending -> generating-data -> data-generated
    (Image generation: data-generated -> generating-images -> completed)

This module can be:
- Integrated into Flask app via APScheduler (recommended)
- Run as standalone systemd service (legacy)
"""

import os
import sys
import json
import logging
import requests
import time
import signal
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from flask import current_app
from models import db, GenerationTask, GenerationResult, Settings
from sqlalchemy import text

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Flowise Configuration
FLOWISE_URL = "https://flowise.electric-marinade.com/api/v1/prediction/71bf0c86-c802-4221-b6e7-0af16e350bb6"
FLOWISE_AUTH_TOKEN = "JJXI5CYV55QYkal9-uce7dyJfyKj3EeRkROOpBgxeO4"
FLOWISE_HEADERS = {
    "Authorization": f"Bearer {FLOWISE_AUTH_TOKEN}",
    "Content-Type": "application/json"
}

# Worker Configuration
MAX_BATCH_SIZE = 10
MULTITHREAD_COUNT = int(os.getenv('MULTITHREAD_FLOWISE', '5'))
REQUEST_TIMEOUT = 600  # 10 minutes timeout for Flowise requests

# Global flag for graceful shutdown (used in standalone mode)
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals (SIGTERM, SIGINT) for graceful shutdown."""
    global shutdown_requested
    logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
    shutdown_requested = True


def get_pending_task_with_lock() -> Optional[GenerationTask]:
    """
    Get a single pending task with PostgreSQL row-level locking.

    Uses SELECT ... FOR UPDATE SKIP LOCKED to ensure that when multiple
    workers are running, each gets a different task without conflicts.

    Returns:
        GenerationTask object or None if no tasks available
    """
    try:
        # Raw SQL query with row-level locking
        # FOR UPDATE locks the row
        # SKIP LOCKED makes other workers skip locked rows
        result = db.session.execute(
            text("""
                SELECT id FROM generation_tasks
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            """)
        ).fetchone()

        if result:
            task_id = result[0]
            # Fetch the actual task object
            task = GenerationTask.query.get(task_id)
            return task

        return None

    except Exception as e:
        logger.error(f"Error fetching pending task: {e}", exc_info=True)
        db.session.rollback()
        return None


def get_bio_settings() -> Dict[str, str]:
    """
    Fetch bio prompt settings from database.

    Returns:
        Dictionary with bio prompts for each platform
    """
    settings = {
        'bio_prompt_facebook': Settings.get_value('bio_prompt_facebook', ''),
        'bio_prompt_instagram': Settings.get_value('bio_prompt_instagram', ''),
        'bio_prompt_x': Settings.get_value('bio_prompt_x', ''),
        'bio_prompt_tiktok': Settings.get_value('bio_prompt_tiktok', '')
    }
    return settings


def calculate_batches(total: int) -> List[int]:
    """
    Split total number into batches of maximum MAX_BATCH_SIZE.

    Args:
        total: Total number of avatars to generate

    Returns:
        List of batch sizes. Example: 50 -> [20, 20, 10]
    """
    batches = []
    remaining = total

    while remaining > 0:
        batch_size = min(remaining, MAX_BATCH_SIZE)
        batches.append(batch_size)
        remaining -= batch_size

    logger.info(f"Split {total} avatars into {len(batches)} batches: {batches}")
    return batches


def call_flowise_api(
    app,
    task_id: str,
    task_db_id: int,
    batch_size: int,
    batch_number: int,
    persona_description: str,
    bio_language: str,
    settings: Dict[str, str]
) -> Tuple[int, Optional[List[Dict]], Optional[str]]:
    """
    Make API call to Flowise to generate persona data.

    This function runs in a thread pool and requires Flask app context
    for proper database access.

    Args:
        app: Flask application object for context
        task_id: Task ID string for logging
        task_db_id: Database ID of GenerationTask for storing results
        batch_size: Number of personas to generate in this batch
        batch_number: Batch identifier for tracking
        persona_description: Description of persona to generate
        bio_language: Language for bios
        settings: Dictionary with bio prompt settings

    Returns:
        Tuple of (batch_number, list of persona dicts or None, error message or None)
    """
    # Wrap entire function in app context to enable database access in threads
    with app.app_context():
        try:
            logger.info(f"[Task {task_id}] Batch {batch_number}: Requesting {batch_size} personas from Flowise...")

            # Build request payload
            payload = {
                "question": "go",
                "overrideConfig": {
                    "startState": {
                        "startAgentflow_0": [
                            {"key": "requested_amount", "value": str(batch_size)},
                            {"key": "persona_description", "value": persona_description},
                            {"key": "bio_language", "value": bio_language},
                            {"key": "instructions_facebook", "value": settings['bio_prompt_facebook']},
                            {"key": "instructions_instagram", "value": settings['bio_prompt_instagram']},
                            {"key": "instructions_x", "value": settings['bio_prompt_x']},
                            {"key": "instructions_tiktok", "value": settings['bio_prompt_tiktok']}
                        ]
                    }
                }
            }

            # Make request to Flowise
            start_time = time.time()
            response = requests.post(
                FLOWISE_URL,
                headers=FLOWISE_HEADERS,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )
            elapsed_time = time.time() - start_time

            # Check response status
            if response.status_code != 200:
                error_msg = f"Flowise API returned status {response.status_code}: {response.text}"
                logger.error(f"[Task {task_id}] Batch {batch_number}: {error_msg}")
                return (batch_number, None, error_msg)

            # Parse response
            response_data = response.json()
            logger.info(f"[Task {task_id}] Batch {batch_number}: Received response in {elapsed_time:.2f}s")

            # Extract text field containing newline-separated JSON objects
            text_content = response_data.get('text', '')
            if not text_content:
                error_msg = "Flowise response missing 'text' field"
                logger.error(f"[Task {task_id}] Batch {batch_number}: {error_msg}")
                return (batch_number, None, error_msg)

            # Parse newline-separated JSON objects
            personas = parse_flowise_response(text_content, batch_number, task_id)

            if not personas:
                error_msg = "Failed to parse any personas from Flowise response"
                logger.error(f"[Task {task_id}] Batch {batch_number}: {error_msg}")
                return (batch_number, None, error_msg)

            logger.info(f"[Task {task_id}] Batch {batch_number}: Successfully parsed {len(personas)} personas")
            return (batch_number, personas, None)

        except requests.exceptions.Timeout:
            error_msg = f"Request timed out after {REQUEST_TIMEOUT}s"
            logger.error(f"[Task {task_id}] Batch {batch_number}: {error_msg}")
            return (batch_number, None, error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(f"[Task {task_id}] Batch {batch_number}: {error_msg}")
            return (batch_number, None, error_msg)

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"[Task {task_id}] Batch {batch_number}: {error_msg}", exc_info=True)
            return (batch_number, None, error_msg)


def parse_flowise_response(text_content: str, batch_number: int, task_id: str) -> List[Dict]:
    """
    Parse Flowise response text containing multiple JSON objects.
    Uses brace-matching to correctly handle special characters.

    The response format is multiple JSON objects separated by newlines, where each
    object spans multiple lines like this:
    {
      "firstname": "Zephyra",
      "lastname": "Drake",
      "gender": "f",
      "bios": "{...}"
    }
    {
      "firstname": "Next",
      ...
    }

    This implementation uses brace-counting to correctly identify complete JSON
    objects, avoiding issues with special characters (emojis, apostrophes, quotes,
    newlines) that may appear in bios.

    Args:
        text_content: Raw text from Flowise response
        batch_number: Batch identifier for logging
        task_id: Task ID for logging

    Returns:
        List of parsed persona dictionaries
    """
    personas = []
    text = text_content.strip()

    i = 0
    obj_num = 0

    while i < len(text):
        # Skip whitespace
        while i < len(text) and text[i].isspace():
            i += 1

        if i >= len(text):
            break

        # Must start with '{'
        if text[i] != '{':
            logger.warning(f"[Task {task_id}] Batch {batch_number}: Expected '{{' at position {i}, got '{text[i]}'")
            break

        # Find matching closing brace using brace-counting
        brace_count = 0
        start = i
        in_string = False
        escape_next = False

        while i < len(text):
            char = text[i]

            if escape_next:
                escape_next = False
                i += 1
                continue

            if char == '\\':
                escape_next = True
                i += 1
                continue

            if char == '"':
                in_string = not in_string
            elif not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # Found complete JSON object
                        json_str = text[start:i+1]
                        obj_num += 1

                        try:
                            persona_data = json.loads(json_str)

                            # Validate required fields
                            required_fields = ['firstname', 'lastname', 'gender', 'bios']
                            if not all(field in persona_data for field in required_fields):
                                logger.warning(f"[Task {task_id}] Batch {batch_number}, Object {obj_num}: Missing required fields")
                                i += 1
                                break

                            # Parse bios field (it's a stringified JSON)
                            try:
                                bios_json = json.loads(persona_data['bios'])
                            except (json.JSONDecodeError, TypeError) as e:
                                logger.warning(f"[Task {task_id}] Batch {batch_number}, Object {obj_num}: Failed to parse bios JSON: {e}")
                                bios_json = {}

                            # Extract individual bios with fallbacks
                            persona = {
                                'firstname': persona_data['firstname'],
                                'lastname': persona_data['lastname'],
                                'gender': persona_data['gender'],
                                'bio_facebook': bios_json.get('facebook_bio', ''),
                                'bio_instagram': bios_json.get('instagram_bio', ''),
                                'bio_x': bios_json.get('x_bio', ''),
                                'bio_tiktok': bios_json.get('tiktok_bio', '')
                            }

                            personas.append(persona)
                            logger.debug(f"[Task {task_id}] Batch {batch_number}, Object {obj_num}: Parsed {persona['firstname']} {persona['lastname']}")

                        except json.JSONDecodeError as e:
                            logger.warning(f"[Task {task_id}] Batch {batch_number}, Object {obj_num}: JSON parse error: {e}")
                        except Exception as e:
                            logger.warning(f"[Task {task_id}] Batch {batch_number}, Object {obj_num}: Unexpected error: {e}")

                        i += 1
                        break

            i += 1

    logger.info(f"[Task {task_id}] Batch {batch_number}: Parsed {len(personas)} personas from response")
    return personas


def store_results(task_db_id: int, batch_number: int, personas: List[Dict]) -> int:
    """
    Store persona results in database.

    Args:
        task_db_id: Database ID (integer, not task_id string) of GenerationTask
        batch_number: Batch identifier
        personas: List of persona dictionaries to store

    Returns:
        Number of personas stored successfully
    """
    stored_count = 0

    try:
        for persona in personas:
            result = GenerationResult(
                task_id=task_db_id,
                batch_number=batch_number,
                firstname=persona['firstname'],
                lastname=persona['lastname'],
                gender=persona['gender'],
                bio_facebook=persona['bio_facebook'],
                bio_instagram=persona['bio_instagram'],
                bio_x=persona['bio_x'],
                bio_tiktok=persona['bio_tiktok']
            )
            db.session.add(result)
            stored_count += 1

        db.session.commit()
        logger.info(f"[Task DB ID {task_db_id}] Batch {batch_number}: Stored {stored_count} results in database")

    except Exception as e:
        db.session.rollback()
        logger.error(f"[Task DB ID {task_db_id}] Batch {batch_number}: Database error while storing results: {e}", exc_info=True)
        return 0

    return stored_count


def process_single_task() -> bool:
    """
    Process a single pending task from the database.

    This function is designed to be called by APScheduler periodically.
    It uses database row-level locking to prevent conflicts when multiple
    workers are running simultaneously.

    Returns:
        True if a task was processed, False if no tasks available
    """
    try:
        # Get a pending task with row-level lock
        task = get_pending_task_with_lock()

        if not task:
            # No pending tasks available
            return False

        logger.info(f"=" * 80)
        logger.info(f"Processing Task: {task.task_id}")
        logger.info(f"User ID: {task.user_id}")
        logger.info(f"Persona: {task.persona_description[:100]}...")
        logger.info(f"Language: {task.bio_language}")
        logger.info(f"Number to Generate: {task.number_to_generate}")
        logger.info(f"Images per Persona: {task.images_per_persona}")
        logger.info(f"=" * 80)

        # Update task status to 'generating-data'
        task.update_status('generating-data')
        db.session.commit()
        logger.info(f"[Task {task.task_id}] Status updated to 'generating-data'")

        # Fetch bio settings
        settings = get_bio_settings()
        logger.info(f"[Task {task.task_id}] Fetched bio prompt settings")

        # Calculate batches
        batches = calculate_batches(task.number_to_generate)

        # Get current app for thread context
        app = current_app._get_current_object()

        # Extract task data to avoid lazy loading issues in threads
        task_id_str = task.task_id
        task_db_id = task.id
        persona_description = task.persona_description
        bio_language = task.bio_language

        # Process batches in parallel using ThreadPoolExecutor
        logger.info(f"[Task {task.task_id}] Starting parallel batch processing with {MULTITHREAD_COUNT} threads")

        all_results = []
        error_logs = []

        with ThreadPoolExecutor(max_workers=MULTITHREAD_COUNT) as executor:
            # Submit all batch jobs with app context and extracted data
            future_to_batch = {
                executor.submit(
                    call_flowise_api,
                    app,                    # Flask app for context
                    task_id_str,            # Task ID string for logging
                    task_db_id,             # Database ID for storing results
                    batch_size,             # Batch size
                    batch_num + 1,          # 1-indexed batch numbers
                    persona_description,    # Extracted persona description
                    bio_language,           # Extracted bio language
                    settings                # Bio prompt settings
                ): (batch_num + 1, batch_size)
                for batch_num, batch_size in enumerate(batches)
            }

            # Collect results as they complete
            for future in as_completed(future_to_batch):
                batch_num, batch_size = future_to_batch[future]

                try:
                    batch_number, personas, error = future.result()

                    if error:
                        error_logs.append(f"Batch {batch_number}: {error}")
                        logger.error(f"[Task {task_id_str}] Batch {batch_number} failed: {error}")
                    elif personas:
                        # Store results immediately
                        stored_count = store_results(task_db_id, batch_number, personas)
                        all_results.append({
                            'batch': batch_number,
                            'requested': batch_size,
                            'received': len(personas),
                            'stored': stored_count
                        })
                    else:
                        error_logs.append(f"Batch {batch_number}: No personas returned")

                except Exception as e:
                    error_logs.append(f"Batch {batch_num}: Exception during processing: {str(e)}")
                    logger.error(f"[Task {task_id_str}] Batch {batch_num} exception: {e}", exc_info=True)

        # Analyze results
        logger.info(f"[Task {task.task_id}] Batch processing completed")
        logger.info(f"[Task {task.task_id}] Successful batches: {len(all_results)}/{len(batches)}")

        if error_logs:
            logger.warning(f"[Task {task.task_id}] Errors encountered:")
            for error_log in error_logs:
                logger.warning(f"  - {error_log}")

        # Count total stored results
        total_stored = sum(result['stored'] for result in all_results)
        logger.info(f"[Task {task.task_id}] Total personas stored: {total_stored}/{task.number_to_generate}")

        # Update final task status
        if total_stored == 0:
            # Complete failure
            task.status = 'failed'
            task.error_log = "All batches failed. Errors:\n" + "\n".join(error_logs)
            task.updated_at = datetime.utcnow()
            logger.error(f"[Task {task.task_id}] Task FAILED - no results stored")
        else:
            # At least partial success - mark as 'data-generated'
            # NOTE: Status is 'data-generated', NOT 'completed'
            # Image generation will be implemented in a separate step
            task.status = 'data-generated'
            task.updated_at = datetime.utcnow()

            if error_logs:
                # Store partial failure info
                task.error_log = f"Partial success: {total_stored}/{task.number_to_generate} personas generated.\nErrors:\n" + "\n".join(error_logs)

            logger.info(f"[Task {task.task_id}] Task completed successfully - status set to 'data-generated'")
            logger.info(f"[Task {task.task_id}] NEXT STEP: Image generation (to be implemented)")

        db.session.commit()
        return True

    except Exception as e:
        logger.error(f"Fatal error during task processing: {e}", exc_info=True)
        db.session.rollback()
        return False


# ===========================
# LEGACY STANDALONE MODE
# ===========================
# Below code is for running as a standalone systemd service
# This is deprecated in favor of APScheduler integration

class TaskProcessor:
    """Legacy task processor class for standalone mode."""

    def __init__(self, app):
        """Initialize task processor with Flask app context."""
        self.app = app

    def run(self):
        """Main worker loop - continuously process pending tasks."""
        global shutdown_requested

        SLEEP_INTERVAL = int(os.getenv('WORKER_SLEEP_INTERVAL', '30'))

        logger.info("=" * 80)
        logger.info("Avatar Data Generator - Task Processor Worker Started (STANDALONE MODE)")
        logger.info(f"Multithread count: {MULTITHREAD_COUNT}")
        logger.info(f"Max batch size: {MAX_BATCH_SIZE}")
        logger.info(f"Request timeout: {REQUEST_TIMEOUT}s")
        logger.info(f"Sleep interval: {SLEEP_INTERVAL}s")
        logger.info("=" * 80)

        # Continuous loop until shutdown requested
        while not shutdown_requested:
            try:
                with self.app.app_context():
                    # Process a single task
                    processed = process_single_task()

                    if not processed:
                        logger.debug("No pending tasks found. Sleeping...")

                # Short sleep before checking for next task
                if not shutdown_requested:
                    logger.debug(f"Sleeping for {SLEEP_INTERVAL}s before next check...")
                    time.sleep(SLEEP_INTERVAL)

            except KeyboardInterrupt:
                logger.info("Received KeyboardInterrupt. Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main worker loop: {e}", exc_info=True)
                logger.info(f"Sleeping for {SLEEP_INTERVAL}s before retry...")
                time.sleep(SLEEP_INTERVAL)

        logger.info("=" * 80)
        logger.info("Task Processor Worker Shutting Down")
        logger.info("=" * 80)


def main():
    """Main entry point for standalone worker mode (LEGACY)."""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Import create_app here to avoid circular imports
    from app import create_app

    # Create Flask app
    app = create_app()

    # Create and run task processor
    processor = TaskProcessor(app)
    processor.run()


if __name__ == '__main__':
    main()
