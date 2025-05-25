#!/bin/bash

# Production-safe database restore script
# Thin wrapper around the enhanced manage_db.py with centralized API service management

set -e

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ Usage: $0 <backup_filename>"
    echo "   Example: $0 qrdb_20250525_044403.sql"
    echo "   Available backups:"
    docker-compose exec api find /app/backups -name "qrdb_*.sql" -type f -printf '   %f\n' 2>/dev/null | sort || echo "   No backups found"
    exit 1
fi

echo "=== PRODUCTION-SAFE DATABASE RESTORE ==="
echo "Backup file: $BACKUP_FILE"
echo "Timestamp: $(date)"
echo "Using enhanced manage_db.py with centralized API service management"
echo

# Load environment variables for database credentials
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Get current database state for verification
echo "1️⃣ Recording current database state..."
QR_COUNT_BEFORE=$(docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -t -c "SELECT COUNT(*) FROM qr_codes;" 2>/dev/null | tr -d ' \r\n' || echo "unknown")
SCAN_COUNT_BEFORE=$(docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -t -c "SELECT COUNT(*) FROM scan_logs;" 2>/dev/null | tr -d ' \r\n' || echo "unknown")
echo "   📊 Current state: $QR_COUNT_BEFORE QR codes, $SCAN_COUNT_BEFORE scan logs"

# Execute restore using manage_db.py with API service management
echo
echo "2️⃣ Starting production-safe restore via manage_db.py..."
echo "   🚨 WARNING: This will replace all current database content"
echo "   📁 Restoring from: $BACKUP_FILE"
echo "   🛡️ Safety backup will be created automatically (with 3-minute timeout)"
echo "   🔄 API service will be managed automatically"
echo "   ⏱️  Note: Safety backup creation may take 1-3 minutes depending on database size"
echo

if docker-compose exec api python /app/scripts/manage_db.py --restore "$BACKUP_FILE" --with-api-stop; then
    echo "✅ Production-safe restore completed successfully!"
    echo "   All operations managed by enhanced manage_db.py"
    echo "   API service lifecycle controlled centrally"
else
    echo "❌ Production-safe restore failed"
    echo "   Check the manage_db.py logs for detailed error information"
    echo "   Logs available in container at /logs/database/"
    echo "   Safety backup was created before restore attempt"
    exit 1
fi

# Verify restore results
echo
echo "3️⃣ Verifying restore results..."
QR_COUNT_AFTER=$(docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -t -c "SELECT COUNT(*) FROM qr_codes;" 2>/dev/null | tr -d ' \r\n' || echo "unknown")
SCAN_COUNT_AFTER=$(docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -t -c "SELECT COUNT(*) FROM scan_logs;" 2>/dev/null | tr -d ' \r\n' || echo "unknown")

echo "   📊 Restore Results:"
echo "      QR codes before: $QR_COUNT_BEFORE"
echo "      QR codes after:  $QR_COUNT_AFTER"
echo "      Scan logs before: $SCAN_COUNT_BEFORE"
echo "      Scan logs after:  $SCAN_COUNT_AFTER"

# Validate database structure using manage_db.py
echo
echo "4️⃣ Validating database structure..."
if docker-compose exec api python /app/scripts/manage_db.py --validate; then
    echo "✅ Database validation passed"
else
    echo "❌ Database validation failed"
    echo "   The restore may have completed but database structure is invalid"
    echo "   Check the manage_db.py logs for detailed error information"
    exit 1
fi

echo
echo "🎉 PRODUCTION-SAFE RESTORE COMPLETED SUCCESSFULLY!"
echo "   ✅ Database restored from $BACKUP_FILE"
echo "   ✅ API service lifecycle managed automatically"
echo "   ✅ Database structure validated"
echo "   ✅ Safety backup created before restore"
echo "   ✅ All operations logged for audit trail" 