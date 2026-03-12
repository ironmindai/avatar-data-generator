# Database Schema Manager

> *Maintained by: database-schema-manager agent*

This document tracks the database schema state, migration history, and structure for the Avatar Data Generator project.

## Database Information

- **Database Type**: PostgreSQL
- **Database Name**: avatar_data_generator
- **Database User**: avatar_data_gen
- **Migration Tool**: Alembic (via Flask-Migrate)
- **Migration Location**: `/home/niro/galacticos/avatar-data-generator/migrations/`

## Schema Overview

The database currently contains the following tables:

1. **users** - User authentication and management
2. **settings** - Application configuration key-value store for bio prompts
3. **config** - Global boolean configuration settings
4. **int_config** - Global integer configuration settings
5. **generation_tasks** - Avatar generation task tracking and management
6. **generation_results** - Persona data and avatar image URLs for each generated avatar
7. **workflow_logs** - LLM workflow execution logs for observability and cost tracking
8. **workflow_node_logs** - Individual node execution logs within LLM workflows
9. **image_datasets** - User-created image datasets for Flickr/URL imports
10. **dataset_images** - Images stored within datasets with source metadata
11. **dataset_permissions** - Sharing permissions for image datasets
12. **dataset_image_usage** - Tracks which scene images have been used in generation tasks

---

## Tables

### users

Stores user authentication and profile information.

**Columns:**
- `id` (Integer, Primary Key) - User unique identifier
- `email` (String(255), UNIQUE, NOT NULL, Indexed) - User email address for login
- `password_hash` (String(255), NOT NULL) - Bcrypt hashed password
- `created_at` (DateTime, NOT NULL) - Timestamp of user creation
- `last_login` (DateTime, NULLABLE) - Timestamp of last successful login
- `is_active` (Boolean, NOT NULL, Default: True) - Account active status flag

**Indexes:**
- `ix_users_email` (UNIQUE) on `email`

**Constraints:**
- Primary Key: `id`

**Model Location**: `/home/niro/galacticos/avatar-data-generator/models.py` - `User` class

---

### settings

Stores application settings as key-value pairs, primarily used for bio prompts for different social media platforms.

**Columns:**
- `id` (Integer, Primary Key) - Setting unique identifier
- `key` (String(255), UNIQUE, NOT NULL, Indexed) - Setting key/name
- `value` (Text, NOT NULL) - Setting value (can store long text)
- `created_at` (DateTime, NOT NULL, Server Default: NOW()) - Timestamp of setting creation
- `updated_at` (DateTime, NOT NULL, Server Default: NOW()) - Timestamp of last update

**Indexes:**
- `ix_settings_key` (UNIQUE) on `key`

**Constraints:**
- Primary Key: `id`
- Unique: `key`

**Default Settings (Populated on Migration):**
- `bio_prompt_facebook` - Bio prompt for Facebook
- `bio_prompt_instagram` - Bio prompt for Instagram
- `bio_prompt_x` - Bio prompt for X (Twitter)
- `bio_prompt_tiktok` - Bio prompt for TikTok
- `max_concurrent_tasks` - Maximum number of avatar generation tasks that can process simultaneously (default: '1' = sequential processing)

**Model Location**: `/home/niro/galacticos/avatar-data-generator/models.py` - `Settings` class

**Helper Methods:**
- `get_value(key, default)` - Class method to get a setting value
- `set_value(key, value)` - Class method to set a setting value

---

### config

Stores global boolean configuration settings for application features.

**Columns:**
- `id` (Integer, Primary Key) - Config unique identifier
- `key` (String(255), UNIQUE, NOT NULL, Indexed) - Config key/name
- `value` (Boolean, NOT NULL) - Boolean config value (TRUE/FALSE)
- `created_at` (DateTime, NOT NULL, Server Default: NOW()) - Timestamp of config creation
- `updated_at` (DateTime, NOT NULL, Server Default: NOW()) - Timestamp of last update

**Indexes:**
- `ix_config_key` (UNIQUE) on `key`

**Constraints:**
- Primary Key: `id`
- Unique: `key`

**Default Config Values (Populated on Migration):**
- `randomize_face_base` (FALSE) - Enables randomizing faces for base image generation
- `randomize_face_gender_lock` (FALSE) - When face randomization is on, locks to matching gender
- `crop_white_borders` (FALSE) - Enables automatic cropping of white borders from generated avatar images
- `randomize_image_style` (FALSE) - Enables randomized style processing (color presets, contrast, sharpness, grain, vignette) to make images look like they came from different sources/photographers
- `show_base_images` (TRUE) - Controls visibility of base images in the dataset detail view

**Face Randomization Feature:**
- When `randomize_face_base` is TRUE, the image generation system uses a random face image from S3 as reference
- When `randomize_face_gender_lock` is TRUE (with randomization enabled), only faces matching the persona's gender are selected

**Model Location**: `/home/niro/galacticos/avatar-data-generator/models.py` - `Config` class

**Helper Methods:**
- `get_value(key, default=False)` - Class method to get a boolean config value
- `set_value(key, value)` - Class method to set a boolean config value

---

### generation_tasks

Tracks avatar generation tasks submitted by users, including status, configuration, and results.

**Columns:**
- `id` (Integer, Primary Key) - Task unique identifier
- `task_id` (String(12), UNIQUE, NOT NULL, Indexed) - Short UUID for user-facing task identification (8-12 characters)
- `user_id` (Integer, Foreign Key to `users.id`, NOT NULL, Indexed) - User who submitted the task
- `persona_description` (Text, NOT NULL) - Persona description provided in the form
- `bio_language` (String(100), NOT NULL) - Selected language for generated bios
- `number_to_generate` (Integer, NOT NULL) - Number of avatars to generate
- `images_per_persona` (Integer, NOT NULL) - Images per persona (4 or 8)
- `image_set_ids` (ARRAY of INTEGER, NULLABLE) - Array of image-set IDs selected for scene-based generation
- `status` (String(50), NOT NULL, Default: 'pending', Indexed) - Task status: pending, generating-data, generating-images, completed, failed
- `error_log` (Text, NULLABLE) - Error messages if task fails
- `created_at` (DateTime, NOT NULL, Server Default: NOW()) - Timestamp of task creation
- `updated_at` (DateTime, NOT NULL, Server Default: NOW()) - Timestamp of last update
- `completed_at` (DateTime, NULLABLE) - Timestamp of task completion (success or failure)

