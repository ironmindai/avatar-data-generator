# Nano Banana 2 Prompt Optimization Guide

## Overview

This guide documents the prompt optimization strategies for base image generation using OpenRouter's Nano Banana 2 (Gemini 3.1 Flash Image Preview).

**Problem Solved:** When using a random S3 face as a seed (for diversity), the model sometimes preserves ethnic features from the reference image instead of fully converting to the target ethnicity.

**Example Issue:**
- Random seed: Asian face
- Target: Israeli male, age 23
- Result: Mixed features (Asian + Israeli) instead of pure Israeli

---

## Prompt Strategy Configuration

Configure via `.env` file:

```bash
NANO_BANANA_PROMPT_STRATEGY=transform_explicit
```

### Available Strategies

#### 1. `original` (Baseline)
**Current production prompt:**
```
based on this face, create a {gender} version of a {age} year old, {ethnicity} ethnicity
```

**Issue:** Too much weight on reference image, preserves source ethnicity.

---

#### 2. `transform_explicit` ⭐ **RECOMMENDED**
**Prompt:**
```
Transform this face into a {age} year old {ethnicity} {gender}.
Complete ethnic conversion required: {ethnicity} skin tone, {ethnicity} facial features, {ethnicity} bone structure.
```

**Why it works:**
- ✅ "Transform" = strong conversion verb
- ✅ "Complete ethnic conversion" = explicit override
- ✅ Repeats ethnicity 3x for emphasis
- ✅ Specifies what must change (skin, features, bone structure)

**Best for:** Strong ethnic override while keeping structural diversity

---

#### 3. `convert_preserve`
**Prompt:**
```
Convert this person into a {age} year old {ethnicity} {gender}.
Preserve only: face shape variation and head structure.
Replace everything else: make skin tone, eyes, nose, lips, and all features authentically {ethnicity}.
```

**Why it works:**
- ✅ "Convert" = direct transformation
- ✅ Explicit preserve/replace instructions
- ✅ Lists specific features to replace

**Best for:** Maximum control over what to keep/change

---

#### 4. `remake_nuclear`
**Prompt:**
```
Remake this face as a completely {ethnicity} person. Age: {age}. Gender: {gender}.
All ethnic characteristics must be {ethnicity}, not from the original image.
Use original only for structural diversity.
```

**Why it works:**
- ✅ "Remake" = complete reconstruction
- ✅ "Completely {ethnicity}" = absolute requirement
- ✅ Negative constraint ("not from original")

**Best for:** Maximum ethnic override, minimal reference influence

---

#### 5. `recreate_balanced`
**Prompt:**
```
Recreate this as a {age} year old {ethnicity} {gender}.
Keep: general facial structure for variation.
Change: all ethnic features to authentic {ethnicity} - skin, eyes, nose, bone structure.
```

**Why it works:**
- ✅ Clear keep/change dichotomy
- ✅ "Authentic" keyword for quality
- ✅ Balanced preservation vs override

**Best for:** Balanced approach when diversity is priority

---

#### 6. `two_step`
**Prompt:**
```
Step 1: Identify the face shape and basic structure.
Step 2: Generate a new {age} year old {ethnicity} {gender} using that structure,
with completely {ethnicity} ethnic features and skin tone.
```

**Why it works:**
- ✅ Pipeline instruction (Gemini understands multi-step)
- ✅ Separates structure extraction from generation
- ✅ "Completely {ethnicity}" in generation step

**Best for:** Complex transformations, high model capability

---

#### 7. `negative_positive`
**Prompt:**
```
Convert this face to {ethnicity} ethnicity. Target: {age} year old {ethnicity} {gender}.
DO NOT preserve: ethnic features from source.
DO preserve: face shape outline for variation.
Result must be 100% {ethnicity} in appearance.
```

**Why it works:**
- ✅ Explicit DO/DON'T constraints
- ✅ "100% {ethnicity}" = absolute requirement
- ✅ Clear negative constraints prevent feature leakage

**Best for:** When other methods fail, maximum clarity

---

#### 8. `authentic_repeat`
**Prompt:**
```
Transform into an authentic {ethnicity} person: {age} year old {gender}.
Authentic {ethnicity} skin tone, authentic {ethnicity} facial features.
Use reference only for pose and face shape diversity.
```

**Why it works:**
- ✅ "Authentic" repeated 3x (quality marker for Gemini)
- ✅ Limits reference use explicitly
- ✅ Emphasizes natural/realistic output

