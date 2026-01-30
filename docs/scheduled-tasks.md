# Scheduled Tasks Documentation

> *Maintained by: scheduled-tasks-coder agent*

This document provides comprehensive information about all scheduled tasks, workers, and background processes in the Avatar Data Generator system.

## Table of Contents

- [Overview](#overview)
- [Task List](#task-list)
- [Worker Details](#worker-details)
- [Manual Execution](#manual-execution)
- [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
- [Dependencies](#dependencies)

---

## Overview

The Avatar Data Generator uses background worker processes to handle time-consuming avatar generation tasks asynchronously. This allows the web application to remain responsive while processing large batches of avatar data.

### Processing Pipeline

The avatar generation process is split into two distinct steps:

1. **Data Generation (IMPLEMENTED)**: Generate persona data (names, bios) via Flowise API
2. **Image Generation (FUTURE)**: Generate avatar images (to be implemented)

### Status Flow

Tasks progress through the following statuses:

```
pending -> generating-data -> data-generated -> generating-images -> completed
                                     |
                                     v
                                  failed
```

**Current Implementation**: Tasks go from `pending` -> `generating-data` -> `data-generated`

---

## Task List

### 1. Avatar Data Generation Worker

**Task Name**: `task_processor.py`

**Purpose**: Process pending avatar generation tasks by calling Flowise API to generate persona data (first names, last names, gender, and social media bios for Facebook, Instagram, X/Twitter, and TikTok).

**Status**: ACTIVE (Step 1 of 2)

**Technology**: Python script (can be run manually or scheduled via cron/systemd)

**Schedule**: Currently run manually (to be automated in future)

**Script Location**: `/home/niro/galacticos/avatar-data-generator/workers/task_processor.py`

**Command**:
```bash
/home/niro/galacticos/avatar-data-generator/venv/bin/python3 /home/niro/galacticos/avatar-data-generator/workers/task_processor.py
```

**Configuration**:
- Environment Variable: `MULTITHREAD_FLOWISE` (default: 5)
  - Controls number of parallel threads for Flowise API requests
  - Higher values = faster processing but higher API load
- Max Batch Size: 20 personas per request (hardcoded in script)
- Request Timeout: 600 seconds (10 minutes)

**Processing Logic**:
1. Query database for tasks with `status='pending'`, ordered by `created_at` (oldest first)
2. Currently processes 1 task at a time
3. Update task status to `generating-data`
4. Fetch bio prompt settings from Settings table:
   - `bio_prompt_facebook`
   - `bio_prompt_instagram`
   - `bio_prompt_x`
   - `bio_prompt_tiktok`
5. Split `number_to_generate` into batches of max 20
   - Example: 50 avatars = [20, 20, 10]
6. Process batches in parallel using ThreadPoolExecutor (5 threads)
7. For each batch, make POST request to Flowise API
8. Parse response and extract persona data
9. Store results in `generation_results` table
10. Update task status to `data-generated` (or `failed` if all batches fail)

**Flowise API Details**:
- URL: `https://flowise.electric-marinade.com/api/v1/prediction/71bf0c86-c802-4221-b6e7-0af16e350bb6`
- Authentication: Bearer token (stored in script)
- Timeout: 600 seconds per request
- Response Format: Multiple JSON objects separated by newlines

**Database Tables Used**:
- **Input**: `generation_tasks` (reads pending tasks)
- **Input**: `settings` (reads bio prompt settings)
- **Output**: `generation_results` (stores generated persona data)
- **Update**: `generation_tasks` (updates status, error_log, updated_at)

**Logging**:
- Level: INFO
- Format: `[YYYY-MM-DD HH:MM:SS] LEVEL - Message`
- Output: STDOUT (can be redirected to file or journald)
- Key Events Logged:
  - Worker startup/shutdown
  - Task processing start/end
  - Batch requests and responses
  - Parsing errors
  - Database operations
  - Final status updates

**Error Handling**:
- Individual batch failures are logged but don't stop other batches
- If ALL batches fail: task marked as `failed` with error_log
- If at least ONE batch succeeds: task marked as `data-generated` with partial error_log
- Network timeouts: Caught and logged
- JSON parsing errors: Logged with warning, persona skipped
- Database errors: Transaction rolled back, error logged

**Dependencies**:
- Python 3.12+
- Flask application and models
- PostgreSQL database
- Internet connection to Flowise API
- Python packages:
  - requests==2.31.0
  - flask
  - sqlalchemy
  - psycopg2-binary
  - python-dotenv

**Lock Mechanism**: None (currently processes one task at a time)

**Idempotency**: Safe to re-run on failed tasks (task status prevents duplicate processing)

**Next Step**: After completion, tasks have status `data-generated` and are ready for image generation step (to be implemented)

**Owner**: Backend team

**Date Created**: 2026-01-30

**Last Modified**: 2026-01-30

**Special Considerations**:
- Flowise API may take 40-60 seconds per batch
- Large batches (50+ personas) may take several minutes
- Network connectivity is critical
- Database connection must remain stable throughout processing
- Status `data-generated` indicates PARTIAL completion (step 1 of 2)

---

## Worker Details

### task_processor.py

**Class**: `TaskProcessor`

**Key Methods**:

1. **`get_pending_tasks(limit=1)`**
   - Fetches pending tasks from database
   - Currently limited to 1 task at a time
   - Returns: List of GenerationTask objects

2. **`get_bio_settings()`**
   - Retrieves bio prompt settings from Settings table
   - Returns: Dictionary with 4 platform-specific prompts

3. **`calculate_batches(total)`**
   - Splits total into batches of max 20
   - Returns: List of batch sizes

4. **`call_flowise_api(batch_size, batch_number, task, settings)`**
   - Makes API request to Flowise
   - Returns: Tuple of (batch_number, personas_list or None, error or None)

5. **`parse_flowise_response(text_content, batch_number, task_id)`**
   - Parses Flowise response containing multiple JSON objects
   - Extracts persona data and bios
   - Returns: List of persona dictionaries

6. **`store_results(task_id, batch_number, personas)`**
   - Stores persona results in generation_results table
   - Returns: Number of personas stored

7. **`process_task(task)`**
   - Main processing logic for a single task
   - Orchestrates all steps
   - Returns: Boolean (success/failure)

8. **`run()`**
   - Main entry point
   - Fetches pending tasks and processes them

**Thread Safety**: Uses ThreadPoolExecutor for parallel batch processing, but processes one task at a time

---

## Manual Execution

### Running the Worker Manually

To process pending tasks manually:

```bash
cd /home/niro/galacticos/avatar-data-generator
/home/niro/galacticos/avatar-data-generator/venv/bin/python3 workers/task_processor.py
```

### Testing with Test Script

```bash
cd /home/niro/galacticos/avatar-data-generator
/home/niro/galacticos/avatar-data-generator/venv/bin/python3 playground/test_worker.py
```

This will show before/after status and sample results.

### Checking Task Status

```bash
/home/niro/galacticos/avatar-data-generator/venv/bin/python3 -c "
from app import create_app
from models import db, GenerationTask

app = create_app()
with app.app_context():
    for status in ['pending', 'generating-data', 'data-generated', 'failed']:
        count = GenerationTask.query.filter_by(status=status).count()
        print(f'{status}: {count}')
"
```

### Viewing Results

```bash
/home/niro/galacticos/avatar-data-generator/venv/bin/python3 -c "
from app import create_app
from models import db, GenerationResult

app = create_app()
with app.app_context():
    results = GenerationResult.query.limit(5).all()
    for r in results:
        print(f'{r.firstname} {r.lastname} ({r.gender}) - Batch {r.batch_number}')
        print(f'  Facebook: {r.bio_facebook[:80]}...')
        print()
"
```

---

## Monitoring and Troubleshooting

### Checking for Stuck Tasks

Tasks stuck in `generating-data` status may indicate a crash:

```bash
/home/niro/galacticos/avatar-data-generator/venv/bin/python3 -c "
from app import create_app
from models import db, GenerationTask
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    # Find tasks generating for more than 30 minutes
    threshold = datetime.utcnow() - timedelta(minutes=30)
    stuck_tasks = GenerationTask.query.filter(
        GenerationTask.status == 'generating-data',
        GenerationTask.updated_at < threshold
    ).all()

    if stuck_tasks:
        print(f'Found {len(stuck_tasks)} stuck tasks:')
        for task in stuck_tasks:
            print(f'  Task {task.task_id}: Last updated {task.updated_at}')
    else:
        print('No stuck tasks found')
"
```

### Resetting Failed Tasks

To reset a failed task back to pending:

```bash
/home/niro/galacticos/avatar-data-generator/venv/bin/python3 -c "
from app import create_app
from models import db, GenerationTask

app = create_app()
with app.app_context():
    task = GenerationTask.query.filter_by(task_id='TASK_ID_HERE').first()
    if task:
        task.status = 'pending'
        task.error_log = None
        db.session.commit()
        print(f'Reset task {task.task_id}')
"
```

### Viewing Error Logs

```bash
/home/niro/galacticos/avatar-data-generator/venv/bin/python3 -c "
from app import create_app
from models import db, GenerationTask

app = create_app()
with app.app_context():
    failed_tasks = GenerationTask.query.filter_by(status='failed').all()
    for task in failed_tasks:
        print(f'Task {task.task_id}:')
        print(task.error_log)
        print('-' * 80)
"
```

### Common Issues

**Issue**: All batches failing with timeout
- **Solution**: Check network connectivity to Flowise API
- **Solution**: Increase REQUEST_TIMEOUT in worker script
- **Solution**: Reduce MULTITHREAD_FLOWISE to avoid overwhelming API

**Issue**: JSON parsing errors
- **Solution**: Check Flowise API response format hasn't changed
- **Solution**: Review debug_flowise_response.py output

**Issue**: Database connection errors
- **Solution**: Verify DATABASE_URL in .env file
- **Solution**: Check PostgreSQL is running
- **Solution**: Verify database credentials

**Issue**: No pending tasks being picked up
- **Solution**: Verify tasks exist with status='pending'
- **Solution**: Check worker is using correct database connection

---

## Dependencies

### System Requirements
- Python 3.12 or higher
- PostgreSQL 12 or higher
- Network access to Flowise API (https://flowise.electric-marinade.com)
- Virtual environment at `/home/niro/galacticos/avatar-data-generator/venv`

### Python Packages
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
psycopg2-binary==2.9.9
SQLAlchemy==2.0.23
python-dotenv==1.0.0
requests==2.31.0
```

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `MULTITHREAD_FLOWISE`: Number of parallel threads (default: 5)

### Database Tables
- `generation_tasks`: Stores task information
- `generation_results`: Stores generated persona data
- `settings`: Stores bio prompt configurations

---

## Future Enhancements

### Planned Features
1. **Automated Scheduling**
   - Implement systemd timer or cron job for automatic worker execution
   - Consider running every 5-10 minutes

2. **Image Generation Step**
   - Implement step 2 of the pipeline
   - Process tasks with status='data-generated'
   - Generate avatar images for each persona
   - Update final status to 'completed'

3. **Monitoring Dashboard**
   - Real-time task status monitoring
   - Performance metrics (processing time, success rate)
   - Alert system for failed tasks

4. **Enhanced Error Handling**
   - Automatic retry logic for transient failures
   - Dead letter queue for permanently failed tasks
   - Detailed error categorization

5. **Performance Optimization**
   - Process multiple tasks in parallel
   - Implement task priority queue
   - Add caching layer for settings

6. **Logging Improvements**
   - Centralized logging to file or journald
   - Log rotation
   - Structured logging (JSON format)

---

## Change Log

### 2026-01-30
- Initial implementation of task_processor.py worker
- Created generation_results table via Alembic migration
- Added GenerationResult model to models.py
- Implemented multithreaded batch processing
- Fixed Flowise response parsing for multi-line JSON objects
- Successfully tested with real pending task
- Created comprehensive documentation

---

## Contact

For questions or issues related to scheduled tasks, contact the backend team or consult this documentation.