**Indexes:**
- `ix_generation_tasks_task_id` (UNIQUE) on `task_id`
- `ix_generation_tasks_user_id` on `user_id`
- `ix_generation_tasks_status` on `status`

**Constraints:**
- Primary Key: `id`
- Unique: `task_id` (via `uq_generation_tasks_task_id`)
- Foreign Key: `user_id` references `users.id` (via `fk_generation_tasks_user_id`)

**Relationships:**
- `user` - Many-to-One relationship with `User` model
- `User.generation_tasks` - One-to-Many backref for accessing user's tasks

**Model Location**: `/home/niro/galacticos/avatar-data-generator/models.py` - `GenerationTask` class

**Helper Methods:**
- `generate_task_id()` - Static method to generate 8-character UUID-based task ID
- `mark_completed(success, error_message)` - Mark task as completed or failed
- `update_status(new_status)` - Update task status with automatic timestamp update

---

### generation_results

Stores persona data and S3 image URLs for generated avatars. Each record represents one generated avatar persona with associated bio data and image URLs.

**Columns:**
- `id` (Integer, Primary Key) - Result unique identifier
- `task_id` (Integer, Foreign Key to `generation_tasks.id`, NOT NULL, Indexed, CASCADE DELETE) - Parent generation task
- `batch_number` (Integer, NOT NULL, Indexed) - Batch number for tracking parallel requests
- `firstname` (String(100), NOT NULL) - Generated first name
- `lastname` (String(100), NOT NULL) - Generated last name
- `gender` (String(10), NOT NULL) - Gender (f/m)
- `ethnicity` (String(100), NULLABLE) - Generated ethnicity (from root level of Flowise response)
- `age` (Integer, NULLABLE) - Generated age (from bios JSON object)
- `bio_facebook` (Text, NULLABLE) - Generated Facebook bio text
- `bio_instagram` (Text, NULLABLE) - Generated Instagram bio text
- `bio_x` (Text, NULLABLE) - Generated X (Twitter) bio text
- `bio_tiktok` (Text, NULLABLE) - Generated TikTok bio text
- `job_title` (Text, NULLABLE) - Generated job title
- `workplace` (Text, NULLABLE) - Generated workplace/company name
- `edu_establishment` (Text, NULLABLE) - Generated educational institution name
- `edu_study` (Text, NULLABLE) - Generated field of study/degree
- `current_city` (String(255), NULLABLE) - Current city of residence
- `current_state` (String(255), NULLABLE) - Current state/province of residence
- `prev_city` (String(255), NULLABLE) - Previous city of residence
- `prev_state` (String(255), NULLABLE) - Previous state/province of residence
- `about` (Text, NULLABLE) - Generated "About" section text
- `base_image_url` (Text, NULLABLE) - Public S3 URL for base selfie image
- `images` (JSONB, NULLABLE) - JSON array of public S3 URLs for split images (flexible: 4, 8, or any number)
- `image_ideas_history` (JSONB, NULLABLE) - JSON array of image idea strings to avoid duplicates in future generations
- `created_at` (DateTime, NOT NULL, Server Default: NOW()) - Timestamp of result creation

**Indexes:**
- `ix_generation_results_task_id` on `task_id`
- `ix_generation_results_batch_number` on `batch_number`

**Constraints:**
- Primary Key: `id`
- Foreign Key: `task_id` references `generation_tasks.id` (via `fk_generation_results_task_id`) with CASCADE DELETE

**Relationships:**
- `task` - Many-to-One relationship with `GenerationTask` model
- `GenerationTask.results` - One-to-Many backref for accessing task's results (with cascade delete)

**Model Location**: `/home/niro/galacticos/avatar-data-generator/models.py` - `GenerationResult` class

**Image Generation Workflow:**
1. Base selfie image is generated first and stored in `base_image_url`
2. Multiple images (4 or 8) are generated from the base image
3. Image URLs are stored as a JSONB array in `images` column (format: `["url1", "url2", ...]`)
4. All images are uploaded to S3 with public URLs

**JSONB Images Column Format:**
```json
["https://s3.../image1.jpg", "https://s3.../image2.jpg", "https://s3.../image3.jpg", "https://s3.../image4.jpg"]
```

---

### image_datasets

Stores user-created image datasets for organizing imported images from Flickr or URLs.

**Columns:**
- `id` (Integer, Primary Key) - Dataset unique identifier
- `dataset_id` (String(36), UNIQUE, NOT NULL, Indexed) - UUID for public-facing dataset identification
- `user_id` (Integer, Foreign Key to `users.id`, NOT NULL, Indexed, CASCADE DELETE) - Dataset owner
- `name` (String(255), NOT NULL) - Dataset name
- `description` (Text, NULLABLE) - Optional dataset description
- `status` (String(50), NOT NULL, Default: 'active', Indexed) - Dataset status: active, archived, deleted
- `is_public` (Boolean, NOT NULL, Default: FALSE, Indexed) - Whether dataset is publicly accessible
- `created_at` (DateTime, NOT NULL, Server Default: NOW()) - Timestamp of dataset creation
- `updated_at` (DateTime, NOT NULL, Server Default: NOW()) - Timestamp of last update

**Indexes:**
- `ix_image_datasets_dataset_id` (UNIQUE) on `dataset_id`
- `ix_image_datasets_user_id` on `user_id`
- `ix_image_datasets_status` on `status`
- `ix_image_datasets_is_public` on `is_public`

