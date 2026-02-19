# Flexible Image Count & History Tracking Update

**Date:** 2026-02-19
**Status:** Complete - Ready for Testing

## Overview

Successfully updated the system to support flexible image counts (1-20) instead of fixed batches of 4, and added image idea history tracking to prevent duplicate image concepts across multiple generation runs.

---

## What Changed

### 1. **Removed Batch-of-4 Constraint** ✅

**Before:**
- Only allowed 4, 8, 12, 16, or 20 images (multiples of 4)
- Generated images in "batches of 4"
- Validation: `if images_per_persona not in [4, 8, 12, 16, 20]`

**After:**
- Supports any number from 1 to 20
- Generates images individually (no batching concept)
- Validation: `if images_per_persona < 1 or images_per_persona > 20`

**Files Modified:**
- `workers/task_processor.py` (lines 770-777)
  - Removed `num_batches` calculation
  - Updated validation to allow 1-20
  - Simplified logging (removed batch references)

---

### 2. **Image Idea History Tracking** ✅

**New Feature:** Prevent duplicate image concepts when generating more images for the same persona.

#### Database Schema Update

**New Column:** `image_ideas_history`
- **Table:** `generation_results`
- **Type:** JSON (JSONB array in PostgreSQL)
- **Nullable:** True
- **Purpose:** Stores array of image idea strings

**Migration:**
- **File:** `migrations/versions/312faec904ca_add_image_ideas_history_to_generation_.py`
- **Applied:** Yes ✅
- **Reversible:** Yes

**Example Data:**
```json
[
  "Mirror selfie in bedroom",
  "Coffee shop laptop work",
  "Gym workout selfie",
  "Beach sunset photo"
]
```

#### Implementation Details

**LLM Chain Update** (`services/image_prompt_chain.py`):

**Changed Return Type:**
```python
# OLD
async def generate_image_prompts(...) -> List[str]:
    return final_prompts

# NEW
async def generate_image_prompts(...) -> tuple[List[str], List[str]]:
    return final_prompts, generated_ideas
```

Now returns:
1. **final_prompts**: Complete prompts with quality modifiers (for image generation)
2. **generated_ideas**: Raw image ideas (for history tracking)

**Task Processor Update** (`workers/task_processor.py`):

1. **Load History** (before prompt generation):
```python
existing_history = result.image_ideas_history or []
if existing_history:
    logger.info(f"Found {len(existing_history)} previous image ideas to avoid")
```

2. **Pass History to LLM**:
```python
prompts, new_ideas = await prompt_chain.generate_image_prompts(
    person_data=person_data,
    num_images=images_per_persona,
    prompts_history=existing_history  # ← Prevents duplicates
)
```

3. **Update History** (after successful generation):
```python
updated_history = existing_history + new_ideas
result.image_ideas_history = updated_history
flag_modified(result, 'image_ideas_history')
db.session.commit()
```

**How It Works:**

1. First generation (4 images):
   - History is empty `[]`
   - Generates 4 new ideas
   - Saves: `["idea1", "idea2", "idea3", "idea4"]`

2. Second generation (3 more images):
   - Loads history: `["idea1", "idea2", "idea3", "idea4"]`
   - LLM avoids these 4 ideas
   - Generates 3 new unique ideas
   - Saves: `["idea1", "idea2", "idea3", "idea4", "idea5", "idea6", "idea7"]`

3. Third generation:
   - Loads all 7 previous ideas
   - Generates only new concepts
   - And so on...

---

### 3. **Frontend UI Update** ✅

**File:** `templates/generate.html`

**Changes:**

**Number Input:**
```html
<!-- OLD -->
<input type="number" min="4" max="20" step="4" value="4" />

<!-- NEW -->
<input type="number" min="1" max="20" step="1" value="4" />
```

**Range Slider:**
```html
<!-- OLD -->
<input type="range" min="4" max="20" step="4" value="4" />

<!-- NEW -->
<input type="range" min="1" max="20" step="1" value="4" />
```

**Help Text:**
```html
<!-- OLD -->
Choose the number of unique avatar images to generate for each persona (4-20, increments of 4)

<!-- NEW -->
Choose the number of unique avatar images to generate for each persona (1-20)
```

**User Experience:**
- Can now select: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20
- Slider moves in increments of 1
- Default remains 4 images

---

## Benefits

### 1. **Flexibility**
- Generate exactly the number of images needed (not forced to multiples of 4)
- Perfect for testing (generate just 1-2 images)
- Budget control (generate 5 images instead of forced 8)

### 2. **No Duplicates**
- System remembers all previous image ideas per persona
- Can generate 5 images today, 10 more tomorrow - no repeats
- LLM actively avoids previously used concepts

