# RunPod Base Image Generation Guide

**Status**: Tested and ready for integration
**Date**: 2026-02-20
**RunPod Endpoint**: `7l3f8add2h9701`

---

## Executive Summary

This document describes how to use the RunPod ComfyUI endpoint for base image generation in the avatar-data-generator project. RunPod provides superior control over image generation through `denoise` and `ip_adapter_weight` parameters, allowing fine-tuned balance between reference face diversity and ethnicity control.

---

## Golden Parameters ⭐

Based on ethnicity override testing (African male → Swedish female), the optimal parameters are:

```python
{
    "denoise": 0.5,              # Balanced img2img strength
    "ip_adapter_weight": 0.5     # Medium face reference influence (LOWER than customeyes default)
}
```

**Why these work best:**
- **denoise: 0.5** - Maintains good structural diversity from reference face
- **ip_adapter_weight: 0.5** - Reduces reference face ethnicity influence, allowing prompt to control ethnicity
- **Result**: Different reference faces → different output faces, but prompt controls ethnicity

**Comparison to customeyes default:**
- Customeyes uses: `denoise: 0.5, ip_adapter_weight: 0.8`
- Our optimal: `denoise: 0.5, ip_adapter_weight: 0.5` (LOWER ip_weight is key!)

---

## RunPod API Configuration

### Endpoint Details

**API Base**: `https://api.runpod.ai/v2/`

**Run Endpoint**: `https://api.runpod.ai/v2/7l3f8add2h9701/run`

**Status Endpoint**: `https://api.runpod.ai/v2/7l3f8add2h9701/status/{jobId}`

**API Key**: `rpa_J35GATUFIYLG7HFV7VZU9V1NMDBYVT6KA6QQJNMSo5wj5l`

**Endpoint ID**: `7l3f8add2h9701`

### Authentication

All requests require Bearer token:
```bash
Authorization: Bearer rpa_J35GATUFIYLG7HFV7VZU9V1NMDBYVT6KA6QQJNMSo5wj5l
```

---

## Face Generation Request

### Request Payload (Golden Parameters)

```json
{
  "input": {
    "generation_type": "face_generator",
    "random_seeds": [123456, 789012, 345678, 901234],
    "prompt": "Professional headshot of a 25 year old Israeli female. Middle Eastern features, olive skin tone, dark hair, brown eyes.",
    "negative_prompt": "male, (smile:1.2), (hand:1.3), (beard:1.4), (facial hair:1.4), nude, cartoon...",
    "width": 1024,
    "height": 1024,
    "face_image": "https://s3-api.dev.iron-mind.ai/faces/female/image_xyz.jpg",
    "denoise": 0.5,
    "ip_adapter_weight": 0.5,
    "ip_adapter_start": 0.2,
    "ip_adapter_end": 0.6
  }
}
```

### Key Parameters Explained

| Parameter | Type | Description | Golden Value |
|-----------|------|-------------|--------------|
| `generation_type` | string | Must be `"face_generator"` for base images | `"face_generator"` |
| `random_seeds` | array | 4 random integers for variation | `[random, random, random, random]` |
| `prompt` | string | Target persona description (ethnicity, age, gender) | Your bio + ethnicity |
| `negative_prompt` | string | What to avoid (gender-specific) | See below |
| `width` | int | Image width | `1024` |
| `height` | int | Image height | `1024` |
| `face_image` | string | S3 URL to reference face (for diversity) | Random face from S3 |
| `denoise` | float | **CRITICAL**: img2img strength (0.0-1.0) | **0.5** ⭐ |
| `ip_adapter_weight` | float | **CRITICAL**: Face reference influence (0.0-1.0) | **0.5** ⭐ |
| `ip_adapter_start` | float | When to start applying face reference | `0.2` |
| `ip_adapter_end` | float | When to stop applying face reference | `0.6` |

### Understanding denoise and ip_adapter_weight

