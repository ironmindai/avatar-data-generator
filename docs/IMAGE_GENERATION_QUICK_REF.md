# Image Generation Service - Quick Reference

## Functions

### 1. generate_base_image()
**Text-to-Image: Create base avatar selfie**

```python
from services.image_generation import generate_base_image

image_bytes = await generate_base_image(
    bio_facebook="Software engineer who loves hiking",
    gender="male"
)
```

- **Endpoint**: `/v1/images/generations`
- **Model**: `gpt-image-1.5`
- **Returns**: PNG bytes (base selfie image)
- **Timeout**: 600s

---

### 2. generate_images_from_base()
**Image-to-Image: Create 4-image grid**

```python
from services.image_generation import generate_images_from_base

grid_bytes = await generate_images_from_base(
    base_image_bytes=image_bytes,
    flowise_prompt="Create variations in different settings"
)
```

- **Endpoint**: `/v1/images/edits`
- **Model**: `gpt-image-1.5`
- **Returns**: PNG bytes (4-image grid)
- **Timeout**: 600s
- **Note**: Uses direct HTTP POST with `image[]` notation

---

## Complete Workflow

```python
from services.flowise_service import generate_image_prompt
from services.image_generation import generate_base_image, generate_images_from_base
from services.image_utils import split_and_trim_image, upload_images_batch

async def generate_avatar(persona):
    # 1. Generate prompt
    person_data = {
        'firstname': persona.firstname,
        'lastname': persona.lastname,
        'gender': persona.gender,
        'bio_facebook': persona.bio_facebook,
        'bio_instagram': persona.bio_instagram,
        'bio_x': persona.bio_x,
        'bio_tiktok': persona.bio_tiktok
    }
    prompt = await generate_image_prompt(person_data)

    # 2. Generate base image
    base = await generate_base_image(persona.bio_facebook, persona.gender)

    # 3. Generate 4-image grid
    grid = await generate_images_from_base(base, prompt)

    # 4. Split into individual images
    images = split_and_trim_image(grid, num_rows=2, num_cols=2)

    # 5. Upload to S3
    urls = upload_images_batch(images, f"avatars/{persona.id}/img")

    return urls
```

---

## For 8 Images (2 Grids)

```python
async def generate_8_images(persona):
    # Generate base
    base = await generate_base_image(persona.bio_facebook, persona.gender)

    # Generate prompt
    prompt = await generate_image_prompt(person_data)

    # Generate 2 grids
    all_images = []
    for i in range(2):
        grid = await generate_images_from_base(base, prompt)
        images = split_and_trim_image(grid)
        all_images.extend(images)

    # Upload all 8 images
    urls = upload_images_batch(all_images, f"avatars/{persona.id}/img")
    return urls
```

---

## Configuration (.env)

```bash
OPENAI_API_KEY="sk-proj-..."
S3_ENDPOINT="http://..."
S3_ACCESS_KEY="..."
S3_SECRET_KEY="..."
S3_BUCKET_NAME="avatars"
```

---

## Testing

```bash
# Test image generation
python playground/test_image_generation.py

# See workflow example
python playground/example_workflow_integration.py
```

---

## Error Handling

```python
try:
    image = await generate_base_image(bio, gender)
except Exception as e:
    if "content_policy_violation" in str(e).lower():
        # Handle policy violation
        logger.error(f"Content policy violation: {e}")
    elif "timeout" in str(e).lower():
        # Handle timeout
        logger.error(f"Timeout: {e}")
    else:
        # Handle other errors
        logger.error(f"Error: {e}")
```

---

## Timing
- Base image: ~10-30s
- Grid (4 images): ~15-45s
- Split & trim: ~1-2s
- S3 upload: ~2-5s

**Total: 30-80s per persona (4 images)**

---

## File Locations

- **Service**: `services/image_generation.py`
- **Tests**: `playground/test_image_generation.py`
- **Example**: `playground/example_workflow_integration.py`
- **Docs**: `docs/image-generation-service.md`

---

## Dependencies

```
httpx==0.27.0
openai==1.12.0
Pillow==10.2.0
split-image==2.0.1
boto3==1.34.34
```

Install: `pip install -r requirements.txt`