**Constraints:**
- Primary Key: `id`
- Unique: `dataset_id` (via `uq_image_datasets_dataset_id`)
- Foreign Key: `user_id` references `users.id` (via `fk_image_datasets_user_id`) with CASCADE DELETE

**Relationships:**
- `user` - Many-to-One relationship with `User` model
- `User.image_datasets` - One-to-Many backref for accessing user's datasets

**Model Location**: `/home/niro/galacticos/avatar-data-generator/models.py` - `ImageDataset` class

**Helper Methods:**
- Auto-generates UUID for `dataset_id` if not provided during initialization

---

### dataset_images

Stores images within datasets, including source information and metadata for Flickr or URL imports.

**Columns:**
- `id` (Integer, Primary Key) - Image record unique identifier
- `dataset_id` (Integer, Foreign Key to `image_datasets.id`, NOT NULL, Indexed, CASCADE DELETE) - Parent dataset
- `image_url` (Text, NOT NULL) - Public URL to the image
- `source_type` (String(50), NULLABLE, Indexed) - Source of image: 'flickr' or 'url_import'
- `source_id` (String(255), NULLABLE, Indexed) - Original ID from source (Flickr photo ID or original URL)
- `source_metadata` (JSONB, NULLABLE) - Source metadata (Flickr tags, owner, license, etc.)
- `image_hash` (String(64), NULLABLE, Indexed) - SHA256 hash for duplicate detection
- `face_count` (Integer, NULLABLE, Indexed) - Number of faces detected in image (NULL = not yet analyzed, 0 = no faces detected, 1+ = number of faces)
- `added_at` (DateTime, NOT NULL, Server Default: NOW()) - Timestamp when image was added to dataset

**Indexes:**
- `ix_dataset_images_dataset_id` on `dataset_id`
- `ix_dataset_images_source_type` on `source_type`
- `ix_dataset_images_source_id` on `source_id`
- `ix_dataset_images_image_hash` on `image_hash`
- `ix_dataset_images_face_count` on `face_count`

**Constraints:**
- Primary Key: `id`
- Foreign Key: `dataset_id` references `image_datasets.id` (via `fk_dataset_images_dataset_id`) with CASCADE DELETE

**Relationships:**
- `dataset` - Many-to-One relationship with `ImageDataset` model
- `ImageDataset.images` - One-to-Many backref for accessing dataset's images (with cascade delete)

**Model Location**: `/home/niro/galacticos/avatar-data-generator/models.py` - `DatasetImage` class

**Source Metadata Format (Flickr example):**
```json
{
  "flickr_id": "53891234567",
  "owner": "flickr_user_id",
  "owner_name": "John Doe",
  "tags": ["portrait", "outdoor", "nature"],
  "license": "CC BY 2.0",
  "date_taken": "2024-01-15",
  "views": 1234,
  "url_original": "https://flickr.com/photos/..."
}
```

---

### dataset_permissions

Manages sharing permissions for image datasets, allowing users to grant view or edit access to other users.

**Columns:**
- `id` (Integer, Primary Key) - Permission record unique identifier
- `dataset_id` (Integer, Foreign Key to `image_datasets.id`, NOT NULL, Indexed, CASCADE DELETE) - Dataset being shared
- `user_id` (Integer, Foreign Key to `users.id`, NOT NULL, Indexed, CASCADE DELETE) - User receiving permission
- `permission_level` (String(50), NOT NULL) - Permission level: 'view' or 'edit'
- `created_at` (DateTime, NOT NULL, Server Default: NOW()) - Timestamp when permission was granted

**Indexes:**
- `ix_dataset_permissions_dataset_id` on `dataset_id`
- `ix_dataset_permissions_user_id` on `user_id`

**Constraints:**
- Primary Key: `id`
- Unique: (`dataset_id`, `user_id`) (via `uq_dataset_permissions_dataset_user`) - prevents duplicate permissions
- Foreign Key: `dataset_id` references `image_datasets.id` (via `fk_dataset_permissions_dataset_id`) with CASCADE DELETE
- Foreign Key: `user_id` references `users.id` (via `fk_dataset_permissions_user_id`) with CASCADE DELETE

**Relationships:**
- `dataset` - Many-to-One relationship with `ImageDataset` model
- `user` - Many-to-One relationship with `User` model
- `ImageDataset.permissions` - One-to-Many backref for accessing dataset's permissions (with cascade delete)
- `User.dataset_permissions` - One-to-Many backref for accessing user's permissions

**Model Location**: `/home/niro/galacticos/avatar-data-generator/models.py` - `DatasetPermission` class

**Permission Levels:**
- `view` - Read-only access to dataset (can view images but not modify)
- `edit` - Full access to dataset (can add/remove images and modify dataset properties)

---

### dataset_image_usage

Tracks which scene images from image-sets have been used in generation tasks. This enables the system to prioritize least-used images globally, avoid repetition within a task, and cycle through images when all have been used.

**Columns:**
- `id` (Integer, Primary Key) - Usage record unique identifier
- `dataset_image_id` (Integer, Foreign Key to `dataset_images.id`, NOT NULL, Indexed, CASCADE DELETE) - Scene image that was used
- `task_id` (Integer, Foreign Key to `generation_tasks.id`, NOT NULL, Indexed, CASCADE DELETE) - Generation task that used this image
- `used_at` (DateTime, NOT NULL, Server Default: NOW()) - Timestamp when this image was used

**Indexes:**
- `ix_dataset_image_usage_dataset_image_id` on `dataset_image_id`
- `ix_dataset_image_usage_task_id` on `task_id`
- `uq_dataset_image_usage_image_task` (UNIQUE) on `(dataset_image_id, task_id)` - prevents double-counting

