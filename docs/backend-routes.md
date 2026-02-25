# Backend Routes - Avatar Data Generator

> *Maintained by: backend-coder agent*
> *Last Updated: 2026-02-25 (Added show_base_images setting)*

## Application Information

- **Framework**: Flask 3.0.0
- **Python Version**: 3.9+
- **Port**: 7001 (configurable via .env)
- **Base URL**: http://localhost:7001

## Authentication System

The application uses **Flask-Login** for session-based authentication with bcrypt password hashing.

### Session Configuration
- Session cookie: HttpOnly, SameSite=Lax
- Session lifetime: 7 days (with "remember me")
- CSRF protection: Enabled on all POST requests

## Routes Overview

### Public Routes (No Authentication Required)

#### GET `/`
**Description**: Home page - redirects based on authentication status
**Returns**:
- Authenticated users → Redirect to `/dashboard`
- Anonymous users → Redirect to `/login`

---

#### GET `/login`
**Description**: Display login form
**Template**: `templates/login.html`
**Returns**: HTML login page

**Query Parameters**:
- `next` (optional): URL to redirect to after successful login

**Template Variables**:
- `error`: Error message string (if login failed)
- `success`: Success message string (if applicable)

---

#### POST `/login`
**Description**: Process login credentials
**Content-Type**: `application/x-www-form-urlencoded`

**Form Fields**:
- `email` (required): User email address
- `password` (required): User password
- `remember` (optional): "on" to enable persistent session

**Responses**:
- **Success**: Redirect to dashboard or `next` parameter URL
- **Failure**: Render login page with error message

**Error Cases**:
- Missing email or password → "Please provide both email and password."
- Invalid credentials → "Invalid email or password."
- Inactive account → "Invalid email or password." (same message for security)

**Security Notes**:
- Passwords are hashed using bcrypt
- Email is normalized to lowercase
- Failed login attempts do not reveal if email exists
- Last login timestamp updated on success

---

#### GET `/logout`
**Description**: Log out current user
**Authentication**: Required
**Returns**: Redirect to `/login` with success message

---

#### GET `/forgot-password`
**Description**: Password reset page (placeholder)
**Returns**: Redirect to `/login` with info message
**Status**: Not yet implemented

---

#### GET `/signup`
**Description**: User registration page (placeholder)
**Returns**: Redirect to `/login` with info message
**Status**: Not yet implemented - registration disabled

---

### Protected Routes (Authentication Required)

All protected routes require a valid session. Unauthenticated users are redirected to `/login` with `next` parameter.

#### GET `/dashboard`
**Description**: Main user dashboard
**Authentication**: Required
**Template**: `templates/dashboard.html`

**Template Variables**:
- `user_name`: String - Username (extracted from email)
- `total_avatars`: Integer - Total avatars generated (default: 0)
- `active_datasets`: Integer - Number of active datasets (default: 0)
- `processing_jobs`: Integer - Number of jobs in progress (default: 0)
- `message`: String (optional) - Info/success message

**Current Implementation**:
All statistics are placeholders (set to 0) pending avatar generation implementation.

---

#### GET `/generate`
**Description**: Avatar generation page
**Authentication**: Required
**Status**: Placeholder - redirects to dashboard with info message
**Planned**: Form to configure and generate avatar datasets

---

#### GET `/datasets`
**Description**: Dataset management page - lists all tasks for current user
**Authentication**: Required
**Template**: `templates/datasets.html`

**Template Variables**:
- `user_name`: String - Username (extracted from email)
- `tasks`: List - All GenerationTask objects for current user, ordered by created_at DESC

**Implementation**:
Lists all avatar generation tasks for the current user, similar to /history but renders different template for dataset viewing interface.

---

#### GET `/api/dashboard/stats`
**Description**: Dashboard statistics API endpoint - returns overview and last 7 days data
**Authentication**: Required
**Content-Type**: `application/json`

