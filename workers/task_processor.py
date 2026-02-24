#!/usr/bin/env python3
"""
Avatar Data Generator - Task Processor Worker
COMPLETE DATA + IMAGE GENERATION

This module provides task processing functions for avatar generation:
1. Fetching pending tasks from the database with row-level locking
2. Calling Flowise API to generate persona data (names, bios)
3. Storing results in generation_results table
4. Updating task status to 'data-generated'
5. Generating images for each persona using OpenAI
6. Uploading images to S3 storage
7. Updating task status to 'completed'

Status Flow:
    pending -> generating-data -> data-generated -> generating-images -> completed

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
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from flask import current_app
from models import db, GenerationTask, GenerationResult, Settings, Config, IntConfig
from sqlalchemy import text

# Import service modules for image generation
from services.flowise_service import generate_image_prompt
from services.image_generation import generate_base_image  # Still used for base image
from services.image_prompt_chain import get_prompt_chain  # NEW: Local LLM chain for prompts
from services.seedream_service import generate_image_with_reference  # NEW: SeeDream for images
from services.image_utils import upload_to_s3, generate_presigned_url
from services.s3_styles import get_random_style_image  # NEW: Random style image for dual-reference
from utils.image_cropper import remove_white_borders
from utils.image_style_randomizer import randomize_image_style

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
CONCURRENT_PERSONA_LIMIT = int(os.getenv('CONCURRENT_PERSONA_LIMIT', '15'))  # Parallel persona processing

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


def get_data_generated_task_with_lock() -> Optional[GenerationTask]:
    """
    Get a single task with status='data-generated' for image generation.

    Uses SELECT ... FOR UPDATE SKIP LOCKED to ensure that when multiple
    workers are running, each gets a different task without conflicts.

    Returns:
        GenerationTask object or None if no tasks available
    """
    try:
        # Raw SQL query with row-level locking
        result = db.session.execute(
            text("""
                SELECT id FROM generation_tasks
                WHERE status = 'data-generated'
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
        logger.error(f"Error fetching data-generated task: {e}", exc_info=True)
        db.session.rollback()
        return None


