# Base Image Face Source Configuration

## Overview

This guide documents how to configure the source for random face images used in base image generation.

**Two Sources Available:**
1. **S3 Faces Bucket** (Default) - Dedicated bucket with male/female folders
2. **Image Datasets** (New) - Use any curated dataset as face source

---

## Configuration

### Option 1: S3 Faces Bucket (Default)

**Use when:**
- You have a dedicated faces bucket with gender-organized folders
- You want gender filtering (male/female)
- You want a separate, curated collection of face images

**Configuration:**
```bash
# .env
BASE_IMAGE_FACE_SOURCE=s3_faces
```

**Structure:**
```
s3://faces/
├── male/
│   ├── face1.jpg
│   ├── face2.png
│   └── ...
└── female/
    ├── face1.jpg
    ├── face2.png
    └── ...
```

**Features:**
- ✅ Gender filtering supported
- ✅ Separate male/female folders
- ✅ Fast random selection
- ✅ Gender lock option (`randomize_face_gender_lock`)

**Gender Lock Behavior:**
- `randomize_face_gender_lock=True` → Male persona gets male faces, female gets female
- `randomize_face_gender_lock=False` → Any persona gets faces from both folders

---

### Option 2: Image Datasets

**Use when:**
- You want to use existing image datasets as face sources
- You have curated datasets with diverse faces
- Gender filtering is not needed/desired
- You want more control over face source quality

**Configuration:**
```bash
# .env
BASE_IMAGE_FACE_SOURCE=image_datasets
BASE_IMAGE_DATASET_IDS=1,2,3
```

**Example:**
```bash
# Use datasets 5, 7, and 12 as face sources
BASE_IMAGE_FACE_SOURCE=image_datasets
BASE_IMAGE_DATASET_IDS=5,7,12
```

