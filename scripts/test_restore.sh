#!/bin/bash

# Enhanced test script for backup and restore functionality
# Implements multi-stage verification logic as per Sub-Task S.1.R4

set -e

# Load environment variables from .env file if it exists (matching test_api_script.sh pattern)
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    source .env
fi

echo "=== ENHANCED BACKUP AND RESTORE TEST ==="
echo "Timestamp: $(date)"
echo "Testing enhanced manage_db.py backup and restore functionality"
echo

# Load environment variables for database credentials
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Function to ensure API service is running
ensure_api_running() {
    echo "🔄 Ensuring API service is running..."
    docker-compose start api > /dev/null 2>&1 || true
    sleep 3
    
    # Wait for API to be healthy using the proper health endpoint
    local max_attempts=10
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        # Use the comprehensive health endpoint that checks database connectivity
        local health_response=$(docker-compose exec api curl -s http://localhost:8000/health 2>/dev/null || echo "")
        local health_status=$(echo "$health_response" | jq -r '.status' 2>/dev/null || echo "unknown")
        local db_status=$(echo "$health_response" | jq -r '.checks.database.status' 2>/dev/null || echo "unknown")
        
        if [ "$health_status" = "healthy" ]; then
            echo "✅ API service is running and healthy (database connectivity verified)"
            return 0
        elif [ "$health_status" = "degraded" ] && [ "$db_status" = "pass" ]; then
            echo "✅ API service is running (degraded but database is operational)"
            echo "   Database status: $db_status"
            return 0
        elif [ "$health_status" = "degraded" ]; then
            echo "⚠️  API service is degraded, checking database status... (attempt $((attempt + 1))/$max_attempts)"
            echo "   Database status: $db_status"
        else
            echo "   Waiting for API service... (attempt $((attempt + 1))/$max_attempts)"
            echo "   Current status: $health_status"
        fi
        
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ API service failed to start properly or database is not operational"
    echo "   Last health status: $health_status"
    echo "   Last database status: $db_status"
    echo "   Full health response:"
    echo "$health_response" | jq . 2>/dev/null || echo "$health_response"
    return 1
}

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

# Function to check if QR exists by ID
qr_exists_by_id() {
    local qr_id="$1"
    local count=$(docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -t -c "SELECT COUNT(*) FROM qr_codes WHERE id = '$qr_id';" 2>/dev/null | tr -d ' \r\n' || echo "0")
    [ "$count" -gt "0" ]
}

# Function to create a test QR code using API (for real-world fidelity)
create_test_qr_api() {
    local qr_type="$1"
    local title="$2"
    local content="$3"
    local redirect_url="$4"
    
    echo "   Creating QR via API (type: $qr_type, title: $title)" >&2
    
    # Load environment variables for API access (matching test_api_script.sh pattern)
    local API_URL=${API_URL:-"https://10.1.6.12"}
    local AUTH_USER=${AUTH_USER:-"admin_user"}
    local AUTH_PASS=${AUTH_PASS:-"strongpassword"}
    local AUTH_HEADER="--user ${AUTH_USER}:${AUTH_PASS}"
    
    echo "   Using API_URL: $API_URL" >&2
    echo "   Using AUTH_USER: $AUTH_USER" >&2
    
    if [ "$qr_type" = "static" ]; then
        local response=$(curl -k -s $AUTH_HEADER -X POST "$API_URL/api/v1/qr/static" \
            -H "Content-Type: application/json" \
            -d "{\"content\": \"$content\", \"title\": \"$title\", \"description\": \"Created by test script via API\"}")
    else
        local response=$(curl -k -s $AUTH_HEADER -X POST "$API_URL/api/v1/qr/dynamic" \
            -H "Content-Type: application/json" \
            -d "{\"redirect_url\": \"$redirect_url\", \"title\": \"$title\", \"description\": \"Created by test script via API\"}")
    fi
    
    # Extract ID from response
    local qr_id=$(echo "$response" | jq -r '.id' 2>/dev/null || echo "")
    
    if [ -n "$qr_id" ] && [ "$qr_id" != "null" ]; then
        echo "   ✅ QR code created via API with ID: $qr_id" >&2
        echo "$qr_id"  # Only the ID goes to stdout
        return 0
    else
        echo "   ❌ Failed to create QR via API" >&2
        echo "   Response: $response" >&2
        echo "   Parsed ID: $qr_id" >&2
        # Try to parse error details
        local error_detail=$(echo "$response" | jq -r '.detail' 2>/dev/null || echo "")
        if [ -n "$error_detail" ] && [ "$error_detail" != "null" ]; then
            echo "   Error detail: $error_detail" >&2
        fi
        return 1
    fi
}

# Function to create a test QR code using direct database insertion (for DB fidelity testing)
create_test_qr_direct() {
    local content="$1"
    local qr_type="${2:-static}"
    local timestamp=$(date -u +"%Y-%m-%d %H:%M:%S")
    
    echo "   Creating QR via direct DB (content: $content, type: $qr_type)" >&2
    
    # Generate a unique ID for the QR code (since id is VARCHAR, not auto-increment)
    local qr_id="test-$(date +%s)-$(shuf -i 1000-9999 -n 1)"
    echo "   Generated QR ID: $qr_id" >&2
    
    # Generate short_id using UUID logic to match API behavior
    local short_id=""
    if [ "$qr_type" = "dynamic" ]; then
        # Use Python to generate UUID-based short_id like the API does
        short_id=$(docker-compose exec api python -c "import uuid; print(str(uuid.uuid4())[:8])" | tr -d '\r\n')
        content="https://web.hccc.edu/r/$short_id"
        echo "   Generated short_id (UUID-based): $short_id, updated content: $content" >&2
    fi
    
    # Insert directly into database with proper escaping and ID
    local sql_command="INSERT INTO qr_codes (id, content, qr_type, redirect_url, created_at, scan_count, last_scan_at, fill_color, back_color, size, border, title, description, short_id) VALUES ('$qr_id', '$content', '$qr_type', $(if [ "$qr_type" = "dynamic" ]; then echo "'https://test.example.com'"; else echo "NULL"; fi), '$timestamp', 0, NULL, '#000000', '#FFFFFF', 10, 4, 'Test QR Code', 'Created by test script via direct DB', $(if [ "$qr_type" = "dynamic" ]; then echo "'$short_id'"; else echo "NULL"; fi));"
    
    echo "   Executing SQL: $sql_command" >&2
    
    if docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -c "$sql_command" >&2; then
        echo "   ✅ QR code inserted successfully with ID: $qr_id" >&2
        echo "$qr_id"  # Only the ID goes to stdout
        return 0
    else
        echo "   ❌ Failed to insert QR code" >&2
        return 1
    fi
}

# Function to delete QR by content using direct database operation
delete_qr_by_content() {
    local content="$1"
    echo "   Attempting to delete QR with content: $content"
    
    # First check if it exists
    local exists_count=$(docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -t -c "SELECT COUNT(*) FROM qr_codes WHERE content = '$content';" 2>/dev/null | tr -d ' \r\n' || echo "0")
    
    if [ "$exists_count" -eq "0" ]; then
        echo "   ⚠️  QR with content '$content' does not exist"
        return 0
    fi
    
    # Delete the QR code
    if docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -c "DELETE FROM qr_codes WHERE content = '$content';" 2>&1; then
        echo "   ✅ Deleted QR with content: $content"
        return 0
    else
        echo "   ❌ Failed to delete QR with content: $content"
        return 1
    fi
}

# Function to delete QR by ID using direct database operation
delete_qr_by_id() {
    local qr_id="$1"
    echo "   Attempting to delete QR with ID: $qr_id"
    
    # First check if it exists
    local exists_count=$(docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -t -c "SELECT COUNT(*) FROM qr_codes WHERE id = '$qr_id';" 2>/dev/null | tr -d ' \r\n' || echo "0")
    
    if [ "$exists_count" -eq "0" ]; then
        echo "   ⚠️  QR with ID '$qr_id' does not exist"
        return 0
    fi
    
    # Delete the QR code
    if docker-compose exec postgres psql -U "${POSTGRES_USER:-pguser}" -d "${POSTGRES_DB:-qrdb}" -c "DELETE FROM qr_codes WHERE id = '$qr_id';" 2>&1; then
        echo "   ✅ Deleted QR with ID: $qr_id"
        return 0
    else
        echo "   ❌ Failed to delete QR with ID: $qr_id"
        return 1
    fi
}

echo "🔍 Step 1: Initial State Validation"
# Ensure API is running for validation
ensure_api_running

# Validate database is okay
if ! docker-compose exec api python /app/scripts/manage_db.py --validate; then
    echo "❌ Initial database validation failed"
    exit 1
fi
echo "✅ Database validation passed"

# Create a known test QR code that we'll delete (using API for real-world fidelity)
TEST_QR_INITIAL="test-initial-qr-$(date +%s)"
echo "Creating initial test QR via API: $TEST_QR_INITIAL"
echo "DEBUG: About to call create_test_qr_api function"
INITIAL_QR_ID=$(create_test_qr_api "static" "Initial Test QR" "$TEST_QR_INITIAL" "")
echo "DEBUG: Function returned, INITIAL_QR_ID='$INITIAL_QR_ID'"

if [ -z "$INITIAL_QR_ID" ]; then
    echo "❌ Failed to create initial test QR via API"
    exit 1
fi

# Verify creation by checking database directly
if ! qr_exists_by_id "$INITIAL_QR_ID"; then
    echo "❌ Initial test QR not found in database after API creation"
    exit 1
fi

# Record initial state
QR_COUNT_BEFORE_TEST=$(get_qr_count)
SCAN_COUNT_BEFORE_TEST=$(get_scan_count)
echo "✅ Initial state: $QR_COUNT_BEFORE_TEST QR codes, $SCAN_COUNT_BEFORE_TEST scan logs"

# Delete the test QR to create a known absence
echo "Deleting initial test QR to create known state"
delete_qr_by_id "$INITIAL_QR_ID"

# Verify deletion
if qr_exists_by_id "$INITIAL_QR_ID"; then
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

# Ensure API is running after backup
ensure_api_running

echo
echo "🔄 Step 3: Change State"
# Create a new, specific QR code using direct DB insertion (tests pure DB backup/restore)
TEST_QR_NEW="test-new-qr-$(date +%s)"
echo "Creating new test QR via direct DB: $TEST_QR_NEW"
NEW_QR_ID=$(create_test_qr_direct "$TEST_QR_NEW")

if [ -z "$NEW_QR_ID" ]; then
    echo "❌ Failed to create new test QR via direct DB"
    exit 1
fi

# Verify new QR exists
if ! qr_exists "$TEST_QR_NEW"; then
    echo "❌ Failed to create new test QR"
    exit 1
fi
echo "✅ New test QR created successfully via direct DB"

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

# Ensure API is running after backup
ensure_api_running

echo
echo "🔄 Step 5: Restore Backup A"
echo "Restoring from Backup A: $BACKUP_A_FILENAME"
if docker-compose exec api python /app/scripts/manage_db.py --restore "$BACKUP_A_FILENAME" --with-api-stop; then
    echo "✅ Backup A restore completed"
else
    echo "❌ Backup A restore failed"
    exit 1
fi

# Ensure API is running after restore
ensure_api_running

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
if qr_exists_by_id "$INITIAL_QR_ID"; then
    echo "❌ Initial test QR still exists after Backup A restore (should be absent)"
    exit 1
fi
echo "✅ Initial test QR correctly absent after Backup A restore"

echo
echo "🔄 Step 7: Restore Backup B"
echo "Restoring from Backup B: $BACKUP_B_FILENAME"
if docker-compose exec api python /app/scripts/manage_db.py --restore "$BACKUP_B_FILENAME" --with-api-stop; then
    echo "✅ Backup B restore completed"
else
    echo "❌ Backup B restore failed"
    exit 1
fi

# Ensure API is running after restore
ensure_api_running

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

# Verify initial QR is still absent (it was deleted before Backup A)
if qr_exists_by_id "$INITIAL_QR_ID"; then
    echo "❌ Initial test QR exists after Backup B restore (should still be absent)"
    exit 1
fi
echo "✅ Initial test QR correctly absent after Backup B restore"

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