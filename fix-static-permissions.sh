#!/bin/bash
#
# Fix Static File Permissions
# =============================
# This script ensures all static files have correct permissions for nginx access.
# Run this after creating new static files (CSS, JS, images, etc.)
#
# Usage: ./fix-static-permissions.sh
#

PROJECT_ROOT="/home/niro/galacticos/avatar-data-generator"
STATIC_DIR="${PROJECT_ROOT}/static"

echo "Fixing permissions for static files in ${STATIC_DIR}..."

# Fix ownership (should already be niro:niro, but ensure it)
chown -R niro:niro "${STATIC_DIR}"

# Fix directory permissions (755 = rwxr-xr-x)
# Owner: read, write, execute
# Group: read, execute
# Others: read, execute
chmod -R 755 "${STATIC_DIR}"

# Fix file permissions (644 = rw-r--r--)
# Owner: read, write
# Group: read
# Others: read
find "${STATIC_DIR}" -type f -exec chmod 644 {} \;

echo "✓ Directory permissions set to 755 (drwxr-xr-x)"
echo "✓ File permissions set to 644 (-rw-r--r--)"
echo ""
echo "Verification:"
ls -la "${STATIC_DIR}/js/" 2>/dev/null | head -8
ls -la "${STATIC_DIR}/css/" 2>/dev/null | head -8

echo ""
echo "Done! All static files are now accessible to nginx (www-data user)."
