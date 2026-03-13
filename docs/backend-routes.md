# Backend Routes - Avatar Data Generator

> *Maintained by: backend-coder agent*
> *Last Updated: 2026-03-13 (Reverted URL import to synchronous - async had GIL/threading issues)*

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

#### GET/POST `/generate`
**Description**: Avatar generation page and task creation endpoint
**Authentication**: Required
**Template**: `templates/generate.html` (GET)

**GET Request**:
- Displays avatar generation form with language selection
- Template Variables:
  - `user_name`: String - Username (extracted from email)

**POST Request**:
- Creates new generation task with image-set selection
- Content-Type: `application/x-www-form-urlencoded` or `application/json`

**Form/Request Parameters**:
- `persona_description` (required): Text - Description of personas to generate
- `bio_language` (required): String - Language code for bio generation (e.g., 'en', 'es', 'fr')
- `number_to_generate` (required): Integer - Number of personas to generate (10-300)
- `images_per_persona` (required): Integer - Number of images per persona (1-20)
- `image_set_ids[]` (required): Array of integers - IDs of image-sets to use for scene-based generation

**Validation**:
1. Persona description must not be empty
2. Bio language must be valid (from LANGUAGE_MAP)
3. Number to generate must be between 10 and 300
4. Images per persona must be between 1 and 20
5. At least one image-set must be selected
6. All selected image-sets must:
   - Exist in database
   - Belong to current user
   - Have status='active'
   - Contain at least 1 image

**Success Response**:
- Redirect to `/history` with flash message
- Flash category: `success`
- Message includes task ID and image-set count

**Error Response**:
- Re-renders form with error messages
- Flash category: `error`
- Returns validation errors as flash messages

**Example Error Messages**:
- "Persona description is required."
- "Number to generate must be between 10 and 300."
- "At least one image set must be selected."
- "One or more selected image sets are invalid or do not belong to you."
- "Image set \"Beach Photos\" has no images. Please add images first."

**Implementation Notes**:
- Language code converted to full name using LANGUAGE_MAP (90+ languages)
- Task ID auto-generated (8-character UUID)
- Image-set validation includes ownership and content checks
- Database transaction ensures atomic task creation
- Error handling with proper rollback on failure

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

#### POST `/api/regenerate-image`
**Description**: Regenerate a single image in a dataset using OpenRouter Nano Banana 2 (Gemini 3.1 Flash Image Preview)
**Authentication**: Required
**Content-Type**: `application/json`

**Request Body**:
```json
{
  "result_id": 123,
  "image_url": "https://s3.../image_2.png",
  "image_index": 2,
  "prompt": "user prompt for regeneration"
}
```

**Required Fields**:
- `result_id`: Integer - GenerationResult ID
- `image_url`: String - S3 URL of the image to regenerate
- `image_index`: Integer - Index of the image in the images array (0-based)
- `prompt`: String - Regeneration prompt (max 2000 characters)

**Workflow**:
1. Validates all input parameters
2. Verifies result exists and belongs to current user
3. Checks task status is 'completed'
4. Validates image_index is within bounds
5. Implements concurrency lock (prevents duplicate regenerations)
6. Extracts S3 key from image_url
7. Generates presigned URL for OpenRouter to access the image
8. Calls OpenRouter Nano Banana 2 with prompt and dual image reference (same image used twice for regeneration)
9. Uploads regenerated image to S3 with temporary name
10. Returns temporary image URL for preview

**Success Response (200)**:
```json
{
  "success": true,
  "new_image_url": "https://s3.../temp_regenerated_1234567890.png"
}
```

**Error Responses**:
- **400**: Invalid input
  ```json
  {
    "success": false,
    "error": "prompt must be 2000 characters or less"
  }
  ```
- **403**: Access denied (result belongs to another user)
  ```json
  {
    "success": false,
    "error": "Access denied"
  }
  ```
- **404**: Result not found
  ```json
  {
    "success": false,
    "error": "Result not found"
  }
  ```
- **409**: Concurrent regeneration conflict
  ```json
  {
    "success": false,
    "error": "This image is already being regenerated. Please wait."
  }
  ```
- **502**: OpenRouter HTTP error
  ```json
  {
    "success": false,
    "error": "Image generation failed: HTTP 500"
  }
  ```