**Features:**
- ✅ Use any dataset as face source
- ✅ Multiple datasets supported (comma-separated)
- ✅ Random selection across all specified datasets
- ⚠️ Gender filtering NOT supported (datasets don't have gender metadata)

**Behavior:**
- Randomly selects from ALL images across specified datasets
- Ignores gender and gender_lock settings
- Uses dataset images directly as face references

---

## Comparison Matrix

| Feature | S3 Faces Bucket | Image Datasets |
|---------|----------------|----------------|
| **Gender Filtering** | ✅ Supported | ❌ Not supported |
| **Gender Lock** | ✅ Works | ❌ Ignored |
| **Multiple Sources** | Single bucket | Multiple datasets |
| **Source Control** | Dedicated bucket | Reuse existing datasets |
| **Setup Complexity** | Requires face bucket | Use existing datasets |
| **Diversity Control** | Folder-based | Dataset-based |

---

## When to Use Each Source

### Use S3 Faces Bucket When:
1. You want gender-specific face selection
2. You have a dedicated collection of face portraits
3. You need consistent face quality/type
4. You want separate male/female control
5. You're using gender lock feature

### Use Image Datasets When:
1. You have high-quality curated datasets
2. Gender filtering is not important
3. You want to leverage existing dataset investments
4. You want more granular control (pick specific datasets)
5. You want to quickly test different face sources

---

## Setup Instructions

### Setup 1: S3 Faces Bucket (Default)

**Step 1: Create bucket structure**
```bash
# On MinIO server
mc mb myminio/faces
mc mb myminio/faces/male
mc mb myminio/faces/female
```

**Step 2: Upload faces**
```bash
# Upload male faces
mc cp male_faces/*.jpg myminio/faces/male/

# Upload female faces
mc cp female_faces/*.jpg myminio/faces/female/
```

**Step 3: Configure .env**
```bash
BASE_IMAGE_FACE_SOURCE=s3_faces
```

**Step 4: Test**
- Generate personas with gender lock enabled
- Verify males get male faces, females get female faces

---

### Setup 2: Image Datasets

**Step 1: Identify dataset IDs**
- Go to Web UI → Datasets
- Note the IDs of datasets you want to use
- Example: "Diverse Faces" = ID 5, "Portrait Studio" = ID 7

**Step 2: Configure .env**
```bash
BASE_IMAGE_FACE_SOURCE=image_datasets
BASE_IMAGE_DATASET_IDS=5,7
```

**Step 3: Test**
- Generate personas
- Check logs to see which dataset images are selected
- Verify face quality and diversity

**Step 4: Adjust as needed**
- Add more datasets for more variety
- Remove datasets with poor quality
- Curate datasets specifically for face sourcing

---

## How It Works Internally

### S3 Faces Flow:
```
1. Check gender and gender_lock setting
2. Determine folder (male/ or female/ or both)
3. List available images in folder(s)
4. Randomly select one image
5. Download from S3 public URL
6. Use as reference for Nano Banana 2
```

### Image Datasets Flow:
```
1. Query database for images in specified datasets
2. Randomly select one image (ORDER BY random())
3. Download from image URL (S3 or external)
4. Use as reference for Nano Banana 2
5. Gender settings ignored (datasets have no gender metadata)
```

---

## Migration Guide

### Migrating from S3 Faces to Datasets

**Why migrate:**
- Better face quality from curated datasets
- More control over face sources
- Easier to test different face collections

**Steps:**
1. Create new dataset(s) for faces
2. Upload faces to dataset via Web UI
3. Note dataset ID(s)
4. Update .env:
   ```bash
   BASE_IMAGE_FACE_SOURCE=image_datasets
   BASE_IMAGE_DATASET_IDS=10,11
   ```
5. Test generation
6. Compare results with old S3 faces method

**Note:** You'll lose gender filtering, so ensure your dataset has good gender diversity.

---

### Migrating from Datasets to S3 Faces

**Why migrate:**
- Need gender filtering
- Want separate male/female control
- Better organization for faces specifically

**Steps:**
1. Export images from datasets
2. Organize into male/ and female/ folders
3. Upload to S3 faces bucket
4. Update .env:
   ```bash
   BASE_IMAGE_FACE_SOURCE=s3_faces
   ```
5. Enable gender lock if desired
6. Test with male and female personas

---

## Advanced Configuration

### Using Both Sources (Advanced)

While you can't use both simultaneously, you can **switch between them easily**:

**Testing scenario:**
```bash
# Test with S3 faces
BASE_IMAGE_FACE_SOURCE=s3_faces

# Generate 10 personas, review quality

# Test with datasets
BASE_IMAGE_FACE_SOURCE=image_datasets
BASE_IMAGE_DATASET_IDS=5,7,12

# Generate 10 personas, compare quality

# Choose the better source for production
```

### Dynamic Dataset Selection

You can change dataset IDs without restarting:
```bash
# Morning: Use high-quality studio portraits
BASE_IMAGE_DATASET_IDS=5,6

# Afternoon: Use more diverse casual photos
BASE_IMAGE_DATASET_IDS=10,11,12

# Just update .env and restart worker
```

---

## Important Notes

### Gender Filtering with Image Datasets

**This will NOT work:**
```bash
BASE_IMAGE_FACE_SOURCE=image_datasets
BASE_IMAGE_DATASET_IDS=5,7
# randomize_face_gender_lock=True (in Config) ← IGNORED!
```

**Why:** Image datasets don't have gender metadata in the database schema.

**Solution:** If you need gender filtering:
1. Use S3 faces bucket instead, OR
2. Create separate datasets (one male, one female) and switch between them manually, OR
3. Accept mixed gender sources (ethnic override will still work)

### Performance Considerations

**S3 Faces:**
- Fast listing (filesystem-based)
- Simple gender filtering
- Minimal database queries

**Image Datasets:**
- Database query required
- Slightly slower (negligible for small datasets)
- More flexible selection

**Recommendation:** Performance difference is negligible for both. Choose based on feature needs, not performance.

---

## Troubleshooting

### Issue: No faces found when using image_datasets

**Diagnosis:**
```
ValueError: No images found in datasets: [5, 7]
```

**Solutions:**
1. Verify dataset IDs exist in database
2. Check datasets have images imported
3. Verify image URLs are accessible
4. Check database connection

**Debug:**
```python
from models import DatasetImage, ImageDataset, db
# Check dataset exists
dataset = ImageDataset.query.filter_by(id=5).first()
print(f"Dataset: {dataset.name if dataset else 'NOT FOUND'}")

# Check image count
count = DatasetImage.query.filter_by(dataset_id=5).count()
print(f"Images in dataset 5: {count}")
```

---

### Issue: Gender lock not working with image_datasets

**Diagnosis:**
Male personas getting female faces (or vice versa)

**Solution:**
This is expected behavior! Image datasets don't support gender filtering.

**Options:**
1. Switch to S3 faces bucket (`BASE_IMAGE_FACE_SOURCE=s3_faces`)
2. Accept mixed gender sources (ethnic override still works correctly)
3. Manually curate datasets with only male or only female faces

---

### Issue: Invalid dataset IDs format

**Diagnosis:**
```
ValueError: Invalid BASE_IMAGE_DATASET_IDS format: 'abc,def'
```

**Solution:**
Dataset IDs must be integers:
```bash
# ❌ Wrong
BASE_IMAGE_DATASET_IDS=abc,def

# ✅ Correct
BASE_IMAGE_DATASET_IDS=5,7,12
```

---

### Issue: Downloaded image is empty or corrupt

**Diagnosis:**
```
Exception: Downloaded image is empty
```

**Solutions:**
1. Check image URL in database is valid
2. Verify S3/storage accessibility
3. Check network connectivity
4. Verify image file isn't corrupted in storage

**Debug:**
```bash
# Test image URL manually
curl -I https://s3-api.dev.iron-mind.ai/image-datasets/some-image.jpg

# Should return 200 OK
```

---

## Logging & Monitoring

### Key Log Messages

**S3 Faces Mode:**
```
[INFO] Using S3 faces bucket as base image source
[INFO] Selecting random face with gender lock: m
[INFO] Selected face from male folder: male/face123.jpg
[INFO] Downloaded face image: 245678 bytes
```

**Image Datasets Mode:**
```
[INFO] Using image datasets as base image source
[INFO] Using dataset IDs for base images: [5, 7, 12]
[INFO] Note: Gender lock is enabled (gender=m), but image datasets typically don't have gender metadata
[INFO] Selected image 456 from dataset 'Diverse Faces'
[INFO] Downloaded dataset face image: 312456 bytes
```

### Monitoring Tips

1. **Track face source distribution** (if using datasets):
   ```sql
   SELECT dataset_id, COUNT(*)
   FROM generation_results
   WHERE base_image_url LIKE '%dataset%'
   GROUP BY dataset_id;
   ```

2. **Monitor gender distribution** (S3 faces only):
   - Check logs for male/female folder selections
   - Verify gender lock is working as expected

3. **Face reuse tracking**:
   - Currently no deduplication for base faces
   - Same face may be used multiple times
   - Consider implementing usage tracking if needed

---

## Best Practices

### 1. Curate Your Face Sources
- High-quality, clear face photos
- Diverse ethnicities (ethnic override will adapt them)
- Good lighting
- Neutral expressions (if not using expression normalization)
- Open eyes (if not using expression normalization)

### 2. Regular Auditing
- Review generated base images periodically
- Check for low-quality faces
- Remove problematic source images
- Add new faces for more variety

### 3. Testing New Sources
- Always test with small batch (10-20 personas)
- Compare quality with previous source
- Check ethnic override works correctly
- Verify expression normalization (if enabled)

### 4. Documentation
- Document which datasets are used as face sources
- Note why specific datasets were chosen
- Track changes to face source configuration

---

## FAQ

**Q: Can I use both S3 faces and datasets at the same time?**
A: No, you must choose one source. However, you can easily switch between them by changing the .env file.

**Q: Does gender lock work with image datasets?**
A: No, gender lock only works with S3 faces bucket (male/female folders). Image datasets don't have gender metadata.

**Q: Can I use external URLs as face sources?**
A: Not directly, but you can import external images into a dataset, then use that dataset as a face source.

**Q: How many datasets should I use?**
A: 2-5 datasets is a good balance. More datasets = more variety, but harder to maintain quality control.

**Q: Will face source affect ethnic override?**
A: No, ethnic override works regardless of source. The Nano Banana prompt will transform any face to the target ethnicity.

**Q: Can I track which face was used for each persona?**
A: The base_image_url field contains the face source. For datasets, you can log the dataset name and image ID.

**Q: Should I use high-resolution faces?**
A: Moderate resolution is fine (1024x1024 or higher). Very high resolution may slow downloads but won't improve quality significantly.

---

## Changelog

**2026-03-11:**
- Initial implementation of dual-source system
- Added S3 faces bucket support (default)
- Added image datasets support (alternative)
- Added unified face selection function
- Documented configuration and troubleshooting