#### denoise (img2img strength)
- **0.0**: Keep reference face exactly (no generation)
- **0.5**: **OPTIMAL** - Balanced between reference structure and prompt control
- **1.0**: Completely ignore reference (pure txt2img)

**Effect on output:**
- Lower (0.3): More similar to reference structure, less prompt control
- **Medium (0.5)**: Sweet spot - diversity + ethnicity control ⭐
- Higher (0.7-0.8): More prompt control, less reference diversity

#### ip_adapter_weight (face reference influence)
- **0.0**: No face reference (pure txt2img)
- **0.5**: **OPTIMAL** - Medium influence, prompt controls ethnicity ⭐
- **0.8**: High influence (customeyes default, too strong for ethnicity override)
- **1.0**: Maximum face reference influence

**Effect on output:**
- Lower (0.3-0.5): **Better ethnicity control**, reference provides structure only ⭐
- Higher (0.7-0.8): Reference ethnicity bleeds through, harder to override

---

## Gender-Specific Negative Prompts

### For Female Personas
```python
negative_prompt = (
    "male, (smile:1.2), (hand:1.3), (beard:1.4), (facial hair:1.4), "
    "nude, body, porn, nudity, sexual, explicit, erotic, semi-nude, "
    "NSFW, underwear, lingerie, adult, erotic pose, beautiful, gorgeous, "
    "handsome, good looking, sexy, pretty, cartoon, cgi, render, "
    "illustration, painting, drawing, bad quality, grainy, low resolution"
)
```

### For Male Personas
```python
negative_prompt = (
    "female, (smile:1.2), (hand:1.3), "
    "nude, body, porn, nudity, sexual, explicit, erotic, semi-nude, "
    "NSFW, underwear, lingerie, adult, erotic pose, beautiful, gorgeous, "
    "handsome, good looking, sexy, pretty, cartoon, cgi, render, "
    "illustration, painting, drawing, bad quality, grainy, low resolution"
)
```

---

## Job Polling

### 1. Queue Job
```bash
POST https://api.runpod.ai/v2/7l3f8add2h9701/run
Authorization: Bearer {API_KEY}
Content-Type: application/json

{payload}
```

**Response:**
```json
{
  "id": "7l3f8add2h9701-abc123",
  "status": "IN_QUEUE"
}
```

### 2. Poll Status
```bash
GET https://api.runpod.ai/v2/7l3f8add2h9701/status/{jobId}
Authorization: Bearer {API_KEY}
```

**Poll every 10 seconds, max 40 minutes (240 attempts)**

### 3. Status Responses

**In Progress:**
```json
{
  "id": "...",
  "status": "IN_PROGRESS"
}
```

**Completed:**
```json
{
  "id": "...",
  "status": "COMPLETED",
  "output": ["https://minio.electric-marinade.com/aoa/generated-images/xyz.png"]
}
```

**Note:** Output is an **array**, take first element: `output[0]`

**Failed:**
```json
{
  "id": "...",
  "status": "FAILED",
  "error": "Error message"
}
```

**Possible statuses:**
- `IN_QUEUE` - Waiting for worker
- `IN_PROGRESS` - Currently generating
- `COMPLETED` - Success
- `FAILED` - Error
- `CANCELLED` - Cancelled

---

## Test Results Summary

### Ethnicity Override Test (2026-02-20)

**Scenario:** African male reference → Swedish female target

**Tested Parameters:**

| Test | denoise | ip_weight | Result | Notes |
|------|---------|-----------|--------|-------|
| 1. Customeyes Default | 0.5 | 0.8 | Good | Reference ethnicity bleeds through slightly |
| 2. Higher Denoise | 0.7 | 0.8 | Good | More prompt control |
| 3. **Lower IP Weight** ⭐ | **0.5** | **0.5** | **Best** | **Perfect balance - diverse + correct ethnicity** |
| 4. Aggressive Override | 0.7 | 0.5 | Good | Strong ethnicity control |
| 5. Maximum Override | 0.8 | 0.3 | OK | Too much prompt, loses diversity |

