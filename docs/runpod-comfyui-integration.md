# RunPod ComfyUI Integration Guide

**Source Server**: backend.electric-marinade.com:/tools/aoa/customeyes
**Date**: 2026-02-20
**Status**: Active production system on RunPod V2

---

## Executive Summary

The customeyes project on backend.electric-marinade.com has a **fully functional RunPod-based ComfyUI image generation system** that supports:
- **Face generation** with seed face images
- **Post generation** (selfie/group) with face reference and denoising controls
- **Subjectless generation** (landscapes/scenery)
- **img2img workflows** with configurable denoising strength
- **Batch processing** with retry logic and state tracking

This system can be integrated into the avatar-data-generator project to replace or augment OpenAI image generation.

---

## System Architecture

### Current OpenAI System (This Project)
```
┌─────────────────────────────────────────────────────────────┐
│  Text-to-Image (OpenAI gpt-image-1.5)                       │
│  ├─ generate_base_image() → base selfie from bio            │
│  └─ generate_images_from_base() → 4-image grid variations   │
└─────────────────────────────────────────────────────────────┘
```

### RunPod ComfyUI System (customeyes)
```
┌──────────────────────────────────────────────────────────────────┐
│  RunPod V2 Multi-Step Pipeline                                    │
│  ├─ Step 1: Face Generation (profile image)                      │
│  │    └─ Uses S3 seed face + prompt + gender                     │
│  ├─ Step 2: Post Generation (with subject)                       │
│  │    └─ Selfie/Group with face reference + denoising            │
│  └─ Step 3: Subjectless Generation (landscapes)                  │
│       └─ No face reference, pure text-to-image                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## RunPod API Configuration

### Endpoint Details

**API Base**: `https://api.runpod.ai/v2/`

**Run Endpoint**: `https://api.runpod.ai/v2/7l3f8add2h9701/run`

**Status Endpoint**: `https://api.runpod.ai/v2/7l3f8add2h9701/status/{jobId}`

**API Key**: `rpa_J35GATUFIYLG7HFV7VZU9V1NMDBYVT6KA6QQJNMSo5wj5l`

**Endpoint ID**: `7l3f8add2h9701`

### Authentication

All requests require Bearer token authentication:
```bash
Authorization: Bearer rpa_J35GATUFIYLG7HFV7VZU9V1NMDBYVT6KA6QQJNMSo5wj5l
```

---

## Generation Types

### 1. Face Generation (`face_generator`)

Generates profile/avatar face images using a seed face for consistency.

**Request Payload:**
```json
{
  "input": {
    "generation_type": "face_generator",
    "random_seeds": [123456, 789012, 345678, 901234],
    "prompt": "Professional headshot, neutral expression, studio lighting",
    "negative_prompt": "female, smile, hand, nude, cartoon, low quality...",
    "width": 1024,
    "height": 1024,
    "face_image": "https://s3.amazonaws.com/bucket/seed-face.jpg",
    "denoise": 0.5,
    "ip_adapter_weight": 0.8,
    "ip_adapter_start": 0.2,
    "ip_adapter_end": 0.6
  }
}
```

**Key Parameters:**
- `random_seeds`: Array of 4 random integers for variation
- `face_image`: S3 URL to seed face (ensures consistency)
- `denoise`: 0.5 for img2img (0.0 = no change, 1.0 = full regeneration)
- `ip_adapter_weight`: Face reference strength (0.8 recommended)

**Response:**
```json
{
  "id": "7l3f8add2h9701-abcd1234",
  "status": "IN_QUEUE"
}
```

---

### 2. Post Generation (`post_generator`)

Generates selfie/group images with face reference (img2img workflow).

**Request Payload:**
```json
{
  "input": {
    "generation_type": "post_generator",
    "random_seed": 567890,
    "prompt": "Selfie at coffee shop, casual lighting, smartphone quality",
    "width": 768,
    "height": 1024,
    "lora_strength": 0.85,
    "face_image": "https://runpod-output.s3.amazonaws.com/generated-face.jpg",
    "denoise": 0.5,
    "disable_lora": false,
    "brightness": 1.1,
    "contrast": 1.25,
    "saturation": 1.0
  }
}
```