def recover_stuck_tasks(stuck_threshold_minutes: int = 15, check_incomplete_completed: bool = False) -> int:
    """
    Detect and recover tasks that are stuck in processing states.

    Tasks are considered stuck if they've been in 'generating-data' or
    'generating-images' status for longer than the threshold without updates.

    Args:
        stuck_threshold_minutes: Minutes without updates before considering stuck (default: 15)
        check_incomplete_completed: Also check 'completed' tasks with incomplete images (default: False)

    Returns:
        Number of tasks recovered
    """
    try:
        from datetime import timedelta

        threshold_time = datetime.utcnow() - timedelta(minutes=stuck_threshold_minutes)
        recovered_count = 0

        # Check for "completed" tasks that are actually incomplete (startup recovery only)
        if check_incomplete_completed:
            completed_tasks = GenerationTask.query.filter(
                GenerationTask.status == 'completed'
            ).all()

            for task in completed_tasks:
                results = GenerationResult.query.filter_by(task_id=task.id).all()
                if results:
                    personas_with_images = sum(1 for r in results if r.images and len(r.images) > 0)
                    total_personas = len(results)

                    if personas_with_images < total_personas:
                        logger.warning(f"[Task {task.task_id}] INCOMPLETE: Marked as 'completed' but only {personas_with_images}/{total_personas} have images. Resetting to 'data-generated'.")
                        task.status = 'data-generated'
                        task.completed_at = None
                        task.updated_at = datetime.utcnow()
                        task.error_log = (task.error_log or '') + f"\n[{datetime.utcnow().isoformat()}] Task was incomplete and auto-recovered by system startup."
                        recovered_count += 1

        # Find tasks stuck in 'generating-data' status
        stuck_data_tasks = GenerationTask.query.filter(
            GenerationTask.status == 'generating-data',
            GenerationTask.updated_at < threshold_time
        ).all()

        for task in stuck_data_tasks:
            logger.warning(f"[Task {task.task_id}] STUCK in 'generating-data' for {stuck_threshold_minutes}+ minutes. Resetting to 'pending'.")
            task.status = 'pending'
            task.updated_at = datetime.utcnow()
            task.error_log = (task.error_log or '') + f"\n[{datetime.utcnow().isoformat()}] Task was stuck and auto-recovered by system."
            recovered_count += 1

        # Find tasks stuck in 'generating-images' status
        stuck_image_tasks = GenerationTask.query.filter(
            GenerationTask.status == 'generating-images',
            GenerationTask.updated_at < threshold_time
        ).all()

        for task in stuck_image_tasks:
            # Check progress: count personas with images vs total personas
            results = GenerationResult.query.filter_by(task_id=task.id).all()

            if not results:
                logger.warning(f"[Task {task.task_id}] STUCK in 'generating-images' with no data. Resetting to 'pending'.")
                task.status = 'pending'
            else:
                # Count how many personas have images
                personas_with_images = sum(1 for r in results if r.images and len(r.images) > 0)
                total_personas = len(results)

                if personas_with_images == total_personas:
                    # All personas have images - mark as completed!
                    logger.info(f"[Task {task.task_id}] STUCK task has all images complete ({personas_with_images}/{total_personas}). Marking as completed.")
                    task.status = 'completed'
                    task.completed_at = datetime.utcnow()
                else:
                    # Some personas missing images - reset to 'data-generated' for retry
                    logger.warning(f"[Task {task.task_id}] STUCK in 'generating-images' ({personas_with_images}/{total_personas} with images). Resetting to 'data-generated'.")
                    task.status = 'data-generated'

            task.updated_at = datetime.utcnow()
            task.error_log = (task.error_log or '') + f"\n[{datetime.utcnow().isoformat()}] Task was stuck and auto-recovered by system."
            recovered_count += 1

        if recovered_count > 0:
            db.session.commit()
            logger.info(f"Recovered {recovered_count} stuck task(s)")

        return recovered_count

    except Exception as e:
        logger.error(f"Error recovering stuck tasks: {e}", exc_info=True)
        db.session.rollback()
        return 0


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
                                'ethnicity': persona_data.get('ethnicity'),  # Root level field
                                'age': bios_json.get('age'),  # Inside bios JSON
                                'bio_facebook': bios_json.get('facebook_bio', ''),
                                'bio_instagram': bios_json.get('instagram_bio', ''),
                                'bio_x': bios_json.get('x_bio', ''),
                                'bio_tiktok': bios_json.get('tiktok_bio', ''),
                                'job_title': bios_json.get('job_title', ''),
                                'workplace': bios_json.get('workplace', ''),
                                'edu_establishment': bios_json.get('edu_establishment', ''),
                                'edu_study': bios_json.get('edu_study', ''),
                                'current_city': bios_json.get('current_city', ''),
                                'current_state': bios_json.get('current_state', ''),
                                'prev_city': bios_json.get('prev_city', ''),
                                'prev_state': bios_json.get('prev_state', ''),
                                'about': bios_json.get('about', '')
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
                ethnicity=persona.get('ethnicity'),
                age=persona.get('age'),
                bio_facebook=persona['bio_facebook'],
                bio_instagram=persona['bio_instagram'],
                bio_x=persona['bio_x'],
                bio_tiktok=persona['bio_tiktok'],
                job_title=persona['job_title'],
                workplace=persona['workplace'],
                edu_establishment=persona['edu_establishment'],
                edu_study=persona['edu_study'],
                current_city=persona['current_city'],
                current_state=persona['current_state'],
                prev_city=persona['prev_city'],
                prev_state=persona['prev_state'],
                about=persona['about']
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


