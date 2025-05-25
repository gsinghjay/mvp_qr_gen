#!/bin/bash

# Production-safe database restore script
# Now a thin wrapper around the enhanced manage_db.py

set -e

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_filename>"
    echo "Example: $0 qrdb_20250525_044403.sql"
    exit 1
fi

echo "=== PRODUCTION-SAFE DATABASE RESTORE ==="
echo "Backup file: $BACKUP_FILE"
echo "Timestamp: $(date)"
echo "Using enhanced manage_db.py with API service management"
echo

# Get current database state for verification
echo "1. Recording current database state..."
QR_COUNT_BEFORE=$(docker-compose exec postgres psql -U pguser -d qrdb -t -c "SELECT COUNT(*) FROM qr_codes;" 2>/dev/null | tr -d ' \r\n' || echo "unknown")
SCAN_COUNT_BEFORE=$(docker-compose exec postgres psql -U pguser -d qrdb -t -c "SELECT COUNT(*) FROM scan_logs;" 2>/dev/null | tr -d ' \r\n' || echo "unknown")
echo "✅ Current state: $QR_COUNT_BEFORE QR codes, $SCAN_COUNT_BEFORE scan logs"

# Execute restore using manage_db.py with API service management
echo "2. Starting production-safe restore via manage_db.py..."
if docker-compose exec api python /app/scripts/manage_db.py --restore "$BACKUP_FILE" --with-api-stop; then
    echo "✅ Production-safe restore completed successfully!"
    echo "Restore completed with API service lifecycle management"
else
    echo "❌ Production-safe restore failed"
    echo "Check the manage_db.py logs for detailed error information"
    exit 1
fi

# Verify restore results
echo "3. Verifying restore results..."
QR_COUNT_AFTER=$(docker-compose exec postgres psql -U pguser -d qrdb -t -c "SELECT COUNT(*) FROM qr_codes;" 2>/dev/null | tr -d ' \r\n' || echo "unknown")
SCAN_COUNT_AFTER=$(docker-compose exec postgres psql -U pguser -d qrdb -t -c "SELECT COUNT(*) FROM scan_logs;" 2>/dev/null | tr -d ' \r\n' || echo "unknown")

echo "Restore Results:"
echo "  QR codes before: $QR_COUNT_BEFORE"
echo "  QR codes after:  $QR_COUNT_AFTER"
echo "  Scan logs before: $SCAN_COUNT_BEFORE"
echo "  Scan logs after:  $SCAN_COUNT_AFTER"

# Validate database structure using manage_db.py
echo "4. Validating database structure..."
if docker-compose exec api python /app/scripts/manage_db.py --validate; then
    echo "✅ Database validation passed"
else
    echo "❌ Database validation failed"
    exit 1
fi

echo
echo "🎉 PRODUCTION-SAFE RESTORE COMPLETED SUCCESSFULLY!"
echo "Database has been safely restored from $BACKUP_FILE"
echo "All operations managed by enhanced manage_db.py with proper API lifecycle control" 