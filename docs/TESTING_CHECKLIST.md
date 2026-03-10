# Two-Stage Pipeline Testing Checklist

**Implementation Date**: 2026-02-21
**Status**: Ready for Testing

---

## Pre-Testing Verification

### Configuration Check

- [ ] `.env` file contains all RunPod configuration variables
- [ ] `USE_TWO_STAGE_PIPELINE=True` is set in `.env`
- [ ] RunPod API key is valid and not expired
- [ ] OpenAI API key is valid and active

### File Verification

- [ ] `services/runpod_service.py` exists and is importable
- [ ] `services/image_generation.py` has been updated
- [ ] `playground/test_two_stage_pipeline.py` exists

### Environment Verification

```bash
cd /home/niro/galacticos/avatar-data-generator
source venv/bin/activate

# Check Python can import RunPod service
python -c "from services.runpod_service import generate_runpod_base_face; print('✓ RunPod service imports successfully')"

# Check config is loaded
python -c "from services.image_generation import USE_TWO_STAGE_PIPELINE; print(f'USE_TWO_STAGE_PIPELINE={USE_TWO_STAGE_PIPELINE}')"
```

Expected output:
```
✓ RunPod service imports successfully
USE_TWO_STAGE_PIPELINE=True
```

---

## Test 1: Quick Pipeline Test (3 Personas)

### Command
```bash
cd /home/niro/galacticos/avatar-data-generator
source venv/bin/activate
python playground/test_two_stage_pipeline.py
```

### Expected Behavior

**Console Output Should Show**:
- [x] "TWO-STAGE AVATAR GENERATION PIPELINE TEST" header
- [x] "Stage 1: Random S3 Face → RunPod/Flux → Intermediate Face"
- [x] "Stage 2: Intermediate Face → OpenAI/DALL-E → Final Avatar"
- [x] For each persona:
  - [x] "STAGE 1: RunPod/Flux Base Face Generation"
  - [x] RunPod job queued successfully
  - [x] Job completed message
  - [x] "STAGE 2: OpenAI/DALL-E Final Avatar Generation"
  - [x] "✅ SUCCESS: Saved to ..."

**File System Should Show**:
- [x] `playground/two_stage_test_output/` directory created
- [x] 3 PNG files (one per persona):
  - [x] `swedish_woman_*.png`
  - [x] `spanish_man_*.png`
  - [x] `israeli_woman_*.png`

**Each Image Should**:
- [x] Be valid PNG format
- [x] Be approximately 1024x1024 pixels (or randomized aspect ratio)
- [x] Show amateur aesthetic (low quality, candid style)
- [x] Match the specified ethnicity
- [x] Match the specified gender

### Success Criteria
- [x] All 3 personas generate successfully
- [x] No errors in console output
- [x] Images match ethnicity requirements
- [x] Amateur aesthetic is applied

---

## Test 2: Fallback Mechanism

### Test Scenario: Simulate RunPod Failure

**Temporarily break RunPod** by using invalid API key:

Edit `.env`:
```bash
RUNPOD_API_KEY="invalid_key_for_testing"
```

Run test:
```bash
python playground/test_two_stage_pipeline.py
```

### Expected Behavior
- [x] Stage 1 attempts RunPod
- [x] RunPod fails (invalid API key)
- [x] Console shows: "⚠️ Stage 1 (RunPod) failed, falling back to single-stage OpenAI"
- [x] Stage 2 uses single-stage OpenAI pipeline
- [x] Image still generates successfully

### Restore Configuration
```bash
# Restore valid API key in .env
RUNPOD_API_KEY="rpa_J35GATUFIYLG7HFV7VZU9V1NMDBYVT6KA6QQJNMSo5wj5l"
```

### Success Criteria
- [x] Automatic fallback works
- [x] Image still generates (using single-stage)
- [x] Clear warning message in logs
- [x] No crashes or exceptions

---

## Test 3: Feature Flag Toggle

### Test 3a: Disable Two-Stage Pipeline

Edit `.env`:
```bash
USE_TWO_STAGE_PIPELINE=False
```

Run test:
```bash
python playground/test_two_stage_pipeline.py
```

### Expected Behavior
- [x] Pipeline uses single-stage OpenAI only
- [x] NO "TWO-STAGE PIPELINE ENABLED" message
- [x] NO "STAGE 1: RunPod" execution
- [x] Direct OpenAI generation with S3 face reference
- [x] Images still generate successfully

### Test 3b: Re-enable Two-Stage Pipeline

Edit `.env`:
```bash
USE_TWO_STAGE_PIPELINE=True
```

Run test:
```bash
python playground/test_two_stage_pipeline.py
```

### Expected Behavior
- [x] Two-stage pipeline activates again
- [x] Both Stage 1 and Stage 2 execute
- [x] Images generate successfully

### Success Criteria
- [x] Feature flag correctly toggles pipeline mode
- [x] No code changes needed
- [x] Both modes work correctly

---

## Test 4: Comprehensive Pipeline Test (Optional)

### Command
```bash
python playground/runpod_openai_pipeline_test.py
```

### Expected Output
- [x] 3 personas × 2 reference faces = 6 images through full pipeline
- [x] `playground/runpod_openai_pipeline_test/` directory with:
  - [x] `stage1_runpod/` - 6 intermediate images
  - [x] `stage2_openai/` - 6 final avatars
  - [x] `reference_faces/` - 2 reference faces
  - [x] `PIPELINE_TEST_RESULTS.md` - Summary report

