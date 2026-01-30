# Image Generation Integration - Implementation Summary

## Overview

The complete image generation workflow has been successfully integrated into the avatar-data-generator task processor. The system now handles the full avatar generation lifecycle from data generation through image creation and S3 storage.

## Status Flow

```
pending → generating-data → data-generated → generating-images → completed
```

## Architecture

### 1. Service Modules (Previously Built)

All service modules are located in `/home/niro/galacticos/avatar-data-generator/services/`:

- **`flowise_service.py`**: Generates image prompts from person data using Flowise workflow
- **`image_generation.py`**: OpenAI image generation (text-to-image and image-to-image)
- **`image_utils.py`**: Image splitting, trimming, and S3 upload functionality

### 2. Task Processor Integration

**File**: `/home/niro/galacticos/avatar-data-generator/workers/task_processor.py`

#### New Functions Added:

##### `get_data_generated_task_with_lock()`
- Fetches tasks with status='data-generated' using row-level locking
- Prevents conflicts when multiple workers are running
- Uses `SELECT ... FOR UPDATE SKIP LOCKED` for concurrency safety

##### `process_persona_images(task_id_str, task_db_id, result)`
- Async function that processes image generation for a single persona
- Executes 7 sequential steps:
  1. Generate image prompt via Flowise
  2. Generate base selfie image using OpenAI
  3. Upload base image to S3
  4. Generate 4-image grid from base image
  5. Split grid into 4 individual images
  6. Upload all 4 images to S3
  7. Update database with all URLs

##### `process_image_generation()`
- Main function called by APScheduler
- Finds tasks with status='data-generated'
- Processes images for all personas in the task sequentially
- Updates task status to 'generating-images' at start
- Updates task status to 'completed' when done
- Handles partial failures gracefully

### 3. Scheduler Integration

**File**: `/home/niro/galacticos/avatar-data-generator/app.py`

Two scheduler jobs are now configured:

1. **Data Generation Job** (`task_processor_job`):
   - Calls `process_single_task()`
   - Processes tasks with status='pending'
   - Updates status to 'data-generated'

2. **Image Generation Job** (`image_processor_job`):
   - Calls `process_image_generation()`
   - Processes tasks with status='data-generated'
   - Updates status to 'completed'

Both jobs run at the interval specified by `WORKER_INTERVAL` (default: 30 seconds).

## Database Schema

The `generation_results` table contains the following image URL fields:

```sql
- base_image_url (TEXT) - Public S3 URL for base selfie image
- image_1_url (TEXT) - Public S3 URL for first split image
- image_2_url (TEXT) - Public S3 URL for second split image
- image_3_url (TEXT) - Public S3 URL for third split image
- image_4_url (TEXT) - Public S3 URL for fourth split image
```

## S3 Storage Structure

Images are stored with the following path structure:

```
avatars/task_{task_id}/persona_{result_id}/base.png
avatars/task_{task_id}/persona_{result_id}/image_0.png
avatars/task_{task_id}/persona_{result_id}/image_1.png
avatars/task_{task_id}/persona_{result_id}/image_2.png
avatars/task_{task_id}/persona_{result_id}/image_3.png
```

Public URLs follow the format:
```
{S3_ENDPOINT}/avatar-images/{object-key}
```

Example:
```
https://s3-api.dev.iron-mind.ai/avatar-images/avatars/task_123/persona_456/base.png
```

## Error Handling

### Graceful Degradation
- If image generation fails for one persona, processing continues for others
- Partial failures are logged in `task.error_log`
- Tasks with partial success are still marked as 'completed'

### Error Tracking
Each persona's errors are logged with:
- Persona name
- Database result ID
- Specific error message

### Status Updates
- **Complete Failure**: status='failed', error_log contains all errors
- **Complete Success**: status='completed', no error_log
- **Partial Success**: status='completed', error_log contains failure details

## Logging