**Key Parameters:**
- `face_image`: Generated face from step 1 (for consistency)
- `denoise`: Controls how much to deviate from face (0.5 = balanced)
- `lora_strength`: Face visibility in final image (0.75-1.0)
  - Indoor group: 0.9-1.0
  - Indoor selfie: 0.75-1.0
  - Outdoor day: 1.0
  - Outdoor night: 0.9
- `brightness/contrast/saturation`: Post-processing adjustments

**Dimension Logic:**
- Profile: 1024x1024 (square)
- Cover: 820x320 (Facebook cover)
- Selfie: 768x1024 (portrait)
- Group: 1024x768 (landscape)

---

### 3. Subjectless Generation (`image_generator`)

Generates landscapes/scenery without any subject.

**Request Payload:**
```json
{
  "input": {
    "generation_type": "image_generator",
    "prompt": "Beautiful sunset over ocean, golden hour, peaceful atmosphere",
    "random_seed": 234567,
    "width": 1024,
    "height": 768
  }
}
```

**Dimensions (Random):**
- Square: 1024x1024
- Landscape: 1024x768
- Portrait: 768x1024

---

## Job Polling and Status

### Poll Status

After queueing a job, poll for completion:

**Request:**
```bash
GET https://api.runpod.ai/v2/7l3f8add2h9701/status/{jobId}
Authorization: Bearer {API_KEY}
```

**Response (In Progress):**
```json
{
  "id": "7l3f8add2h9701-abcd1234",
  "status": "IN_PROGRESS"
}
```

**Response (Completed):**
```json
{
  "id": "7l3f8add2h9701-abcd1234",
  "status": "COMPLETED",
  "output": "https://runpod-output.s3.amazonaws.com/image.jpg"
}
```

**Response (Failed):**
```json
{
  "id": "7l3f8add2h9701-abcd1234",
  "status": "FAILED",
  "error": "ComfyUI workflow error: Invalid seed face URL"
}
```

**Status Values:**
- `IN_QUEUE` - Job queued, waiting for worker
- `IN_PROGRESS` - Currently generating
- `COMPLETED` - Success, `output` contains image URL
- `FAILED` - Error, `error` contains message
- `CANCELLED` - Job cancelled

### Polling Strategy

From customeyes implementation:
```javascript
// Poll every 10 seconds for up to 40 minutes
maxAttempts = 240
intervalMs = 10000

for (attempt = 1; attempt <= maxAttempts; attempt++) {
  const response = await fetch(statusUrl);
  const status = response.data.status;

  if (status === 'COMPLETED') {
    return response.data.output; // Image URL
  } else if (status === 'FAILED' || status === 'CANCELLED') {
    throw new Error(response.data.error);
  }

  await sleep(intervalMs); // Wait 10s
}
```

---

## Retry Logic

### Face Generation (Critical)
```javascript
MAX_FACE_RETRIES = 3 // Must succeed
BACKOFF = [2s, 4s, 8s] // Exponential backoff

for (attempt = 1; attempt <= 3; attempt++) {
  try {
    jobId = await queueFaceJob();
    imageUrl = await pollJob(jobId);
    return imageUrl; // Success
  } catch (error) {
    if (attempt < 3) {
      await sleep(Math.pow(2, attempt) * 1000);
    } else {
      throw error; // Failed all retries
    }
  }
}
```

### Post Generation (Partial Success Allowed)
```javascript
MAX_POST_RETRIES = 3 // Per-post limit
BACKOFF = 2s // Fixed 2s delay

for (attempt = 1; attempt <= 3; attempt++) {
  try {
    jobId = await queuePostJob();
    imageUrl = await pollJob(jobId);
    return imageUrl; // Success
  } catch (error) {
    if (attempt >= 3) {
      return null; // Allow partial batch success
    }
    await sleep(2000);
  }
}
```

