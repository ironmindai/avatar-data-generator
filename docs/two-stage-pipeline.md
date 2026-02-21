# Two-Stage Avatar Generation Pipeline

**Status**: Implemented and Ready for Testing
**Date**: 2026-02-21
**Feature Flag**: `USE_TWO_STAGE_PIPELINE=True`

---

## Overview

The two-stage avatar generation pipeline replaces the single-stage OpenAI generation with a more sophisticated approach that leverages the strengths of two different AI models:

1. **Stage 1 (RunPod/Flux)**: Generate diverse intermediate faces with simple visual prompts
2. **Stage 2 (OpenAI/DALL-E)**: Apply detailed bio, ethnicity control, and amateur aesthetic

---

## Pipeline Flow

### Previous Single-Stage Flow
```
Random S3 Face → OpenAI (with bio/persona) → Final Avatar
```

### New Two-Stage Flow
```
Random S3 Face → RunPod/Flux (simple visual prompt) → Intermediate Face
                                                           ↓
                                         OpenAI (bio/persona/ethnicity) → Final Avatar
```

---

## Why Two Stages?

### Model Strengths

**RunPod/Flux (CLIP-based)**
- ✅ Excellent at visual/aesthetic generation
- ✅ Great for structural diversity
- ✅ Cost-effective (~50-75% cheaper than OpenAI)
- ❌ NOT good at following complex instructions
- ❌ Limited ethnicity control with detailed prompts

**OpenAI/DALL-E**
- ✅ Excellent at instruction-following
- ✅ Superior ethnicity control with detailed prompts
- ✅ Better at applying complex styles (amateur aesthetic)
- ❌ More expensive
- ❌ Can struggle with diversity when using reference faces

### The Solution

By combining both models, we get:
1. **Better diversity** from RunPod's structural variation
2. **Better ethnicity adherence** from OpenAI's instruction-following
3. **Cost optimization** by using cheaper RunPod for preprocessing
4. **Better overall quality** through specialized model usage

---

## Implementation Details

### Stage 1: RunPod/Flux Base Face Generation

**File**: `services/runpod_service.py`

**Input**: Random S3 face URL (from existing face database)

**Prompt Strategy**:
- ❌ NO complex instructions (Flux limitation)
- ✅ Simple visual descriptions (under 20 words)
- ✅ Format: "woman, fair skin, light hair, natural portrait"

**Key Parameters** (Optimized from testing):
```python
denoise = 0.47              # Balanced img2img strength
ip_adapter_weight = 0.75    # Face reference influence
guidance_scale = 7.5        # Prompt adherence
steps = 30                  # Generation quality
```

**Ethnicity Mapping**:
```python
'Swedish' → "fair skin, light hair, Northern European"
'Spanish' → "olive skin, Mediterranean features"
'Israeli' → "olive skin, dark hair, Middle Eastern features"
```

**Output**: Intermediate face image (diverse base structure)

---

### Stage 2: OpenAI Final Avatar Generation

**File**: `services/image_generation.py` (updated)

**Input**: Intermediate face from RunPod Stage 1

**Prompt Strategy**:
- ✅ Full bio with personality details
- ✅ STRONG ethnicity control instructions
- ✅ Amateur aesthetic qualifiers
- ✅ POV selfie framing

**Example Prompt**:
```
Low quality phone camera photo. Shot on old smartphone camera, bad lighting,
not professional. POV selfie. not well-produced, amateur aesthetic, low resolution.
Person: Swedish woman, 26 years old, works as a marketing coordinator in Stockholm.
Enjoys hiking, photography, and visiting cafes. female. Close-up portrait showing
face and upper body. STRONG ETHNIC ADHERENCE REQUIRED: Swedish person with
authentic Swedish facial features and skin tone. Age: 26.
```

**Key Parameters**:
```python
model = "gpt-image-1.5"
input_fidelity = "low"      # Allow creative reinterpretation
size = "1024x1024"          # Or randomized aspect ratio
```

**Output**: Final avatar image with correct ethnicity and personality

---

## Configuration

### Environment Variables (.env)