**Winner:** Test 3 with `denoise: 0.5, ip_adapter_weight: 0.5`

**Image URL:** https://minio.electric-marinade.com/aoa/generated-images/f0994bd0-bbf3-4773-9987-0cab32d9d687.png

---

## Integration Example (Python)

```python
import asyncio
import httpx
import random

RUNPOD_API_KEY = "rpa_J35GATUFIYLG7HFV7VZU9V1NMDBYVT6KA6QQJNMSo5wj5l"
RUNPOD_ENDPOINT = "7l3f8add2h9701"

async def generate_base_image_runpod(
    prompt: str,
    reference_face_url: str,
    gender: str
) -> str:
    """Generate base image using RunPod with golden parameters."""

    # Gender-specific negative prompt
    if gender.lower() == 'male':
        negative = "female, (smile:1.2), (hand:1.3), nude, cartoon..."
    else:
        negative = "male, (smile:1.2), (hand:1.3), (beard:1.4), (facial hair:1.4), nude, cartoon..."

    # Build payload with GOLDEN PARAMETERS
    payload = {
        "input": {
            "generation_type": "face_generator",
            "random_seeds": [random.randint(0, 1_000_000_000) for _ in range(4)],
            "prompt": prompt,
            "negative_prompt": negative,
            "width": 1024,
            "height": 1024,
            "face_image": reference_face_url,
            "denoise": 0.5,              # GOLDEN ⭐
            "ip_adapter_weight": 0.5,    # GOLDEN ⭐
            "ip_adapter_start": 0.2,
            "ip_adapter_end": 0.6
        }
    }

    # Queue job
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT}/run",
            json=payload,
            headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"}
        )
        job_id = response.json()["id"]

    # Poll for completion
    for _ in range(240):  # 40 minutes max
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT}/status/{job_id}",
                headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"}
            )
            result = response.json()

            if result["status"] == "COMPLETED":
                # Output is array, take first element
                return result["output"][0]
            elif result["status"] in ["FAILED", "CANCELLED"]:
                raise Exception(f"Generation failed: {result.get('error')}")

        await asyncio.sleep(10)

    raise Exception("Timeout after 40 minutes")
```

---

## Cost Comparison

| Service | Cost per Image | Quality | Ethnicity Control | Diversity |
|---------|---------------|---------|-------------------|-----------|
| **OpenAI gpt-image-1.5** | ~$0.04-0.08 | Excellent | Medium (with input_fidelity: low) | Good |
| **RunPod ComfyUI** | ~$0.01-0.02 | Excellent | **Better** (with golden params) | Excellent |

**RunPod advantages:**
- 50-75% cheaper
- Fine-grained control (denoise + ip_adapter_weight)
- Better ethnicity override
- Already containerized and battle-tested (customeyes project)

---

## Next Steps for Integration

1. **Create RunPod service** (`services/runpod_service.py`)
2. **Add configuration** (`.env` already has credentials from customeyes)
3. **Update image_generation.py** to use RunPod for base images
4. **Keep SeeDream** for additional images (already working well)
5. **A/B test** against current OpenAI implementation

---

## Reference Files

- **Test script**: `playground/test_ethnicity_override.py`
- **Diversity matrix test**: `playground/test_diversity_matrix.py`
- **RunPod integration guide**: `docs/runpod-comfyui-integration.md`
- **Customeyes source**: `backend.electric-marinade.com:/tools/aoa/customeyes`

---

## Notes

- The customeyes project has been using RunPod successfully in production
- The ComfyUI workflow is containerized and stable
- Workers warm up after first request (~2-5 min first request, 30-60 sec subsequent)
- Output format is **array of URLs**, always take first element: `output[0]`
- Golden parameters discovered through systematic testing (5 parameter combinations)

---

**Last Updated**: 2026-02-20
**Tested By**: Claude Sonnet 4.5 + User
**Status**: Ready for production integration
