# Image Generation - Quick Start Guide

## Overview

The avatar-data-generator now includes complete image generation functionality. When you submit an avatar generation task, the system will:

1. Generate persona data (names, bios) - **existing functionality**
2. Generate images for each persona - **NEW functionality**
3. Upload all images to S3 storage
4. Provide public URLs for all generated images

## How It Works

### Automated Process

The entire process is **fully automated** through the APScheduler integration:

1. **Data Generation Scheduler** (runs every 30 seconds):
   - Picks up tasks with status='pending'
   - Generates persona data via Flowise
   - Updates status to 'data-generated'

2. **Image Generation Scheduler** (runs every 30 seconds):
   - Picks up tasks with status='data-generated'
   - For each persona:
     - Generates image prompt
     - Creates base selfie image
     - Creates 4 variations
     - Uploads all to S3
   - Updates status to 'completed'

### No Manual Intervention Required

Once you submit a task through the web UI, everything happens automatically. You can monitor progress by checking the task status in the History page.

## Task Status Flow

```
pending → generating-data → data-generated → generating-images → completed
```

### Status Meanings

- **pending**: Task queued, waiting for data generation
- **generating-data**: Currently generating persona data (names, bios)
- **data-generated**: Data complete, waiting for image generation
- **generating-images**: Currently generating images for personas
- **completed**: All done! Images are ready
- **failed**: Something went wrong (check error_log)

## Generated Images

For each persona, the system generates:

1. **Base Image** (`base_image_url`): Initial selfie-style image
2. **Image 1** (`image_1_url`): First variation
3. **Image 2** (`image_2_url`): Second variation
4. **Image 3** (`image_3_url`): Third variation
5. **Image 4** (`image_4_url`): Fourth variation

All images are stored in S3 with public URLs for easy access.

## Accessing Generated Images

### Via Database

```sql
-- Get all images for a specific task
SELECT
    firstname,
    lastname,
    base_image_url,
    image_1_url,
    image_2_url,
    image_3_url,
    image_4_url
FROM generation_results gr
JOIN generation_tasks gt ON gr.task_id = gt.id
WHERE gt.task_id = 'YOUR_TASK_ID';
```

### Via Web UI

The History page shows task status. Once completed, you can view/download the generated data which includes image URLs.

## Monitoring Progress

### Check Logs

```bash
# View live logs
journalctl -u avatar-data-generator -f

# Filter for specific task
journalctl -u avatar-data-generator | grep "Task YOUR_TASK_ID"

# View only image generation logs
journalctl -u avatar-data-generator | grep "Step [1-7]/7"
```

### Check Database

```sql
-- Check task status
SELECT task_id, status, created_at, updated_at, completed_at
FROM generation_tasks
WHERE task_id = 'YOUR_TASK_ID';

-- Count completed personas with images
SELECT
    COUNT(*) as total_personas,
    COUNT(base_image_url) as with_base_image,
    COUNT(image_1_url) as with_variations
FROM generation_results gr
JOIN generation_tasks gt ON gr.task_id = gt.id
WHERE gt.task_id = 'YOUR_TASK_ID';
```

## Timing Expectations

### Small Task (1-5 personas)
- Data generation: ~2-5 minutes
- Image generation: ~10-15 minutes
- **Total**: ~12-20 minutes

### Medium Task (10-20 personas)
- Data generation: ~5-10 minutes
- Image generation: ~30-60 minutes
- **Total**: ~35-70 minutes

### Large Task (50+ personas)
- Data generation: ~15-30 minutes
- Image generation: ~2-4 hours
- **Total**: ~2.5-4.5 hours

## Testing the Integration

### Test with Web UI

1. Log in to the application
2. Navigate to "Generate" page
3. Create a small test task (e.g., 2 personas)
4. Go to "History" page and monitor status
5. Wait for status to change to 'completed'
6. Check database for image URLs

### Test with Command Line

```bash
# Run the example workflow script
cd /home/niro/galacticos/avatar-data-generator
python3 playground/example_full_image_workflow.py

# This will:
# - Generate persona data
# - Create base image
# - Create 4-image grid
# - Save images to playground/ directory
```

### Test Individual Components

```bash
# Test Flowise prompt generation
python3 playground/test_flowise_prompt_generation.py

# Test OpenAI image generation
python3 playground/test_image_generation.py

# Test image splitting and S3 upload
python3 playground/test_image_utils.py
```

## Troubleshooting

### Task Stuck at 'data-generated'

**Symptom**: Task status remains 'data-generated' for a long time

**Solutions**:
1. Check if image generation scheduler is running
2. Check logs for errors: `journalctl -u avatar-data-generator | grep ERROR`
3. Verify OpenAI API key is set in .env
4. Check S3 credentials

### Images Not Uploading

**Symptom**: Base image generated but image URLs are NULL

**Solutions**:
1. Verify S3 endpoint is accessible
2. Check S3 credentials in .env
3. Verify bucket exists and has proper permissions
4. Check logs for S3 upload errors

### OpenAI API Errors

**Symptom**: "Content policy violation" or "API error" in logs

**Solutions**:
1. Check OpenAI API key is valid
2. Review bio content for policy violations
3. Check OpenAI account has available credits
4. Review rate limits

### Slow Processing

**Symptom**: Image generation takes much longer than expected

**Explanation**: This is normal! Image generation is sequential to avoid overwhelming the API. Each persona takes ~2-3 minutes.

## Configuration

### Environment Variables

```bash
# Required for image generation
OPENAI_API_KEY=sk-...

# Required for S3 upload
S3_ENDPOINT=https://s3-api.dev.iron-mind.ai
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_BUCKET_NAME=avatar-images
S3_REGION=us-east-1

# Worker configuration
WORKER_INTERVAL=30  # Check for tasks every 30 seconds
```

### Adjusting Check Interval

To change how often the system checks for tasks, update `WORKER_INTERVAL` in your .env file:

```bash
# Check every 10 seconds (more responsive)
WORKER_INTERVAL=10

# Check every 60 seconds (less frequent)
WORKER_INTERVAL=60
```

Then restart the service:
```bash
sudo systemctl restart avatar-data-generator
```

## S3 Storage Structure

Images are organized in S3 as follows:

```
avatar-images/
  └── avatars/
      └── task_123/              (task database ID)
          ├── persona_456/        (result database ID)
          │   ├── base.png        (base selfie image)
          │   ├── image_0.png     (variation 1)
          │   ├── image_1.png     (variation 2)
          │   ├── image_2.png     (variation 3)
          │   └── image_3.png     (variation 4)
          └── persona_457/
              ├── base.png
              ├── image_0.png
              └── ...
```

## API Reference

### Database Fields

**generation_tasks table:**
- `status`: Task status (pending, generating-data, data-generated, generating-images, completed, failed)
- `error_log`: Error messages if task fails or has partial failures

**generation_results table:**
- `base_image_url`: Public S3 URL for base selfie image
- `image_1_url`: Public S3 URL for first variation
- `image_2_url`: Public S3 URL for second variation
- `image_3_url`: Public S3 URL for third variation
- `image_4_url`: Public S3 URL for fourth variation

## Support

For issues or questions:
1. Check logs: `journalctl -u avatar-data-generator -f`
2. Review this guide
3. Check the detailed documentation: `IMAGE_GENERATION_INTEGRATION.md`

---

**Last Updated**: 2026-01-30
