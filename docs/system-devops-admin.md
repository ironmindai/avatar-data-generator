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
  - Configuration updated: 2026-01-30

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
**Service Name**: avatar-data-generator.service
**Service File**: `/etc/systemd/system/avatar-data-generator.service`
**Status**: ACTIVE (enabled and running)

### Service Configuration
- **Type**: simple
- **User**: niro
- **Working Directory**: /home/niro/galacticos/avatar-data-generator
- **Command**: gunicorn with 4 workers, 2 threads per worker
- **Restart Policy**: Always (with 10s delay, max 5 restarts in 300s)
- **Dependencies**: Requires network.target, wants postgresql.service

### Service Logs
- Access Log: `/var/log/avatar-data-generator/access.log`
- Error Log: `/var/log/avatar-data-generator/error.log`
- Journald: `StandardOutput=journal` and `StandardError=journal` configured
- View service logs: `sudo journalctl -u avatar-data-generator.service`
- Follow logs in real-time: `sudo journalctl -u avatar-data-generator.service -f`

### Service Management Commands
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

### Static Files 403 Forbidden Error (2026-01-30)
**Issue**: Specific static files (generate.css, generate.js) were returning HTTP 403 Forbidden errors
**Root Cause**: Files created by frontend-brand-guardian agent had restrictive permissions (600) that prevented nginx (www-data user) from reading them:
- `/home/niro/galacticos/avatar-data-generator/static/css/generate.css` (was 600)
- `/home/niro/galacticos/avatar-data-generator/static/js/generate.js` (was 600)
**Solution**: Fixed permissions on problematic files:
```bash
chmod 644 /home/niro/galacticos/avatar-data-generator/static/css/generate.css
chmod 644 /home/niro/galacticos/avatar-data-generator/static/js/generate.js
```
**Verification**:
- All static files now have proper permissions (644 for files, 755 for directories)
- Nginx (www-data user) can now read all static assets
**Prevention**: Ensure future static files are created with proper read permissions (644) for nginx

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

## Notes
- This is a production deployment on the shared dev.iron-mind.ai server
- Database credentials are stored securely in .env file (NOT in version control)
- Application uses gunicorn WSGI server (4 workers, 2 threads each) for production
- Service auto-restarts on failure
- SSL certificate auto-renews via certbot
- For database schema changes (tables, migrations, etc.), consult the database-schema-manager agent
- Static files served directly by nginx for better performance