**Constraints:**
- Primary Key: `id`
- Unique: (`dataset_image_id`, `task_id`) (via `uq_dataset_image_usage_image_task`)
- Foreign Key: `dataset_image_id` references `dataset_images.id` (via `dataset_image_usage_dataset_image_id_fkey`) with CASCADE DELETE
- Foreign Key: `task_id` references `generation_tasks.id` (via `dataset_image_usage_task_id_fkey`) with CASCADE DELETE

**Relationships:**
- `dataset_image` - Many-to-One relationship with `DatasetImage` model
- `task` - Many-to-One relationship with `GenerationTask` model
- `DatasetImage.usage_records` - One-to-Many backref for accessing image's usage records (with cascade delete)
- `GenerationTask.image_usage_records` - One-to-Many backref for accessing task's usage records (with cascade delete)

**Model Location**: `/home/niro/galacticos/avatar-data-generator/models.py` - `DatasetImageUsage` class

**Use Cases:**
- Track global usage count for each scene image to prioritize least-used images
- Prevent using the same scene image multiple times within a single task
- Enable fair rotation through all available scene images
- Support intelligent scene image selection algorithms

---

## Migration History

### Migration: 25698f3f906f - initial_migration
**Date**: 2026-01-30 09:31:15
**Parent**: None (initial)

**Changes:**
- Created `users` table with authentication fields
- Added unique index on `users.email`

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/25698f3f906f_initial_migration.py`

---

### Migration: d8cfd3cb4083 - create_settings_table
**Date**: 2026-01-30 11:33:28
**Parent**: 25698f3f906f

**Changes:**
- Created `settings` table for application configuration
- Added unique index on `settings.key`
- Inserted default bio prompts for Facebook, Instagram, X, and TikTok

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/d8cfd3cb4083_create_settings_table.py`

**Data Migration Included**: Yes - populates default bio prompts

---

### Migration: 3a0f944324eb - create_generation_tasks_table
**Date**: 2026-01-30 12:02:12
**Parent**: d8cfd3cb4083

**Changes:**
- Created `generation_tasks` table for tracking avatar generation tasks
- Added unique index on `generation_tasks.task_id` (user-facing task identifier)
- Added index on `generation_tasks.user_id` (foreign key to users)
- Added index on `generation_tasks.status` (for filtering tasks by status)
- Added foreign key constraint linking `user_id` to `users.id`
- Set server-side defaults for `status` ('pending'), `created_at`, and `updated_at` (NOW())

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/3a0f944324eb_create_generation_tasks_table.py`

**Safety Notes:**
- No destructive operations
- Fully reversible via downgrade function
- Foreign key constraint ensures referential integrity with users table
- Task ID uniqueness enforced at database level

---

### Migration: 3d677a879bd9 - create_generation_results_table
**Date**: 2026-01-30 13:07:31
**Parent**: 3a0f944324eb

**Changes:**
- Created `generation_results` table for storing generated persona data
- Added indexes on `task_id` and `batch_number` for query performance
- Added foreign key constraint to `generation_tasks.id` with CASCADE DELETE
- Set server-side default for `created_at` (NOW())

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/3d677a879bd9_create_generation_results_table.py`

**Safety Notes:**
- No destructive operations
- Fully reversible via downgrade function
- Foreign key CASCADE DELETE ensures orphaned results are cleaned up when tasks are deleted

---

### Migration: 36b6aa503da9 - add_s3_image_url_fields_to_generation_results
**Date**: 2026-01-30 15:01:07
**Parent**: 3d677a879bd9

**Changes:**
- Added `base_image_url` (Text, NULLABLE) - Public S3 URL for base selfie image
- Added `image_1_url` (Text, NULLABLE) - Public S3 URL for first split image
- Added `image_2_url` (Text, NULLABLE) - Public S3 URL for second split image
- Added `image_3_url` (Text, NULLABLE) - Public S3 URL for third split image
- Added `image_4_url` (Text, NULLABLE) - Public S3 URL for fourth split image

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/36b6aa503da9_add_s3_image_url_fields_to_generation_.py`

**Purpose:**
These fields store public S3 URLs for generated avatar images. The workflow is:
1. Generate base selfie image → store in `base_image_url`
2. Generate 4-image grid from base image
3. Split grid into 4 individual images → store in `image_1_url` through `image_4_url`

**Safety Notes:**
- All fields are nullable (images generated after persona data)
- TEXT type supports long S3 URLs
- Non-destructive operation (adding columns only)
- Fully reversible via downgrade function
- **Downgrade Warning**: Rolling back this migration will permanently delete all stored image URLs

**Status**: SUPERSEDED by migration 30c18b6939ce (converted to JSONB array)

---

### Migration: 30c18b6939ce - convert_image_urls_to_jsonb_array
**Date**: 2026-01-30 15:24:25
**Parent**: 36b6aa503da9

**Changes:**
- Added `images` (JSONB, NULLABLE) - JSON array for flexible image URL storage
- Migrated existing data from `image_1_url` through `image_4_url` to JSONB array
- Dropped columns: `image_1_url`, `image_2_url`, `image_3_url`, `image_4_url`
- Retained `base_image_url` column (unchanged)

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/30c18b6939ce_convert_image_urls_to_jsonb_array.py`

**Purpose:**
BREAKING CHANGE - Converts individual image URL columns to a JSONB array for better flexibility and scalability:
- **Before**: Fixed 4 columns (`image_1_url` through `image_4_url`) - inflexible for 8+ images
- **After**: Single JSONB array column `images` - supports 4, 8, or any number of images

**Data Migration:**
- Upgrade: Combines non-null values from `image_1_url` through `image_4_url` into JSONB array
- Downgrade: Extracts first 4 elements from JSONB array back to individual columns

**JSONB Format:**
```json
["https://s3.../image1.jpg", "https://s3.../image2.jpg", "https://s3.../image3.jpg", "https://s3.../image4.jpg"]
```

