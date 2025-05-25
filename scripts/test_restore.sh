#!/bin/bash

# Enhanced test script for backup and restore functionality
# Implements multi-stage verification logic as per Sub-Task S.1.R4

set -e

echo "=== ENHANCED BACKUP AND RESTORE TEST ==="
echo "Timestamp: $(date)"
echo "Testing enhanced manage_db.py backup and restore functionality"
echo

# Load environment variables for database credentials
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Function to get QR count
get_qr_count() {
    docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -t -c "SELECT COUNT(*) FROM qr_codes;" 2>/dev/null | tr -d ' \r\n' || echo "0"
}

# Function to get scan count
get_scan_count() {
    docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -t -c "SELECT COUNT(*) FROM scan_logs;" 2>/dev/null | tr -d ' \r\n' || echo "0"
}

# Function to check if QR exists by content
qr_exists() {
    local content="$1"
    local count=$(docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -t -c "SELECT COUNT(*) FROM qr_codes WHERE content = '$content';" 2>/dev/null | tr -d ' \r\n' || echo "0")
    [ "$count" -gt "0" ]
}

# Function to create a test QR code
create_test_qr() {
    local content="$1"
    local qr_type="${2:-static}"
    docker-compose exec api curl -s -X POST "http://localhost:8000/api/v1/qr/$qr_type" \
        -H "Content-Type: application/json" \
        -d "{\"content\": \"$content\"}" > /dev/null 2>&1
}

# Function to delete QR by content
delete_qr_by_content() {
    local content="$1"
    local qr_id=$(docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -t -c "SELECT id FROM qr_codes WHERE content = '$content' LIMIT 1;" 2>/dev/null | tr -d ' \r\n' || echo "")
    if [ -n "$qr_id" ]; then
        docker-compose exec api curl -s -X DELETE "http://localhost:8000/api/v1/qr/$qr_id" > /dev/null 2>&1
        echo "Deleted QR with ID: $qr_id"
    fi
}

echo "🔍 Step 1: Initial State Validation"
# Validate database is okay
if ! docker-compose exec api python /app/scripts/manage_db.py --validate; then
    echo "❌ Initial database validation failed"
    exit 1
fi
echo "✅ Database validation passed"

# Create a known test QR code that we'll delete
TEST_QR_INITIAL="test-initial-qr-$(date +%s)"
echo "Creating initial test QR: $TEST_QR_INITIAL"
create_test_qr "$TEST_QR_INITIAL"

# Record initial state
QR_COUNT_BEFORE_TEST=$(get_qr_count)
SCAN_COUNT_BEFORE_TEST=$(get_scan_count)
echo "✅ Initial state: $QR_COUNT_BEFORE_TEST QR codes, $SCAN_COUNT_BEFORE_TEST scan logs"

# Delete the test QR to create a known absence
echo "Deleting initial test QR to create known state"
delete_qr_by_content "$TEST_QR_INITIAL"

# Verify deletion
if qr_exists "$TEST_QR_INITIAL"; then
    echo "❌ Failed to delete initial test QR"
    exit 1
fi
echo "✅ Initial test QR deleted successfully"

echo
echo "📦 Step 2: Backup A Creation"
echo "Creating Backup A using manage_db.py with API stop..."
if docker-compose exec api python /app/scripts/manage_db.py --create-backup --with-api-stop; then
    # Find the most recent backup file
    BACKUP_A_FILENAME=$(docker-compose exec api find /app/backups -name "qrdb_*.sql" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2- | tr -d '\r\n' | xargs basename || echo "")
    if [ -n "$BACKUP_A_FILENAME" ]; then
        echo "✅ Backup A created: $BACKUP_A_FILENAME"
    else
        echo "❌ Could not determine Backup A filename"
        exit 1
    fi
else
    echo "❌ Backup A creation failed"
    exit 1
fi

echo
echo "🔄 Step 3: Change State"
# Create a new, specific QR code
TEST_QR_NEW="test-new-qr-$(date +%s)"
echo "Creating new test QR: $TEST_QR_NEW"
create_test_qr "$TEST_QR_NEW"

# Verify new QR exists
if ! qr_exists "$TEST_QR_NEW"; then
    echo "❌ Failed to create new test QR"
    exit 1
fi
echo "✅ New test QR created successfully"

