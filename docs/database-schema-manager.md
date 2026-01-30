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

**Latest Migration**: d8cfd3cb4083 (create_settings_table) - APPLIED
**Total Tables**: 2
**Total Migrations**: 2
**Database State**: Up to date

---

## Notes

- All migrations are fully reversible with proper `upgrade()` and `downgrade()` functions
- The `settings` table uses server-side defaults (NOW()) for timestamp fields
- Bio prompts are pre-populated during migration and can be updated via the application
- The initial migration (25698f3f906f) was stamped as the database already had the users table
- Settings can be accessed via the `Settings.get_value(key, default)` and `Settings.set_value(key, value)` class methods