- **504**: OpenRouter timeout
  ```json
  {
    "success": false,
    "error": "Image generation timed out"
  }
  ```
- **500**: Server error
  ```json
  {
    "success": false,
    "error": "An unexpected error occurred"
  }
  ```

**Concurrency Control**:
- Uses global `REGENERATION_LOCKS` dictionary
- Lock key: `(result_id, image_index)`
- Lock duration: 5 minutes
- Prevents multiple concurrent regenerations of same image
- Lock automatically released in finally block

**Security**:
- Requires authentication
- Verifies result ownership
- Validates task status
- Sanitizes prompt (removes null bytes)
- Validates prompt length (≤2000 characters)
- Validates image_index bounds

**Implementation Notes**:
- Uses `asyncio.run()` to call async OpenRouter function
- Generates presigned URL with 1-hour expiration
- For image regeneration, the same presigned URL is passed twice (as both scene_image_url and person_image_url) since we're modifying a single reference image
- Preserves original image dimensions by detecting size before regeneration
- Temporary images stored with timestamp in filename
- Logs all errors with full stack trace
- Catches specific httpx exceptions for better error handling

---

#### POST `/api/save-regenerated-image`
**Description**: Save a regenerated image to replace the original in the dataset
**Authentication**: Required
**Content-Type**: `application/json`

**Request Body**:
```json
{
  "result_id": 123,
  "image_index": 2,
  "new_image_url": "https://s3.../temp_regenerated_1234567890.png"
}
```

**Required Fields**:
- `result_id`: Integer - GenerationResult ID
- `image_index`: Integer - Index of the image to replace (0-based)
- `new_image_url`: String - S3 URL of the regenerated image

