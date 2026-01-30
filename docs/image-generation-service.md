# OpenAI Image Generation Service

## Overview

The image generation service provides two main functions for creating avatar images using OpenAI's `gpt-image-1.5` model:

1. **Text-to-Image**: Generate base avatar selfie from persona bio
2. **Image-to-Image**: Generate 4-image grid variations from base image

## Module Location

`/home/niro/galacticos/avatar-data-generator/services/image_generation.py`

## Functions

### 1. generate_base_image()

Generates a base avatar image from the persona's Facebook bio and gender using text-to-image generation.

**Signature:**
```python
async def generate_base_image(bio_facebook: str, gender: str) -> Optional[bytes]
```

**Parameters:**
- `bio_facebook` (str): The person's Facebook bio text
- `gender` (str): Gender of the person (used in prompt)

**Returns:**
- `bytes`: PNG image data as bytes
- `None`: If generation fails

**Raises:**
- `Exception`: If API call fails or returns invalid response

**Prompt Template:**
```
generate an image of how this person would look like in a selfie.
the image should be not well-produced, amateur digital camera aesthetic,
low resolution. Person: {bio_facebook}. {gender}.
```

**Example Usage:**
```python
from services.image_generation import generate_base_image

bio = "Software engineer from Seattle who loves hiking and coffee"
gender = "male"

image_bytes = await generate_base_image(bio, gender)

# Save to file
with open('base_image.png', 'wb') as f:
    f.write(image_bytes)
```

**API Details:**
- **Endpoint**: `/v1/images/generations`
- **Model**: `gpt-image-1.5`
- **Method**: Standard OpenAI SDK method
- **Size**: `auto`
- **Response Format**: `b64_json`
- **Timeout**: 600 seconds (10 minutes)

---

### 2. generate_images_from_base()

Generates a 4-image grid from the base image using image-to-image generation with a Flowise-generated prompt.

**Signature:**
```python
async def generate_images_from_base(
    base_image_bytes: bytes,
    flowise_prompt: str
) -> Optional[bytes]
```

**Parameters:**
- `base_image_bytes` (bytes): Base image data from `generate_base_image()`
- `flowise_prompt` (str): Prompt describing desired image variations

**Returns:**
- `bytes`: PNG image data as bytes (4-image grid)
- `None`: If generation fails

**Raises:**
- `Exception`: If API call fails or returns invalid response

**Example Usage:**
```python
from services.image_generation import generate_images_from_base

# Assume we have base_image_bytes from generate_base_image()
prompt = "Create variations with different poses, lighting, and backgrounds"

grid_bytes = await generate_images_from_base(base_image_bytes, prompt)

# Save to file
with open('grid_image.png', 'wb') as f:
    f.write(grid_bytes)
```

**API Details:**
- **Endpoint**: `/v1/images/edits`
- **Model**: `gpt-image-1.5`
- **Method**: Direct HTTP POST (not SDK) - required for `image[]` field notation
- **Size**: `auto`
- **Response Format**: `b64_json`
- **Timeout**: 600 seconds (10 minutes)

**CRITICAL IMPLEMENTATION NOTE:**

This function uses **direct HTTP POST with httpx** instead of the OpenAI Python SDK because:
- The SDK's `images.edit()` method only accepts a single image parameter
- We need to use the `image[]` field notation to send the base image
- This is the only way to properly send image data to the `/v1/images/edits` endpoint

The multipart form data structure:
```python
files = [
    ('image[]', ('base_image.png', base_image_bytes, 'image/png'))
]
```

---

## Configuration

### Environment Variables

Required in `.env` file:
```bash
OPENAI_API_KEY="sk-proj-..."
```

### Constants

Defined in `services/image_generation.py`:
```python
OPENAI_API_BASE = "https://api.openai.com/v1"
IMAGE_MODEL = "gpt-image-1.5"
IMAGE_GENERATION_TIMEOUT = 600  # 10 minutes
```

---

## Workflow Integration

### Complete Avatar Generation Flow

```python
import asyncio
from services.image_generation import generate_base_image, generate_images_from_base

async def generate_avatar_images(persona):
    """Generate all images for a persona."""

    # Step 1: Generate base image
    base_image = await generate_base_image(
        bio_facebook=persona.bio_facebook,
        gender=persona.gender
    )

    if not base_image:
        raise Exception("Failed to generate base image")

    # Save base image
    with open(f'avatars/{persona.id}_base.png', 'wb') as f:
        f.write(base_image)

    # Step 2: Generate 4-image grid
    flowise_prompt = "Create natural variations in different settings"
    grid_image = await generate_images_from_base(base_image, flowise_prompt)

    if not grid_image:
        raise Exception("Failed to generate grid image")

    # Save grid image
    with open(f'avatars/{persona.id}_grid.png', 'wb') as f:
        f.write(grid_image)

    return {
        'base_image_path': f'avatars/{persona.id}_base.png',
        'grid_image_path': f'avatars/{persona.id}_grid.png'
    }

# Run async function
result = asyncio.run(generate_avatar_images(persona))
```

