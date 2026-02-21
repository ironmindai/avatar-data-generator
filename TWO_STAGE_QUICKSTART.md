# Two-Stage Avatar Pipeline - Quick Start

## What is it?

A new two-stage image generation pipeline that produces better quality avatars:

**Stage 1**: Random S3 Face → RunPod/Flux → Diverse Intermediate Face
**Stage 2**: Intermediate Face → OpenAI → Final Avatar (with bio + ethnicity)

## Quick Test

```bash
cd /home/niro/galacticos/avatar-data-generator
source venv/bin/activate
python playground/test_two_stage_pipeline.py
```

Output: `playground/two_stage_test_output/`

## Enable/Disable

Edit `.env`:
```bash
# Enable two-stage pipeline
USE_TWO_STAGE_PIPELINE=True

# Disable (revert to legacy single-stage)
USE_TWO_STAGE_PIPELINE=False
```

## How It Works

1. **When enabled**: If `randomize_face=True`, uses RunPod Stage 1 → OpenAI Stage 2
2. **Automatic fallback**: If RunPod fails, falls back to single-stage OpenAI
3. **Backward compatible**: No API changes, works with existing code

## Configuration

All settings in `.env`:

```bash
# Feature flag
USE_TWO_STAGE_PIPELINE=True

# RunPod API
RUNPOD_API_KEY="rpa_J35GATUFIYLG7HFV7VZU9V1NMDBYVT6KA6QQJNMSo5wj5l"
RUNPOD_ENDPOINT_ID="7l3f8add2h9701"

# Optimized parameters (from testing)
RUNPOD_DENOISE=0.47
RUNPOD_IP_WEIGHT=0.75
RUNPOD_GUIDANCE_SCALE=7.5
RUNPOD_STEPS=30

# Optional: Save intermediate images for debugging
SAVE_INTERMEDIATE_IMAGES=False
```

## Files Changed

- `services/runpod_service.py` - NEW: RunPod Stage 1 implementation
- `services/image_generation.py` - UPDATED: Two-stage pipeline logic
- `.env` - UPDATED: New configuration variables
- `config.py` - UPDATED: Added RunPod config

## Monitoring

Check logs for pipeline activity:
```bash
# Look for these markers in logs
================================================================================
TWO-STAGE PIPELINE ENABLED
Stage 1: RunPod/Flux → Stage 2: OpenAI/DALL-E
================================================================================
STAGE 1: RunPod/Flux Base Face Generation
...
STAGE 2: OpenAI/DALL-E Final Avatar Generation
...
```

## Troubleshooting

**Pipeline not activating?**
- Check `USE_TWO_STAGE_PIPELINE=True` in `.env`
- Verify `randomize_face=True` when calling `generate_base_image()`

**RunPod failures?**
- Pipeline auto-falls back to single-stage OpenAI
- Check RunPod API key is valid
- Verify S3 face URLs are accessible

**Poor quality?**
- Enable `SAVE_INTERMEDIATE_IMAGES=True` to inspect Stage 1 output
- Adjust `RUNPOD_DENOISE` or `RUNPOD_IP_WEIGHT` in `.env`

## Full Documentation

See `docs/two-stage-pipeline.md` for complete details.

## Testing Strategy

1. Run quick test: `python playground/test_two_stage_pipeline.py`
2. Compare outputs with legacy single-stage
3. Monitor logs for fallback frequency
4. Validate ethnicity adherence and diversity
5. Roll out to production if quality improves

---

**Date**: 2026-02-21
**Status**: Ready for Testing
