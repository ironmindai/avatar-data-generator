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
2. **settings** - Application configuration key-value store
3. **generation_tasks** - Avatar generation task tracking and management

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

**Latest Migration**: 3a0f944324eb (create_generation_tasks_table) - APPLIED
**Total Tables**: 3
**Total Migrations**: 3
**Database State**: Up to date

---

## Notes

- All migrations are fully reversible with proper `upgrade()` and `downgrade()` functions
- The `settings` table uses server-side defaults (NOW()) for timestamp fields
- Bio prompts are pre-populated during migration and can be updated via the application
- The initial migration (25698f3f906f) was stamped as the database already had the users table
- Settings can be accessed via the `Settings.get_value(key, default)` and `Settings.set_value(key, value)` class methods