**Success Response (200)**:
```json
{
  "overview": {
    "total_tasks": 150,
    "total_personas": 1500,
    "total_images": 6000,
    "completed_tasks": 145,
    "failed_tasks": 5,
    "tasks_in_progress": 2,
    "average_personas_per_task": 10.0,
    "average_images_per_persona": 4.0
  },
  "last_7_days": {
    "tasks_by_date": [
      {"date": "2026-01-24", "count": 10},
      {"date": "2026-01-25", "count": 15},
      {"date": "2026-01-26", "count": 12},
      {"date": "2026-01-27", "count": 8},
      {"date": "2026-01-28", "count": 20},
      {"date": "2026-01-29", "count": 18},
      {"date": "2026-01-30", "count": 5}
    ],
    "personas_by_date": [
      {"date": "2026-01-24", "count": 100},
      {"date": "2026-01-25", "count": 150},
      {"date": "2026-01-26", "count": 120},
      {"date": "2026-01-27", "count": 80},
      {"date": "2026-01-28", "count": 200},
      {"date": "2026-01-29", "count": 180},
      {"date": "2026-01-30", "count": 50}
    ],
    "images_by_date": [
      {"date": "2026-01-24", "count": 400},
      {"date": "2026-01-25", "count": 600},
      {"date": "2026-01-26", "count": 480},
      {"date": "2026-01-27", "count": 320},
      {"date": "2026-01-28", "count": 800},
      {"date": "2026-01-29", "count": 720},
      {"date": "2026-01-30", "count": 200}
    ]
  }
}
```

**Error Response (500)**:
```json
{
  "success": false,
  "error": "An error occurred while generating dashboard statistics"
}
```

**Implementation Details**:
- All statistics filtered by current user (user_id)
- Overview counts:
  - Total tasks, personas, images across all time
  - Tasks grouped by status (completed, failed, in-progress)
  - Averages calculated with proper division-by-zero handling
- Last 7 days data:
  - Includes today (7 days total)
  - Missing dates filled with 0 count
  - Dates sorted ascending
  - Images counted by summing JSON array lengths
  - Personas and images grouped by task creation date

**Database Queries**:
- Uses SQLAlchemy `func.date()` and `func.count()` for efficient aggregation
- Joins GenerationResult with GenerationTask for user filtering
- Separate queries for tasks, personas, and images for optimal performance

**Security**:
- Requires authentication via `@login_required`
- Only shows data for current user
- Proper error handling with rollback on exceptions

---

#### GET `/datasets/<task_id>/data`
**Description**: Dataset detail API endpoint - returns task details, progress stats, and paginated results
**Authentication**: Required
**Content-Type**: `application/json`

**Path Parameters**:
- `task_id`: String - Task ID (short UUID, e.g., "a1b2c3d4")

**Query Parameters**:
- `page`: Integer (default: 1) - Page number for results
- `per_page`: Integer (default: 20, max: 100) - Results per page

**Success Response (200)**:
```json
{
  "success": true,
  "task": {
    "task_id": "a1b2c3d4",
    "status": "completed",
    "persona_description": "Young professionals in tech",
    "bio_language": "English",
    "number_to_generate": 50,
    "images_per_persona": 4,
    "created_at": "2025-01-30T10:00:00",
    "completed_at": "2025-01-30T10:15:00",
    "error_log": null,
    "show_base_images": true
  },
  "progress": {
    "total_personas": 50,
    "completed_personas": 50,
    "completed_images": 50,
    "progress_percentage": 100.0,
    "time_elapsed": "15m 30s",
    "status_message": "Completed! Generated 50 personas with images."
  },
  "results": [
    {
      "id": 1,
      "firstname": "John",
      "lastname": "Doe",
      "gender": "m",
      "bios": {
        "facebook": "Tech enthusiast...",
        "instagram": "Code, coffee, repeat...",
        "x": "Building the future...",
        "tiktok": "Developer life..."
      },
      "supplementary": {
        "job_title": "Software Engineer",
        "workplace": "Tech Corp",
        "edu_establishment": "MIT",
        "edu_study": "Computer Science",
        "current_city": "San Francisco",
        "current_state": "California",
        "prev_city": "New York",
        "prev_state": "New York",
        "about": "Passionate about technology"
      },
      "images": ["https://s3.amazonaws.com/...", ...]
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 3,
    "total_results": 50,
    "has_next": true,
    "has_prev": false,
    "per_page": 20
  }
}
```

**Error Responses**:
- **404**: Task not found
- **403**: Access denied (task belongs to another user)

**Security**:
- Verifies task ownership before returning data
- Pagination prevents memory issues with large datasets

---

#### GET `/datasets/<task_id>/export/json`
**Description**: Export complete task data and all results as JSON file
**Authentication**: Required

**Path Parameters**:
- `task_id`: String - Task ID (short UUID)

**Response**:
- Content-Type: `application/json`
- Content-Disposition: `attachment; filename="dataset_{task_id}.json"`