**Workflow**:
1. Validates all input parameters
2. Acquires row-level lock on GenerationResult
3. Verifies result exists and belongs to current user
4. Checks task status is 'completed'
5. Validates image_index is within bounds
6. Stores old image URL for cleanup
7. Updates images array atomically
8. Commits database change
9. Attempts to delete old image from S3 (non-critical)

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Image replaced successfully"
}
```

**Error Responses**:
- **400**: Invalid input
  ```json
  {
    "success": false,
    "error": "image_index must be an integer"
  }
  ```
- **403**: Access denied
  ```json
  {
    "success": false,
    "error": "Access denied"
  }
  ```
- **404**: Result not found
  ```json
  {
    "success": false,
    "error": "Result not found"
  }
  ```
- **500**: Server error
  ```json
  {
    "success": false,
    "error": "An error occurred while saving the regenerated image"
  }
  ```

**Database Transaction**:
- Uses `with_for_update()` for row-level locking
- Prevents concurrent modifications
- Uses `flag_modified()` for JSON array update detection
- Rollback on any error
- Atomic update ensures data consistency

**S3 Cleanup**:
- Deletes old image from S3 after successful database update
- Non-critical operation (logs warning if fails)
- Does not fail the request if S3 deletion fails
- Uses `delete_s3_url()` from services.image_utils

**Security**:
- Requires authentication
- Verifies result ownership
- Validates task status
- Row-level locking prevents race conditions
- Validates image_index bounds

**Implementation Notes**:
- Imports `flag_modified` from sqlalchemy.orm.attributes
- Old image URL stored before modification
- S3 deletion is best-effort (non-blocking)
- Logs success and warnings appropriately

---

## Image Datasets Feature Routes

The Image Datasets feature allows users to create, manage, and share collections of images imported from Flickr or external URLs.

### GET `/image-datasets`
**Description**: List all datasets accessible to the user
**Authentication**: Required
**Template**: `templates/image_datasets.html`

**Template Variables**:
- `user_name`: String - Username (extracted from email)
- `datasets`: List of dicts with structure:
  ```python
  {
    'dataset': ImageDataset object,
    'image_count': Integer - Number of images in dataset,
    'access_type': String - 'owner', 'shared (view/edit)', or 'public'
  }
  ```

**Implementation**:
Lists datasets in three categories:
1. Owned datasets (user is owner)
2. Shared datasets (via DatasetPermission)
3. Public datasets (is_public=True, not owned)

**Security**:
- Shows only active datasets (status='active')
- Includes image counts for each dataset
- Proper access control via permissions

---

### POST `/api/image-datasets`
**Description**: Create a new image dataset
**Authentication**: Required
**Content-Type**: `application/json`

**Request Body**:
```json
{
  "name": "Dataset Name",
  "description": "Optional description",
  "is_public": false
}
```

**Required Fields**:
- `name`: String - Dataset name (cannot be empty)

**Optional Fields**:
- `description`: String - Dataset description
- `is_public`: Boolean - Make dataset publicly accessible (default: false)

**Success Response (201)**:
```json
{
  "success": true,
  "dataset_id": "uuid-string",
  "message": "Dataset created successfully"
}
```

**Error Response (400)**:
```json
{
  "success": false,
  "message": "Dataset name is required"
}
```

**Implementation**:
- Auto-generates UUID for dataset_id
- Sets status to 'active'
- Associates with current user as owner

---

### GET `/image-datasets/<dataset_id>`
**Description**: View dataset details with paginated images
**Authentication**: Required
**Template**: `templates/image_dataset_detail.html`

**Path Parameters**:
- `dataset_id`: String - Dataset UUID

**Query Parameters**:
- `page`: Integer (default: 1) - Page number
- `source_type`: String (optional) - Filter by source type (e.g., 'flickr', 'url_import')

**Template Variables**:
- `user_name`: String - Username
- `dataset`: ImageDataset object
- `images`: List - Paginated DatasetImage objects (50 per page)
- `pagination`: Flask-SQLAlchemy pagination object
- `total_images`: Integer - Total image count
- `source_types`: List - Unique source types for filtering
- `source_type_filter`: String - Current filter value
- `is_owner`: Boolean - True if user owns dataset
- `has_edit_access`: Boolean - True if user can edit

**Access Control**:
- Owner: Full access
- Shared with edit permission: Can view and edit
- Shared with view permission: Can only view
- Public datasets: Anyone can view
- Returns 404/403 if no access

---

### PUT `/api/image-datasets/<dataset_id>`
**Description**: Update dataset metadata
**Authentication**: Required
**Content-Type**: `application/json`

**Path Parameters**:
- `dataset_id`: String - Dataset UUID

**Request Body** (all fields optional):
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "is_public": true
}
```

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Dataset updated successfully"
}
```

**Error Response (403)**:
```json
{
  "success": false,
  "message": "Only the owner can update dataset settings"
}
```

**Security**:
- Only owner can update
- Name cannot be empty if provided
- Updates updated_at timestamp

---

### DELETE `/api/image-datasets/<dataset_id>`
**Description**: Delete dataset and all its images
**Authentication**: Required

**Path Parameters**:
- `dataset_id`: String - Dataset UUID

**Success Response (200)**:
```json
{
  "success": true,
  "deleted_images": 25,
  "message": "Dataset deleted successfully (25 images removed)"
}
```

**Workflow**:
1. Verify ownership
2. Delete all images from S3 (using delete_s3_url)
3. Delete database records (CASCADE handles images and permissions)
4. Return deletion statistics

**Security**:
- Only owner can delete
- Logs S3 deletion failures as warnings (continues deletion)
- Database transaction ensures consistency

---

### POST `/api/image-datasets/<dataset_id>/search-flickr`
**Description**: Search Flickr for images with simple filtering
**Authentication**: Required
**Content-Type**: `application/json`

**Path Parameters**:
- `dataset_id`: String - Dataset UUID

**Request Body**:
```json
{
  "keyword": "search term",
  "page": 1,
  "per_page": 50,
  "exclude_used": true,
  "license_filter": "cc",
  "search_mode": "tags",
  "tag_mode": "any"
}
```

**Required Fields**:
- `keyword`: String - Search keyword/phrase

**Optional Fields**:
- `page`: Integer (default: 1) - Page number
- `per_page`: Integer (default: 50, max: 100) - Results per page
- `exclude_used`: Boolean (default: true) - Exclude already-imported photos
- `license_filter`: String (optional) - License filter ('cc' for Creative Commons only, null for any)
- `search_mode`: String (default: 'tags') - Search mode ('tags' or 'text')
- `tag_mode`: String (default: 'any') - Tag matching mode ('any' or 'all', only applies when search_mode='tags')

**License Filter Options**:
- `'cc'`: Creative Commons licenses only (CC BY, CC BY-SA, CC BY-NC, etc.)
- `null` or omitted: All licenses (includes All Rights Reserved)

**Search Mode Options**:
- `'tags'`: Tag-based search - searches the tags field of Flickr photos (faster, more precise)
  - When using tag mode, the `tag_mode` parameter controls matching behavior:
    - `'any'`: Match photos with ANY of the provided tags (OR logic, default)
    - `'all'`: Match photos with ALL of the provided tags (AND logic)
  - Keywords can include comma-separated tags (e.g., "coffee,shop" searches for photos tagged with "coffee" OR "shop" when tag_mode='any')
- `'text'`: Full-text search - searches titles, descriptions, and tags (slower, broader results)
  - The `tag_mode` parameter is ignored when using text mode

**Success Response (200)**:
```json
{
  "success": true,
  "photos": [
    {
      "id": "flickr_photo_id",
      "url_o": "https://...",
      "url_l": "https://...",
      "url_m": "https://...",
      "title": "Photo Title",
      "tags": "tag1 tag2 tag3",
      "owner_name": "photographer",
      "license": "CC BY 2.0",
      "date_taken": "2020-05-15 14:30:00",
      "views": 1234
    }
  ],
  "total": 500,
  "page": 1,
  "pages": 10
}
```

**Implementation**:
- Simple keyword search without scoring
- Photos returned as-is from Flickr API
- License filtering for Creative Commons vs. all licenses
- Excludes already-used photos if enabled

**Security**:
- Requires edit access to dataset
- Uses flickr_service for search
- Rate-limited via Flickr API

---

### GET `/api/proxy-image`
**Description**: CORS proxy for external images (Flickr thumbnails) to enable face detection
**Authentication**: Required
**Content-Type**: Image binary (JPEG, PNG, etc.)

**Query Parameters**:
- `url`: String (required) - URL-encoded image URL to proxy

**Purpose**:
Proxies image requests from allowed domains to enable canvas/WebGL access for MediaPipe face detection. Flickr images served from external domains (staticflickr.com) trigger cross-origin restrictions that prevent browser APIs from accessing pixel data. This proxy fetches the image server-side and serves it with proper CORS headers.

**Allowed Domains**:
- flickr.com (including subdomains)
- staticflickr.com (including subdomains)

**Success Response (200)**:
- Content-Type: Matches original image (e.g., image/jpeg, image/png)
- Headers:
  - `Access-Control-Allow-Origin: *` - Allows canvas/WebGL access
  - `Access-Control-Allow-Methods: GET`
  - `Access-Control-Allow-Headers: Content-Type`
  - `Cache-Control: public, max-age=3600` - 1 hour browser cache
- Body: Image binary data

**Error Responses**:
- **400**: Missing or invalid URL parameter
  ```json
  {
    "success": false,
    "message": "Missing url parameter"
  }
  ```
- **400**: Domain not allowed
  ```json
  {
    "success": false,
    "message": "Domain not allowed: example.com"
  }
  ```
- **404**: Image fetch failed
  ```json
  {
    "success": false,
    "message": "Failed to fetch image"
  }
  ```
- **500**: Server error
  ```json
  {
    "success": false,
    "message": "Internal server error"
  }
  ```

**Security**:
- Requires authentication (@login_required)
- Whitelist of allowed domains (Flickr only)
- URL validation and domain checking
- 10-second timeout for external requests
- Prevents SSRF attacks via domain whitelist

**Usage Example**:
```javascript
// Frontend JavaScript
const flickrUrl = 'https://live.staticflickr.com/65535/123456789_abc.jpg';
const proxyUrl = `/api/proxy-image?url=${encodeURIComponent(flickrUrl)}`;