### 3. **Better UX**
- More granular control in UI
- Can incrementally add images (e.g., add 2 more to existing 7)
- Smoother workflow for iterative generation

---

## Testing Checklist

### Test Case 1: Single Image Generation
```
Persona: Test User
First run: 1 image
Expected: Generates 1 image, saves 1 idea to history
```

### Test Case 2: Incremental Generation
```
Persona: Test User
First run: 4 images → History: 4 ideas
Second run: 3 images → History: 7 ideas (4 + 3)
Third run: 2 images → History: 9 ideas (7 + 2)
Expected: No duplicate image concepts
```

### Test Case 3: Maximum Images
```
Persona: Test User
First run: 20 images
Expected: Generates 20 images successfully
```

### Test Case 4: History Prevents Duplicates
```
Persona: Test User
First run: 10 images
Second run: 5 images
Expected: Check logs - should see "Found 10 previous image ideas to avoid"
New ideas should be different from first 10
```

### Test Case 5: UI Validation
```
Frontend:
- Slider should allow values 1-20
- Number input should allow 1-20
- Default value: 4
- Step: 1 (smooth sliding)
```

---

## Database Migration

### Apply Migration
Already applied ✅

### Verify Migration
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'generation_results'
AND column_name = 'image_ideas_history';
```

Expected Output:
```
column_name          | data_type | is_nullable
---------------------|-----------|-------------
image_ideas_history  | jsonb     | YES
```

### Rollback (if needed)
```bash
source venv/bin/activate
flask db downgrade
```

**Warning:** Rollback will delete all image ideas history data!

---

## Code Changes Summary

### Modified Files

1. **workers/task_processor.py**
   - Removed batch constraint validation
   - Added history loading logic
   - Updated prompt generation to use history
   - Added history saving after generation
   - Updated logging (removed batch references)

2. **services/image_prompt_chain.py**
   - Changed return type to tuple (prompts, ideas)
   - Returns both final prompts and raw ideas

3. **templates/generate.html**
   - Updated min/max/step for number input
   - Updated min/max/step for range slider
   - Updated help text

4. **models.py**
   - Added `image_ideas_history` column definition

5. **migrations/versions/312faec904ca_*.py**
   - NEW: Database migration file

---

## Logs to Monitor

When testing, watch for these log entries:

### First Generation
```
[Task XXX] [Persona Name] PHASE 1: Generating 5 prompts using local LLM chain...
[Task XXX] [Persona Name] PHASE 1 COMPLETE: Generated 5 prompts with 5 new ideas
[Task XXX] [Persona Name] UPDATED history: 0 → 5 total ideas
```

### Subsequent Generation
```
[Task XXX] [Persona Name] Found 5 previous image ideas to avoid
[Previous ideas: ['idea1', 'idea2', 'idea3', 'idea4', 'idea5']]
[Task XXX] [Persona Name] PHASE 1: Generating 3 prompts using local LLM chain...
[Task XXX] [Persona Name] PHASE 1 COMPLETE: Generated 3 prompts with 3 new ideas
[Task XXX] [Persona Name] UPDATED history: 5 → 8 total ideas
```

---

## Backwards Compatibility

### Existing Tasks
- ✅ Old validation (4/8/12/16/20) will still work
- ✅ Existing records with no history will have `image_ideas_history = null`
- ✅ First generation for these records will start tracking history

### New Tasks
- ✅ Can use any value 1-20
- ✅ History tracking starts automatically

---

## Known Limitations

1. **History is Per-Persona**
   - Each persona has independent history
   - No cross-persona duplicate detection
   - (This is intentional - different people can have similar images)

2. **History Grows Indefinitely**
   - No auto-cleanup of history
   - After 100+ generations, history array could be large
   - (Performance impact minimal - JSONB is efficient)

3. **Manual History Reset**
   - If you want to allow repeats, manually clear history:
   ```sql
   UPDATE generation_results
   SET image_ideas_history = NULL
   WHERE id = XXX;
   ```

---

## Next Steps

1. **Test with 1 image generation**
2. **Test incremental generation** (4 → 3 → 2)
3. **Verify history prevents duplicates**
4. **Monitor logs for history loading/saving**
5. **Check frontend UI responsiveness** (slider smoothness)

---

## Support

- **Database Schema:** `docs/database-schema-manager.md`
- **Migration Files:** `migrations/versions/`
- **Models:** `models.py`
- **Task Processor:** `workers/task_processor.py`

---

**All changes complete and ready for testing!** 🚀

Generate a task with any number from 1-20 images and watch the magic happen!
