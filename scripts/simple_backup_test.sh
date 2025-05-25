#!/bin/bash

# Simple backup test to isolate the issue
set -e

echo "=== Simple Backup Test ==="
echo "Timestamp: $(date)"
echo

# Test 1: Check PostgreSQL connectivity
echo "1. Testing PostgreSQL connectivity..."
if timeout 10 docker-compose exec postgres psql -U pguser -d qrdb -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ PostgreSQL connection successful"
else
    echo "❌ PostgreSQL connection failed"
    exit 1
fi

# Test 2: Check active connections
echo "2. Checking active connections..."
ACTIVE_CONNECTIONS=$(timeout 10 docker-compose exec postgres psql -U pguser -d qrdb -t -c "SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'qrdb';" | tr -d ' \r\n')
echo "✅ Active connections to qrdb: $ACTIVE_CONNECTIONS"

# Test 3: Simple backup using pg_dump directly
echo "3. Testing simple pg_dump..."
BACKUP_FILE="/tmp/simple_test_$(date +%Y%m%d_%H%M%S).sql"
echo "Creating backup: $BACKUP_FILE"

if timeout 60 docker-compose exec postgres bash -c "
    export PGPASSWORD=pgpassword
    pg_dump -h localhost -U pguser -d qrdb --format=c -f '$BACKUP_FILE'
    echo 'Backup file size:' \$(stat -c%s '$BACKUP_FILE' 2>/dev/null || echo 'File not found')
"; then
    echo "✅ Simple backup successful"
else
    echo "❌ Simple backup failed"
    exit 1
fi

# Test 4: Verify backup file
echo "4. Verifying backup file..."
if docker-compose exec postgres test -f "$BACKUP_FILE"; then
    BACKUP_SIZE=$(docker-compose exec postgres stat -c%s "$BACKUP_FILE" | tr -d '\r\n')
    echo "✅ Backup file exists, size: $BACKUP_SIZE bytes"
    
    # Clean up test file
    docker-compose exec postgres rm -f "$BACKUP_FILE"
    echo "✅ Test backup file cleaned up"
else
    echo "❌ Backup file not found"
    exit 1
fi

echo
echo "🎉 SIMPLE BACKUP TEST PASSED!"
echo "Basic backup functionality is working" 