---

## Batch Processing

### Rate Limiting

Process posts in batches of 10 to avoid overwhelming RunPod:

```javascript
BATCH_SIZE = 10

// Split posts into batches
const batches = [];
for (let i = 0; i < posts.length; i += BATCH_SIZE) {
  batches.push(posts.slice(i, i + BATCH_SIZE));
}

// Process each batch sequentially
for (const batch of batches) {
  const jobIds = [];

  // Queue all jobs in batch
  for (const post of batch) {
    const jobId = await queuePostJob(post);
    jobIds.push(jobId);
  }

  // Poll all jobs in parallel
  const results = await Promise.all(
    jobIds.map(id => pollJob(id))
  );
}
```

---

## Seed Face System

### S3 Bucket Structure

The customeyes system uses S3 seed faces to ensure facial consistency:

**Bucket**: (Not specified in code, likely environment variable)

**Structure**:
```
s3://bucket/seed-faces/
  ├─ male/
  │   ├─ face-001.jpg
  │   ├─ face-002.jpg
  │   └─ ...
  └─ female/
      ├─ face-001.jpg
      ├─ face-002.jpg
      └─ ...
```

### Selection Logic

```javascript
// Random selection from S3 bucket based on gender
const seedFaceUrl = await s3SeedFaces.getRandomSeedFaceUrl(gender);

// Example return: https://s3.amazonaws.com/bucket/seed-faces/male/face-042.jpg
```

**Integration Note**: To use this system, you'll need:
1. S3 bucket with seed face images
2. AWS credentials with read access
3. Utility to randomly select faces by gender

---

## Negative Prompts

### Gender-Specific Negative Prompts

**Male:**
```
female, (smile:1.2), (hand:1.3), nude, body, porn, nudity, sexual,
explicit, erotic, semi-nude, NSFW, underwear, lingerie, adult,
erotic pose, beautiful, gorgeous, handsome, good looking, sexy,
pretty, cartoon, cgi, render, illustration, painting, drawing,
bad quality, grainy, low resolution
```

**Female:**
```
male, (smile:1.2), (hand:1.3), (beard:1.4), (facial hair:1.4),
nude, body, porn, nudity, sexual, explicit, erotic, semi-nude,
NSFW, underwear, lingerie, adult, erotic pose, beautiful, gorgeous,
handsome, good looking, sexy, pretty, cartoon, cgi, render,
illustration, painting, drawing, bad quality, grainy, low resolution
```

**Key Elements:**
- Prevents opposite gender
- Reduces smiling (more natural)
- Prevents hands in frame (common AI artifact)
- NSFW filtering
- Anti-beauty bias (more realistic)
- No artistic styles

---

## Integration into Avatar Data Generator

### Option 1: Replace OpenAI with RunPod

**Advantages:**
- More control over denoising/LoRA strength
- Facial consistency via seed faces
- Batch processing with retry logic
- Lower cost per image (depending on RunPod pricing)

**Disadvantages:**
- Requires S3 seed face setup
- More complex workflow (3-step vs 2-step)
- Longer generation time (polling overhead)

**Migration Path:**
1. Set up S3 bucket with seed faces
2. Create Python wrapper around RunPod API
3. Replace `generate_base_image()` with RunPod face generation
4. Replace `generate_images_from_base()` with RunPod post generation
5. Migrate existing personas one batch at a time

---

### Option 2: Hybrid Approach

Use **OpenAI for base images** and **RunPod for variations**:

```python
# Step 1: Generate base with OpenAI (fast, simple)
base_image = await openai_generate_base_image(bio, gender)

# Step 2: Upload base image to S3 as "seed face"
seed_face_url = await upload_to_s3(base_image)

# Step 3: Use RunPod for variations with denoising control
variations = []
for prompt in flowise_prompts:
    image_url = await runpod_generate_post(
        prompt=prompt,
        face_image=seed_face_url,
        denoise=0.5  # Control similarity
    )
    variations.append(image_url)
```