// Use proxy URL for face detection
const img = new Image();
img.crossOrigin = 'anonymous';  // Not needed with proxy, but safe to include
img.src = proxyUrl;
```

**Implementation Notes**:
- Uses `urllib.parse.unquote()` to decode potentially double-encoded URLs
- Supports subdomain wildcards (*.flickr.com, *.staticflickr.com)
- Streams image response with original Content-Type
- Logs denied domain requests as warnings
- Logs fetch errors for debugging

**Performance**:
- 1-hour browser cache reduces server load
- 10-second timeout prevents hung requests
- Streaming response (no in-memory buffering)

**Common Issues**:
- **CORS errors on thumbnails**: Use this proxy to resolve
- **MediaPipe SecurityError**: Proxy fixes cross-origin data access
- **403 Forbidden**: External domain may block server IPs (rare)

---

### POST `/api/image-datasets/<dataset_id>/import-flickr`
**Description**: Import selected Flickr photos into dataset (optimized - no API calls during import)
**Authentication**: Required
**Content-Type**: `application/json`

**Path Parameters**:
- `dataset_id`: String - Dataset UUID

**Request Body**:
```json
{
  "photos": [
    {
      "id": "53819404623",
      "url": "https://live.staticflickr.com/...",
      "url_o": "https://live.staticflickr.com/original.jpg",
      "url_l": "https://live.staticflickr.com/large.jpg",
      "url_m": "https://live.staticflickr.com/medium.jpg",
      "title": "Coffee Shop Interior",
      "tags": ["coffee", "interior", "design"],
      "owner_name": "photographer",
      "license": "CC BY 2.0",
      "date_taken": "2024-01-15",
      "views": 1234
    }
  ]
}
```

**Required Fields**:
- `photos`: Array of objects - Full photo data from search results (includes all metadata and URLs)

**Success Response (200)**:
```json
{
  "success": true,
  "imported_count": 8,
  "failed_count": 2,
  "message": "Import complete: 8 imported, 2 failed"
}
```

**Workflow** (Optimized):
1. Verify edit access
2. Use photo data from frontend (already cached from search - **no API calls**)
3. Batch download images from URLs (concurrent, max 3 workers)
4. Compute image hash for duplicate detection
5. Upload to S3 (bucket: image-datasets) in parallel (max 5 workers)
6. Insert DatasetImage records with metadata

**Performance Optimization**:
- **No Flickr API calls during import** (uses cached data from search)
- Previously: 2 API calls per image × 1 second rate limit = 2 seconds/image
- Now: Direct download from URLs = ~0.2 seconds/image
- **10x faster** for import operations

**Duplicate Handling**:
- Skips if same photo_id already in dataset
- Skips if image hash matches existing image

**Source Metadata Stored**:
- title, tags, owner_name
- license, date_taken, views

**Security**:
- Requires edit access
- No rate limiting needed (no API calls)
- Validates all downloads

---

### POST `/api/image-datasets/<dataset_id>/import-urls`
**Description**: Import images from URLs into dataset (synchronous - waits for completion)
**Authentication**: Required
**Content-Type**: `application/json`

**Path Parameters**:
- `dataset_id`: String - Dataset UUID

**Request Body**:
```json
{
  "urls": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.png"
  ]
}
```

**Required Fields**:
- `urls`: Array of strings - Image URLs to import

**Success Response (200)**:
```json
{
  "success": true,
  "imported": 3,
  "failed": 1,
  "failed_urls": [
    {
      "url": "https://example.com/invalid.jpg",
      "error": "HTTP error 404: Not Found"
    }
  ],
  "message": "Import complete: 3 imported, 1 failed"
}
```

**Error Response (400)**:
```json
{
  "success": false,
  "message": "No URLs provided"
}
```

**Workflow**:
1. Verify edit access
2. Process URLs concurrently (max 5 workers):
   - Download images directly (no pre-validation for speed)
   - Compute hash for tracking
   - Upload to S3
   - Insert DatasetImage records
3. Return results when all URLs processed

**URL Validation** (during download):
- Must start with http:// or https://
- Content-Type must be image/*
- Max file size: 50 MB
- 30-second timeout per download

**Performance**:
- Duplicate checking is **disabled during import** for speed
- Users can filter/remove duplicates later using the UI
- Fast synchronous operation (no job polling needed)

**Security**:
- Requires edit access
- URL validation prevents abuse
- Size limits prevent resource exhaustion

**Implementation Notes**:
- Uses `services.url_import_service.batch_import_urls()`
- No background threading or job tracking
- Simple synchronous request/response model

---

### POST `/api/image-datasets/<dataset_id>/upload-files`
**Description**: Upload image files to dataset from local file system
**Authentication**: Required
**Content-Type**: `multipart/form-data`

**Path Parameters**:
- `dataset_id`: String - Dataset UUID

**Form Fields**:
- `files[]`: File array - Multiple image files to upload

**Supported File Types**:
- `image/jpeg` - JPEG/JPG images
- `image/png` - PNG images

**File Validation**:
- Max file size: 50 MB per file
- Only PNG and JPG formats allowed
- Files must not be empty

**Success Response (200)**:
```json
{
  "success": true,
  "imported": 5,
  "failed": 1,
  "failed_files": [
    {
      "filename": "invalid.gif",
      "error": "Invalid file type (only PNG and JPG allowed)"
    }
  ],
  "message": "Upload complete: 5 imported, 1 failed"
}
```

**Error Response (400)** - No files provided:
```json
{
  "success": false,
  "message": "No files provided"
}
```

**Error Response (403)** - Access denied:
```json
{
  "success": false,
  "message": "Dataset not found or access denied"
}
```

**Workflow**:
1. Verify edit access to dataset
2. Validate file type (PNG/JPG only)
3. Validate file size (≤50 MB)
4. Read file bytes
5. Compute SHA256 hash for duplicate detection
6. Check for duplicate images in dataset (by hash)
7. Upload to S3 (bucket: image-datasets)
8. Create DatasetImage record with metadata

**DatasetImage Fields**:
- `source_type`: 'file_upload'
- `source_id`: NULL (no external source)
- `source_metadata`: JSON with original filename, content type, file size
- `image_hash`: SHA256 hash of file bytes
- `face_count`: NULL (processed by background job)

**Duplicate Detection**:
- Skips files if image hash matches existing image in dataset
- Returns duplicate files in `failed_files` array with error message

**Failed Upload Reasons**:
- Invalid file type (not PNG/JPG)
- File too large (>50 MB)
- Empty file (0 bytes)
- Duplicate image (hash already exists)
- Upload/processing errors

**Example cURL Upload**:
```bash
curl -X POST http://localhost:7001/api/image-datasets/abc123/upload-files \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -b cookies.txt \
  -F "files[]=@image1.jpg" \
  -F "files[]=@image2.png" \
  -F "files[]=@image3.jpg"
