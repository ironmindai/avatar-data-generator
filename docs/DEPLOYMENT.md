# Production Deployment Guide

This document covers deploying the Avatar Data Generator service to production.

## System Requirements

- Python 3.12+
- PostgreSQL database
- MinIO S3 storage
- Nginx reverse proxy

## Environment Setup

### 1. Virtual Environment

```bash
cd /home/niro/galacticos/avatar-data-generator
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure all required values:

```bash
cp .env.example .env
```

Required configuration in `.env`:
- Database credentials (PostgreSQL)
- OpenRouter/OpenAI API keys
- S3/MinIO credentials and endpoints
- Flask secret key
- Application port (default: 8085)

### 3. Database Initialization

Run database migrations to create all required tables:

```bash
source venv/bin/activate
flask db upgrade
```

## Systemd Service Configuration

### Service File Location

`/etc/systemd/system/avatar-data-generator.service`

### Service Configuration

```ini
[Unit]
Description=Avatar Data Generator Flask Application
After=network.target postgresql.service

[Service]
Type=simple
User=niro
WorkingDirectory=/home/niro/galacticos/avatar-data-generator
Environment="PATH=/home/niro/galacticos/avatar-data-generator/venv/bin"

# Gunicorn configuration
# - 1 worker: APScheduler runs inside Flask app (multiple workers = duplicate jobs)
# - 2 threads: Handle concurrent requests within single worker
# - Port 8085: Internal port (Nginx reverse proxy required)
# - Timeout 300s: Long-running image generation requests
# - NO max-requests: Worker recycling conflicts with APScheduler background jobs
ExecStart=/home/niro/galacticos/avatar-data-generator/venv/bin/gunicorn \
    --workers=1 \
    --threads=2 \
    --bind=0.0.0.0:8085 \
    --timeout=300 \
    --access-logfile=- \
    --error-logfile=- \
    app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Critical Notes:**
- **Single Worker Only**: APScheduler runs inside the Flask app. Multiple workers would create duplicate scheduled jobs.
- **No max-requests**: Worker recycling (`--max-requests`) MUST NOT be used with APScheduler. Restarting workers kills background jobs.
- **Logs to systemd**: All logs go to journald via stdout/stderr.

## APScheduler Background Jobs

The service runs APScheduler inside the Flask application (not as a separate daemon). Background jobs include:

1. **Avatar Generation Task Processor**: Processes queued avatar generation tasks
2. **Image Generation Task Processor**: Processes scene-based image generation
3. **Stuck Task Recovery**: Automatically recovers tasks stuck in "processing" state
4. **Face Detection Processor**: Detects and validates faces in uploaded images

Jobs run at configurable intervals (default: 5 seconds). See `docs/scheduled-tasks.md` for details.

## Service Management

### Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable avatar-data-generator
sudo systemctl start avatar-data-generator
```

### Service Control Commands

```bash
# Check service status
sudo systemctl status avatar-data-generator

# View live logs (follows new entries)
sudo journalctl -u avatar-data-generator -f

# View recent logs (last 100 lines)
sudo journalctl -u avatar-data-generator -n 100

# Filter logs by date
sudo journalctl -u avatar-data-generator --since "2026-03-12 10:00:00"

# Restart service
sudo systemctl restart avatar-data-generator

# Stop service
sudo systemctl stop avatar-data-generator
```

## Nginx Reverse Proxy

### Configuration

The service listens on `0.0.0.0:8085` and requires Nginx for HTTPS termination.

**Domain:** `avatar-data-generator.dev.iron-mind.ai`

Nginx configuration should include:
- Reverse proxy to `http://127.0.0.1:8085`
- SSL certificate configuration
- Long timeout values for image generation endpoints (300s+)
- CORS headers if needed for frontend access

Consult `docs/system-devops-admin.md` for Nginx configuration details.

## Monitoring and Troubleshooting

### Health Check

```bash
curl http://localhost:8085/
```

Should return the login page HTML.

### Common Issues

**Service won't start:**
- Check logs: `sudo journalctl -u avatar-data-generator -n 50`
- Verify `.env` file exists and contains valid configuration
- Ensure database is running and migrations are applied
- Verify venv has all dependencies: `venv/bin/pip list`

**Background jobs not running:**
- Check scheduler logs: `sudo journalctl -u avatar-data-generator | grep SCHEDULER`
- Verify single worker configuration (multiple workers cause issues)
- Ensure `max-requests` is NOT set in gunicorn command

**Database connection errors:**
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check database credentials in `.env`
- Test connection: `psql -h localhost -U avatar_data_gen -d avatar_data_generator`

## Related Documentation

- API Routes: `docs/backend-routes.md`
- Scheduled Tasks: `docs/scheduled-tasks.md`
- Image Generation: `docs/OPENROUTER_INTEGRATION.md`
- Database Schema: `docs/database-schema-manager.md`
- System Administration: `docs/system-devops-admin.md`