**Advantages:**
- Leverage OpenAI's speed for initial generation
- Use RunPod's img2img for controlled variations
- Best of both systems

---

### Option 3: A/B Testing

Run **both systems in parallel** and compare results:

```python
# Generate same persona with both systems
openai_images = await generate_with_openai(persona)
runpod_images = await generate_with_runpod(persona)

# Store both sets, allow manual review/selection
await save_images(persona.id, {
    'openai': openai_images,
    'runpod': runpod_images
})
```

**Use Cases:**
- Quality comparison
- Cost/performance analysis
- Gradual migration validation

---

## Code Integration Example

### Python RunPod Client

```python
import httpx
import asyncio
from typing import Optional, Dict, Any

class RunPodClient:
    def __init__(self, api_key: str, endpoint_id: str):
        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.run_url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
        self.status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status"

    async def generate_face(
        self,
        prompt: str,
        seed_face_url: str,
        gender: str
    ) -> Optional[str]:
        """Generate face image using RunPod."""

        # Build payload
        payload = {
            "input": {
                "generation_type": "face_generator",
                "random_seeds": [random.randint(0, 1e9) for _ in range(4)],
                "prompt": prompt,
                "negative_prompt": self._build_negative_prompt(gender),
                "width": 1024,
                "height": 1024,
                "face_image": seed_face_url,
                "denoise": 0.5,
                "ip_adapter_weight": 0.8,
                "ip_adapter_start": 0.2,
                "ip_adapter_end": 0.6
            }
        }

        # Queue job
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.run_url,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0
            )
            response.raise_for_status()
            job_id = response.json()["id"]

        # Poll for completion
        return await self._poll_job(job_id)

    async def _poll_job(
        self,
        job_id: str,
        max_attempts: int = 240,
        interval_sec: int = 10
    ) -> Optional[str]:
        """Poll job status until completion."""

        async with httpx.AsyncClient() as client:
            for attempt in range(max_attempts):
                response = await client.get(
                    f"{self.status_url}/{job_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=15.0
                )
                response.raise_for_status()
                data = response.json()

                if data["status"] == "COMPLETED":
                    return data["output"]
                elif data["status"] in ["FAILED", "CANCELLED"]:
                    raise Exception(f"Job failed: {data.get('error')}")

                await asyncio.sleep(interval_sec)

        raise Exception(f"Job {job_id} timed out after {max_attempts * interval_sec}s")

    def _build_negative_prompt(self, gender: str) -> str:
        """Build gender-specific negative prompt."""
        base = "nude, body, porn, nudity, sexual, explicit, cartoon, low quality"
        if gender.lower() == "male":
            return f"female, (smile:1.2), (hand:1.3), {base}"
        else:
            return f"male, (smile:1.2), (hand:1.3), (beard:1.4), {base}"
```

### Usage Example

```python
# Initialize client
client = RunPodClient(
    api_key="rpa_J35GATUFIYLG7HFV7VZU9V1NMDBYVT6KA6QQJNMSo5wj5l",
    endpoint_id="7l3f8add2h9701"
)

# Generate face
face_url = await client.generate_face(
    prompt="Professional headshot, neutral expression",
    seed_face_url="https://s3.amazonaws.com/bucket/seed-face.jpg",
    gender="male"
)

print(f"Generated face: {face_url}")
```

---

## Performance Benchmarks (from customeyes)

### Timing Estimates

**Face Generation:**
- Queue time: 2-10 seconds
- Generation time: 30-120 seconds
- Total: ~45-130 seconds

**Post Generation (per image):**
- Queue time: 1-5 seconds
- Generation time: 20-90 seconds
- Total: ~25-95 seconds

**Batch of 10 Posts:**
- Parallel polling: ~30-120 seconds
- Sequential batches: Add 10s per batch

**Complete Profile (1 face + 8 posts):**
- Best case: ~5 minutes
- Average: ~10 minutes
- Worst case: ~20 minutes