```bash
# Enable/disable two-stage pipeline
USE_TWO_STAGE_PIPELINE=True   # Set to False for legacy single-stage

# Save intermediate RunPod images for debugging (optional)
SAVE_INTERMEDIATE_IMAGES=False

# RunPod API Configuration
RUNPOD_API_KEY="rpa_J35GATUFIYLG7HFV7VZU9V1NMDBYVT6KA6QQJNMSo5wj5l"
RUNPOD_ENDPOINT_ID="7l3f8add2h9701"
RUNPOD_TIMEOUT=2400           # 40 minutes
RUNPOD_POLL_INTERVAL=10       # Poll every 10 seconds

# Optimized Parameters (from testing)
RUNPOD_DENOISE=0.47
RUNPOD_IP_WEIGHT=0.75
RUNPOD_GUIDANCE_SCALE=7.5
RUNPOD_STEPS=30
```

### Feature Flag

Set `USE_TWO_STAGE_PIPELINE=False` to revert to legacy single-stage OpenAI pipeline.

---

## Error Handling & Fallbacks

### Automatic Fallback

If Stage 1 (RunPod) fails for any reason:
- Pipeline automatically falls back to single-stage OpenAI
- No user intervention required
- Logged as warning in application logs

### Failure Scenarios

1. **RunPod API timeout**: Falls back to OpenAI single-stage
2. **RunPod job fails**: Falls back to OpenAI single-stage
3. **OpenAI Stage 2 fails**: Returns None (same as legacy behavior)
4. **Network issues**: Logs error and retries according to httpx timeout settings

### Logging

All stages are logged with clear markers:
```
================================================================================
TWO-STAGE PIPELINE ENABLED
Stage 1: RunPod/Flux → Stage 2: OpenAI/DALL-E
================================================================================
STAGE 1: RunPod/Flux Base Face Generation
...
STAGE 2: OpenAI/DALL-E Final Avatar Generation
...
```

---

## Testing

### Quick Test Script

**File**: `playground/test_two_stage_pipeline.py`

```bash
cd /home/niro/galacticos/avatar-data-generator
source venv/bin/activate
python playground/test_two_stage_pipeline.py
```

Tests 3 personas (Swedish woman, Spanish man, Israeli woman) through full pipeline.

### Comprehensive Pipeline Test

**File**: `playground/runpod_openai_pipeline_test.py`

Full matrix test with multiple reference faces and personas.

---

## Performance & Cost

### Timing Comparison

| Pipeline | Stage 1 Time | Stage 2 Time | Total Time |
|----------|--------------|--------------|------------|
| Single-Stage (OpenAI only) | - | ~30-60s | 30-60s |
| Two-Stage (RunPod + OpenAI) | ~30-60s | ~30-60s | 60-120s |

**Note**: Two-stage is ~2x slower but produces better quality.

### Cost Comparison

| Pipeline | Cost per Image |
|----------|----------------|
| Single-Stage (OpenAI only) | ~$0.04-0.08 |
| Two-Stage (RunPod + OpenAI) | ~$0.05-0.10 |

RunPod Stage 1: ~$0.01-0.02
OpenAI Stage 2: ~$0.04-0.08
**Total**: Roughly same or slightly higher, but with better quality.

---

## Backward Compatibility

### Maintaining Legacy Support

The two-stage pipeline is **fully backward compatible**:

1. **API interface unchanged**: `generate_base_image()` signature is identical
2. **Feature flag control**: Toggle via `USE_TWO_STAGE_PIPELINE`
3. **Automatic fallback**: If RunPod fails, reverts to legacy behavior
4. **No database changes**: Works with existing schema

### Migration Path

1. **Testing Phase**: Set `USE_TWO_STAGE_PIPELINE=True`, test with small batches
2. **A/B Comparison**: Compare quality against legacy images
3. **Gradual Rollout**: Monitor logs for fallback frequency
4. **Full Deployment**: Once validated, keep enabled

---

## Troubleshooting

### RunPod Stage Fails Frequently

**Symptoms**: Logs show many fallbacks to single-stage
**Causes**:
- RunPod endpoint busy/down
- Network connectivity issues
- Invalid reference face URLs

**Solutions**:
- Check RunPod endpoint status
- Verify S3 face URLs are publicly accessible
- Increase `RUNPOD_TIMEOUT` if needed