**Export Structure**:
```json
{
  "task": {
    "task_id": "abc123",
    "status": "completed",
    "persona_description": "...",
    "bio_language": "English",
    "number_to_generate": 10,
    "images_per_persona": 8,
    "created_at": "2026-02-05T12:00:00",
    "completed_at": "2026-02-05T12:15:00"
  },
  "results": [
    {
      "firstname": "John",
      "lastname": "Doe",
      "gender": "m",
      "bios": {
        "facebook": "...",
        "instagram": "...",
        "x": "...",
        "tiktok": "..."
      },
      "supplementary": {
        "job_title": "Software Engineer",
        "workplace": "Tech Corp",
        "edu_establishment": "MIT",
        "edu_study": "Computer Science",
        "current_city": "San Francisco",
        "current_state": "California",
        "prev_city": "New York",
        "prev_state": "New York",
        "about": "Passionate about technology"
      },
      "images": ["url1", "url2", ...]
    }
  ]
}
```

**Security**:
- Verifies task ownership
- Returns 404 if task not found
- Returns 403 if user doesn't own task

---

#### GET `/datasets/<task_id>/export/csv`
**Description**: Export task results as flattened CSV file
**Authentication**: Required

**Path Parameters**:
- `task_id`: String - Task ID (short UUID)

**Response**:
- Content-Type: `text/csv`
- Content-Disposition: `attachment; filename="dataset_{task_id}.csv"`

**CSV Columns**:
- firstname, lastname, gender
- bio_facebook, bio_instagram, bio_x, bio_tiktok
- job_title, workplace (supplementary fields)
- edu_establishment, edu_study (supplementary fields)
- current_city, current_state (supplementary fields)
- prev_city, prev_state (supplementary fields)
- about (supplementary field)
- image_1, image_2, ..., image_N (N = images_per_persona, up to 20)

**Notes**:
- Column count adapts to images_per_persona setting
- Missing images export as empty strings
- All text properly escaped for CSV format

**Security**:
- Verifies task ownership
- Returns 404 if task not found
- Returns 403 if user doesn't own task

---

#### DELETE/POST `/datasets/<task_id>/delete`
**Description**: Delete a dataset and all associated S3 files
**Authentication**: Required
**Methods**: DELETE (preferred), POST (for HTML forms)

**Path Parameters**:
- `task_id`: String - Task ID (short UUID)

**Behavior**:
1. Validates dataset exists and belongs to current user
2. Deletes all S3 files:
   - Base images (base_image_url for each result)
   - Split images (all images in images array for each result)
3. Deletes all GenerationResult records for the task
4. Deletes the GenerationTask record

**Success Response (200)** - JSON (DELETE/AJAX):
```json
{
  "success": true,
  "message": "Dataset deleted successfully",
  "deleted_base_images": 10,
  "deleted_split_images": 80,
  "total_deleted": 90,
  "warning": "2 file(s) failed to delete from S3",
  "failed_deletions": [
    "https://s3.../image1.png",
    "https://s3.../image2.png"
  ]
}
```

**Success Response** - HTML form (POST):
- Redirect to `/datasets` with flash message
- Flash category: `success` or `warning` (if some S3 deletions failed)

**Error Responses**:
- **404**: Task not found
  ```json
  {
    "success": false,
    "error": "Task not found"
  }
  ```
- **403**: Access denied (task belongs to another user)
  ```json
  {
    "success": false,
    "error": "Access denied"
  }
  ```
- **500**: Server error during deletion
  ```json
  {
    "success": false,
    "error": "An error occurred while deleting the dataset"
  }
  ```

**S3 Deletion Behavior**:
- Uses `delete_s3_url()` from `services.image_utils`
- Logs warnings for failed S3 deletions but continues
- Returns warning in response if any S3 deletions failed
- Non-existent S3 objects are treated as successful deletions

**Database Transaction**:
- All database changes are wrapped in a transaction
- Rollback occurs on any error
- CASCADE delete on GenerationResult ensures referential integrity

**Security**:
- Verifies task ownership before deletion
- Requires authentication
- Proper error handling prevents information leakage

**Logging**:
- Logs each S3 file deletion (success and failure)
- Logs deletion summary with statistics
- Error logs include full stack trace for debugging

---

#### GET `/datasets/<task_id>/export/zip`
**Description**: Export complete dataset as ZIP file with images and data.json
**Authentication**: Required

**Path Parameters**:
- `task_id`: String - Task ID (short UUID)

**Response**:
- Content-Type: `application/zip`
- Content-Disposition: `attachment; filename="dataset_{task_id}.zip"`