async def process_persona_images(
    task_id_str: str,
    task_db_id: int,
    result: GenerationResult,
    images_per_persona: int
) -> Tuple[bool, Optional[str]]:
    """
    Process image generation for a single persona with multi-batch support.

    This function handles the complete image generation workflow with immediate saves:
    1. Check if base image exists (resumption support)
    2. Generate base selfie image using OpenAI (if not exists)
    3. Upload base image to S3 and SAVE IMMEDIATELY
    4. Check if images already exist (resumption support)
    5. Loop through batches (4, 8, 12, 16, or 20 images = 1-5 batches):
       - Generate image prompt from person data using Flowise (with prompts_history)
       - Generate 4-image grid from SAME base image
       - Split grid into 4 individual images
       - Apply post-processing (crop, randomize) to all 4 images
       - Collect images and prompts for next iteration
    6. Upload ALL images to S3 and SAVE IMMEDIATELY to JSONB array

    Args:
        task_id_str: Task ID string for logging
        task_db_id: Database ID of GenerationTask
        result: GenerationResult object containing persona data
        images_per_persona: Number of images to generate (4, 8, 12, 16, or 20)

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    from sqlalchemy.orm.attributes import flag_modified

    try:
        persona_name = f"{result.firstname} {result.lastname}"
        logger.info(f"[Task {task_id_str}] Processing images for persona: {persona_name} (result_id={result.id})")
        logger.info(f"[Task {task_id_str}] [{persona_name}] Images per persona: {images_per_persona}")

        # Validate images_per_persona (now supports 1-20 instead of multiples of 4)
        if images_per_persona < 1 or images_per_persona > 20:
            error_msg = f"Invalid images_per_persona: {images_per_persona}. Must be between 1 and 20."
            logger.error(f"[Task {task_id_str}] [{persona_name}] {error_msg}")
            return False, error_msg

        logger.info(f"[Task {task_id_str}] [{persona_name}] Will generate {images_per_persona} individual images")

        # Step 0: Fetch face randomization settings from Config table
        randomize_face = Config.get_value('randomize_face_base', False)
        randomize_face_gender_lock = Config.get_value('randomize_face_gender_lock', False)

        logger.info(f"[Task {task_id_str}] [{persona_name}] Face randomization settings:")
        logger.info(f"[Task {task_id_str}] [{persona_name}] - randomize_face_base: {randomize_face}")
        logger.info(f"[Task {task_id_str}] [{persona_name}] - randomize_face_gender_lock: {randomize_face_gender_lock}")

        # Step 1: Check if base image already exists (resumption support)
        base_image_bytes = None

        if result.base_image_url:
            logger.info(f"[Task {task_id_str}] [{persona_name}] Base image already exists: {result.base_image_url}")
            logger.info(f"[Task {task_id_str}] [{persona_name}] Skipping base image generation (resumption mode)")
            # Note: We don't download the base image here unless needed for grid generation
            # The base image will be regenerated if needed
        else:
            # Step 2: Generate base selfie image ONCE
            logger.info(f"[Task {task_id_str}] [{persona_name}] Step 1/3: Generating base selfie image...")

            try:
                base_image_bytes = await generate_base_image(
                    bio_facebook=result.bio_facebook or '',
                    gender=result.gender,
                    randomize_face=randomize_face,
                    randomize_face_gender_lock=randomize_face_gender_lock,
                    ethnicity=result.ethnicity,
                    age=result.age
                )
                if not base_image_bytes:
                    raise Exception("OpenAI returned empty image")
                logger.info(f"[Task {task_id_str}] [{persona_name}] Base image generated ({len(base_image_bytes)} bytes)")
            except Exception as e:
                error_msg = f"Base image generation failed: {str(e)}"
                logger.error(f"[Task {task_id_str}] [{persona_name}] {error_msg}")
                return False, error_msg

            # Step 3: Upload base image to S3 and SAVE IMMEDIATELY
            logger.info(f"[Task {task_id_str}] [{persona_name}] Step 2/3: Uploading base image to S3...")

            base_object_key = f"avatars/task_{task_db_id}/persona_{result.id}/base.png"

            try:
                _, base_image_url = upload_to_s3(base_image_bytes, base_object_key)
                logger.info(f"[Task {task_id_str}] [{persona_name}] Base image uploaded: {base_image_url}")

                # SAVE IMMEDIATELY to database
                result.base_image_url = base_image_url
                db.session.commit()
                logger.info(f"[Task {task_id_str}] [{persona_name}] SAVED base_image_url to database immediately")

            except Exception as e:
                error_msg = f"Base image S3 upload failed: {str(e)}"
                logger.error(f"[Task {task_id_str}] [{persona_name}] {error_msg}")
                db.session.rollback()
                return False, error_msg

        # Step 4: Check if images already exist (resumption support)
        if result.images and len(result.images) >= images_per_persona:
            logger.info(f"[Task {task_id_str}] [{persona_name}] Images already exist ({len(result.images)} images, need {images_per_persona})")
            logger.info(f"[Task {task_id_str}] [{persona_name}] Skipping image generation (resumption mode)")
            logger.info(f"[Task {task_id_str}] [{persona_name}] Image processing completed successfully (from cache)!")
            return True, None

        # If we didn't generate base image earlier (resumption mode), generate it now for grid
        if not base_image_bytes:
            logger.info(f"[Task {task_id_str}] [{persona_name}] Regenerating base image for grid generation...")
            try:
                base_image_bytes = await generate_base_image(
                    bio_facebook=result.bio_facebook or '',
                    gender=result.gender,
                    randomize_face=randomize_face,
                    randomize_face_gender_lock=randomize_face_gender_lock,
                    ethnicity=result.ethnicity,
                    age=result.age
                )
                if not base_image_bytes:
                    raise Exception("OpenAI returned empty image")
                logger.info(f"[Task {task_id_str}] [{persona_name}] Base image regenerated ({len(base_image_bytes)} bytes)")
            except Exception as e:
                error_msg = f"Base image regeneration failed: {str(e)}"
                logger.error(f"[Task {task_id_str}] [{persona_name}] {error_msg}")
                return False, error_msg

        # Step 3: Parallel Individual Image Generation
        logger.info(f"[Task {task_id_str}] [{persona_name}] Step 3/3: Starting parallel image generation ({images_per_persona} images)...")
        logger.info("=" * 80)
        logger.info(f"BASE IMAGE S3 URL (will be used as reference for ALL images):")
        logger.info(f"{result.base_image_url}")
        logger.info("=" * 80)

        # Fetch post-processing settings (apply consistently to all images)
        crop_white_borders_enabled = Config.get_value('crop_white_borders', False)
        randomize_image_style_enabled = Config.get_value('randomize_image_style', False)

        logger.info(f"[Task {task_id_str}] [{persona_name}] Post-processing settings:")
        logger.info(f"[Task {task_id_str}] [{persona_name}] - crop_white_borders: {crop_white_borders_enabled}")
        logger.info(f"[Task {task_id_str}] [{persona_name}] - randomize_image_style: {randomize_image_style_enabled}")

        person_data = {
            'firstname': result.firstname,
            'lastname': result.lastname,
            'gender': result.gender,
            'bio_facebook': result.bio_facebook or '',
            'bio_instagram': result.bio_instagram or '',
            'bio_x': result.bio_x or '',
            'bio_tiktok': result.bio_tiktok or '',
            'ethnicity': result.ethnicity or '',
            'age': result.age
        }

        # ===== PHASE 1: Generate ALL Prompts Using Local LLM Chain =====
        logger.info(f"[Task {task_id_str}] [{persona_name}] PHASE 1: Generating {images_per_persona} prompts using local LLM chain...")

        try:
            # Get the prompt chain instance
            prompt_chain = get_prompt_chain()

            # Load existing image ideas history to avoid duplicates
            existing_history = result.image_ideas_history or []
            if existing_history:
                logger.info(f"[Task {task_id_str}] [{persona_name}] Found {len(existing_history)} previous image ideas to avoid")
                logger.debug(f"[Task {task_id_str}] [{persona_name}] Previous ideas: {existing_history}")

            # Generate all prompts at once (chain handles history internally)
            # Returns: (final_prompts, image_ideas)
            prompts, new_ideas = await prompt_chain.generate_image_prompts(
                person_data=person_data,
                num_images=images_per_persona,
                prompts_history=existing_history,  # Pass history to avoid duplicates
                task_id=task_db_id,  # Pass task ID for workflow logging
                persona_id=result.id  # Pass persona ID for workflow logging
            )

            if not prompts or len(prompts) != images_per_persona:
                raise Exception(f"Expected {images_per_persona} prompts, got {len(prompts) if prompts else 0}")

            logger.info(f"[Task {task_id_str}] [{persona_name}] PHASE 1 COMPLETE: Generated {len(prompts)} prompts with {len(new_ideas)} new ideas")
            logger.debug(f"[Task {task_id_str}] [{persona_name}] New ideas: {new_ideas}")

        except Exception as e:
            error_msg = f"LLM prompt chain failed: {str(e)}"
            logger.error(f"[Task {task_id_str}] [{persona_name}] {error_msg}")
            return False, error_msg

        # ===== PHASE 2: Generate Individual Images with SeeDream =====
        logger.info(f"[Task {task_id_str}] [{persona_name}] PHASE 2: Generating {images_per_persona} individual images with SeeDream...")

        # Generate presigned URL for base image (SeeDream needs to download it)
        logger.info(f"[Task {task_id_str}] [{persona_name}] Generating presigned URL for base image...")
        try:
            # Extract object key from base_image_url
            # URL format: {S3_PUBLIC_URL_BASE}/{bucket}/{object_key}
            base_image_parts = result.base_image_url.split('/')
            bucket_index = base_image_parts.index(os.getenv('S3_BUCKET_NAME'))
            base_image_key = '/'.join(base_image_parts[bucket_index + 1:])

            # Generate presigned URL (1 hour expiry)
            base_image_presigned_url = generate_presigned_url(base_image_key, expiration=3600)
            logger.info(f"[Task {task_id_str}] [{persona_name}] Presigned URL generated: {base_image_presigned_url[:100]}...")

        except Exception as e:
            error_msg = f"Failed to generate presigned URL for base image: {str(e)}"
            logger.error(f"[Task {task_id_str}] [{persona_name}] {error_msg}")
            return False, error_msg

        # Generate each image individually with SeeDream
        async def generate_single_image(image_index: int, prompt: str) -> str:
            """
            Generate a single image using SeeDream with dual-reference (base + style).

            Args:
                image_index: Image index (0-indexed)
                prompt: Image generation prompt

            Returns:
                S3 image URL
            """
            # Fetch random style reference image for THIS specific image
            style_image_url = None
            try:
                style_image_url = get_random_style_image()
                if style_image_url:
                    logger.info(f"[Task {task_id_str}] [{persona_name}] [Image {image_index + 1}] Using style: {style_image_url[:80]}...")
            except Exception as e:
                logger.warning(f"[Task {task_id_str}] [{persona_name}] [Image {image_index + 1}] Failed to fetch style: {e}")

            mode_str = "dual-reference" if style_image_url else "single-reference"
            logger.info(f"[Task {task_id_str}] [{persona_name}] [Image {image_index + 1}/{images_per_persona}] Generating with SeeDream ({mode_str})...")

            try:
                # Generate image with SeeDream using dual-reference if style image available
                image_bytes = await generate_image_with_reference(
                    prompt=prompt,
                    base_image_url=base_image_presigned_url,
                    style_image_url=style_image_url  # NEW: Pass style image for dual-reference
                )
                if not image_bytes:
                    raise Exception("SeeDream returned empty image")

                logger.info(f"[Task {task_id_str}] [{persona_name}] [Image {image_index + 1}/{images_per_persona}] Generated ({len(image_bytes)} bytes)")

                # Apply post-processing if enabled
                processed_bytes = image_bytes

                # Conditionally crop white borders
                if crop_white_borders_enabled:
                    try:
                        processed_bytes = remove_white_borders(processed_bytes, threshold=220, min_border_width=1)
                        logger.debug(f"[Task {task_id_str}] [{persona_name}] [Image {image_index + 1}] Cropped borders: {len(image_bytes)} -> {len(processed_bytes)} bytes")
                    except Exception as e:
                        logger.warning(f"[Task {task_id_str}] [{persona_name}] [Image {image_index + 1}] Border cropping failed: {str(e)}")

                # Conditionally apply style randomization
                if randomize_image_style_enabled:
                    try:
                        processed_bytes = randomize_image_style(processed_bytes)
                        logger.debug(f"[Task {task_id_str}] [{persona_name}] [Image {image_index + 1}] Style randomized")
                    except Exception as e:
                        logger.warning(f"[Task {task_id_str}] [{persona_name}] [Image {image_index + 1}] Style randomization failed: {str(e)}")

                # Upload to S3
                object_key = f"avatars/task_{task_db_id}/persona_{result.id}/image_{image_index}.png"
                _, image_url = upload_to_s3(processed_bytes, object_key)

                logger.info(f"[Task {task_id_str}] [{persona_name}] [Image {image_index + 1}/{images_per_persona}] Uploaded: {image_url}")
                return image_url

            except Exception as e:
                error_msg = f"Image generation failed for image {image_index + 1}: {str(e)}"
                logger.error(f"[Task {task_id_str}] [{persona_name}] {error_msg}")
                raise Exception(error_msg)

        # Generate all images in parallel
        image_tasks = [
            generate_single_image(i, prompts[i])
            for i in range(images_per_persona)
        ]

        try:
            all_image_urls = await asyncio.gather(*image_tasks)
        except Exception as e:
            error_msg = f"Parallel image generation failed: {str(e)}"
            logger.error(f"[Task {task_id_str}] [{persona_name}] {error_msg}")
            return False, error_msg

        logger.info(f"[Task {task_id_str}] [{persona_name}] PHASE 2 COMPLETE: Generated {len(all_image_urls)} images with SeeDream")

        # Step 6: Save ALL images AND image ideas history to database IMMEDIATELY
        logger.info(f"[Task {task_id_str}] [{persona_name}] Saving {len(all_image_urls)} images and updating history...")

        try:
            # Save image URLs
            result.images = all_image_urls
            flag_modified(result, 'images')

            # Update image ideas history (append new ideas to existing)
            updated_history = existing_history + new_ideas
            result.image_ideas_history = updated_history
            flag_modified(result, 'image_ideas_history')

            db.session.commit()
            logger.info(f"[Task {task_id_str}] [{persona_name}] SAVED {len(all_image_urls)} images to database")
            logger.info(f"[Task {task_id_str}] [{persona_name}] UPDATED history: {len(existing_history)} → {len(updated_history)} total ideas")
        except Exception as e:
            error_msg = f"Database update failed: {str(e)}"
            logger.error(f"[Task {task_id_str}] [{persona_name}] {error_msg}")
            db.session.rollback()
            return False, error_msg

        logger.info(f"[Task {task_id_str}] [{persona_name}] Image processing completed successfully!")
        logger.info(f"[Task {task_id_str}] [{persona_name}] Total images generated: {len(all_image_urls)}")
        return True, None

    except Exception as e:
        error_msg = f"Unexpected error during image processing: {str(e)}"
        logger.error(f"[Task {task_id_str}] [{persona_name}] {error_msg}", exc_info=True)
        return False, error_msg


def process_image_generation() -> bool:
    """
    Process image generation for a single task with status='data-generated'.

    This function is designed to be called by APScheduler periodically.
    It finds tasks that have completed data generation and processes
    images for all personas in the task sequentially.

    Returns:
        True if a task was processed, False if no tasks available
    """
    try:
        # Get a task with data-generated status
        task = get_data_generated_task_with_lock()

        if not task:
            # No tasks ready for image generation
            return False

        logger.info(f"=" * 80)
        logger.info(f"Processing Image Generation for Task: {task.task_id}")
        logger.info(f"User ID: {task.user_id}")
        logger.info(f"Number of Personas: {task.number_to_generate}")
        logger.info(f"=" * 80)

        # Update task status to 'generating-images'
        task.update_status('generating-images')
        db.session.commit()
        logger.info(f"[Task {task.task_id}] Status updated to 'generating-images'")

        # Get all results for this task
        results = GenerationResult.query.filter_by(task_id=task.id).all()

        if not results:
            logger.error(f"[Task {task.task_id}] No results found for image generation")
            task.status = 'failed'
            task.error_log = "No persona data found for image generation"
            task.updated_at = datetime.utcnow()
            db.session.commit()
            return True

        logger.info(f"[Task {task.task_id}] Found {len(results)} personas to process")
        logger.info(f"[Task {task.task_id}] Images per persona: {task.images_per_persona}")
        logger.info(f"[Task {task.task_id}] Concurrent persona limit: {CONCURRENT_PERSONA_LIMIT}")

        # Process personas in parallel with concurrency limit
        # OpenAI Tier 3: 50 images/min for gpt-image-1, so we can safely do 15-20 concurrent personas
        success_count = 0
        error_logs = []

        async def process_persona_with_semaphore(semaphore: asyncio.Semaphore, idx: int, result):
            """Process a single persona with semaphore-based concurrency control."""
            persona_name = f"{result.firstname} {result.lastname}"

            async with semaphore:  # Limit concurrent executions
                logger.info(f"[Task {task.task_id}] Processing persona {idx}/{len(results)}: {persona_name}")

                try:
                    success, error_msg = await process_persona_images(
                        task.task_id, task.id, result, task.images_per_persona
                    )

                    if success:
                        logger.info(f"[Task {task.task_id}] [{persona_name}] SUCCESS")
                        return {'success': True, 'persona_name': persona_name, 'persona_id': result.id}
                    else:
                        logger.error(f"[Task {task.task_id}] [{persona_name}] FAILED: {error_msg}")
                        return {
                            'success': False,
                            'persona_name': persona_name,
                            'persona_id': result.id,
                            'error': error_msg
                        }

                except Exception as e:
                    error_msg = f"Exception during image processing: {str(e)}"
                    logger.error(f"[Task {task.task_id}] [{persona_name}] EXCEPTION: {error_msg}", exc_info=True)
                    return {
                        'success': False,
                        'persona_name': persona_name,
                        'persona_id': result.id,
                        'error': error_msg
                    }

        # Create event loop and run parallel processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Create semaphore to limit concurrent persona processing
        semaphore = asyncio.Semaphore(CONCURRENT_PERSONA_LIMIT)

        # Create tasks for all personas
        persona_tasks = [
            process_persona_with_semaphore(semaphore, idx, result)
            for idx, result in enumerate(results, 1)
        ]

        # Run all tasks in parallel (limited by semaphore)
        logger.info(f"[Task {task.task_id}] Starting parallel persona processing...")
        persona_results = loop.run_until_complete(asyncio.gather(*persona_tasks))
        loop.close()

        # Process results
        for result in persona_results:
            if result['success']:
                success_count += 1
            else:
                error_logs.append(f"Persona {result['persona_name']} (ID {result['persona_id']}): {result['error']}")

        logger.info(f"[Task {task.task_id}] Parallel processing completed: {success_count}/{len(results)} succeeded")

        # Update final task status
        logger.info(f"[Task {task.task_id}] Image generation completed")
        logger.info(f"[Task {task.task_id}] Success: {success_count}/{len(results)} personas")

        if error_logs:
            logger.warning(f"[Task {task.task_id}] Errors encountered:")
            for error_log in error_logs:
                logger.warning(f"  - {error_log}")

        if success_count == 0:
            # Complete failure
            task.status = 'failed'
            task.error_log = f"All image generation failed. Errors:\n" + "\n".join(error_logs)
            task.updated_at = datetime.utcnow()
            logger.error(f"[Task {task.task_id}] Task FAILED - no images generated")
        elif success_count == len(results):
            # Complete success
            task.status = 'completed'
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()
            logger.info(f"[Task {task.task_id}] Task COMPLETED successfully - all images generated")
        else:
            # Partial success
            task.status = 'completed'
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()
            task.error_log = f"Partial success: {success_count}/{len(results)} personas with images.\nErrors:\n" + "\n".join(error_logs)
            logger.warning(f"[Task {task.task_id}] Task COMPLETED with partial success - {success_count}/{len(results)} images generated")

        db.session.commit()
        return True

    except Exception as e:
        logger.error(f"Fatal error during image generation: {e}", exc_info=True)
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