```

**Security**:
- Requires authentication
- Requires edit access to dataset
- File type validation (MIME type check)
- File size limits prevent abuse
- Hash-based duplicate detection
- Each file processed independently (failures don't stop batch)

**Implementation Notes**:
- Uses `upload_dataset_image_to_s3` from services.image_utils
- Uses `compute_image_hash` for duplicate detection
- Original filename preserved in source_metadata
- Face detection handled by background job (not during upload)
- Database transaction per file (failures are isolated)
- Logs all uploads and failures

**Performance**:
- Files processed sequentially (no concurrency overhead)
- Fast uploads directly from bytes
- No external API calls required
- Typical upload time: ~0.5 seconds per file

---

### DELETE `/api/image-datasets/<dataset_id>/images/<int:image_id>`
**Description**: Remove an image from a dataset
**Authentication**: Required

**Path Parameters**:
- `dataset_id`: String - Dataset UUID
- `image_id`: Integer - DatasetImage ID

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Image deleted successfully"
}
```

**Workflow**:
1. Verify edit access to dataset
2. Verify image belongs to dataset
3. Delete from S3
4. Delete DatasetImage record

**Security**:
- Requires edit access
- Validates image belongs to dataset
- Logs S3 deletion failures

---

### GET `/api/image-datasets/<dataset_id>/permissions`
**Description**: List users with access to dataset
**Authentication**: Required
**Content-Type**: `application/json`

