#!/bin/bash

# Test script for backup and restore functionality
# This script validates the backup and restore procedures for Task S.1

set -e

echo "=== Testing Backup and Restore Functionality ==="
echo "Timestamp: $(date)"
echo

# Get the latest backup file
echo "1. Finding latest backup file..."
LATEST_BACKUP=$(docker-compose exec api sh -c "ls -t /app/data/backups/qrdb_*.sql 2>/dev/null | head -n 1" | tr -d '\r')
if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ No backup files found, creating one..."
    docker-compose exec api python /app/scripts/manage_db.py --create-backup
    LATEST_BACKUP=$(docker-compose exec api sh -c "ls -t /app/data/backups/qrdb_*.sql | head -n 1" | tr -d '\r')
fi
echo "✅ Found latest backup: $LATEST_BACKUP"
echo

# Get current row counts for comparison
echo "2. Getting current database state..."
QR_COUNT_BEFORE=$(docker-compose exec postgres psql -U pguser -d qrdb -t -c "SELECT COUNT(*) FROM qr_codes;" | tr -d ' \r\n')
SCAN_COUNT_BEFORE=$(docker-compose exec postgres psql -U pguser -d qrdb -t -c "SELECT COUNT(*) FROM scan_logs;" | tr -d ' \r\n')
echo "✅ Current QR codes: $QR_COUNT_BEFORE"
echo "✅ Current scan logs: $SCAN_COUNT_BEFORE"
echo

# Create a new QR code to verify restore overwrites current data
echo "3. Creating test QR code to verify restore overwrites..."
RESPONSE_CODE=$(docker-compose exec api curl -s -o /dev/null -w "%{http_code}" \
    -X POST http://localhost:8000/api/v1/qr/static \
    -H "Content-Type: application/json" \
    -d '{"content": "Test QR for restore validation", "title": "Restore Test QR"}')

if [ "$RESPONSE_CODE" = "201" ]; then
    echo "✅ Test QR created"
else
    echo "❌ Failed to create test QR (HTTP $RESPONSE_CODE)"
    exit 1
fi
echo

# Get new counts
QR_COUNT_AFTER_ADD=$(docker-compose exec postgres psql -U pguser -d qrdb -t -c "SELECT COUNT(*) FROM qr_codes;" | tr -d ' \r\n')
echo "✅ QR codes after adding test: $QR_COUNT_AFTER_ADD"
echo

# Extract just the filename from the full path
BACKUP_FILENAME=$(basename "$LATEST_BACKUP")
echo "4. Testing restore functionality with backup: $BACKUP_FILENAME"

# Test the restore functionality using production-safe method
echo "Executing production-safe restore..."
if ./scripts/safe_restore.sh "$BACKUP_FILENAME"; then
    echo "✅ Production-safe restore completed successfully"
else
    echo "❌ Production-safe restore failed"
    exit 1
fi
echo

# Verify restore worked by checking counts
echo "5. Verifying restore results..."
QR_COUNT_AFTER_RESTORE=$(docker-compose exec postgres psql -U pguser -d qrdb -t -c "SELECT COUNT(*) FROM qr_codes;" | tr -d ' \r\n')
SCAN_COUNT_AFTER_RESTORE=$(docker-compose exec postgres psql -U pguser -d qrdb -t -c "SELECT COUNT(*) FROM scan_logs;" | tr -d ' \r\n')

echo "Results:"
echo "  QR codes before: $QR_COUNT_BEFORE"
echo "  QR codes after adding test: $QR_COUNT_AFTER_ADD"
echo "  QR codes after restore: $QR_COUNT_AFTER_RESTORE"
echo "  Scan logs before: $SCAN_COUNT_BEFORE"
echo "  Scan logs after restore: $SCAN_COUNT_AFTER_RESTORE"
echo

# Verify that restore worked correctly
if [ "$QR_COUNT_AFTER_RESTORE" -eq "$QR_COUNT_BEFORE" ] && [ "$SCAN_COUNT_AFTER_RESTORE" -eq "$SCAN_COUNT_BEFORE" ]; then
    echo "✅ RESTORE TEST PASSED: Database successfully restored to backup state"
else
    echo "❌ RESTORE TEST FAILED: Database state does not match backup"
    exit 1
fi

# Test basic functionality after restore
echo
echo "6. Testing basic functionality after restore..."
docker-compose exec api python /app/scripts/manage_db.py --validate
if [ $? -eq 0 ]; then
    echo "✅ Database validation passed after restore"
else
    echo "❌ Database validation failed after restore"
    exit 1
fi

echo
echo "🎉 ALL BACKUP AND RESTORE TESTS PASSED!"
echo "Task S.1 - Backup and Restore procedures are working correctly" 