**ZIP Contents**:
```
dataset_{task_id}.zip/
├── data.json          # Complete task and results data
└── images/
    ├── 1_base.jpg     # Base selfie image for result ID 1
    ├── 1_1.jpg        # Split image 1 for result ID 1
    ├── 1_2.jpg        # Split image 2 for result ID 1
    ├── ...
    ├── 2_base.jpg     # Base selfie image for result ID 2
    └── ...
```

**Image Naming Convention**:
- Base images: `{result_id}_base.{ext}`
- Split images: `{result_id}_{index}.{ext}`
- Extension determined from S3 URL (jpg, png, gif, webp)

**Implementation Details**:
- Downloads images from S3 using requests library
- Creates temporary directory for processing
- Streams ZIP to avoid memory issues with large datasets
- Gracefully handles S3 download errors (logs and continues)
- Cleans up temporary files after send

**Error Handling**:
- Logs warnings for failed image downloads (continues processing)
- Cleans up temp directory on error
- Flash message on failure with redirect to /datasets

**Security**:
- Verifies task ownership
- 30-second timeout for S3 downloads
- Validates file extensions from URLs
- Returns 404 if task not found
- Returns 403 if user doesn't own task

---

#### GET `/history`
**Description**: Generation history page
**Authentication**: Required
**Template**: `templates/history.html`

**Template Variables**:
- `user_name`: String - Username (extracted from email)
- `tasks`: List - All GenerationTask objects for current user, ordered by created_at DESC

**Implementation**:
Lists all avatar generation tasks for the current user with status and basic information.

---

#### GET `/workflow-logs`
**Description**: Workflow execution logs page - displays all LLM workflow runs with filtering and pagination
**Authentication**: Required
**Template**: `templates/workflow_logs.html`

**Query Parameters**:
- `page`: Integer (default: 1) - Page number for pagination
- `workflow_name`: String (optional) - Filter by workflow name
- `status`: String (optional) - Filter by status (completed, failed, running)

**Template Variables**:
- `user_name`: String - Username (extracted from email)
- `logs`: List - Paginated WorkflowLog objects
- `pagination`: Object - Flask-SQLAlchemy pagination object
- `workflow_names`: List - Unique workflow names for filter dropdown
- `current_workflow_filter`: String - Current workflow name filter
- `current_status_filter`: String - Current status filter

**Features**:
- Displays workflow execution logs in table format
- Shows truncated workflow run IDs (first 8 characters)
- Links to task datasets when task_id is available
- Displays status with color-coded badges (green=completed, red=failed, yellow=running)
- Shows total tokens, total cost (formatted as $X.XXXXXX), execution time (ms)
- Formatted timestamps (YYYY-MM-DD HH:MM:SS)
- Filter by workflow name and status
- Pagination (25 logs per page)
- Mobile-responsive design

**Implementation**:
Lists all workflow execution logs from the `workflow_logs` table, ordered by `started_at DESC` (newest first). Supports filtering and pagination for efficient browsing of large log datasets.

---

#### GET `/workflow-logs/<workflow_run_id>`
**Description**: Workflow log detail page - displays detailed execution information for a specific workflow run
**Authentication**: Required
**Template**: `templates/workflow_log_detail.html`

**Path Parameters**:
- `workflow_run_id`: String - Workflow run UUID (supports full UUID or first 8 characters)

**Template Variables**:
- `user_name`: String - Username (extracted from email)
- `workflow_log`: Object - WorkflowLog object with workflow execution details
- `node_logs`: List - WorkflowNodeLog objects ordered by node_order

**Workflow Information Displayed**:
- Workflow run ID (full UUID)
- Workflow name
- Status (with color coding)
- Execution time (ms)
- Started at / Completed at timestamps
- Task ID (linked to dataset if available)
- Persona ID
- Total tokens used
- Total cost (USD)
- Error message (if failed)

**Node Execution Table Columns**:
- Node Order (execution sequence)
- Node Name
- Model Name (e.g., gpt-4o-mini)
- Temperature setting
- Max Tokens setting
- Prompt Tokens used
- Completion Tokens generated
- Total Tokens
- Cost (USD, formatted to 6 decimal places)
- Execution Time (ms)
- Status (with badge)
- Actions (View Prompts, View Output buttons)

**Expandable Sections**:
- **View Prompts**: Expands to show system_prompt and user_prompt sent to LLM
  - Always shows buttons (even if data is null)
  - Displays fallback message if prompt data not available
  - JavaScript console logging for debugging