**Path Parameters**:
- `dataset_id`: String - Dataset UUID

**Success Response (200)**:
```json
{
  "success": true,
  "permissions": [
    {
      "user_id": 1,
      "email": "user@example.com",
      "permission_level": "view",
      "created_at": "2026-03-09T12:00:00"
    }
  ]
}
```

**Security**:
- Only owner can view permissions
- Joins with User table for email display

---

### POST `/api/image-datasets/<dataset_id>/permissions`
**Description**: Grant access to a user
**Authentication**: Required
**Content-Type**: `application/json`

**Path Parameters**:
- `dataset_id`: String - Dataset UUID

**Request Body**:
```json
{
  "user_email": "user@example.com",
  "permission_level": "view"
}
```

**Required Fields**:
- `user_email`: String - Email of user to grant access
- `permission_level`: String - 'view' or 'edit'

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Granted view access to user@example.com"
}
```

**Behavior**:
- Creates new permission or updates existing
- Cannot grant permission to self
- User must exist in system

**Security**:
- Only owner can grant permissions
- Validates permission_level values

---

### DELETE `/api/image-datasets/<dataset_id>/permissions/<int:user_id>`
**Description**: Revoke user's access to dataset
**Authentication**: Required

**Path Parameters**:
- `dataset_id`: String - Dataset UUID
- `user_id`: Integer - User ID to revoke

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Permission revoked successfully"
}
```

