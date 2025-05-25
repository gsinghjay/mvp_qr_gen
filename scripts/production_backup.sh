#!/bin/bash

# Production-safe backup script
# Temporarily stops API to avoid connection conflicts during backup

set -e

echo "=== PRODUCTION-SAFE DATABASE BACKUP ==="
echo "Timestamp: $(date)"
echo

# Check if API is running
echo "1. Checking API status..."
if docker-compose ps api | grep -q "Up"; then
    API_WAS_RUNNING=true
    echo "✅ API is currently running"
else
    API_WAS_RUNNING=false
    echo "ℹ️  API is not running"
fi

# Stop API to prevent connection conflicts
if [ "$API_WAS_RUNNING" = true ]; then
    echo "2. Stopping API service for safe backup..."
    docker-compose stop api
    echo "✅ API service stopped"
    
    # Wait for connections to close
    echo "   Waiting 5 seconds for connections to close..."
    sleep 5
else
    echo "2. API already stopped, proceeding with backup..."
fi

# Create backup using direct PostgreSQL connection
echo "3. Creating database backup..."
BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="qrdb_${BACKUP_TIMESTAMP}.sql"

if docker-compose exec postgres bash -c "
    export PGPASSWORD=pgpassword
    pg_dump -h localhost -U pguser -d qrdb --format=c --verbose --no-tablespaces --no-privileges --no-owner -f /tmp/$BACKUP_FILE
    
    # Check if backup was created
    if [ -f /tmp/$BACKUP_FILE ]; then
        BACKUP_SIZE=\$(stat -c%s /tmp/$BACKUP_FILE)
        echo \"Backup created: \$BACKUP_SIZE bytes\"
    else
        echo \"ERROR: Backup file not created\"
        exit 1
    fi
"; then
    echo "✅ Database backup completed successfully"
    
    # Copy backup file from PostgreSQL container to host-mounted backups directory
    echo "   Copying backup to host directory..."
    docker cp qr_generator_postgres:/tmp/$BACKUP_FILE ./backups/$BACKUP_FILE
    
    # Clean up temporary file in PostgreSQL container
    docker-compose exec postgres rm -f /tmp/$BACKUP_FILE
    
    echo "   File: backups/$BACKUP_FILE"
else
    echo "❌ Database backup failed"
    
    # Restart API even if backup failed
    if [ "$API_WAS_RUNNING" = true ]; then
        echo "   Restarting API service..."
        docker-compose start api
    fi
    exit 1
fi

# Restart API service if it was running
if [ "$API_WAS_RUNNING" = true ]; then
    echo "4. Restarting API service..."
    docker-compose start api
    
    # Wait for API to be healthy
    echo "5. Waiting for API to become healthy..."
    timeout=60
    counter=0
    while [ $counter -lt $timeout ]; do
        if docker-compose exec api curl -f http://localhost:8000/health >/dev/null 2>&1; then
            echo "✅ API service is healthy"
            break
        fi
        echo "   Waiting for API to be ready... ($counter/$timeout)"
        sleep 2
        counter=$((counter+2))
    done
    
    if [ $counter -ge $timeout ]; then
        echo "❌ API service failed to become healthy within $timeout seconds"
        exit 1
    fi
else
    echo "4. API was not running initially, leaving it stopped"
fi

# Show backup file info
echo "6. Backup summary..."
if [ -f "backups/$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(stat -c%s "backups/$BACKUP_FILE")
    BACKUP_SIZE_MB=$(echo "scale=2; $BACKUP_SIZE / 1024 / 1024" | bc)
    echo "✅ Backup file: backups/$BACKUP_FILE"
    echo "   Size: $BACKUP_SIZE bytes (${BACKUP_SIZE_MB} MB)"
else
    echo "❌ Backup file not found in backups directory"
    exit 1
fi

echo
echo "🎉 PRODUCTION-SAFE BACKUP COMPLETED SUCCESSFULLY!"
echo "Database backup created: backups/$BACKUP_FILE" 