**Safety Notes:**
- **BREAKING CHANGE**: Application code must be updated to use `images` JSONB array instead of individual columns
- Data migration preserves existing image URLs during upgrade
- Downgrade is possible but limited to first 4 images (extras are lost if array has more than 4)
- Fully tested and reversible
- **Downgrade Warning**: If JSONB array has more than 4 images, downgrade will lose extras

---

### Migration: d59663db64e2 - create_config_table_for_boolean_settings
**Date**: 2026-01-31 14:13:31
**Parent**: 30c18b6939ce

**Changes:**
- Created `config` table for storing global boolean configuration settings
- Added unique index on `config.key` for fast lookups
- Seeded initial data: `randomize_face_base` (FALSE), `randomize_face_gender_lock` (FALSE)

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/d59663db64e2_create_config_table_for_boolean_settings.py`

**Purpose:**
Creates a new Config table for storing global boolean configuration settings. This replaces the flawed design where boolean flags were incorrectly added as columns to the Settings table (which is meant for key-value bio prompts with only 4 rows).

**Design Rationale:**
- Settings table is for bio prompts (4 rows with key-value pairs for text)
- Config table is for global boolean flags (separate rows for each config)
- This separation provides proper schema normalization and flexibility

**Table Structure:**
- `id` - Integer primary key
- `key` - String(255), unique, indexed
- `value` - Boolean (TRUE/FALSE)
- `created_at` - DateTime with server default NOW()
- `updated_at` - DateTime with server default NOW()

**Safety Notes:**
- Non-destructive operation (creating new table only)
- Fully reversible via downgrade function
- Initial data seeded for face randomization feature
- **Downgrade Warning**: Rolling back this migration will permanently delete the config table and all config values

**Status**: APPLIED

---

### Migration: 70c50b9233b6 - add_crop_white_borders_config
**Date**: 2026-01-31 15:02:23
**Parent**: d59663db64e2

**Changes:**
- Added new config setting `crop_white_borders` (FALSE) to the `config` table
- This setting controls whether white borders should be automatically cropped from generated avatar images

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/70c50b9233b6_add_crop_white_borders_config.py`

**Purpose:**
Adds a new boolean configuration flag to control image post-processing. When enabled, the image generation system will automatically detect and crop white borders from generated avatar images.

**Data Migration:**
- Upgrade: Inserts new row into `config` table with key `crop_white_borders` and value `FALSE`
- Downgrade: Deletes the `crop_white_borders` row from `config` table

**Safety Notes:**
- Non-destructive operation (inserting new config row only)
- Fully reversible via downgrade function
- Default value is FALSE (feature disabled by default)
- **Downgrade Warning**: Rolling back this migration will delete the `crop_white_borders` config setting

**Status**: APPLIED

---

### Migration: d8982580d2a4 - add_randomize_image_style_config
**Date**: 2026-02-01 07:24:32
**Parent**: 70c50b9233b6

**Changes:**
- Added new config setting `randomize_image_style` (FALSE) to the `config` table
- This setting controls whether images should have randomized style processing applied

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/d8982580d2a4_add_randomize_image_style_config.py`

**Purpose:**
Adds a new boolean configuration flag to control image style randomization. When enabled, the image generation system will apply randomized style processing (color presets, contrast, sharpness, grain, vignette variations) to make images look like they came from different sources/photographers, increasing dataset diversity.

**Data Migration:**
- Upgrade: Inserts new row into `config` table with key `randomize_image_style` and value `FALSE`
- Downgrade: Deletes the `randomize_image_style` row from `config` table

**Safety Notes:**
- Non-destructive operation (inserting new config row only)
- Fully reversible via downgrade function
- Default value is FALSE (feature disabled by default)
- **Downgrade Warning**: Rolling back this migration will delete the `randomize_image_style` config setting

**Status**: APPLIED

---

### Migration: 7e1fabd32d40 - add_max_concurrent_tasks_setting
**Date**: 2026-02-01 08:18:07
**Parent**: d8982580d2a4

**Changes:**
- Added new setting `max_concurrent_tasks` (default value '1') to the `settings` table
- This setting controls how many avatar generation tasks can process simultaneously

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/7e1fabd32d40_add_max_concurrent_tasks_setting.py`

**Purpose:**
Adds a new integer setting to control task concurrency for avatar generation. The value determines how many tasks can be processed in parallel:
- Value of '1': Tasks process sequentially (one at a time)
- Value of '2+': Multiple tasks can run concurrently up to the specified limit

**Data Migration:**
- Upgrade: Inserts new row into `settings` table with key `max_concurrent_tasks` and value `'1'`
- Downgrade: Deletes the `max_concurrent_tasks` row from `settings` table

**Implementation Notes:**
- Value stored as Text in `settings` table (must be converted to integer when reading)
- Default value '1' ensures backward-compatible sequential processing
- Use `Settings.get_value('max_concurrent_tasks', '1')` and convert to int in application code

**Safety Notes:**
- Non-destructive operation (inserting new setting row only)
- Fully reversible via downgrade function
- Default value is '1' (sequential processing, safest default)
- **Downgrade Warning**: Rolling back this migration will delete the `max_concurrent_tasks` setting

**Status**: APPLIED

---

### Migration: 7e69fd85074a - add_supplementary_persona_fields_job_education_location_about
**Date**: 2026-02-05 18:40:45
**Parent**: 8a3b5c7d9e0f

