#!/bin/bash

# Production-safe backup script
# Now a thin wrapper around the enhanced manage_db.py

set -e

echo "=== PRODUCTION-SAFE DATABASE BACKUP ==="
echo "Timestamp: $(date)"
echo "Using enhanced manage_db.py with API service management"
echo

# Execute backup using manage_db.py with API service management
echo "🚀 Starting production-safe backup via manage_db.py..."
if docker-compose exec api python /app/scripts/manage_db.py --create-backup --with-api-stop; then
    echo "✅ Production-safe backup completed successfully!"
    echo "Backup created with API service lifecycle management"
    
    # Show latest backup file info
    echo
    echo "📊 Latest backup file:"
    LATEST_BACKUP=$(docker-compose exec api find /app/backups -name "qrdb_*.sql" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2- | tr -d '\r\n' || echo "")
    
    if [ -n "$LATEST_BACKUP" ]; then
        BACKUP_SIZE=$(docker-compose exec api stat -c%s "$LATEST_BACKUP" 2>/dev/null | tr -d '\r\n' || echo "unknown")
        BACKUP_NAME=$(basename "$LATEST_BACKUP")
        if [ "$BACKUP_SIZE" != "unknown" ] && [ -n "$BACKUP_SIZE" ]; then
            BACKUP_SIZE_MB=$(echo "scale=2; $BACKUP_SIZE / 1024 / 1024" | bc 2>/dev/null || echo "unknown")
            echo "   File: $BACKUP_NAME"
            echo "   Size: $BACKUP_SIZE bytes (${BACKUP_SIZE_MB} MB)"
        else
            echo "   File: $BACKUP_NAME"
            echo "   Size: Could not determine"
        fi
    else
        echo "   Could not locate latest backup file"
    fi
else
    echo "❌ Production-safe backup failed"
    echo "Check the manage_db.py logs for detailed error information"
    exit 1
fi

echo
echo "🎉 PRODUCTION-SAFE BACKUP COMPLETED SUCCESSFULLY!"
echo "All operations managed by enhanced manage_db.py with proper API lifecycle control" 