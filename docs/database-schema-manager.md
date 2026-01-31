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
4. **generation_tasks** - Avatar generation task tracking and management
5. **generation_results** - Persona data and avatar image URLs for each generated avatar

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
- `bio_facebook` (Text, NULLABLE) - Generated Facebook bio text
- `bio_instagram` (Text, NULLABLE) - Generated Instagram bio text
- `bio_x` (Text, NULLABLE) - Generated X (Twitter) bio text
- `bio_tiktok` (Text, NULLABLE) - Generated TikTok bio text
- `base_image_url` (Text, NULLABLE) - Public S3 URL for base selfie image
- `images` (JSONB, NULLABLE) - JSON array of public S3 URLs for split images (flexible: 4, 8, or any number)
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

**Status**: APPLIED (Current)

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

**Latest Migration**: d59663db64e2 (create_config_table_for_boolean_settings) - APPLIED
**Total Tables**: 5
**Total Migrations**: 7 (1 reverted)
**Database State**: Up to date

**Recent Schema Changes:**
- NEW `config` table created for global boolean configuration settings
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