The task processor provides detailed logging for each step:

```
[Task {task_id}] Processing images for persona: {name} (result_id={id})
[Task {task_id}] [{name}] Step 1/7: Generating image prompt via Flowise...
[Task {task_id}] [{name}] Step 2/7: Generating base selfie image...
[Task {task_id}] [{name}] Step 3/7: Uploading base image to S3...
[Task {task_id}] [{name}] Step 4/7: Generating 4-image grid...
[Task {task_id}] [{name}] Step 5/7: Splitting and trimming grid image...
[Task {task_id}] [{name}] Step 6/7: Uploading 4 split images to S3...
[Task {task_id}] [{name}] Step 7/7: Updating database with image URLs...
[Task {task_id}] [{name}] Image processing completed successfully!
```

## Configuration

### Environment Variables Required

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...

# S3 Configuration
S3_ENDPOINT=https://s3-api.dev.iron-mind.ai
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_BUCKET_NAME=avatar-images
S3_REGION=us-east-1

# Worker Configuration
WORKER_INTERVAL=30  # Seconds between scheduler checks
MULTITHREAD_FLOWISE=5  # Thread count for parallel Flowise requests
```

## Processing Flow Example

1. User submits avatar generation request via web UI
2. Task created with status='pending'
3. **Data Generation Scheduler** picks up task:
   - Status: `pending` → `generating-data`
   - Calls Flowise to generate persona data (names, bios)
   - Stores results in `generation_results` table
   - Status: `generating-data` → `data-generated`
4. **Image Generation Scheduler** picks up task:
   - Status: `data-generated` → `generating-images`
   - For each persona:
     - Generate image prompt via Flowise
     - Generate base selfie image via OpenAI
     - Upload base image to S3
     - Generate 4-image grid via OpenAI
     - Split grid into 4 images
     - Upload all 4 images to S3
     - Update database with URLs
   - Status: `generating-images` → `completed`

## Sequential Processing

Image generation is **sequential** (one persona at a time) to:
- Prevent overwhelming the OpenAI API with concurrent requests
- Ensure better rate limit management
- Provide clearer error tracking
- Maintain predictable resource usage

## API Rate Limits

### OpenAI API
- Text-to-image generation: ~30-60 seconds per image
- Image-to-image generation: ~30-60 seconds per grid
- Total per persona: ~2-3 minutes

### Flowise API
- Prompt generation: ~20 seconds per request

### Example Timing
For a task with 10 personas:
- Data generation: ~5-10 minutes (parallel batches)
- Image generation: ~20-30 minutes (sequential processing)
- Total: ~25-40 minutes

## Testing

To test the integration:

1. Create a small test task (e.g., 1-2 personas)
2. Monitor logs for progress:
   ```bash
   journalctl -u avatar-data-generator -f
   ```
3. Check database for updated image URLs:
   ```sql
   SELECT firstname, lastname, base_image_url, image_1_url
   FROM generation_results
   WHERE task_id = (SELECT id FROM generation_tasks WHERE task_id = 'YOUR_TASK_ID');
   ```
4. Verify S3 storage and public URL access

## Maintenance Notes

### Monitoring
- Check APScheduler logs for job execution
- Monitor database for stuck tasks (status='generating-images' for >1 hour)
- Check S3 storage usage

### Troubleshooting
- **Stuck at 'data-generated'**: Check image generation scheduler is running
- **Missing image URLs**: Check S3 credentials and bucket access
- **OpenAI errors**: Check API key and rate limits
- **Flowise errors**: Verify workflow URL and auth token

## Future Enhancements

Potential improvements:
- Parallel image processing with rate limiting
- Retry mechanism for failed image generations
- Image quality validation before upload
- Thumbnail generation for faster loading
- CDN integration for image delivery
- Image cleanup for failed/cancelled tasks

---

**Implementation Date**: 2026-01-30
**Status**: Complete and Ready for Testing
