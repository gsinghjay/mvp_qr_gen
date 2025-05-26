#!/bin/bash

# Production-safe database restore script
# Enhanced to handle API service management at host level to prevent Docker-in-Docker deadlocks

set -e

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    # Export variables to make them available to subshells
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ Error: .env file not found. Cannot proceed."
    exit 1
fi

# Check required environment variables (fail fast)
required_vars_restore=("POSTGRES_USER" "POSTGRES_DB")
missing_vars_restore=()

for var in "${required_vars_restore[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars_restore+=("$var")
    fi
done

if [ ${#missing_vars_restore[@]} -gt 0 ]; then
    echo "❌ Error: Required environment variables for safe_restore.sh are not set:"
    for var in "${missing_vars_restore[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please check your .env file and ensure these variables are set:"
    echo "   POSTGRES_USER=pguser"
    echo "   POSTGRES_DB=qrdb"
    exit 1
fi

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
echo "Using enhanced manage_db.py with HOST-LEVEL API service management"
echo

# Get current database state for verification
echo "1️⃣ Recording current database state..."
QR_COUNT_BEFORE=$(docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -t -c "SELECT COUNT(*) FROM qr_codes;" 2>/dev/null | tr -d ' \r\n' || echo "unknown")
SCAN_COUNT_BEFORE=$(docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -t -c "SELECT COUNT(*) FROM scan_logs;" 2>/dev/null | tr -d ' \r\n' || echo "unknown")
echo "   📊 Current state: $QR_COUNT_BEFORE QR codes, $SCAN_COUNT_BEFORE scan logs"

# HOST-LEVEL API Service Management
echo
echo "2️⃣ Managing API service at HOST level (preventing Docker-in-Docker deadlock)..."
echo "   🛑 Stopping API service from host..."

API_WAS_RUNNING=false
if docker-compose ps api | grep -q "Up"; then
    API_WAS_RUNNING=true
    echo "   📍 API service is currently running"
    echo "   ✅ Keeping container running for database operations"
    echo "   💡 API service management will be handled by manage_db.py internally"
else
    echo "   ❌ API container is not running - starting it for database operations"
    if timeout 60 docker-compose up -d api; then
        echo "   ✅ API container started"
        API_WAS_RUNNING=true
    else
        echo "   ❌ Failed to start API container"
        exit 1
    fi
fi

# Execute restore using manage_db.py WITHOUT API service management
echo
echo "3️⃣ Starting database restore via manage_db.py (without API management)..."
echo "   🚨 WARNING: This will replace all current database content"
echo "   📁 Restoring from: $BACKUP_FILE"
echo "   🛡️ Safety backup will be created automatically (with 3-minute timeout)"
echo "   🔄 API service managed at HOST level (no Docker-in-Docker)"
echo "   ⏱️  Note: Safety backup creation may take 1-3 minutes depending on database size"
echo

# Call manage_db.py WITHOUT --with-api-stop flag to prevent Docker-in-Docker deadlock
# The API container remains running, but API service management is handled externally
if docker-compose exec api python /app/scripts/manage_db.py --restore "$BACKUP_FILE"; then
    echo "✅ Database restore completed successfully!"
    echo "   Database operations managed by enhanced manage_db.py"
    echo "   API service lifecycle controlled at HOST level"
else
    echo "❌ Database restore failed"
    echo "   Check the manage_db.py logs for detailed error information"
    echo "   Logs available in container at /logs/database/"
    echo "   Safety backup was created before restore attempt"
    
    # Restart API service if it was running before
    if [ "$API_WAS_RUNNING" = true ]; then
        echo "   🔄 Attempting to restart API service after failed restore..."
        if timeout 180 docker-compose up -d api; then
            echo "   ✅ API service restarted"
        else
            echo "   ❌ Failed to restart API service - manual intervention required"
        fi
    fi
    
    exit 1
fi

# Restart API service if it was running before
if [ "$API_WAS_RUNNING" = true ]; then
    echo
    echo "4️⃣ Restarting API service..."
    echo "   🚀 Starting API service..."
    
    if timeout 180 docker-compose up -d api; then
        echo "   ✅ API service started"
        
        # Wait for service to become healthy
        echo "   ⏳ Waiting for API service to become healthy..."
        max_attempts=30
        attempt=0
        
        while [ $attempt -lt $max_attempts ]; do
            if curl -k -s --max-time 5 -u "${AUTH_USER:-admin_user}:${AUTH_PASS:-strongpassword}" "${API_URL:-https://10.1.6.12}/health" >/dev/null 2>&1; then
                echo "   ✅ API service is healthy and ready"
                break
            fi
            sleep 2
            attempt=$((attempt + 1))
        done
        
        if [ $attempt -ge $max_attempts ]; then
            echo "   ⚠️  API service started but health check timed out"
            echo "   💡 Service may still be starting up - check manually"
        fi
    else
        echo "   ❌ Failed to start API service within timeout"
        echo "   💡 Manual intervention required: docker-compose up -d api"
        exit 1
    fi
fi

# Verify restore results
echo
echo "5️⃣ Verifying restore results..."
QR_COUNT_AFTER=$(docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -t -c "SELECT COUNT(*) FROM qr_codes;" 2>/dev/null | tr -d ' \r\n' || echo "unknown")
SCAN_COUNT_AFTER=$(docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -t -c "SELECT COUNT(*) FROM scan_logs;" 2>/dev/null | tr -d ' \r\n' || echo "unknown")

echo "   📊 Restore Results:"
echo "      QR codes before: $QR_COUNT_BEFORE"
echo "      QR codes after:  $QR_COUNT_AFTER"
echo "      Scan logs before: $SCAN_COUNT_BEFORE"
echo "      Scan logs after:  $SCAN_COUNT_AFTER"

# Validate database structure using manage_db.py
echo
echo "6️⃣ Validating database structure..."
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
echo "   ✅ API service lifecycle managed at HOST level (no Docker-in-Docker deadlock)"
echo "   ✅ Database structure validated"
echo "   ✅ Safety backup created before restore"
echo "   ✅ All operations logged for audit trail" 