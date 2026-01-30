# Quick Deployment Guide - APScheduler Integration

## Prerequisites
- PostgreSQL database is running
- Virtual environment exists at `/home/niro/galacticos/avatar-data-generator/venv`
- Flask app systemd service is configured

## Deployment Steps

### 1. Install APScheduler

```bash
cd /home/niro/galacticos/avatar-data-generator
source venv/bin/activate
pip install -r requirements.txt
```

Expected output:
```
Successfully installed APScheduler-3.10.4 ...
```

### 2. Verify Configuration

Check that `.env` has the worker interval setting:

```bash
grep WORKER_INTERVAL /home/niro/galacticos/avatar-data-generator/.env
```

Expected output:
```
WORKER_INTERVAL=30
```

### 3. Restart Flask Service

```bash
sudo systemctl restart avatar-data-generator
```

### 4. Verify Scheduler Started

```bash
sudo journalctl -u avatar-data-generator -n 50 | grep SCHEDULER
```

Expected output:
```
[SCHEDULER] Background scheduler started - checking for tasks every 30 seconds
```

### 5. Monitor Logs

```bash
sudo journalctl -u avatar-data-generator -f
```

### 6. Test with a Real Task

1. Open browser and navigate to the web interface
2. Log in
3. Navigate to `/generate`
4. Submit an avatar generation task
5. Watch the logs - you should see processing start within 30 seconds

## Quick Verification Commands

```bash
# Check service status
sudo systemctl status avatar-data-generator

# View recent logs
sudo journalctl -u avatar-data-generator -n 100

# Check for errors
sudo journalctl -u avatar-data-generator | grep ERROR

# Check scheduler activity
sudo journalctl -u avatar-data-generator | grep SCHEDULER

# View pending tasks
psql -U avatar_data_gen -d avatar_data_generator -c "SELECT task_id, status FROM generation_tasks WHERE status = 'pending';"
```

## Rollback (If Needed)

If you encounter issues, you can temporarily disable the scheduler:

### Option 1: Revert to Previous Version

```bash
cd /home/niro/galacticos/avatar-data-generator
git checkout HEAD~1
pip install -r requirements.txt
sudo systemctl restart avatar-data-generator
```

### Option 2: Comment Out Scheduler in app.py

Edit `/home/niro/galacticos/avatar-data-generator/app.py` and comment out the scheduler section:

```python
# # Initialize APScheduler for background task processing
# if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
#     scheduler = BackgroundScheduler()
#     ...
```

Then restart:
```bash
sudo systemctl restart avatar-data-generator
```

## Success Indicators

✅ Scheduler starts on app boot
✅ No errors in logs
✅ Tasks are processed automatically
✅ Database shows tasks moving from 'pending' to 'data-generated'
✅ Single systemd service manages everything

## Common Issues

### Scheduler Not Starting
- **Check:** APScheduler installed: `pip list | grep APScheduler`
- **Fix:** Run `pip install -r requirements.txt`

### Import Errors
- **Check:** Logs for Python import errors
- **Fix:** Verify all dependencies installed, check Python path

### Tasks Not Processing
- **Check:** Pending tasks exist: `SELECT COUNT(*) FROM generation_tasks WHERE status = 'pending';`
- **Check:** Scheduler running: `journalctl -u avatar-data-generator | grep SCHEDULER`
- **Fix:** Restart service, check database connection

## Support Files

- Full documentation: `/home/niro/galacticos/avatar-data-generator/APSCHEDULER_INTEGRATION.md`
- Detailed guide: `/home/niro/galacticos/avatar-data-generator/playground/SCHEDULER_INTEGRATION_README.md`
- Test script: `/home/niro/galacticos/avatar-data-generator/playground/test_scheduler_integration.py`

## Post-Deployment

After successful deployment, you can optionally:

1. **Remove the old worker service** (if it exists):
   ```bash
   sudo systemctl stop avatar-task-processor
   sudo systemctl disable avatar-task-processor
   sudo rm /etc/systemd/system/avatar-task-processor.service
   sudo systemctl daemon-reload
   ```

2. **Adjust worker interval** based on task volume:
   - Edit `.env` and change `WORKER_INTERVAL`
   - Restart: `sudo systemctl restart avatar-data-generator`

3. **Monitor performance** for the first few hours to ensure stability

## Done!

Your Flask application now includes an integrated task processor. No separate worker service is needed.
