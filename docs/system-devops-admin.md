# DevOps Configuration - Avatar Data Generator

> *Maintained by: system-devops-admin agent*

## PostgreSQL Database

### Database Information
- **Database Name**: `avatar_data_generator`
- **Database User**: `avatar_data_gen`
- **Host**: `localhost` (PostgreSQL running on same server)
- **Port**: `5432` (PostgreSQL default port)
- **Connection String**: `postgresql://avatar_data_gen:[PASSWORD]@localhost:5432/avatar_data_generator`
- **Password**: `AvatarGen2025!Secure#DB` (stored in .env file)

### Database Setup Status
**Created**: 2026-01-30
**Schema Initialized**: 2026-01-30 (via init_db.py)

Database created successfully using setup-database.sql script. All privileges granted to avatar_data_gen user.

### Database Schema
- **users** table: User authentication and management
  - Initialized via Flask-Migrate
  - Migration ID: 25698f3f906f
  - Password hashing: bcrypt

### Security Notes
- Database password stored in `/home/niro/galacticos/avatar-data-generator/.env` (NOT committed to git)
- PostgreSQL is configured for localhost connections only (peer + scram-sha-256 authentication)
- The `avatar_data_gen` user has full privileges only on the `avatar_data_generator` database
- .env file is in .gitignore

## Application Backend Port
**Allocated Port**: 8085

Port 8085 allocated for Avatar Data Generator Flask application.
- **Previously**: Port 8082 (conflicted with QuickPen)
- **Changed to**: Port 8085 on 2026-01-30
- Available ports checked: 8080, 8081, 8082, 8093-8096 were already in use
- Selected 8085 from available range 7000-8999

## Python Virtual Environment
**Location**: `/home/niro/galacticos/avatar-data-generator/venv`
**Python Version**: 3.12
**Status**: Created and activated

### Installed Packages (in venv)
- Flask==3.0.0
- Flask-SQLAlchemy==3.1.1
- Flask-Migrate==4.0.5
- Flask-Login==0.6.3
- Flask-WTF==1.2.1
- psycopg2-binary==2.9.9
- SQLAlchemy==2.0.23
- bcrypt==4.1.2
- python-dotenv==1.0.0
- email-validator==2.1.0
- Werkzeug==3.0.1
- gunicorn==24.1.1 (production WSGI server)
- APScheduler==3.11.0 (background task scheduling - installed 2026-01-30)
- opencv-python==4.13.0.90 (image processing - installed 2026-02-01)
- numpy==2.4.2 (dependency for opencv-python)

## Nginx Sites
**Subdomain**: avatar-data-generator.dev.iron-mind.ai
**Config File**: `/etc/nginx/sites-available/avatar-data-generator.dev.iron-mind.ai`
**Status**: ACTIVE (enabled and running)

### Configuration Details
- HTTP: Redirects to HTTPS (configured by certbot)
- HTTPS: Port 443 with SSL/TLS
- Reverse Proxy: Proxies to localhost:8085
- Client Max Body Size: 10M
- Static Files: /static served from /home/niro/galacticos/avatar-data-generator/static
  - Directory permissions: 755 (drwxr-xr-x)
  - File permissions: 644 (-rw-r--r--)
  - Nginx (www-data) has read access to all static assets
- Security Headers: X-Frame-Options, X-Content-Type-Options, X-XSS-Protection enabled
- Caching: COMPLETELY DISABLED (Development Environment)
  - Cache-Control: no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0
  - Pragma: no-cache
  - Expires: 0
  - proxy_cache: off
  - proxy_buffering: off
  - Applied to ALL content (proxied application + static files)
  - Configuration updated: 2026-01-30 (enhanced for CSRF protection)
- Proxy Headers: Complete set for session/cookie handling
  - Host, X-Real-IP, X-Forwarded-For, X-Forwarded-Proto
  - X-Forwarded-Host, X-Forwarded-Port (added 2026-01-30)
  - Cookie preservation: proxy_set_header Cookie + proxy_pass_header Set-Cookie
  - Referer preservation for CSRF validation
  - Request buffering disabled for better session handling
  - HTTP/1.1 with persistent connections

### Logs
- Access Log: `/var/log/nginx/avatar-data-generator.access.log`
- Error Log: `/var/log/nginx/avatar-data-generator.error.log`