### Generating 8 Images (Two Grids)

For personas requiring 8 images, call `generate_images_from_base()` twice:

```python
async def generate_8_images(persona):
    """Generate 8 images (2x 4-image grids)."""

    # Generate base image
    base_image = await generate_base_image(
        persona.bio_facebook,
        persona.gender
    )

    # Generate two 4-image grids
    grids = []
    for i in range(2):
        grid = await generate_images_from_base(
            base_image,
            f"Create natural variations - set {i+1}"
        )
        grids.append(grid)

        # Save
        with open(f'avatars/{persona.id}_grid_{i+1}.png', 'wb') as f:
            f.write(grid)

    return grids
```

---

## Error Handling

### Common Errors

1. **API Key Missing/Invalid**
   ```
   Exception: OpenAI API error: {'error': {'message': 'Invalid API key'}}
   ```
   - Check `.env` file has correct `OPENAI_API_KEY`

2. **Timeout**
   ```
   Exception: Image generation timed out after 600s
   ```
   - Image generation taking too long
   - May need to retry

3. **Content Policy Violation**
   ```
   Exception: Content policy violation: {...}
   ```
   - Generated prompt violates OpenAI's content policy
   - Review bio content for inappropriate material

4. **Invalid Response Format**
   ```
   Exception: Invalid response format: missing b64_json
   ```
   - Unexpected API response structure
   - Check OpenAI API status

### Error Handling Pattern

```python
try:
    image = await generate_base_image(bio, gender)
    # Process image...

except Exception as e:
    logger.error(f"Image generation failed: {e}")
    # Handle error (retry, skip, etc.)
    if "content_policy_violation" in str(e).lower():
        # Handle policy violation specifically
        pass
```

---

## Testing

### Unit Test Script

Located at: `/home/niro/galacticos/avatar-data-generator/playground/test_image_generation.py`

Run tests:
```bash
cd /home/niro/galacticos/avatar-data-generator
python playground/test_image_generation.py
```

Tests both functions and saves output images to `playground/` directory.

### Example Integration

Located at: `/home/niro/galacticos/avatar-data-generator/playground/example_workflow_integration.py`

Demonstrates how to integrate into the task processing workflow.

---

## Dependencies

Required packages (already in `requirements.txt`):
```
httpx==0.27.0
openai==1.12.0
```

Install with:
```bash
pip install -r requirements.txt
```

---

## Performance Considerations

### Timing

- **Base image generation**: ~10-30 seconds
- **4-image grid generation**: ~15-45 seconds
- **Total per persona (4 images)**: ~30-75 seconds
- **Total per persona (8 images)**: ~45-120 seconds

### Rate Limits

OpenAI API has rate limits:
- Requests per minute
- Tokens per minute
- Images per minute

For batch processing, consider:
- Adding delays between requests
- Implementing retry logic with exponential backoff
- Monitoring rate limit headers in responses

### Parallel Processing

For processing multiple personas:
```python
import asyncio

async def process_batch(personas):
    """Process multiple personas in parallel."""
    tasks = [
        generate_avatar_images(persona)
        for persona in personas
    ]

    # Process with semaphore to limit concurrency
    sem = asyncio.Semaphore(3)  # Max 3 concurrent

    async def bounded_task(task):
        async with sem:
            return await task

    results = await asyncio.gather(*[
        bounded_task(task) for task in tasks
    ])

    return results
```

---

## Logging

The service uses Python's `logging` module:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Generated base image: 1234567 bytes")
logger.error("Failed to generate image: timeout")
```

Configure logging in your application:
```python
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
```

---

## Future Enhancements

Potential improvements:
1. Image quality validation (resolution, file size)
2. Automatic retry with exponential backoff
3. Image caching to avoid regeneration
4. Support for additional image sizes
5. Batch image generation endpoint
6. Progress tracking for long-running generations

---

## References

- **OpenAI Images API**: https://platform.openai.com/docs/api-reference/images
- **KB Article**: `~/.claude/kb/openai-image-generation.md`
- **Project README**: `/home/niro/galacticos/avatar-data-generator/README.md`

---

## Support

For issues or questions:
1. Check OpenAI API status: https://status.openai.com/
2. Review error logs for specific error messages
3. Test with `playground/test_image_generation.py`
4. Verify API key is valid and has credits