**Changes:**
- Added `job_title` (Text, NULLABLE) - Generated job title for persona
- Added `workplace` (Text, NULLABLE) - Generated workplace/company name for persona
- Added `edu_establishment` (Text, NULLABLE) - Generated educational institution name
- Added `edu_study` (Text, NULLABLE) - Generated field of study/degree
- Added `current_city` (String(255), NULLABLE) - Current city of residence
- Added `current_state` (String(255), NULLABLE) - Current state/province of residence
- Added `prev_city` (String(255), NULLABLE) - Previous city of residence
- Added `prev_state` (String(255), NULLABLE) - Previous state/province of residence
- Added `about` (Text, NULLABLE) - Generated "About" section text

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/7e69fd85074a_add_supplementary_persona_fields_job_.py`

**Purpose:**
Extends the generation_results table to capture additional persona details from the updated Flowise workflow (71bf0c86-c802-4221-b6e7-0af16e350bb6). These supplementary fields enable more complete persona profiles beyond just basic bio text, adding employment, education, location, and about information.

**Schema Changes:**
All new columns are nullable (Text or String) to maintain backward compatibility with existing records and allow for partial data if certain fields are not generated by the workflow.

**Use Cases:**
- Job/Employment: `job_title` and `workplace` provide professional context
- Education: `edu_establishment` and `edu_study` provide educational background
- Location: `current_city`, `current_state`, `prev_city`, `prev_state` provide geographic context
- About: `about` provides additional narrative persona information

**Safety Notes:**
- Non-destructive operation (adding nullable columns only)
- Fully reversible via downgrade function
- Backward compatible - existing records will have NULL values for new fields
- **Downgrade Warning**: Rolling back this migration will permanently delete all data stored in these 9 columns

**Status**: APPLIED

---

### Migration: fbc78f685fa2 - add_ethnicity_and_age_to_generation_results
**Date**: 2026-02-19 06:41:56
**Parent**: 7e69fd85074a

**Changes:**
- Added `ethnicity` (String(100), NULLABLE) - Ethnicity from root level of Flowise response
- Added `age` (Integer, NULLABLE) - Age from bios JSON object

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/fbc78f685fa2_add_ethnicity_and_age_to_generation_.py`

**Purpose:**
Extends the generation_results table to capture ethnicity and age fields from the updated Flowise workflow (71bf0c86-c802-4221-b6e7-0af16e350bb6). These fields provide additional demographic information for generated personas.

**Schema Changes:**
- `ethnicity`: String(100), nullable - Extracted from root level of Flowise response (e.g., "ethnicity": "White")
- `age`: Integer, nullable - Extracted from inside the bios JSON object (e.g., "age": 23)

**Data Source:**
- Flowise workflow ID: 71bf0c86-c802-4221-b6e7-0af16e350bb6
- Ethnicity comes from root-level response field
- Age comes from nested bios JSON string

**Safety Notes:**
- Non-destructive operation (adding nullable columns only)
- Fully reversible via downgrade function
- Backward compatible - existing records will have NULL values for new fields
- **Downgrade Warning**: Rolling back this migration will permanently delete all ethnicity and age data

**Status**: APPLIED

---

### Migration: 312faec904ca - add_image_ideas_history_to_generation_results
**Date**: 2026-02-19 12:42:06
**Parent**: fbc78f685fa2

**Changes:**
- Added `image_ideas_history` (JSONB, NULLABLE) - JSONB array for storing image idea/prompt history

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/312faec904ca_add_image_ideas_history_to_generation_.py`

**Purpose:**
Adds a new JSONB column to track image ideas/prompts that have been generated for each persona. This enables duplicate detection and prevention in future image generation cycles, ensuring variety and avoiding repetitive content.

**JSONB Format:**
```json
["Mirror selfie in bedroom", "Coffee shop laptop work", "Gym workout selfie", "Beach sunset photo"]
```

**Use Cases:**
- Track all image ideas generated for a persona
- Prevent duplicate image prompts across multiple generation cycles
- Maintain variety and diversity in generated content
- Support intelligent prompt generation by excluding previously used ideas

**Safety Notes:**
- Non-destructive operation (adding nullable column only)
- Fully reversible via downgrade function
- Backward compatible - existing records will have NULL values for this field
- JSONB type is efficient for storing and querying array data in PostgreSQL
- **Downgrade Warning**: Rolling back this migration will permanently delete all image ideas history data

**Status**: APPLIED

---

### Migration: 42eba0ec3095 - remove_base_image_size_from_generation_results
**Date**: 2026-02-25 16:26:48
**Parent**: 312faec904ca

**Changes:**
- Removed `base_image_size` column from `generation_results` table

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/42eba0ec3095_remove_base_image_size_from_generation_.py`

**Purpose:**
Removes the `base_image_size` field that was previously added to store base image dimensions. This field is no longer needed as SeeDream dimensions are now randomized directly in the application code rather than being stored in the database. The dimension randomization happens at generation time, making database storage unnecessary.

**Rationale:**
- SeeDream dimensions are randomized in code on-the-fly for each generation
- No need to persist dimensions in database after generation completes
- Reduces schema complexity and removes unused column
- Dimensions don't need to be stored for future reference

**Safety Notes:**
- **DESTRUCTIVE OPERATION**: Permanently deletes the `base_image_size` column and any data it contained
- Fully reversible via downgrade function (restores empty column)
- Any data previously stored in `base_image_size` will be lost
- **Downgrade Warning**: Rolling back this migration will restore the column but data will be NULL

**Status**: APPLIED

---

### Migration: a5b7c9d1e3f5 - add_show_base_images_config
**Date**: 2026-02-25 18:00:00
**Parent**: 42eba0ec3095