## SSL Certificate
**Provider**: Let's Encrypt (via certbot)
**Certificate Path**: `/etc/letsencrypt/live/avatar-data-generator.dev.iron-mind.ai/fullchain.pem`
**Private Key Path**: `/etc/letsencrypt/live/avatar-data-generator.dev.iron-mind.ai/privkey.pem`
**Expires**: 2026-04-30
**Auto-Renewal**: Enabled (certbot.timer runs twice daily)

## Systemd Services

### Main Application Service
**Service Name**: avatar-data-generator.service
**Service File**: `/etc/systemd/system/avatar-data-generator.service`
**Status**: ACTIVE (enabled and running)

#### Service Configuration
- **Type**: simple
- **User**: niro
- **Working Directory**: /home/niro/galacticos/avatar-data-generator
- **Command**: gunicorn with 1 worker, 2 threads per worker
- **Restart Policy**: Always (with 10s delay, max 5 restarts in 300s)
- **Dependencies**: Requires network.target, wants postgresql.service

#### Service Logs
- Access Log: `/var/log/avatar-data-generator/access.log`
- Error Log: `/var/log/avatar-data-generator/error.log`
- Journald: `StandardOutput=journal` and `StandardError=journal` configured
- View service logs: `sudo journalctl -u avatar-data-generator.service`
- Follow logs in real-time: `sudo journalctl -u avatar-data-generator.service -f`

#### Service Management Commands
```bash
# Start service
sudo systemctl start avatar-data-generator.service

# Stop service
sudo systemctl stop avatar-data-generator.service

# Restart service
sudo systemctl restart avatar-data-generator.service

# View status
sudo systemctl status avatar-data-generator.service

# View logs
sudo journalctl -u avatar-data-generator.service -f
```

### Task Processor (Integrated Background Scheduler)
**Architecture**: APScheduler integrated into main Flask application
**Status**: ACTIVE (running within main application service)
**Migration Date**: 2026-01-30 13:28 UTC (migrated from separate worker service)

#### Scheduler Configuration
- **Library**: APScheduler (Advanced Python Scheduler)
- **Scheduler Type**: BackgroundScheduler (non-blocking, runs in separate thread)
- **Execution**: Starts automatically when Flask application initializes
- **Interval**: Checks for pending tasks every 30 seconds
- **Thread Safety**: Uses separate thread pool for task processing
- **No Separate Process**: Integrated into gunicorn worker process

#### Scheduler Behavior
- **Automatic Startup**: Scheduler starts when Flask app initializes (via `create_app()`)
- **Background Thread**: Runs in background thread, doesn't block Flask request handling
- **Task Checking**: IntervalTrigger checks database for pending tasks every 30 seconds
- **Task Processing**: Processes one task at a time from the database queue
- **Graceful Shutdown**: APScheduler handles cleanup on application shutdown
- **Single Worker Model**: Works seamlessly with gunicorn's single-worker configuration

#### Environment Variables
Configuration from `/home/niro/galacticos/avatar-data-generator/.env`:
- `MULTITHREAD_FLOWISE`: Number of threads for parallel Flowise API calls (default: 5)
- All standard app configuration (database credentials, etc.)

#### Monitoring & Logs
- **Startup Log**: `[SCHEDULER] Background scheduler started - checking for tasks every 30 seconds`
- **Task Processing Logs**: Same format as previous worker logs
- **View Logs**: `sudo journalctl -u avatar-data-generator -f | grep SCHEDULER`
- **All Logs**: Integrated into main application logs (`sudo journalctl -u avatar-data-generator`)

#### Advantages Over Separate Worker Service
1. **Simplified Architecture**: No separate service to manage
2. **Resource Efficiency**: Shares Flask application process and database connections
3. **Consistent Environment**: Same environment variables, imports, and context
4. **Easier Deployment**: Single service to manage
5. **Thread Safety**: APScheduler handles concurrency correctly
6. **Automatic Lifecycle**: Starts/stops with Flask application

#### Migration Notes
- **Previous Architecture**: Separate systemd service (avatar-data-generator-worker.service)
- **Migration Date**: 2026-01-30 13:28 UTC
- **Old Service File**: Removed from `/etc/systemd/system/`
- **Old Worker Script**: Still exists at `/home/niro/galacticos/avatar-data-generator/workers/task_processor.py` (for reference)
- **Status**: Old worker service stopped, disabled, and removed