- **View Output**: Expands to show output_data JSON response from LLM
  - Always shows button (even if data is null)
  - Displays fallback message if output data not available
  - JavaScript console logging for debugging

**Features**:
- Breadcrumb navigation back to logs list
- Info cards for status, context, and token/cost metrics
- Expandable prompt and output viewing (always visible, with fallbacks)
- Mobile-responsive design
- Formatted JSON output with syntax preservation
- Error message display for failed workflows
- Debug console logging for JavaScript toggle functions

**Implementation**:
Displays complete observability data for a single workflow execution. Node logs are ordered by execution sequence. Prompts and outputs are hidden by default and can be expanded inline for detailed inspection. All nodes always show "View Prompts" and "View Output" buttons regardless of data availability - fallback messages are displayed when data is null/None.

**Debugging**:
- Route logs node data availability (system_prompt, user_prompt, output_data)
- JavaScript console logs toggle actions and DOM element detection
- Check browser console for troubleshooting expandable sections

**Error Handling**:
- Returns 404 flash message and redirects to `/workflow-logs` if workflow_run_id not found
- Gracefully handles missing prompt/output data with fallback messages

---

#### GET `/settings`
**Description**: Settings page - display bio prompts, face generation, and image degradation configuration
**Authentication**: Required
**Template**: `templates/settings.html`

**Template Variables**:
- `user_name`: String - Username (extracted from email)
- `bio_prompts`: Dictionary containing:
  - `bio_prompt_facebook`: String - Facebook bio prompt text
  - `bio_prompt_instagram`: String - Instagram bio prompt text
  - `bio_prompt_x`: String - X (Twitter) bio prompt text
  - `bio_prompt_tiktok`: String - TikTok bio prompt text
- `randomize_face_base`: Boolean - Enable random face generation for base images
- `randomize_face_gender_lock`: Boolean - Lock gender during face randomization
- `crop_white_borders`: Boolean - Auto-crop white borders from generated images
- `randomize_image_style`: Boolean - Apply random style variations to images
- `obfuscate_exif_metadata`: Boolean - Strip and replace EXIF metadata with randomized fake data for persona images
- `show_base_images`: Boolean - Show base images in dataset detail view (default: True)
- `max_concurrent_tasks`: Integer - Max concurrent generation tasks (1-5)
- `degradation_states`: Dictionary - Enabled state for each degradation prompt (key: `degradation_<prompt_id>`, value: Boolean)
- `degradation_prompts`: Dictionary - Map of all available degradation prompts with metadata

**Degradation Prompts Structure**:
Each prompt in `degradation_prompts` has the following structure:
```python
{
  'prompt_id': {
    'name': 'Human-readable name',
    'description': 'Short description of the effect',
    'prompt': 'Full prompt text used in generation',
    'category': 'Category name'
  }
}
```

**Degradation Categories**:
- Backlighting (2 prompts)
- Flash Problems (2 prompts)
- Overexposure (2 prompts)
- Low Light (2 prompts)
- Old Camera Quality (3 prompts)
- Focus Issues (1 prompt)
- White Balance (1 prompt)

**Current Implementation**:
Displays three main settings sections:
1. Face Generation Settings - Control face randomization, EXIF obfuscation, and concurrency
2. Image Degradation Settings - Toggle individual degradation prompts on/off
3. Bio Prompts Configuration - Edit AI prompts for bio generation

All settings are loaded from the database. Degradation prompt states default to enabled (True) if not found in Config table.

**EXIF Metadata Obfuscation** (`obfuscate_exif_metadata`):
- When enabled, strips existing EXIF metadata from persona images and injects randomized fake data
- Applies to persona images ONLY (image_0.png, image_1.png, etc.), NOT base images
- Randomized data includes:
  - Timestamps: Random dates between 2017-2021
  - GPS coordinates: Random worldwide locations (100+ cities with offsets)
  - Camera models: 50+ smartphones and cameras from 2015-2020 era
  - Technical EXIF: ISO, aperture, focal length, shutter speed, etc.
- Provides astronomical variety: billions of unique metadata combinations
- Gracefully degrades on failure (returns original image if obfuscation fails)
- See `playground/EXIF_OBFUSCATION_IMPLEMENTATION.md` for full documentation

---

#### POST `/settings/save`
**Description**: Save bio prompts, face generation, and degradation settings (AJAX endpoint)
**Authentication**: Required
**Content-Type**: `application/json`

**Request Body**:
Can include any combination of the following settings:

**String Settings** (stored in Settings table):
```json
{
  "bio_prompt_facebook": "string",
  "bio_prompt_instagram": "string",
  "bio_prompt_x": "string",
  "bio_prompt_tiktok": "string"
}
```

**Boolean Settings** (stored in Config table):
```json
{
  "randomize_face_base": true,
  "randomize_face_gender_lock": false,
  "crop_white_borders": true,
  "randomize_image_style": false,
  "obfuscate_exif_metadata": true,
  "show_base_images": true,
  "degradation_backlight_1": true,
  "degradation_backlight_2": false,
  "degradation_flash_1": true,
  "degradation_flash_2": true,
  "degradation_overexposure_1": true,
  "degradation_overexposure_2": false,
  "degradation_lowlight_1": true,
  "degradation_lowlight_2": true,
  "degradation_oldcamera_1": true,
  "degradation_oldcamera_2": false,
  "degradation_oldcamera_3": true,
  "degradation_blur_1": true,
  "degradation_whitebalance_1": true
}
```

**Integer Settings** (stored in IntConfig table):
```json
{
  "max_concurrent_tasks": 3
}
```

**Validation**:
- Request body must contain valid JSON
- At least one valid setting key must be provided
- String values must be strings
- Boolean values must be booleans
- Integer values must be integers
- `max_concurrent_tasks` must be between 1 and 5
- Only accepts expected setting keys
- Degradation prompt keys dynamically validated against `DEGRADATION_PROMPTS_MAP`

**Responses**:

**Success (200)**:
```json
{
  "success": true,
  "message": "Settings saved successfully",
  "saved_settings": ["bio_prompt_facebook", "bio_prompt_instagram", ...]
}
```

**Error (400)** - No data provided:
```json
{
  "success": false,
  "error": "No data provided"
}
```

**Error (400)** - No valid settings:
```json
{
  "success": false,
  "error": "No valid settings provided"
}
```

**Error (400)** - Invalid value type:
```json
{
  "success": false,
  "error": "Invalid value type for {key}"
}
```

**Error (500)** - Server error:
```json
{
  "success": false,
  "error": "An error occurred while saving settings"
}
```

**Usage Example**:
You can send any combination of settings in a single request:
```json
{
  "bio_prompt_facebook": "Updated prompt...",
  "randomize_face_base": true,
  "degradation_backlight_1": false,
  "max_concurrent_tasks": 3
}
```

**Implementation Notes**:
- String settings saved to `settings` table via `Settings.set_value()`
- Boolean settings saved to `config` table via `Config.set_value()`
- Integer settings saved to `int_config` table via `IntConfig.set_value()`
- All changes committed in a single transaction
- Partial updates supported (only provided keys are updated)
- Degradation prompt keys are dynamically generated from `services.style_degradation_prompts.DEGRADATION_PROMPTS_MAP`

**Security Notes**:
- CSRF protection enabled (automatic via Flask-WTF)
- Bio prompt settings are application-wide (shared across all users)
- Face generation and degradation settings are application-wide
- Input validation by type (string, boolean, integer)
- Database rollback on error to maintain data integrity
- Strict validation of integer ranges (e.g., max_concurrent_tasks: 1-5)

---

## Error Handlers

### 404 Not Found
**Trigger**: Invalid URL
**Response**: Redirect to dashboard (if authenticated) or login (if not)
**Flash Message**: "Page not found."

### 500 Internal Server Error
**Trigger**: Unhandled exception
**Response**: Redirect to dashboard (if authenticated) or login (if not)
**Flash Message**: "An internal error occurred. Please try again."
**Side Effect**: Database session rollback

---

## Security Features

### CSRF Protection
- Enabled on all POST/PUT/DELETE requests
- Token generated automatically by Flask-WTF
- Templates must include `{{ csrf_token() }}` in forms

### Password Security
- Hashing: bcrypt with automatic salt generation
- Minimum length: 8 characters (enforced in create_admin.py)
- Stored as: VARCHAR(255) hashed string
- Never transmitted or logged in plain text

### Security Headers
All responses include:
- `X-Frame-Options: SAMEORIGIN` - Prevent clickjacking
- `X-Content-Type-Options: nosniff` - Prevent MIME sniffing
- `X-XSS-Protection: 1; mode=block` - XSS protection
- `Strict-Transport-Security` - HTTPS enforcement (production)