**Security**:
- Only owner can revoke permissions
- Validates permission exists

---

### GET `/image-datasets/<dataset_id>/export/json`
**Description**: Export dataset metadata and image URLs as JSON
**Authentication**: Required

**Path Parameters**:
- `dataset_id`: String - Dataset UUID

**Response**:
- Content-Type: `application/json`
- Content-Disposition: `attachment; filename="{dataset_name}_export.json"`

**Export Structure**:
```json
{
  "dataset": {
    "dataset_id": "uuid",
    "name": "Dataset Name",
    "description": "Description",
    "is_public": false,
    "created_at": "2026-03-09T12:00:00",
    "updated_at": "2026-03-09T12:00:00",
    "image_count": 25
  },
  "images": [
    {
      "image_url": "https://s3.../image.jpg",
      "source_type": "flickr",
      "source_id": "flickr_photo_id",
      "source_metadata": {...},
      "image_hash": "sha256_hash",
      "added_at": "2026-03-09T12:00:00"
    }
  ]
}
```

**Security**:
- Requires view access
- Includes all metadata

---

### GET `/image-datasets/<dataset_id>/export/zip`
**Description**: Export dataset as ZIP with images and metadata
**Authentication**: Required

**Path Parameters**:
- `dataset_id`: String - Dataset UUID

**Response**:
- Content-Type: `application/zip`
- Content-Disposition: `attachment; filename="{dataset_name}_export.zip"`

**ZIP Contents**:
```
{dataset_name}_export.zip/
├── data.json          # Dataset and image metadata
└── images/
    ├── image_0000.jpg
    ├── image_0001.png
    └── ...
```

**Workflow**:
1. Verify access
2. Create temporary directory
3. Download all images from S3
4. Create data.json with metadata
5. Create ZIP with images/ folder and data.json
6. Stream ZIP to user
7. Clean up temporary files

**Implementation**:
- Uses tempfile for temporary storage
- 30-second timeout per S3 download
- Gracefully handles download failures (logs and continues)
- Cleans up temp directory after send

**Security**:
- Requires view access
- Validates all URLs
- Proper error handling

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

## Backend Services

### Face Detection Service

**Module**: `services/face_detection_service.py`

**Description**: Provides automatic face detection for imported images using the YuNet face detection model from OpenCV.

**Key Features**:
- Uses YuNet (face_detection_yunet_2023mar.onnx) - lightweight and accurate
- Model is downloaded once and cached in `/tmp/`
- 100% accuracy on test images (based on testing)
- Detection threshold: 0.6 (configurable)
- Graceful error handling (returns None on failure)

**Functions**:

#### `detect_faces_in_image_bytes(image_bytes: bytes, threshold: float = 0.6) -> Optional[int]`
Detect faces in image from raw bytes.

**Parameters**:
- `image_bytes`: Raw image bytes
- `threshold`: Confidence threshold (0.0 - 1.0)

**Returns**: Number of faces detected (0, 1+) or None if detection fails

**Example**:
```python
from services.face_detection_service import detect_faces_in_image_bytes

face_count = detect_faces_in_image_bytes(image_bytes)
if face_count is not None:
    print(f"Detected {face_count} faces")
```

#### `detect_faces_in_image_url(image_url: str, threshold: float = 0.6, timeout: int = 30) -> Optional[int]`
Detect faces in image from URL.

**Parameters**:
- `image_url`: Public URL to image
- `threshold`: Confidence threshold (0.0 - 1.0)
- `timeout`: Download timeout in seconds

**Returns**: Number of faces detected (0, 1+) or None if download/detection fails

#### `warmup_face_detector() -> bool`
Pre-download YuNet model to warm up the detector. Useful for application startup.

**Returns**: True if model is ready, False if download fails