---

## Cost Comparison

### OpenAI (Current System)
- Model: `gpt-image-1.5`
- Base image: ~$0.10-0.20 per generation
- Grid (4 images): ~$0.15-0.30 per generation
- Total per persona (8 images): ~$0.40-1.00

### RunPod (Proposed System)
- Pricing model: Per-second GPU usage
- Typical cost: $0.50-2.00 per hour (depends on GPU tier)
- Estimated per image: ~$0.05-0.15
- Total per persona (9 images): ~$0.45-1.35

**Note**: Actual RunPod costs depend on:
- GPU tier (A40, A100, etc.)
- Queue time (doesn't count toward billing)
- Generation complexity

---

## Next Steps

### To Integrate RunPod into This Project:

1. **Set up infrastructure:**
   - Create S3 bucket for seed faces
   - Collect/generate seed face dataset (male/female)
   - Configure AWS credentials in `.env`

2. **Create Python client:**
   - Implement `RunPodClient` class (see example above)
   - Add to `services/runpod_client.py`
   - Update `requirements.txt` with dependencies

3. **Test integration:**
   - Create test script in `playground/`
   - Generate test images for one persona
   - Compare quality with OpenAI output

4. **Migrate workflow:**
   - Update task processor to use RunPod
   - Implement fallback to OpenAI (redundancy)
   - Add configuration flag to toggle between systems

5. **Monitor performance:**
   - Track generation times
   - Monitor costs
   - Compare image quality
   - Adjust batch sizes and retry logic as needed

---

## References

### Source Code Locations (customeyes server)

**Main Image Generator:**
- `/tools/aoa/customeyes/services/task-processor/phases/image-generator.js`

**Documentation:**
- `/tools/aoa/customeyes/docs/image-generation-architecture.md`
- `/tools/aoa/customeyes/docs/runpod-v2-migration-plan.md`
- `/tools/aoa/customeyes/docs/image-generation-feature.md`

**Environment:**
- `/tools/aoa/customeyes/.env`
  - `RUNPOD_API=rpa_J35GATUFIYLG7HFV7VZU9V1NMDBYVT6KA6QQJNMSo5wj5l`
  - `RUNPOD_RUN_ENDPOINT=https://api.runpod.ai/v2/7l3f8add2h9701/run`

### Access Credentials

**Server**: backend.electric-marinade.com
**User**: archimedes
**Password**: Chachapuri!2
**Path**: /tools/aoa/customeyes

---

## Support and Troubleshooting

### Common Issues

1. **Job stuck in IN_QUEUE**
   - RunPod workers may be busy
   - Increase polling timeout
   - Check RunPod dashboard for worker status

2. **FAILED status with "Invalid seed face URL"**
   - Seed face URL must be publicly accessible
   - Check S3 bucket permissions
   - Verify URL format

3. **Empty output after COMPLETED**
   - RunPod workflow may have crashed
   - Check RunPod logs for ComfyUI errors
   - Retry with different parameters

4. **Rate limiting (429 errors)**
   - Reduce batch size
   - Add delays between queue requests
   - Contact RunPod support for quota increase

### Debugging

**Enable verbose logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

**Inspect job details:**
```bash
curl -H "Authorization: Bearer {API_KEY}" \
  https://api.runpod.ai/v2/7l3f8add2h9701/status/{jobId}
```

---

## Conclusion

The RunPod ComfyUI system from customeyes provides a **production-ready, battle-tested solution** for AI image generation with:
- Advanced img2img controls (denoising, LoRA strength)
- Facial consistency via seed faces
- Batch processing with retry logic
- Flexible dimensions and post-processing

This system can be integrated into avatar-data-generator to either **replace OpenAI** (full migration) or **complement it** (hybrid approach) for enhanced image generation capabilities.

**Recommended Next Step**: Set up a test integration in `playground/` to generate sample images and compare with current OpenAI output before committing to full migration.