### Input Validation
- Email: Normalized to lowercase, validated format
- SQL Injection: Prevented by SQLAlchemy ORM parameterized queries
- XSS: Prevented by Jinja2 auto-escaping

---

## Database Models

### User Model (`models.User`)

**Table**: `users`

**Fields**:
- `id`: Integer, Primary Key, Auto-increment
- `email`: String(255), Unique, Indexed, Not Null
- `password_hash`: String(255), Not Null
- `created_at`: DateTime, Default: current timestamp
- `last_login`: DateTime, Nullable
- `is_active`: Boolean, Default: True

**Methods**:
- `set_password(password)`: Hash and store password
- `check_password(password)`: Verify password
- `update_last_login()`: Update last_login timestamp
- `get_id()`: Return user ID as string (Flask-Login)

**Properties**:
- `is_authenticated`: Always True for User objects
- `is_anonymous`: Always False for User objects

---

### Settings Model (`models.Settings`)

**Table**: `settings`

**Fields**:
- `id`: Integer, Primary Key, Auto-increment
- `key`: String(255), Unique, Indexed, Not Null
- `value`: Text, Nullable
- `created_at`: DateTime, Default: current timestamp
- `updated_at`: DateTime, Default: current timestamp, Auto-update on change

**Class Methods**:
- `get_value(key, default=None)`: Retrieve setting value by key, returns default if not found
- `set_value(key, value)`: Set or update setting value, creates new record if doesn't exist

**Usage**:
Settings are stored as key-value pairs and are application-wide (not user-specific). The model provides convenient class methods for retrieving and updating settings without manual session management.

**Example**:
```python
# Get a setting
facebook_prompt = Settings.get_value('bio_prompt_facebook', 'Default prompt')

# Set a setting
Settings.set_value('bio_prompt_facebook', 'New prompt text')
db.session.commit()
```

---

### WorkflowLog Model (`models.WorkflowLog`)

**Table**: `workflow_logs`

**Description**: Stores LLM workflow execution logs for observability and cost analysis

**Fields**:
- `id`: Integer, Primary Key, Auto-increment
- `workflow_run_id`: String(36), Unique UUID for this workflow execution, Indexed
- `workflow_name`: String(100), Name of workflow (e.g., "image_prompt_chain"), Indexed
- `task_id`: Integer, Foreign Key to generation_tasks.id, Nullable, Indexed
- `persona_id`: Integer, Foreign Key to generation_results.id, Nullable, Indexed
- `status`: String(50), Workflow status (running, completed, failed), Indexed
- `input_data`: JSONB, Workflow input parameters
- `output_data`: JSONB, Workflow output/results
- `total_tokens`: Integer, Total tokens used across all nodes
- `total_cost`: Float, Total cost in USD across all nodes
- `execution_time_ms`: Integer, Total execution time in milliseconds
- `error_message`: Text, Error message if workflow failed
- `started_at`: DateTime, Timestamp when workflow started, Indexed (DESC)
- `completed_at`: DateTime, Timestamp when workflow completed
- `created_at`: DateTime, Default: current timestamp

**Relationships**:
- `nodes`: One-to-many relationship with WorkflowNodeLog (CASCADE delete)
- `task`: Many-to-one relationship with GenerationTask (SET NULL on delete)
- `persona`: Many-to-one relationship with GenerationResult (SET NULL on delete)

**Indexes**:
- `workflow_run_id` (unique)
- `workflow_name`
- `task_id`
- `persona_id`
- `status`
- `started_at DESC`

---

### WorkflowNodeLog Model (`models.WorkflowNodeLog`)

**Table**: `workflow_node_logs`

**Description**: Stores individual node execution logs within LLM workflows for detailed observability

**Fields**:
- `id`: Integer, Primary Key, Auto-increment
- `workflow_log_id`: Integer, Foreign Key to workflow_logs.id, Not Null, Indexed
- `node_name`: String(100), Name of the node (e.g., "generate_idea"), Indexed
- `node_order`: Integer, Execution order (0-indexed), Indexed with workflow_log_id
- `status`: String(50), Node status (running, completed, failed)
- `model_name`: String(100), LLM model used (e.g., "gpt-4o-mini")
- `temperature`: Float, Temperature setting used
- `max_tokens`: Integer, Max tokens setting
- `system_prompt`: Text, System prompt sent to LLM
- `user_prompt`: Text, User prompt sent to LLM
- `input_data`: JSONB, Node input parameters
- `output_data`: JSONB, Node output/response
- `prompt_tokens`: Integer, Number of prompt tokens used
- `completion_tokens`: Integer, Number of completion tokens generated
- `total_tokens`: Integer, Total tokens used (prompt + completion)
- `cost`: Float, Cost in USD for this node execution
- `execution_time_ms`: Integer, Execution time in milliseconds
- `error_message`: Text, Error message if node failed
- `started_at`: DateTime, Timestamp when node started
- `completed_at`: DateTime, Timestamp when node completed
- `created_at`: DateTime, Default: current timestamp