**Integration**:
- **URL Import**: Face detection is **disabled during import** - `face_count` is set to NULL
- **Flickr Import**: Face detection is **disabled during import** - `face_count` is set to NULL
- **Database**: Face count is stored in `DatasetImage.face_count` field (NULL = not analyzed, 0 = no faces, 1+ = faces, -1 = error)
- **Background Processing**: Face detection runs as an APScheduler job every 60 seconds (see Background Jobs section)
- **Reason**: Face detection during import caused worker crashes and performance issues. Imports are now fast and simple, with face detection handled by a scheduled background job.

**Model Information**:
- **Model File**: `face_detection_yunet_2023mar.onnx`
- **Download URL**: https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/
- **Cache Location**: `/tmp/face_detection_yunet_2023mar.onnx`
- **Model Size**: ~2.8MB

**Error Handling**:
Face detection failures are logged as warnings but do not block image imports. If detection fails, `face_count` is set to NULL in the database.

---

## Background Jobs (APScheduler)

The application uses **APScheduler** (BackgroundScheduler) to run background tasks. The scheduler starts automatically when the Flask app starts and runs continuously.

### Configuration
- **Scheduler Type**: BackgroundScheduler (runs in a background thread)
- **Log Level**: ERROR (suppressed INFO/WARNING to reduce log spam)
- **Auto-start**: Only starts in main process (not in Flask reloader process)

### Active Jobs

#### 1. Avatar Data Generation Task Processor
**ID**: `task_processor_job`
**Interval**: Every `WORKER_INTERVAL` seconds (configurable via env)
**Function**: `scheduled_task_processor()`
**Purpose**: Processes pending avatar data generation tasks
**Features**:
- Configurable concurrent tasks (via `max_concurrent_tasks` setting)
- Thread pool execution (max 3 parallel tasks)
- Respects capacity limits (checks currently processing tasks)
- Only logs when work is done (avoids spam)

#### 2. Image Generation Processor
**ID**: `image_processor_job`
**Interval**: Every `WORKER_INTERVAL` seconds (configurable via env)
**Function**: `scheduled_image_processor()`
**Purpose**: Processes image generation for completed data tasks
**Features**:
- Same concurrency model as data generation
- Thread pool execution
- Capacity-aware (respects `max_concurrent_tasks`)
- Only logs when work is done

#### 3. Stuck Task Recovery
**ID**: `stuck_task_recovery_job`
**Interval**: Every 5 minutes
**Function**: `scheduled_stuck_task_recovery()`
**Purpose**: Recovers tasks stuck in processing state for 15+ minutes
**Features**:
- Runs immediately on startup with stricter checks
- Startup check uses 0-minute threshold
- Only logs when tasks are recovered

#### 4. Face Detection Processor
**ID**: `face_detection_job`
**Interval**: Every 60 seconds
**Function**: `scheduled_face_detection()`
**Purpose**: Processes face detection for unanalyzed dataset images
**Features**:
- Batch processing (50 images per run)
- Only processes images with `face_count = NULL`
- Updates `face_count` field (0+ for success, -1 for error)
- Only logs when work is done (avoids spam)
- No locking needed (APScheduler prevents overlapping executions)

**Implementation Details**:
```python
def scheduled_face_detection():
    """Wrapper function to run face detection processor with Flask app context."""
    with app.app_context():
        try:
            from workers.face_detection_worker import process_face_detection_batch
            processed_count = process_face_detection_batch(batch_size=50)
            # Only log if work was done to avoid log spam
            if processed_count > 0:
                logging.info(f"[SCHEDULER] Face detection processed {processed_count} image(s)")
        except Exception as e:
            logging.error(f"[SCHEDULER] Error processing face detection: {e}", exc_info=True)
```

**Worker Function**: `workers.face_detection_worker.process_face_detection_batch(batch_size=50)`
- Queries `DatasetImage.query.filter_by(face_count=None).limit(batch_size)`
- Calls `detect_faces_in_image_url()` for each image
- Updates `face_count` (0+ for success, -1 for error)
- Logs progress every 10 images
- Commits all changes in a single transaction
- Returns number of images processed

### Shutdown Handling
The scheduler is registered with `atexit` to ensure proper shutdown when the application exits.

### Concurrency Control
- APScheduler prevents overlapping executions of the same job
- Each job runs in Flask app context for database access
- Thread pool executors manage parallel task processing
- Row-level locking used for database operations where needed

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