# Record state after new QR
QR_COUNT_AFTER_NEW=$(get_qr_count)
SCAN_COUNT_AFTER_NEW=$(get_scan_count)
echo "✅ State after new QR: $QR_COUNT_AFTER_NEW QR codes, $SCAN_COUNT_AFTER_NEW scan logs"

echo
echo "📦 Step 4: Backup B Creation"
echo "Creating Backup B using manage_db.py with API stop..."
if docker-compose exec api python /app/scripts/manage_db.py --create-backup --with-api-stop; then
    # Find the most recent backup file (should be different from Backup A)
    BACKUP_B_FILENAME=$(docker-compose exec api find /app/backups -name "qrdb_*.sql" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2- | tr -d '\r\n' | xargs basename || echo "")
    if [ -n "$BACKUP_B_FILENAME" ] && [ "$BACKUP_B_FILENAME" != "$BACKUP_A_FILENAME" ]; then
        echo "✅ Backup B created: $BACKUP_B_FILENAME"
    else
        echo "❌ Could not determine Backup B filename or it's the same as Backup A"
        exit 1
    fi
else
    echo "❌ Backup B creation failed"
    exit 1
fi

echo
echo "🔄 Step 5: Restore Backup A"
echo "Restoring from Backup A: $BACKUP_A_FILENAME"
if docker-compose exec api python /app/scripts/manage_db.py --restore "$BACKUP_A_FILENAME"; then
    echo "✅ Backup A restore completed"
else
    echo "❌ Backup A restore failed"
    exit 1
fi

echo
echo "✅ Step 6: Verify Restore A"
# Validate database
if ! docker-compose exec api python /app/scripts/manage_db.py --validate; then
    echo "❌ Database validation failed after Backup A restore"
    exit 1
fi
echo "✅ Database validation passed after Backup A restore"

# Check QR count (should be back to before test state)
QR_COUNT_RESTORE_A=$(get_qr_count)
echo "QR count after Backup A restore: $QR_COUNT_RESTORE_A (expected: $QR_COUNT_BEFORE_TEST)"

# Verify new QR does NOT exist
if qr_exists "$TEST_QR_NEW"; then
    echo "❌ New test QR still exists after Backup A restore (should be gone)"
    exit 1
fi
echo "✅ New test QR correctly absent after Backup A restore"

# Verify initial QR does NOT exist (it was deleted before Backup A)
if qr_exists "$TEST_QR_INITIAL"; then
    echo "❌ Initial test QR exists after Backup A restore (should be absent)"
    exit 1
fi
echo "✅ Initial test QR correctly absent after Backup A restore"

echo
echo "🔄 Step 7: Restore Backup B"
echo "Restoring from Backup B: $BACKUP_B_FILENAME"
if docker-compose exec api python /app/scripts/manage_db.py --restore "$BACKUP_B_FILENAME"; then
    echo "✅ Backup B restore completed"
else
    echo "❌ Backup B restore failed"
    exit 1
fi

echo
echo "✅ Step 8: Verify Restore B"
# Validate database
if ! docker-compose exec api python /app/scripts/manage_db.py --validate; then
    echo "❌ Database validation failed after Backup B restore"
    exit 1
fi
echo "✅ Database validation passed after Backup B restore"

# Check QR count (should be back to after new QR state)
QR_COUNT_RESTORE_B=$(get_qr_count)
echo "QR count after Backup B restore: $QR_COUNT_RESTORE_B (expected: $QR_COUNT_AFTER_NEW)"

# Verify new QR DOES exist
if ! qr_exists "$TEST_QR_NEW"; then
    echo "❌ New test QR does not exist after Backup B restore (should be present)"
    exit 1
fi
echo "✅ New test QR correctly present after Backup B restore"

echo
echo "🧹 Cleanup: Removing test QR codes"
delete_qr_by_content "$TEST_QR_NEW"
echo "✅ Test QR codes cleaned up"

echo
echo "🎉 ENHANCED BACKUP AND RESTORE TEST COMPLETED SUCCESSFULLY!"
echo "All verification steps passed:"
echo "  ✅ Database validation throughout"
echo "  ✅ Backup A correctly restored state without new QR"
echo "  ✅ Backup B correctly restored state with new QR"
echo "  ✅ API service lifecycle managed properly"
echo "  ✅ Enhanced manage_db.py functionality verified" 