#### Troubleshooting
```bash
# Check if scheduler is running
sudo journalctl -u avatar-data-generator -f | grep SCHEDULER

# View task processing logs
sudo journalctl -u avatar-data-generator -f | grep "Found.*pending task"

# Check for scheduler errors
sudo journalctl -u avatar-data-generator -p err -n 50 | grep SCHEDULER

# Restart application (includes scheduler)
sudo systemctl restart avatar-data-generator
```

## S3 Storage (MinIO)
**Bucket Name**: `avatar-images`
**Endpoint**: http://127.0.0.1:9000 (internal)
**Region**: us-east-1
**Created**: 2026-01-30

### Bucket Configuration
- **Purpose**: Store avatar images generated by the application
- **Access**: PUBLIC READ (download policy applied 2026-01-30)
- **Endpoint Type**: Internal (applications on server use http://127.0.0.1:9000)
- **Public Access**: https://s3-api.dev.iron-mind.ai

### Public Access Configuration
**Policy Applied**: 2026-01-30
**Access Level**: `download` (public read access for all objects)

**Public URL Format**:
```
https://s3-api.dev.iron-mind.ai/{bucket-name}/{object-key}
```

**Example**:
```
https://s3-api.dev.iron-mind.ai/avatar-images/avatars/user123_avatar.png
```

**In Application Code**:
```python
# Generate public URL for an uploaded image
def get_public_url(object_key):
    return f"https://s3-api.dev.iron-mind.ai/avatar-images/{object_key}"

# Example: After uploading to S3
s3_client.upload_file('avatar.png', 'avatar-images', 'avatars/user123.png')
public_url = get_public_url('avatars/user123.png')
# Returns: https://s3-api.dev.iron-mind.ai/avatar-images/avatars/user123.png
```

**Verification**:
- Tested with curl: `curl -I https://s3-api.dev.iron-mind.ai/avatar-images/test.txt`
- Response: HTTP/2 200 OK with public access headers
- CORS enabled: Access-Control-Allow-Origin: *
- No authentication required for GET requests

### S3 Credentials
- **Access Key**: 5Soxws147E52vCKWyfQA (stored in .env)
- **Secret Key**: b1RUAbi2vJAIzA3gUK4A0NVZjewNO2RQSG9TkrAo (stored in .env)

### Management
```bash
# List buckets
mc ls local/

# List objects in avatar-images bucket
mc ls local/avatar-images/

# Upload file to bucket
mc cp myfile.png local/avatar-images/

# Download file from bucket
mc cp local/avatar-images/myfile.png ./

# View bucket info
mc stat local/avatar-images

# Check public access policy
mc anonymous get local/avatar-images

# Set public read access (download policy)
mc anonymous set download local/avatar-images

# Remove public access (make private)
mc anonymous set private local/avatar-images
```

### Web Console Access
- **URL**: https://s3.dev.iron-mind.ai
- **Credentials**: Same as S3 API (access key / secret key)

## Environment Variables
**File**: `/home/niro/galacticos/avatar-data-generator/.env`
**Status**: Configured

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=avatar_data_generator
DB_USER=avatar_data_gen
DB_PASSWORD=AvatarGen2025!Secure#DB

# Application Configuration
APP_PORT=8085
FLASK_ENV=production
SECRET_KEY=gsFzMyKySaW0UdxJK9hbubsxydXlMEAxZ-gaVRW7a20

# Database URL (alternative format)
DATABASE_URL=postgresql://avatar_data_gen:AvatarGen2025!Secure#DB@localhost:5432/avatar_data_generator

# S3 Storage Configuration (MinIO)
S3_ENDPOINT=http://127.0.0.1:9000
S3_ACCESS_KEY=5Soxws147E52vCKWyfQA
S3_SECRET_KEY=b1RUAbi2vJAIzA3gUK4A0NVZjewNO2RQSG9TkrAo
S3_REGION=us-east-1
S3_BUCKET_NAME=avatar-images
```

## Admin User
**Email**: admin@galacticos.ai
**Password**: `Galacticos2025!AdminAccess#Secure`
**Created**: 2026-01-30
**User ID**: 1

## Deployment Status
**URL**: https://avatar-data-generator.dev.iron-mind.ai
**Status**: LIVE AND OPERATIONAL

### Deployment Checklist
- ✅ Database created and configured
- ✅ Python virtual environment created
- ✅ Dependencies installed (including gunicorn)
- ✅ .env file configured with secure credentials
- ✅ Database schema initialized (Flask-Migrate)
- ✅ Admin user created
- ✅ Port 8082 allocated and verified
- ✅ Nginx virtual host configured
- ✅ SSL certificate provisioned (Let's Encrypt)
- ✅ Systemd service created and enabled
- ✅ Service running and accessible via HTTPS

### Verification Tests
```bash
# Check service status
sudo systemctl status avatar-data-generator.service

# Check port listening
sudo ss -tulpn | grep 8085

# Test HTTPS access
curl -I https://avatar-data-generator.dev.iron-mind.ai

# Test login page
curl -sL https://avatar-data-generator.dev.iron-mind.ai/login

# View application logs
sudo journalctl -u avatar-data-generator.service -n 50

# View nginx logs
sudo tail -f /var/log/nginx/avatar-data-generator.access.log
```

## Troubleshooting History

### Database Password Parsing Error (2026-01-30)
**Issue**: Service was failing to start with database connection errors
**Root Cause**: The `#` character in the database password `AvatarGen2025!Secure#DB` was being interpreted as a comment in the `.env` file, truncating the password
**Solution**:
- Modified `/home/niro/galacticos/avatar-data-generator/.env` to properly quote the password value
- Restarted service: `sudo systemctl restart avatar-data-generator.service`
**Verification**:
- Service started successfully: `systemctl status avatar-data-generator.service` shows `active (running)`
- Database connection verified: Python test script successfully connected and retrieved admin user
- Password verification confirmed: Admin credentials work correctly
**Prevention**: Always quote environment variable values containing special characters (#, $, etc.) in .env files

### Static Files 403 Forbidden Error - Recurring Issue (2026-01-30)
**Issue**: Static files (CSS, JS) repeatedly returning HTTP 403 Forbidden errors after creation
**Affected Files**:
- First occurrence: `generate.css`, `generate.js` (morning)
- Second occurrence: `history.css`, `history.js` (afternoon)

**Root Cause Analysis**:
Files created by Claude Code (and agents like frontend-brand-guardian) have restrictive permissions (600 = rw-------) that prevent nginx (www-data user) from reading them. This is due to:
1. **Umask Setting**: Current umask is `0002`, which would normally create files with 664 permissions
2. **Claude Code File Creation**: Claude Code's Write tool creates files with more restrictive permissions (600) for security
3. **Nginx Requirements**: Nginx (www-data user) needs read permissions (at least 644) to serve static files

**Technical Details**:
- Gunicorn service runs as: `niro:niro`
- Nginx runs as: `www-data:www-data`
- Files created: `600 (rw-------)` - only owner can read/write
- Files needed: `644 (rw-r--r--)` - owner can read/write, group/others can read
- Directories needed: `755 (rwxr-xr-x)` - executable bit required for directory traversal

**Permanent Solution Implemented**:
Created `/home/niro/galacticos/avatar-data-generator/fix-static-permissions.sh` helper script:
```bash
#!/bin/bash
# Fix ownership and permissions for all static files
chown -R niro:niro /home/niro/galacticos/avatar-data-generator/static/
chmod -R 755 /home/niro/galacticos/avatar-data-generator/static/
find /home/niro/galacticos/avatar-data-generator/static/ -type f -exec chmod 644 {} \;
```

**Usage Workflow**:
1. After creating new static files (CSS, JS, images), run:
   ```bash
   ./fix-static-permissions.sh
   ```
2. Script will automatically fix all permissions in `/static` directory
3. Verify with: `ls -la static/js/` and `ls -la static/css/`
4. Test access: `curl -I https://avatar-data-generator.dev.iron-mind.ai/static/js/[filename]`

**Why This Happens**:
- Claude Code's file creation tools prioritize security by creating files with restrictive permissions (600)
- This is intentional behavior to prevent accidental exposure of sensitive files
- For static web assets served by nginx, we need less restrictive permissions (644)
- The fix script is the correct approach rather than changing Claude Code's default behavior

**Prevention**:
- Run `./fix-static-permissions.sh` after creating/modifying static files
- Add this step to deployment/update procedures
- Consider adding to git hooks or CI/CD pipeline if implemented
- Document this requirement for other developers/agents working on frontend

### Service Restart for Frontend Template Updates (2026-01-30 11:01 UTC)
**Reason**: Frontend code was completely updated with new templates and CSS, but gunicorn was still serving cached templates
**Action**: Restarted avatar-data-generator.service to pick up new template changes
**Command**: `sudo systemctl restart avatar-data-generator.service`
**Verification**:
- Service status: active (running) with PID 1959804
- Workers: 4 gunicorn workers successfully booted (PIDs 1959806, 1959807, 1959809, 1959810)
- Port 8085: Listening and accepting connections
- HTTPS access: Confirmed working (HTTP 302 redirect to /login)
- No errors in error log after restart
**Note**: Gunicorn caches templates in memory; service restart required after template/static file changes

### CSRF Token Validation Errors - Reduced Workers (2026-01-30 12:15 UTC)
**Issue**: Users experiencing CSRF token validation errors during form submissions
**Root Cause**: Multiple gunicorn workers (4) each maintaining separate Flask sessions. When a form was rendered by one worker and submitted to a different worker, the CSRF token validation would fail because the session data didn't match
**Solution**: Reduced gunicorn workers from 4 to 1 to ensure all requests are handled by the same worker with consistent session state
**Changes Made**:
1. Edited `/etc/systemd/system/avatar-data-generator.service`
2. Changed `--workers 4` to `--workers 1` on line 23
3. Executed `sudo systemctl daemon-reload`
4. Executed `sudo systemctl restart avatar-data-generator.service`
**Verification**:
- Service status: active (running) with PID 1992191 (master), 1992193 (worker)
- Workers: 1 gunicorn worker with 2 threads
- Port 8085: Listening and accepting connections
- Tasks: 2 total (1 master + 1 worker)
**Note**: For production with multiple workers, need to implement server-side session storage (Redis, Memcached, or database-backed sessions) to share session data across workers. For development, single worker is sufficient.

### CSRF Token Validation Errors - Nginx Proxy Headers Fix (2026-01-30 12:24 UTC)
**Issue**: Continued CSRF token validation errors even with single worker and fresh incognito sessions
**Root Cause Analysis**: Nginx configuration was missing critical proxy headers for proper cookie and session handling:
  1. Missing `X-Forwarded-Host` and `X-Forwarded-Port` headers
  2. No explicit cookie handling directives (`proxy_set_header Cookie`, `proxy_pass_header Set-Cookie`)
  3. Missing `proxy_request_buffering off` which can cause session issues
  4. Not using HTTP/1.1 for proxy connections
**Solution**: Enhanced nginx configuration with complete proxy header set and cookie handling
**Changes Made**:
1. Backed up original config: `/etc/nginx/sites-available/avatar-data-generator.dev.iron-mind.ai.backup`
2. Added missing proxy headers to `/etc/nginx/sites-available/avatar-data-generator.dev.iron-mind.ai`:
   - `proxy_set_header X-Forwarded-Host $host`
   - `proxy_set_header X-Forwarded-Port $server_port`
   - `proxy_set_header Cookie $http_cookie` (explicit cookie forwarding)
   - `proxy_pass_header Set-Cookie` (preserve Set-Cookie headers from backend)
   - `proxy_request_buffering off` (disable request buffering)
   - `proxy_http_version 1.1` (use HTTP/1.1 for better compatibility)
   - `proxy_set_header Connection ""` (persistent connections)
3. Tested nginx configuration: `sudo nginx -t` (successful)
4. Reloaded nginx: `sudo systemctl reload nginx`
5. Restarted application: `sudo systemctl restart avatar-data-generator.service`
**Verification**:
- Nginx status: active (running), reloaded at 12:24:52 UTC
- Service status: active (running) with PID 1997261 (master), 1997263 (worker)
- Configuration test: passed with no errors
- Application initialized successfully with debug logging enabled
**Impact**: These changes ensure cookies are properly forwarded through the nginx reverse proxy, which is critical for Flask session management and CSRF token validation. The issue was that cookies set by Flask were not being correctly passed back to the client or forwarded from the client to Flask, causing session mismatch.

## Notes
- This is a production deployment on the shared dev.iron-mind.ai server
- Database credentials are stored securely in .env file (NOT in version control)
- Application uses gunicorn WSGI server (1 worker, 2 threads) for production
- Service auto-restarts on failure
- SSL certificate auto-renews via certbot
- For database schema changes (tables, migrations, etc.), consult the database-schema-manager agent
- Static files served directly by nginx for better performance
- Single worker configuration prevents CSRF token validation errors by ensuring session consistency