**Changes:**
- Added new config setting `show_base_images` (TRUE) to the `config` table
- This setting controls whether base images are displayed in the dataset detail view

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/a5b7c9d1e3f5_add_show_base_images_config.py`

**Purpose:**
Adds a new boolean configuration flag to control the visibility of base images in the dataset detail view. When enabled (default), users can see the base selfie images that were used to generate the split images. When disabled, only the split images are shown in the UI.

**Data Migration:**
- Upgrade: Inserts new row into `config` table with key `show_base_images` and value `TRUE`
- Downgrade: Deletes the `show_base_images` row from `config` table

**Safety Notes:**
- Non-destructive operation (inserting new config row only)
- Fully reversible via downgrade function
- Default value is TRUE (base images shown by default)
- Uses ON CONFLICT DO NOTHING to prevent duplicate key errors on re-run
- **Downgrade Warning**: Rolling back this migration will delete the `show_base_images` config setting

**Status**: APPLIED

---

### Migration: 562b42df8d87 - create_image_datasets_tables
**Date**: 2026-03-09 11:08:47
**Parent**: a5b7c9d1e3f5

**Changes:**
- Created `image_datasets` table for user-created image datasets
- Created `dataset_images` table for images within datasets
- Created `dataset_permissions` table for dataset sharing permissions
- Added indexes on all foreign keys and frequently queried fields
- Configured CASCADE DELETE on all foreign keys for automatic cleanup

**Tables Created:**

1. **image_datasets**:
   - Stores dataset metadata (name, description, status, visibility)
   - Each dataset has a unique UUID (`dataset_id`) for public identification
   - Owned by a user via `user_id` foreign key with CASCADE DELETE
   - Supports public/private datasets via `is_public` flag
   - Status field for lifecycle management (active, archived, deleted)

2. **dataset_images**:
   - Stores individual images within a dataset
   - Links to parent dataset with CASCADE DELETE
   - Tracks image source (`source_type`: 'flickr' or 'url_import')
   - Stores source metadata as JSONB (tags, license, owner info)
   - Includes `image_hash` (SHA256) for duplicate detection
   - Maintains original source ID for traceability

3. **dataset_permissions**:
   - Manages dataset sharing between users
   - Links to both dataset and user with CASCADE DELETE
   - Permission levels: 'view' (read-only) or 'edit' (full access)
   - Unique constraint prevents duplicate permissions for same dataset+user

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/562b42df8d87_create_image_datasets_tables.py`

**Purpose:**
Implements the Image Datasets feature, allowing users to:
- Create and organize collections of images from Flickr or URL imports
- Import images with full source metadata preservation
- Share datasets with other users (view or edit permissions)
- Track image sources and detect duplicates via hashing
- Manage dataset lifecycle (active, archived, deleted)

**Indexes Created:**
- `image_datasets`: dataset_id (unique), user_id, status, is_public
- `dataset_images`: dataset_id, source_type, source_id, image_hash
- `dataset_permissions`: dataset_id, user_id

**Safety Notes:**
- Non-destructive operation (creating new tables only)
- Fully reversible via downgrade function
- CASCADE DELETE ensures automatic cleanup when users or datasets are deleted
- Unique constraints prevent data integrity issues
- JSONB type used for flexible metadata storage
- **Downgrade Warning**: Rolling back this migration will permanently delete all image datasets, dataset images, and dataset permissions

**Status**: APPLIED

---

### Migration: 1a0315a32006 - add_image_set_ids_and_dataset_image_usage_tracking
**Date**: 2026-03-10 07:02:30
**Parent**: 562b42df8d87

**Changes:**
- Added `image_set_ids` (ARRAY of INTEGER, NULLABLE) column to `generation_tasks` table
  - Stores array of image-set IDs selected by user for scene-based generation
  - Example value: [1, 5, 12] for using image-sets with IDs 1, 5, and 12
  - Nullable for backward compatibility with existing tasks

- Created `dataset_image_usage` table for tracking scene image usage
  - Columns: id, dataset_image_id, task_id, used_at
  - Foreign keys to dataset_images.id and generation_tasks.id (both CASCADE DELETE)
  - Unique constraint on (dataset_image_id, task_id) to prevent double-counting
  - Indexed on dataset_image_id and task_id for efficient lookups

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/1a0315a32006_add_image_set_ids_and_dataset_image_.py`

**Purpose:**
Implements the scene-based image generation feature, enabling:
- Selection of multiple image-sets for a generation task
- Tracking which scene images have been used in which tasks
- Prioritizing least-used images globally across all tasks
- Avoiding repetition of scene images within a single task
- Fair rotation through available scene images when all have been used

**Schema Changes Details:**

1. **generation_tasks.image_set_ids**: PostgreSQL ARRAY column stores list of dataset IDs
   - NULL value means traditional generation (no scene images)
   - Non-NULL array means scene-based generation using images from specified datasets
   - Array format: {1,5,12} in PostgreSQL, [1,5,12] in Python

2. **dataset_image_usage table**: Tracking table for scene image usage
   - Each row represents one use of a scene image in a generation task
   - Unique constraint ensures each image is only counted once per task
   - CASCADE DELETE ensures automatic cleanup when images or tasks are deleted
   - Enables queries like "which images have been used least?" or "which images has this task used?"

**Safety Notes:**
- Non-destructive operation (adding column and new table only)
- Fully reversible via downgrade function
- Backward compatible - existing tasks will have NULL for image_set_ids
- CASCADE DELETE ensures data integrity when parent records are deleted
- Unique constraint prevents duplicate usage records
- **Downgrade Warning**: Rolling back this migration will permanently delete the dataset_image_usage table and all usage tracking data, and remove the image_set_ids column from generation_tasks

**Status**: APPLIED

---

### Migration: 5999ec64f0aa - add_face_count_to_dataset_images
**Date**: 2026-03-12 11:47:09
**Parent**: 9f2e3d4b6c8a

**Changes:**
- Added `face_count` (Integer, NULLABLE, Indexed) column to `dataset_images` table
  - Stores the number of faces detected in each image using YuNet face detection
  - NULL = image not yet analyzed for faces
  - 0 = no faces detected in image
  - 1+ = number of faces detected in image

**Files**: `/home/niro/galacticos/avatar-data-generator/migrations/versions/5999ec64f0aa_add_face_count_to_dataset_images.py`

**Purpose:**
Enables server-side face detection during image import to improve scene selection quality and reduce client-side processing. The face_count field is populated during image import by running YuNet face detection on the server, eliminating the need for client-side face detection in the UI.

**Schema Changes Details:**
- Column is nullable to maintain backward compatibility with existing images
- Index on `face_count` enables efficient filtering of images by face count
- Supports queries like "find all images with exactly 1 face" or "exclude images with no faces"

**Use Cases:**
- Filter images to only show those with detected faces
- Prioritize images with specific face counts for scene generation
- Improve image selection quality by excluding images without faces
- Display face count statistics in UI without client-side processing

**Safety Notes:**
- Non-destructive operation (adding nullable column and index only)
- Fully reversible via downgrade function
- Backward compatible - existing images will have NULL for face_count until analyzed
- Index creation is fast and non-blocking for existing data
- **Downgrade Warning**: Rolling back this migration will permanently delete all face_count data and the associated index

**Status**: APPLIED (Current HEAD)

---

### Migration: 0601dbe40e04 - add_base_image_size_to_generation_results
**Date**: 2026-02-25 15:49:00
**Parent**: 312faec904ca

**Status**: REVERTED (File Deleted)

**Why Reverted:**
This migration added the `base_image_size` field to store base image dimensions for SeeDream generation. However, this approach was replaced with direct code-based dimension randomization, making database storage unnecessary. The field was removed by migration 42eba0ec3095.

**Resolution:**
- Migration rolled forward to 42eba0ec3095 which removes the column
- Original migration file deleted as it's superseded by the removal migration
- Dimensions now randomized in code without database persistence

---

### Migration: 9d413bd6c3bd - add_face_randomization_settings_to_settings_table
**Date**: 2026-01-31 14:03:48
**Parent**: 30c18b6939ce

**Status**: REVERTED (Bad Design)

**Why Reverted:**
This migration incorrectly added `randomize_face_base` and `randomize_face_gender_lock` boolean columns to the `settings` table. The settings table is designed for key-value bio prompts (4 rows), not for boolean configuration flags. This created a flawed schema where global config booleans were columns on rows meant for text prompts.

**Resolution:**
- Migration was rolled back on 2026-01-31
- Migration file deleted from versions directory
- Replaced with proper Config table design (migration d59663db64e2)
- Face randomization settings moved to dedicated Config table

---

## How to Apply Migrations

```bash
# Activate virtual environment
source venv/bin/activate

