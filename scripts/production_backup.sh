#!/bin/bash

# Production-safe backup script
# Thin wrapper around the enhanced manage_db.py with centralized API service management

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
required_vars_backup=("POSTGRES_USER" "POSTGRES_DB")
missing_vars_backup=()

for var in "${required_vars_backup[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars_backup+=("$var")
    fi
done

if [ ${#missing_vars_backup[@]} -gt 0 ]; then
    echo "❌ Error: Required environment variables for production_backup.sh are not set:"
    for var in "${missing_vars_backup[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please check your .env file and ensure these variables are set:"
    echo "   POSTGRES_USER=pguser"
    echo "   POSTGRES_DB=qrdb"
    exit 1
fi

echo "=== PRODUCTION-SAFE DATABASE BACKUP ==="
echo "Timestamp: $(date)"
echo "Using enhanced manage_db.py with centralized API service management"
echo

# HOST-LEVEL API Service Management (keeping container running)
echo "🛑 Managing API service at HOST level (preventing Docker-in-Docker deadlock)..."

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

# Execute backup using manage_db.py WITH API service management (--with-api-stop)
echo "🚀 Starting production-safe backup via manage_db.py (with internal API management)..."
if docker-compose exec api python /app/scripts/manage_db.py --create-backup --with-api-stop; then
    echo "✅ Production-safe backup completed successfully!"
    echo "   Database operations managed by enhanced manage_db.py"
    echo "   API service lifecycle controlled internally by manage_db.py"
    
    # Show latest backup file info
    echo
    echo "📊 Latest backup file information:"
    LATEST_BACKUP=$(docker-compose exec api find /app/backups -name "qrdb_*.sql" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2- | tr -d '\r\n' || echo "")
    
    if [ -n "$LATEST_BACKUP" ]; then
        BACKUP_SIZE=$(docker-compose exec api stat -c%s "$LATEST_BACKUP" 2>/dev/null | tr -d '\r\n' || echo "unknown")
        BACKUP_NAME=$(basename "$LATEST_BACKUP")
        if [ "$BACKUP_SIZE" != "unknown" ] && [ -n "$BACKUP_SIZE" ]; then
            BACKUP_SIZE_MB=$(echo "scale=2; $BACKUP_SIZE / 1024 / 1024" | bc 2>/dev/null || echo "unknown")
            echo "   📁 File: $BACKUP_NAME"
            echo "   📏 Size: $BACKUP_SIZE bytes (${BACKUP_SIZE_MB} MB)"
        else
            echo "   📁 File: $BACKUP_NAME"
            echo "   📏 Size: Could not determine"
        fi
        
        # Show backup location
        echo "   📍 Location: /app/backups/ (container) and ./backups/ (host)"
    else
        echo "   ⚠️  Could not locate latest backup file"
    fi
    
    # API service restart is handled internally by manage_db.py
    echo
    echo "ℹ️  API service restart handled internally by manage_db.py"
    echo "   No additional host-level service management required"
else
    echo "❌ Production-safe backup failed"
    echo "   Check the manage_db.py logs for detailed error information"
    echo "   Logs available in container at /logs/database/"
    echo "   💡 API service state management was handled internally by manage_db.py"
    
    exit 1
fi

echo
echo "🎉 PRODUCTION-SAFE BACKUP COMPLETED SUCCESSFULLY!"
echo "   ✅ Database backup created with production-safe procedures"
echo "   ✅ API service lifecycle managed internally by manage_db.py (no Docker-in-Docker deadlock)"
echo "   ✅ All operations logged for audit trail"
echo "   ✅ Backup available in both container and host directories" 