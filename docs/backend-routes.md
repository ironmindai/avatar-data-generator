# Backend Routes - Avatar Data Generator

> *Maintained by: backend-coder agent*
> *Last Updated: 2025-01-30*

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
**Description**: Dataset management page
**Authentication**: Required
**Status**: Placeholder - redirects to dashboard with info message
**Planned**: List and manage avatar datasets

---

#### GET `/history`
**Description**: Generation history page
**Authentication**: Required
**Status**: Placeholder - redirects to dashboard with info message
**Planned**: View past generation jobs and results

---

#### GET `/settings`
**Description**: User settings page - display bio prompt configuration
**Authentication**: Required
**Template**: `templates/settings.html`

**Template Variables**:
- `user_name`: String - Username (extracted from email)
- `bio_prompts`: Dictionary containing:
  - `bio_prompt_facebook`: String - Facebook bio prompt text
  - `bio_prompt_instagram`: String - Instagram bio prompt text
  - `bio_prompt_x`: String - X (Twitter) bio prompt text
  - `bio_prompt_tiktok`: String - TikTok bio prompt text

**Current Implementation**:
Loads current bio prompt settings from the database and displays them in an editable form.

---

#### POST `/settings/save`
**Description**: Save bio prompt settings (AJAX endpoint)
**Authentication**: Required
**Content-Type**: `application/json`

**Request Body**:
```json
{
  "bio_prompt_facebook": "string",
  "bio_prompt_instagram": "string",
  "bio_prompt_x": "string",
  "bio_prompt_tiktok": "string"
}
```

**Validation**:
- Request body must contain valid JSON
- At least one valid setting key must be provided
- All values must be strings
- Only accepts expected setting keys (bio_prompt_*)

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

**Security Notes**:
- CSRF protection enabled (automatic via Flask-WTF)
- Settings are user-agnostic (shared across application)
- Input validation ensures only string values are stored
- Database rollback on error to maintain data integrity

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
- `DELETE /api/datasets/:id` - Delete dataset

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