# Apply all pending migrations
flask db upgrade

# Or using alembic directly
alembic upgrade head
```

## How to Rollback Migrations

```bash
# Rollback last migration
flask db downgrade

# Or using alembic directly
alembic downgrade -1
```

## Current Schema Status

**Latest Migration**: 5999ec64f0aa (add_face_count_to_dataset_images) - APPLIED (HEAD)
**Total Tables**: 12
**Total Migrations**: 18 (2 reverted/deleted)
**Database State**: Up to date

**Recent Schema Changes:**
- NEW `dataset_images.face_count` (Integer, Indexed) - stores number of faces detected in each image via YuNet face detection (NULL = not analyzed, 0 = no faces, 1+ = face count)
- NEW `dataset_image_usage` table - tracks which scene images have been used in generation tasks for intelligent selection
- NEW `generation_tasks.image_set_ids` (ARRAY of INTEGER) - stores selected image-set IDs for scene-based generation
- NEW `image_datasets` table - user-created image datasets with UUID identifiers, status management, and public/private visibility
- NEW `dataset_images` table - images within datasets with source tracking (Flickr/URL), JSONB metadata, and SHA256 hashing for duplicates
- NEW `dataset_permissions` table - dataset sharing with view/edit permission levels
- NEW `config.show_base_images` (TRUE) - controls visibility of base images in dataset detail view
- REMOVED `generation_results.base_image_size` - no longer needed as dimensions are randomized in code
- NEW `generation_results.image_ideas_history` (JSONB array) - tracks image ideas/prompts to prevent duplicates in future generations
- NEW `generation_results.ethnicity` (String(100)), `age` (Integer) - demographic fields from updated Flowise workflow (71bf0c86-c802-4221-b6e7-0af16e350bb6)
- NEW `generation_results.job_title`, `workplace`, `edu_establishment`, `edu_study`, `current_city`, `current_state`, `prev_city`, `prev_state`, `about` - supplementary persona fields from updated Flowise workflow
- `settings.max_concurrent_tasks` ('1') - controls maximum number of concurrent avatar generation tasks
- `config.randomize_image_style` (FALSE) - enables randomized style processing for image diversity (color presets, contrast, sharpness, grain, vignette)
- `config.crop_white_borders` (FALSE) - enables automatic cropping of white borders from generated images
- `config` table created for global boolean configuration settings
- `config.randomize_face_base` (FALSE) - enables face randomization for base image generation
- `config.randomize_face_gender_lock` (FALSE) - locks face randomization to matching gender
- `settings` table cleaned (removed incorrectly added boolean columns)
- `generation_results.images` is JSONB array (supports 4, 8, or any number of images)
- `generation_results.base_image_url` retained as-is

---

## Notes

- All migrations are fully reversible with proper `upgrade()` and `downgrade()` functions
- The `settings` and `config` tables use server-side defaults (NOW()) for timestamp fields
- Bio prompts are pre-populated during migration and can be updated via the application
- Config values are pre-populated during migration for face randomization features
- The initial migration (25698f3f906f) was stamped as the database already had the users table
- Settings can be accessed via `Settings.get_value(key, default)` and `Settings.set_value(key, value)` class methods
- Config values can be accessed via `Config.get_value(key, default=False)` and `Config.set_value(key, value)` class methods

## Design Principles

**Settings Table vs Config Table:**
- **Settings table**: For text-based key-value configuration (bio prompts for social platforms)
  - Uses Text data type for values
  - Currently contains 4 rows (Facebook, Instagram, X, TikTok bio prompts)
  - Accessed via `Settings.get_value()` / `Settings.set_value()`

- **Config table**: For boolean feature flags and global configuration
  - Uses Boolean data type for values
  - Each config is a separate row (scalable design)
  - Accessed via `Config.get_value()` / `Config.set_value()`

This separation ensures proper schema normalization and prevents the anti-pattern of adding configuration columns to existing tables.