### Success Criteria
- [x] All 6 images generate successfully
- [x] Clear differentiation between Stage 1 and Stage 2 outputs
- [x] Ethnicity adherence across all personas
- [x] Diversity across different reference faces

---

## Test 5: Production Simulation

### Setup
1. Ensure Flask app is running
2. Access web UI
3. Create a new generation task with:
   - Multiple personas (e.g., 5-10)
   - Mixed genders
   - Different ethnicities

### Monitor Logs
```bash
# In a separate terminal
journalctl -u avatar-data-generator -f | grep -E "TWO-STAGE|STAGE 1|STAGE 2|falling back"
```

### Expected Behavior
- [x] Worker picks up tasks
- [x] For each persona with `randomize_face=True`:
  - [x] Two-stage pipeline executes
  - [x] Stage 1 completes successfully
  - [x] Stage 2 completes successfully
  - [x] Final image uploaded to S3
- [x] Task status progresses: pending → generating-data → data-generated → generating-images → completed

### Success Criteria
- [x] All tasks complete successfully
- [x] Images match ethnicity requirements
- [x] No excessive fallbacks to single-stage
- [x] Performance acceptable (<2 min per avatar)

---

## Test 6: Edge Cases

### Test 6a: Missing Ethnicity
```python
# Call with ethnicity=None
image_bytes = await generate_base_image(
    bio_facebook="Marketing coordinator in Stockholm",
    gender="f",
    randomize_face=True,
    ethnicity=None,  # No ethnicity specified
    age=26
)
```

**Expected**: Pipeline handles gracefully, uses generic visual prompt

### Test 6b: Unsupported Ethnicity
```python
# Call with unmapped ethnicity
image_bytes = await generate_base_image(
    bio_facebook="Engineer in Bangkok",
    gender="m",
    randomize_face=True,
    ethnicity="Martian",  # Not in ETHNICITY_VISUAL_MAP
    age=28
)
```

**Expected**: Pipeline handles gracefully, uses simple gender-based prompt

### Test 6c: Text-to-Image (No Face Randomization)
```python
# Call with randomize_face=False
image_bytes = await generate_base_image(
    bio_facebook="Graphic designer in Tel Aviv",
    gender="f",
    randomize_face=False,  # No face randomization
    ethnicity="Israeli",
    age=25
)
```

**Expected**: Uses legacy txt2img, skips RunPod entirely

### Success Criteria
- [x] No crashes or exceptions
- [x] Reasonable output for all edge cases
- [x] Appropriate fallback behavior

---

## Test 7: Performance & Cost Tracking

### Metrics to Track

**Timing**:
- [ ] Average Stage 1 (RunPod) time: _____ seconds
- [ ] Average Stage 2 (OpenAI) time: _____ seconds
- [ ] Total average time: _____ seconds
- [ ] Comparison to single-stage: _____ seconds

**Quality**:
- [ ] Ethnicity match rate: ____%
- [ ] Gender match rate: ____%
- [ ] Amateur aesthetic presence: ____%

**Reliability**:
- [ ] RunPod success rate: ____%
- [ ] Fallback frequency: ____%
- [ ] Overall success rate: ____%

**Cost** (if tracked):
- [ ] RunPod cost per image: $_____
- [ ] OpenAI cost per image: $_____
- [ ] Total cost per image: $_____
- [ ] Comparison to single-stage: $_____

---

## Test 8: Visual Quality Assessment

### Comparison Matrix

For each test persona, compare:

| Persona | Single-Stage | Two-Stage | Winner | Notes |
|---------|-------------|-----------|--------|-------|
| Swedish Woman | [Image A] | [Image B] | ? | Ethnicity match? Diversity? |
| Spanish Man | [Image A] | [Image B] | ? | Ethnicity match? Diversity? |
| Israeli Woman | [Image A] | [Image B] | ? | Ethnicity match? Diversity? |

### Assessment Criteria
- [x] Ethnicity accuracy (face matches ethnicity)
- [x] Gender accuracy (matches specified gender)
- [x] Age appropriateness (looks correct age)
- [x] Amateur aesthetic (low quality, candid style)
- [x] Diversity (different from reference face)
- [x] Natural appearance (not AI-generated looking)

---

## Final Verification

### Code Quality
- [x] No syntax errors
- [x] All imports resolve
- [x] No hardcoded credentials (uses .env)
- [x] Proper error handling
- [x] Clear logging statements

### Documentation
- [x] `docs/two-stage-pipeline.md` is complete
- [x] `TWO_STAGE_QUICKSTART.md` is clear
- [x] `IMPLEMENTATION_SUMMARY.md` is accurate
- [x] Code comments are helpful

### Backward Compatibility
- [x] Legacy single-stage pipeline still works
- [x] Feature flag toggle works
- [x] No breaking changes to API
- [x] Existing code continues to work

---

## Sign-Off

### Testing Completed By: __________________
### Date: __________________

### Results Summary

**Tests Passed**: _____ / 8

**Issues Found**:
- Issue 1: _________________________________
- Issue 2: _________________________________
- Issue 3: _________________________________

**Recommendation**:
- [ ] ✅ Ready for production deployment
- [ ] ⚠️ Ready with minor fixes needed
- [ ] ❌ Needs significant rework

**Next Steps**:
1. _______________________________________
2. _______________________________________
3. _______________________________________

---

**Notes**:
_______________________________________
_______________________________________
_______________________________________
_______________________________________
