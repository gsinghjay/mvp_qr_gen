#!/bin/bash

# Production-safe database restore script
# This script properly manages service lifecycle during restore operations

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
echo

# Verify backup file exists
echo "1. Verifying backup file exists..."
if ! docker-compose exec api test -f "/app/data/backups/$BACKUP_FILE" && ! docker-compose exec api test -f "/app/backups/$BACKUP_FILE"; then
    echo "❌ Backup file $BACKUP_FILE not found in either /app/data/backups/ or /app/backups/"
    exit 1
fi
echo "✅ Backup file found"

# Get current database state for verification
echo "2. Recording current database state..."
QR_COUNT_BEFORE=$(docker-compose exec postgres psql -U pguser -d qrdb -t -c "SELECT COUNT(*) FROM qr_codes;" | tr -d ' \r\n')
SCAN_COUNT_BEFORE=$(docker-compose exec postgres psql -U pguser -d qrdb -t -c "SELECT COUNT(*) FROM scan_logs;" | tr -d ' \r\n')
echo "✅ Current state: $QR_COUNT_BEFORE QR codes, $SCAN_COUNT_BEFORE scan logs"

# Create safety backup
echo "3. Creating safety backup before restore..."
SAFETY_BACKUP_NAME="safety_backup_$(date +%Y%m%d_%H%M%S).sql"
docker-compose exec api python /app/scripts/manage_db.py --create-backup
echo "✅ Safety backup created"

# Stop API service to prevent database access during restore
echo "4. Stopping API service for safe restore..."
docker-compose stop api
echo "✅ API service stopped"

# Wait a moment for connections to close
echo "Waiting 5 seconds for connections to close..."
sleep 5

# Perform the restore
echo "5. Performing database restore..."
if docker-compose exec postgres bash -c "
    export PGPASSWORD=pgpassword
    # Find the backup file
    if [ -f '/app/data/backups/$BACKUP_FILE' ]; then
        BACKUP_PATH='/app/data/backups/$BACKUP_FILE'
    elif [ -f '/app/backups/$BACKUP_FILE' ]; then
        BACKUP_PATH='/app/backups/$BACKUP_FILE'
    else
        echo 'Backup file not found'
        exit 1
    fi
    
    # Drop existing tables
    psql -h localhost -U pguser -d qrdb -c 'DROP TABLE IF EXISTS scan_logs CASCADE;'
    psql -h localhost -U pguser -d qrdb -c 'DROP TABLE IF EXISTS qr_codes CASCADE;'
    psql -h localhost -U pguser -d qrdb -c 'DROP TABLE IF EXISTS alembic_version CASCADE;'
    
    # Restore from backup
    pg_restore -h localhost -U pguser -d qrdb --no-owner --no-privileges --single-transaction --exit-on-error \"\$BACKUP_PATH\"
"; then
    echo "✅ Database restore completed successfully"
else
    echo "❌ Database restore failed"
    echo "Starting API service..."
    docker-compose start api
    exit 1
fi

# Start API service
echo "6. Starting API service..."
docker-compose start api

# Wait for API to be healthy
echo "7. Waiting for API to become healthy..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if docker-compose exec api curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ API service is healthy"
        break
    fi
    echo "Waiting for API to be ready... ($counter/$timeout)"
    sleep 2
    counter=$((counter+2))
done

if [ $counter -ge $timeout ]; then
    echo "❌ API service failed to become healthy within $timeout seconds"
    exit 1
fi

# Verify restore results
echo "8. Verifying restore results..."
QR_COUNT_AFTER=$(docker-compose exec postgres psql -U pguser -d qrdb -t -c "SELECT COUNT(*) FROM qr_codes;" | tr -d ' \r\n')
SCAN_COUNT_AFTER=$(docker-compose exec postgres psql -U pguser -d qrdb -t -c "SELECT COUNT(*) FROM scan_logs;" | tr -d ' \r\n')

echo "Restore Results:"
echo "  QR codes before: $QR_COUNT_BEFORE"
echo "  QR codes after:  $QR_COUNT_AFTER"
echo "  Scan logs before: $SCAN_COUNT_BEFORE"
echo "  Scan logs after:  $SCAN_COUNT_AFTER"

# Validate database structure
echo "9. Validating database structure..."
if docker-compose exec api python /app/scripts/manage_db.py --validate; then
    echo "✅ Database validation passed"
else
    echo "❌ Database validation failed"
    exit 1
fi

echo
echo "🎉 PRODUCTION-SAFE RESTORE COMPLETED SUCCESSFULLY!"
echo "Database has been safely restored from $BACKUP_FILE"
echo "API service is running and healthy" 