### Ethnicity Not Matching

**Symptoms**: Final avatar doesn't match specified ethnicity
**Causes**:
- RunPod Stage 1 dominant (ip_weight too high)
- OpenAI Stage 2 not receiving ethnicity parameter

**Solutions**:
- Reduce `RUNPOD_IP_WEIGHT` (try 0.5 instead of 0.75)
- Verify ethnicity is passed to both stages
- Check logs for prompt content

### Poor Image Quality

**Symptoms**: Images look degraded or artifacted
**Causes**:
- Two-stage compression
- Low quality intermediate image from RunPod

**Solutions**:
- Increase `RUNPOD_STEPS` (try 40-50)
- Adjust `RUNPOD_GUIDANCE_SCALE` (try 8.0-9.0)
- Verify intermediate image quality by enabling `SAVE_INTERMEDIATE_IMAGES=True`

---

## File Structure

```
services/
  ├── image_generation.py         # Updated with two-stage logic
  └── runpod_service.py            # NEW: RunPod Stage 1 implementation

playground/
  ├── test_two_stage_pipeline.py  # Quick test script
  └── runpod_openai_pipeline_test.py  # Comprehensive test

docs/
  ├── two-stage-pipeline.md        # This file
  ├── runpod-base-image-generation.md  # RunPod integration details
  └── runpod-comfyui-integration.md    # ComfyUI workflow details

.env                                 # Configuration (updated)
config.py                            # Flask config (updated)
```

---

## API Reference

### `generate_base_image()`

**Updated signature** (unchanged, backward compatible):
```python
async def generate_base_image(
    bio_facebook: str,
    gender: str,
    randomize_face: bool = False,
    randomize_face_gender_lock: bool = False,
    ethnicity: Optional[str] = None,
    age: Optional[int] = None
) -> Optional[bytes]
```

**Behavior**:
- If `USE_TWO_STAGE_PIPELINE=True` and `randomize_face=True`: Two-stage pipeline
- If `USE_TWO_STAGE_PIPELINE=False`: Legacy single-stage pipeline
- If `randomize_face=False`: Text-to-image (no pipeline, same as before)

### `generate_runpod_base_face()` (New)

```python
async def generate_runpod_base_face(
    reference_face_url: str,
    gender: str,
    ethnicity: Optional[str] = None,
    age: Optional[int] = None,
    save_debug: bool = False
) -> Optional[bytes]
```

**Parameters**:
- `reference_face_url`: S3 URL to reference face
- `gender`: 'm' or 'f'
- `ethnicity`: Optional ethnicity for simple visual prompt
- `age`: Optional age (mostly ignored by Flux)
- `save_debug`: If True, log intermediate image URL

**Returns**: Intermediate face image bytes or None

---

## Best Practices

1. **Monitor Logs**: Check for frequent fallbacks indicating RunPod issues
2. **A/B Testing**: Compare two-stage vs single-stage quality before full deployment
3. **Cost Tracking**: Monitor RunPod + OpenAI costs vs single-stage
4. **Intermediate Images**: Enable `SAVE_INTERMEDIATE_IMAGES=True` during testing
5. **Parameter Tuning**: Adjust RunPod parameters based on quality needs
6. **Fallback Strategy**: Ensure single-stage pipeline is always working as backup

---

## Future Enhancements

Potential improvements:
1. **Caching**: Cache RunPod intermediate images for similar personas
2. **Batch Processing**: Generate multiple Stage 1 images concurrently
3. **Quality Metrics**: Automated quality scoring to compare pipelines
4. **Dynamic Parameters**: Adjust RunPod parameters based on ethnicity complexity
5. **Alternative Models**: Test other Stage 1 models (Stable Diffusion, Midjourney)

---

## References

- **RunPod Integration Guide**: `docs/runpod-base-image-generation.md`
- **ComfyUI Workflow**: `docs/runpod-comfyui-integration.md`
- **Test Results**: `playground/runpod_openai_pipeline_test/PIPELINE_TEST_RESULTS.md`
- **Customeyes Source**: Previous production implementation of RunPod

---

**Last Updated**: 2026-02-21
**Implemented By**: Backend Coder Agent
**Status**: Ready for Testing
