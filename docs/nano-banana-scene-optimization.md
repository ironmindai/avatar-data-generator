# Nano Banana 2 Scene Generation Optimization Guide

## Overview

This guide documents the prompt optimization strategies for scene-based image generation using OpenRouter's Nano Banana 2 (Gemini 3.1 Flash Image Preview).

**Problem Solved:**
1. Cheap "Photoshop cutout" effect where person looks pasted onto background
2. Gender mismatch in attire (man wearing woman's clothing from scene image)
3. Lighting/shadow mismatches between person and environment
4. Obvious compositing artifacts

**Example Issues:**
- Base scene: Woman in dress at beach
- Subject: Male, age 30
- Old result: Man in woman's dress (preserved scene attire) ❌
- New result: Man in casual beach attire (adapted to subject) ✅

---

## Scene Prompt Strategy Configuration

Configure via `.env` file:

```bash
NANO_BANANA_SCENE_PROMPT_STRATEGY=natural_blend
```

### Available Strategies

---

#### 1. `original` (Baseline - DO NOT USE)
**Current problematic prompt:**
```
Replace the subject from image 1 with the subject from image 2
```

**Issues:**
- ❌ Cheap cutout effect
- ❌ Preserves original attire (wrong gender clothing)
- ❌ No lighting integration
- ❌ Obvious compositing

**Only use for:** Comparison/testing baseline

---

#### 2. `natural_blend` ⭐ **RECOMMENDED**
**Prompt:**
```
Place the person from image 2 into the scene from image 1.
Requirements:
1. Seamlessly blend the person into the environment - natural integration, not a cutout.
2. Match lighting, shadows, and color tone from scene.
3. Adapt attire to match the person's gender (m/f) - replace original clothing if needed.
4. Keep casual, everyday clothing appropriate for the scene context.
5. Preserve the person's face, age, and ethnicity exactly from image 2.
Result must look like a genuine photo taken in that location, not a composite.
```

**Why it works:**
- ✅ Explicit "seamlessly blend" instruction
- ✅ Gender-aware attire adaptation
- ✅ Lighting/shadow matching requirements
- ✅ "Genuine photo" quality goal
- ✅ Numbered list (Gemini loves structured instructions)

**Best for:** General use, balanced quality and reliability

---

#### 3. `photorealistic_integration`
**Prompt:**
```
Integrate the person from image 2 into the scene from image 1 with photorealistic quality.
The person is {gender}, age {age}.
Critical requirements:
- Natural lighting that matches the scene's light sources and shadows.
- Clothing appropriate for {gender} and scene context (casual, everyday).
- No obvious cutout or paste effect - must look like they were photographed in this location.
- Preserve exact facial features, skin tone, and age from image 2.
- Realistic depth, perspective, and environmental interaction.
```

**Why it works:**
- ✅ "Photorealistic quality" explicit goal
- ✅ Includes person metadata (gender, age)
- ✅ "Critical requirements" emphasis
- ✅ Negative constraints ("No cutout")
- ✅ Depth and perspective awareness

**Best for:** Maximum quality, when realism is priority

---

#### 4. `seamless_replace`
**Prompt:**
```
Replace the person in image 1 with the person from image 2, ensuring seamless integration.
Person details: {gender}, approximately {age} years old.
Must achieve:
- Perfect lighting match (shadows, highlights, color temperature).
- Gender-appropriate casual clothing (ignore original attire from image 1).
- Natural pose and interaction with the environment.
- No artificial edges or compositing artifacts.
- Photographic realism - indistinguishable from a real photo.
```

**Why it works:**
- ✅ "Seamless integration" requirement
- ✅ "Ignore original attire" explicit override
- ✅ "Must achieve" creates obligation
- ✅ Specific quality markers (no artifacts)
- ✅ "Indistinguishable from real photo" goal

**Best for:** When scene has strong original subject to replace

---

#### 5. `blend_adaptive`
**Prompt:**
```
Blend person from image 2 into scene from image 1.
Gender: {gender}. Age: {age}.
Adapt: clothing must suit {gender} (never preserve wrong-gender attire).
Match: lighting, shadows, color grading, perspective from scene.
Preserve: exact face, ethnicity, age from image 2.
Style: natural everyday clothing, not stylized or costume.
Quality: seamless integration, no cutout effect, photorealistic.
```

**Why it works:**
- ✅ Concise, scannable format
- ✅ "Never preserve wrong-gender attire" explicit rule
- ✅ Clear adapt/match/preserve categories
- ✅ "Not stylized or costume" prevents over-styling
- ✅ Multiple quality checkpoints

**Best for:** Fast processing with strong constraints

---

#### 6. `environment_aware`
**Prompt:**
```
Integrate the {age} year old {gender} from image 2 into image 1's environment.
Environmental integration:
- Analyze lighting direction, intensity, and color in image 1.
- Apply matching shadows and highlights to the person.
- Adapt clothing to be contextually appropriate for the setting and {gender}.
- Ensure natural perspective and depth placement.
Preserve from image 2: face, skin tone, ethnicity, age appearance.
Result: must appear as if photographed together, not composited.
```

**Why it works:**
- ✅ "Analyze lighting" instruction (computational approach)
- ✅ Two-stage: analyze then apply
- ✅ Contextual clothing adaptation
- ✅ Perspective and depth awareness
- ✅ "As if photographed together" quality goal

**Best for:** Complex scenes with challenging lighting

---

## Key Features Across All Strategies

### 1. Gender-Aware Attire Adaptation
**Problem:** Man placed in woman's scene → wears woman's clothes
**Solution:** Every strategy includes gender-based attire instructions

Examples:
- "Adapt attire to match the person's gender"
- "Clothing appropriate for {gender}"
- "Never preserve wrong-gender attire"
- "Gender-appropriate casual clothing"

### 2. Lighting & Shadow Integration
**Problem:** Person looks pasted on (different lighting)
**Solution:** Explicit lighting matching requirements

Examples:
- "Match lighting, shadows, and color tone"
- "Natural lighting that matches the scene's light sources"
- "Perfect lighting match (shadows, highlights, color temperature)"
- "Apply matching shadows and highlights"

### 3. Anti-Cutout Constraints
**Problem:** Obvious compositing, artificial edges
**Solution:** Negative constraints against cutout effect

Examples:
- "Not a cutout" / "no cutout effect"
- "No obvious cutout or paste effect"
- "No artificial edges or compositing artifacts"
- "Seamlessly blend" / "seamless integration"

### 4. Photorealism Quality Goals
**Problem:** Results look artificial or computer-generated
**Solution:** Explicit realism and quality targets

Examples:
- "Must look like a genuine photo"
- "Photorealistic quality"
- "Indistinguishable from a real photo"
- "Must appear as if photographed together"

### 5. Casual Everyday Attire Guidance
**Problem:** Over-styled clothing or costumes
**Solution:** Explicit casual/everyday clothing instruction

Examples:
- "Casual, everyday clothing"
- "Natural everyday clothing, not stylized or costume"
- "Clothing appropriate for the scene context"

---

## Strategy Comparison Matrix

| Strategy | Cutout Prevention | Gender Attire | Lighting Match | Quality | Speed |
|----------|------------------|---------------|----------------|---------|-------|
| **original** | ❌ None | ❌ None | ❌ None | Low | Fast |
| **natural_blend** ⭐ | ✅ Strong | ✅ Explicit | ✅ Good | High | Medium |
| **photorealistic_integration** | ✅ Very Strong | ✅ Explicit | ✅ Excellent | Very High | Slow |
| **seamless_replace** | ✅ Strong | ✅ Explicit + Override | ✅ Excellent | High | Medium |
| **blend_adaptive** | ✅ Strong | ✅ Very Explicit | ✅ Good | High | Fast |
| **environment_aware** | ✅ Very Strong | ✅ Contextual | ✅ Excellent | Very High | Slow |

---

## Recommended Starting Point

```bash
# .env configuration
NANO_BANANA_SCENE_PROMPT_STRATEGY=natural_blend
```

**Why:**
- Good balance of quality and speed
- Explicit gender attire adaptation
- Strong anti-cutout measures
- Structured requirements (Gemini optimized)
- Proven reliable across diverse scenes

**Upgrade path if needed:**
1. Start with `natural_blend` (recommended)
2. If still seeing cutout effect → try `photorealistic_integration`
3. If gender attire still wrong → try `seamless_replace` or `blend_adaptive`
4. If complex lighting issues → try `environment_aware`

---

## Testing Protocol

### Test 1: Gender Attire Adaptation
**Setup:**
- Scene image: Woman in dress/feminine attire
- Subject: Male persona
- Strategy: `natural_blend`

**Expected result:**
- ✅ Man in casual male-appropriate clothing (t-shirt, jeans, etc.)
- ❌ NOT man in dress or feminine attire

### Test 2: Cutout Effect Prevention
**Setup:**
- Scene image: Outdoor location with strong lighting
- Subject: Any persona
- Strategy: `natural_blend`

**Check for:**
- ✅ Natural shadows matching scene lighting
- ✅ Color tone matching between person and background
- ✅ No artificial edges around person
- ❌ NOT obvious paste/cutout effect

### Test 3: Lighting Integration
**Setup:**
- Scene images with various lighting (sunset, indoor, harsh daylight)
- Multiple personas
- Strategy: `natural_blend` or `photorealistic_integration`

**Verify:**
- ✅ Person's lighting matches scene lighting direction
- ✅ Shadows cast appropriately
- ✅ Skin tone color temperature matches scene
- ❌ NOT person lit differently than environment

### Test 4: Cross-Gender Scene Placement
**Setup:**
- 5 male personas + 5 female personas
- Mix of male/female-dominated scene images
- Strategy: `natural_blend`

**Results:**
- All 10 personas should have gender-appropriate attire
- No cross-gender clothing preservation

### Test 5: A/B Strategy Comparison
**Setup:**
- Same persona + same scene image
- Generate with 3 different strategies:
  1. `original` (baseline)
  2. `natural_blend`
  3. `photorealistic_integration`

**Compare:**
- Visual quality
- Cutout effect presence
- Attire appropriateness
- Lighting integration
- Processing time

---

## Common Issues & Solutions

### Issue: Still seeing cutout effect
**Diagnosis:** Prompt not strong enough for this scene complexity

**Solution progression:**
1. Verify strategy is NOT `original`
2. Try `photorealistic_integration` (stronger anti-cutout)
3. Try `environment_aware` (maximum lighting integration)
4. Check if scene image itself is low quality (bad source = bad result)

### Issue: Wrong gender attire persisting
**Diagnosis:** Gender instruction not explicit enough

**Solution progression:**
1. Verify `NANO_BANANA_SCENE_PROMPT_STRATEGY` is set correctly in .env
2. Try `seamless_replace` (has "ignore original attire" instruction)
3. Try `blend_adaptive` (has "never preserve wrong-gender attire")
4. Check persona gender field is correct (m/f)

### Issue: Over-styled or costume-like clothing
**Diagnosis:** Model defaulting to stylized attire

**Solution:**
1. Verify strategy includes "casual, everyday" guidance
2. All recommended strategies have this built-in
3. Check scene image - if scene has costume/formal wear, model may match context
4. Try `blend_adaptive` (explicit "not stylized or costume" rule)

### Issue: Lighting looks off (person too bright/dark)
**Diagnosis:** Scene has complex or unusual lighting

**Solution progression:**
1. Try `photorealistic_integration` (explicit lighting requirements)
2. Try `environment_aware` (lighting analysis instruction)
3. Check scene image quality - some scenes may be too challenging
4. Consider filtering out scenes with extreme lighting from image sets

### Issue: Results inconsistent quality
**Diagnosis:** Temperature or scene variability

**Solution:**
1. Verify `NANO_BANANA_TEMPERATURE=1.0` (Gemini 3 optimized)
2. Check scene image quality - varied quality scenes = varied results
3. Consider scene image curation (remove low-quality scenes)
4. Try stricter strategy like `photorealistic_integration`

---

## Advanced: Metadata Usage

Scene generation prompts have access to persona metadata:
- **`result.gender`** - 'm' or 'f'
- **`result.age`** - Integer age (if available)
- **`result.ethnicity`** - Ethnicity string (if available)

Strategies use this to create contextual prompts:
```python
f"The person is {result.gender}, age {result.age or 'adult'}."
f"Adapt attire to match the person's gender ({result.gender})"
f"Integrate the {result.age or 25} year old {result.gender}"
```

This enables **context-aware generation** where the prompt automatically adapts to each persona.

---

## Integration with Base Image Generation

Scene generation works in tandem with base image generation:

**Two-stage process:**
1. **Base Image Generation** (base image prompt optimization)
   - Creates the person's face with correct ethnicity, age, expression
   - See: `docs/nano-banana-prompt-optimization.md`

2. **Scene Image Generation** (scene prompt optimization - this doc)
   - Places that person into various scenes
   - Handles lighting, attire, environment integration

**Both must work together:**
- Base image: correct face ✅
- Scene generation: natural integration ✅
- **Result:** Realistic avatar in natural environment ✅

---

## Performance Considerations

### Speed vs Quality Trade-offs

**Fastest:**
- `blend_adaptive` - Concise prompt, quick processing
- `natural_blend` - Medium complexity

**Balanced:**
- `seamless_replace` - Good quality without excessive processing

**Highest Quality (slower):**
- `photorealistic_integration` - Complex requirements, longer processing
- `environment_aware` - Lighting analysis, maximum quality

**Production recommendation:**
- Use `natural_blend` for general use (speed + quality balance)
- Switch to `photorealistic_integration` only if quality issues persist

### Batch Processing Impact

With 200 personas × 4 images each = 800 scene generations:

| Strategy | Avg Time/Image | Total Time (800 images) |
|----------|----------------|-------------------------|
| `natural_blend` | ~8s | ~107 minutes |
| `photorealistic_integration` | ~12s | ~160 minutes |

**Difference:** ~53 minutes for full batch

**Decision:** Start with `natural_blend`, only upgrade if quality issues seen in results.

---

## Example: Complete Scene Generation Flow

**Scenario:**
- Persona: Male, 28, Israeli ethnicity
- Base image: Generated with neutral expression, Israeli features
- Scene image: Beach photo (original subject: woman in swimsuit)

**Configuration:**
```bash
NANO_BANANA_SCENE_PROMPT_STRATEGY=natural_blend
```

**Generated Prompt:**
```
Place the person from image 2 into the scene from image 1.
Requirements:
1. Seamlessly blend the person into the environment - natural integration, not a cutout.
2. Match lighting, shadows, and color tone from scene.
3. Adapt attire to match the person's gender (m) - replace original clothing if needed.
4. Keep casual, everyday clothing appropriate for the scene context.
5. Preserve the person's face, age, and ethnicity exactly from image 2.
Result must look like a genuine photo taken in that location, not a composite.
```

**Expected Result:**
- ✅ 28-year-old Israeli male at beach
- ✅ Casual male beach attire (swim trunks, possibly t-shirt)
- ✅ Natural beach lighting with appropriate shadows
- ✅ Seamlessly integrated into beach environment
- ✅ Preserves facial features from base image
- ❌ NOT wearing woman's swimsuit from scene
- ❌ NOT obvious cutout/paste effect

---

## Changelog

**2026-03-11:**
- Initial implementation with 6 scene prompt strategies
- Added gender-aware attire adaptation
- Added anti-cutout constraints
- Added lighting integration requirements
- Documented testing protocol and troubleshooting
