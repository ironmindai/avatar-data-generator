# Static Files Permission Fix

## The Problem
When Claude Code creates new static files (CSS, JS, images), they have restrictive permissions (600) that prevent nginx from serving them, resulting in **403 Forbidden errors**.

## Quick Fix
After creating or modifying any static files, run:
```bash
./fix-static-permissions.sh
```

## Why This Happens
- **Claude Code** creates files with `600` permissions (rw-------) for security
- **Nginx** (www-data user) needs `644` permissions (rw-r--r--) to read files
- This is by design - Claude Code prioritizes security over convenience

## Manual Fix (if needed)
```bash
# Fix ownership (ensure files are owned by niro:niro)
chown -R niro:niro static/

# Fix directory permissions (755 = rwxr-xr-x)
chmod -R 755 static/

# Fix file permissions (644 = rw-r--r--)
find static/ -type f -exec chmod 644 {} \;
```

## Verification
1. Check permissions: `ls -la static/js/` and `ls -la static/css/`
2. Files should show: `-rw-r--r--` (644)
3. Directories should show: `drwxr-xr-x` (755)
4. Test access: `curl -I https://avatar-data-generator.dev.iron-mind.ai/static/js/yourfile.js`
5. Should return `HTTP/2 200` (not 403)

## Remember
- Run `./fix-static-permissions.sh` after creating new static files
- This is a normal part of the development workflow on this server
- The fix script is safe to run multiple times

---
For detailed technical explanation, see: `docs/system-devops-admin.md` → Troubleshooting History → Static Files 403 Forbidden Error