**Relationships**:
- `workflow_log`: Many-to-one relationship with WorkflowLog

**Indexes**:
- `workflow_log_id`
- `node_name`
- Composite index on (workflow_log_id, node_order)

**Usage**:
WorkflowNodeLog records are created for each step in an LLM workflow execution. The `node_order` field maintains the execution sequence, and the complete prompts, responses, and token usage are stored for full observability.

---

## Flash Message Categories

Used with `flash(message, category)`:

- `error`: Error messages (red alert)
- `success`: Success messages (green alert)
- `info`: Informational messages (blue alert)
- `warning`: Warning messages (yellow alert)

Templates should handle these categories with appropriate styling.

---

## Environment Variables

Required configuration (see `.env.example`):

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=avatar_data_generator
DB_USER=avatar_data_gen
DB_PASSWORD=your_secure_password_here

# Application
APP_PORT=7001
FLASK_ENV=development
SECRET_KEY=your_secret_key_here

# Optional: Direct connection string
DATABASE_URL=postgresql://avatar_data_gen:password@localhost:5432/avatar_data_generator
```

---

## Future Routes (Planned)

### Avatar Generation API
- `POST /api/generate` - Start avatar generation job
- `GET /api/generate/:id` - Check generation status
- `GET /api/generate/:id/download` - Download generated avatars

### Dataset Management API
- `GET /api/datasets` - List datasets
- `POST /api/datasets` - Create dataset
- `GET /api/datasets/:id` - Get dataset details

### User Management
- `POST /api/users` - Create user (admin only)
- `PUT /api/users/:id` - Update user
- `DELETE /api/users/:id` - Delete user (admin only)

### API Authentication
- API key based authentication for programmatic access
- Rate limiting per user/API key
- Usage quotas and tracking

---

## Development Scripts

### Database Management
- `python init_db.py` - Initialize database and migrations
- `flask db migrate -m "message"` - Create migration
- `flask db upgrade` - Apply migrations
- `flask db downgrade` - Rollback migration

### User Management
- `python create_admin.py` - Create/update user
- `python create_admin.py --email user@example.com --password pass123`
- `python create_admin.py --force` - Replace existing user

### Verification
- `python verify_setup.py` - Verify complete setup

---

## Testing Endpoints

### Manual Testing with cURL

**Login**:
```bash
curl -X POST http://localhost:7001/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=admin@example.com&password=yourpassword" \
  -c cookies.txt
```

**Access Protected Route**:
```bash
curl http://localhost:7001/dashboard \
  -b cookies.txt
```

**Logout**:
```bash
curl http://localhost:7001/logout \
  -b cookies.txt
```

**Save Settings (AJAX)**:
```bash
# Get CSRF token from settings page first
curl http://localhost:7001/settings -b cookies.txt

# Save settings with CSRF token
curl -X POST http://localhost:7001/settings/save \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN_HERE" \
  -b cookies.txt \
  -d '{
    "bio_prompt_facebook": "Facebook bio text",
    "bio_prompt_instagram": "Instagram bio text",
    "bio_prompt_x": "X bio text",
    "bio_prompt_tiktok": "TikTok bio text"
  }'
```

---

## Notes

- All timestamps stored in UTC
- Email addresses stored in lowercase
- Session cookies are HTTP-only (not accessible via JavaScript)
- CSRF tokens required for all state-changing operations
- Database connections use connection pooling via SQLAlchemy
- Application uses factory pattern for easier testing

---

## Troubleshooting

**Login fails with valid credentials**:
- Check database connectivity
- Verify user exists: `SELECT * FROM users WHERE email='your@email.com';`
- Ensure user.is_active = true

**CSRF token errors**:
- Clear browser cookies
- Ensure form includes `{{ csrf_token() }}`
- Check WTF_CSRF_ENABLED in config

**Session not persisting**:
- Verify SECRET_KEY is set and constant
- Check browser cookie settings
- Ensure "remember me" is checked for persistent sessions

---

## Contact

For changes to this documentation or route implementations, contact the **backend-coder** agent.