**Best for:** High-quality, natural-looking results

---

#### 9. `percentage`
**Prompt:**
```
Convert this face: 100% {ethnicity} ethnic features required, 0% preservation of source ethnicity.
Age {age}, {gender}. Use source only for structural variation (head shape, face proportions).
```

**Why it works:**
- ✅ Quantitative constraints (100%/0%)
- ✅ Mathematical precision appeals to Gemini
- ✅ Explicit structural use case

**Best for:** When you need absolute ethnic purity

---

#### 10. `as_if`
**Prompt:**
```
Transform this person as if they were born {ethnicity}. Age: {age}, Gender: {gender}.
Keep the general face structure for diversity, but replace all ethnic characteristics
with authentic {ethnicity} features.
```

**Why it works:**
- ✅ "As if born" = complete genetic rewrite
- ✅ Natural language Gemini understands well
- ✅ Balances diversity with ethnic accuracy

**Best for:** Natural language fans, intuitive approach

---

## Temperature Configuration

```bash
NANO_BANANA_TEMPERATURE=1.0
```

### What Temperature Does
- **NOT image weight** (that's more like `guidance_scale`)
- **Controls randomness/creativity** in generation
- `0.0` = deterministic, strict prompt following
- `1.0` = default, balanced (GEMINI 3 OPTIMIZED)
- `2.0` = maximum creativity/variation

### ⚠️ Important: Gemini 3.1 Temperature Warning

According to [Google's Gemini 3 documentation](https://ai.google.dev/gemini-api/docs/gemini-3):

> **Gemini 3 models are optimized for temperature=1.0**
>
> Values < 1.0 may cause degraded performance, including:
> - Looping behavior
> - Unexpected outputs
> - Poor reasoning quality

**Recommendation:** Keep at `1.0` unless you have a specific reason to change it.

**Testing Lower Values:**
If you want to try lower temperature for stricter prompt adherence:
- Start at `0.9` and test
- Monitor for quality degradation
- Compare results with `1.0` baseline

---

## Testing Protocol

### Quick Test (Single Persona)
1. Set strategy in `.env`: `NANO_BANANA_PROMPT_STRATEGY=transform_explicit`
2. Generate 1 persona with challenging combination (e.g., Asian seed → Israeli result)
3. Review base image for ethnic accuracy
4. Compare with `original` strategy

### A/B Comparison Test
1. Generate 10 personas with strategy A
2. Generate 10 personas with strategy B
3. Compare ethnic accuracy across both sets
4. Look for:
   - Ethnic feature leakage from seed
   - Skin tone accuracy
   - Facial structure preservation (good diversity)
   - Overall authenticity

### Full Production Test
1. Select 2-3 strategies to test
2. Run on 50 personas each
3. Analyze results:
   - Ethnic accuracy rate
   - Diversity/uniqueness
   - Quality/realism
4. Choose winner for production

---

## Expression Normalization

### Problem: Seed Image Expression Leakage

**Issue:**
- Random S3 seed has closed eyes → generated person has closed eyes
- Random S3 seed is shouting → generated person looks aggressive
- Random S3 seed looks sad → generated person inherits sadness

**Solution:** Expression normalization automatically neutralizes expressions from seed images.

### Configuration

```bash
# Enable expression normalization (RECOMMENDED)
NANO_BANANA_NORMALIZE_EXPRESSION=True

# Choose target expression style
NANO_BANANA_EXPRESSION_STYLE=neutral_natural
```

### Expression Styles

#### 1. `neutral_natural` ⭐ **RECOMMENDED**
**Instruction added to prompt:**
```
Eyes must be OPEN and looking at camera.
Neutral, relaxed facial expression with natural slight smile.
No extreme emotions (no shouting, crying, laughing).
Calm, approachable demeanor.
```

**Best for:** Professional-looking avatars, natural social media profiles

---

#### 2. `slight_smile`
**Instruction:**
```
Eyes OPEN, looking at camera.
Slight friendly smile, warm and approachable.
Ignore any extreme expressions from reference image.
```

**Best for:** Friendly, approachable personas

---

#### 3. `relaxed`
**Instruction:**
```
Eyes OPEN. Completely relaxed face, neutral expression.
No tension, no extreme emotions from source.
Natural, at-ease appearance.
```

**Best for:** Casual, authentic-looking profiles

---

#### 4. `candid`
**Instruction:**
```
Eyes OPEN. Natural candid expression as if caught in a genuine moment.
Not posed, not exaggerated. Replace any extreme expressions from source.
```

**Best for:** Realistic, "caught in the moment" aesthetics

---

#### 5. `friendly`
**Instruction:**
```
Eyes OPEN, gentle smile. Friendly, warm expression.
Approachable and positive demeanor.
Neutralize any negative or extreme expressions from reference.
```

**Best for:** Positive, welcoming personas

---

### Key Features

**Explicit "Eyes OPEN" Constraint:**
- Prevents closed-eye inheritance from seed
- Ensures all personas are looking at camera
- Critical for profile photos

**Negative Constraints:**
- "No extreme emotions"
- "Ignore expressions from reference"
- "Replace extreme expressions from source"
- Tells model what NOT to preserve

**Positive Guidance:**
- Specifies exact expression desired
- Consistent output across all personas
- Natural, believable results

---

### Testing Expression Normalization

**Before enabling:**
```bash
NANO_BANANA_NORMALIZE_EXPRESSION=False
```
Generate 5 personas → observe expression variety (may include closed eyes, shouting, etc.)

**After enabling:**
```bash
NANO_BANANA_NORMALIZE_EXPRESSION=True
NANO_BANANA_EXPRESSION_STYLE=neutral_natural
```
Generate 5 personas → all should have open eyes, neutral/friendly expression

---

## Gender-Appropriate Attire Control

### Problem: Wrong-Gender Clothing in Base Images

**Issue:**
- Reference face: Woman in dress
- Target: Male persona
- Old result: Male with feminine attire from reference
- New result: Male with casual male-appropriate clothing

**Solution:** Attire control automatically ensures gender-appropriate clothing in base images.

### Configuration

```bash
# Enable attire control (RECOMMENDED)
NANO_BANANA_BASE_ATTIRE_CONTROL=True
```

### How It Works

Adds gender-appropriate attire instruction to all base image prompts:

**Instruction added:**
```
Clothing: casual, everyday attire appropriate for {gender}
(never preserve wrong-gender clothing from reference image).
Natural, not stylized or costume.
```

**Example:**
- **Reference:** Asian woman in dress
- **Target:** Israeli male, age 28
- **With attire control:** Male in casual male clothing (t-shirt, etc.)
- **Without attire control:** Risk of feminine attire preservation

### Key Features

**Gender-Appropriate:**
- Male personas get male clothing
- Female personas get female clothing
- Never preserves wrong-gender attire from reference

**Casual & Natural:**
- "Casual, everyday attire"
- "Not stylized or costume"
- Prevents over-styled or formal results

**Explicit Override:**
- "Never preserve wrong-gender clothing from reference"
- Strong negative constraint
- Ensures attire matches target gender

### Integration with Scene Generation

This feature mirrors the attire control in scene generation:

**Base Image (Step 1):**
- Generates person with correct ethnicity, expression, AND attire
- Base image ready for scene integration

**Scene Integration (Step 2):**
- Places person into various scenes
- Also has attire control to ensure gender-appropriate clothing in scenes

**Result:**
- Double layer of attire protection
- Consistent gender-appropriate clothing throughout pipeline

---

## Recommended Starting Point

```bash
# .env configuration
NANO_BANANA_PROMPT_STRATEGY=transform_explicit
NANO_BANANA_TEMPERATURE=1.0
NANO_BANANA_NORMALIZE_EXPRESSION=True
NANO_BANANA_EXPRESSION_STYLE=neutral_natural
NANO_BANANA_BASE_ATTIRE_CONTROL=True
```

**Why:**
- `transform_explicit` = proven strong override
- `temperature=1.0` = Gemini 3 optimized default
- Good balance of ethnic accuracy + diversity

**Next Steps:**
1. Test with current challenging cases (Asian → Israeli, etc.)
2. If still seeing ethnic leakage, try `convert_preserve` or `remake_nuclear`
3. Monitor quality across 20-30 generations
4. Fine-tune based on results

---

## Troubleshooting

### Issue: Still seeing ethnic feature leakage
**Solution:** Try stronger strategies in order:
1. `transform_explicit` (current)
2. `convert_preserve` (more explicit)
3. `negative_positive` (DO/DON'T constraints)
4. `remake_nuclear` (maximum override)

### Issue: Results look too similar (losing diversity)
**Solution:** Balance approaches:
1. Check if temperature is too low (should be 1.0)
2. Try `recreate_balanced` or `as_if` for better diversity preservation
3. Ensure random face pool is diverse

### Issue: Quality degradation
**Solution:**
1. Verify temperature is at 1.0 (Gemini 3 optimized)
2. Try `authentic_repeat` strategy (emphasizes quality)
3. Check reference image quality (bad seed = bad result)

### Issue: Still seeing closed eyes or extreme expressions
**Solution:**
1. Verify `NANO_BANANA_NORMALIZE_EXPRESSION=True` in .env
2. Try more explicit expression style:
   - `neutral_natural` (default, strong constraints)
   - `relaxed` (even more explicit about neutralization)
3. Check if expression instruction is being logged
4. If still failing, try combining with `negative_positive` prompt strategy (has stronger DO/DON'T constraints)

### Issue: Expressions look too similar/robotic
**Solution:**
1. Try `candid` expression style for more variation
2. Verify temperature is at 1.0 (not too low)
3. Consider `slight_smile` or `friendly` for more warmth
4. Balance: expression normalization vs natural variety

### Issue: Wrong-gender clothing in base images
**Solution:**
1. Verify `NANO_BANANA_BASE_ATTIRE_CONTROL=True` in .env
2. Check if attire instruction is being logged
3. If still seeing wrong-gender clothing, try stronger prompt strategy like `convert_preserve` or `negative_positive`
4. Review reference images - some may have ambiguous clothing

### Issue: Over-styled or formal attire in base images
**Solution:**
1. Attire control already includes "casual, everyday" and "not stylized or costume"
2. If still too formal, may be inheriting from reference images
3. Consider curating reference image sources (S3 faces or datasets)
4. Verify reference images have casual clothing

---

## Advanced: Custom Strategies

You can add custom strategies by editing `services/image_generation.py` around line 245:

```python
elif prompt_strategy == 'my_custom_strategy':
    simple_prompt = f"Your custom prompt here with {ethnicity}, {age}, {gender_word}"
```

Then use in `.env`:
```bash
NANO_BANANA_PROMPT_STRATEGY=my_custom_strategy
```

---

## Sources & References

- [Nano Banana 2 on OpenRouter](https://openrouter.ai/google/gemini-3.1-flash-image-preview)
- [Gemini 3 Developer Guide](https://ai.google.dev/gemini-api/docs/gemini-3)
- [OpenRouter API Documentation](https://openrouter.ai/docs)

---

## Example: Complete Prompt Construction

With recommended settings:
```bash
NANO_BANANA_PROMPT_STRATEGY=transform_explicit
NANO_BANANA_NORMALIZE_EXPRESSION=True
NANO_BANANA_EXPRESSION_STYLE=neutral_natural
NANO_BANANA_BASE_ATTIRE_CONTROL=True
NANO_BANANA_TEMPERATURE=1.0
```

**Input:**
- Random seed: Asian woman in dress, closed eyes, shouting expression
- Target: Israeli male, age 23

**Generated Prompt:**
```
Transform this face into a 23 year old Israeli male.
Complete ethnic conversion required: Israeli skin tone, Israeli facial features, Israeli bone structure.
Eyes must be OPEN and looking at camera.
Neutral, relaxed facial expression with natural slight smile.
No extreme emotions (no shouting, crying, laughing).
Calm, approachable demeanor.
Clothing: casual, everyday attire appropriate for male (never preserve wrong-gender clothing from reference image). Natural, not stylized or costume.
```

**Result:**
- ✅ Israeli ethnicity (not Asian)
- ✅ Male gender (not female)
- ✅ Eyes open, looking at camera
- ✅ Neutral, friendly expression (not shouting)
- ✅ Casual male attire (not dress)
- ✅ Age-appropriate appearance
- ✅ Maintains structural diversity from seed (face shape, proportions)

---

## Quick Reference: What Gets Preserved vs Replaced

### ✅ PRESERVED from Random Seed (for diversity)
- Face shape outline/structure
- Head proportions
- General facial geometry
- Structural variation

### ❌ REPLACED from Prompt Instructions
- Ethnicity (skin tone, features, bone structure)
- Age appearance
- Gender characteristics
- Facial expression
- Eye state (open/closed)
- Emotional state
- **Clothing/attire** ← NEW!

---

## Changelog

**2026-03-11:**
- Initial implementation with 10 prompt strategies
- Added temperature configuration with Gemini 3 optimization
- Added expression normalization with 5 expression styles
- Documented testing protocol and recommendations
