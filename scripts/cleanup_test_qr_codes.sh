#!/bin/bash

# QR Code Database Cleanup Script
# Removes test-generated QR codes from the database

set -e

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    source .env
else
    echo "❌ Error: .env file not found. Cannot proceed."
    exit 1
fi

# Check required environment variables
required_vars=("POSTGRES_USER" "POSTGRES_DB")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "❌ Error: Required environment variables are not set:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    exit 1
fi

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 QR Code Database Cleanup Script${NC}"
echo "=================================================="

# Function to get count before cleanup
get_initial_counts() {
    echo -e "${YELLOW}📊 Getting initial database state...${NC}"
    
    TOTAL_BEFORE=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM qr_codes;" | tr -d ' \r\n')
    TEST_PATTERNS=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM qr_codes WHERE title LIKE '%Test%' OR title LIKE '%test%' OR description LIKE '%test%' OR description LIKE '%Test%' OR content LIKE '%test%' OR content LIKE '%Test%';" | tr -d ' \r\n')
    EMPTY_TITLES=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM qr_codes WHERE (title IS NULL OR title = '') AND (description IS NULL OR description = '');" | tr -d ' \r\n')
    
    echo "   Total QR codes: $TOTAL_BEFORE"
    echo "   QR codes with test patterns: $TEST_PATTERNS"
    echo "   QR codes with empty titles/descriptions: $EMPTY_TITLES"
}

# Function to create backup before cleanup
create_safety_backup() {
    echo -e "${YELLOW}💾 Creating safety backup before cleanup...${NC}"
    
    if docker-compose exec api python /app/scripts/manage_db.py --create-backup --with-api-stop; then
        BACKUP_FILE=$(docker-compose exec api find /app/backups -name "qrdb_*.sql" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2- | tr -d '\r\n' | xargs basename || echo "")
        echo -e "${GREEN}✅ Safety backup created: $BACKUP_FILE${NC}"
    else
        echo -e "${RED}❌ Failed to create safety backup${NC}"
        exit 1
    fi
}

# Function to clean up specific test patterns
cleanup_test_patterns() {
    echo -e "${YELLOW}🗑️  Cleaning up test-generated QR codes...${NC}"
    
    # 1. Clean up QR codes with test.example.com
    echo "   Removing QR codes pointing to test.example.com..."
    DELETED_1=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "WITH deleted AS (DELETE FROM qr_codes WHERE content LIKE '%test.example.com%' RETURNING *) SELECT COUNT(*) FROM deleted;" | tr -d ' \r\n')
    echo "   Deleted: $DELETED_1 QR codes"
    
    # 2. Clean up QR codes with test-initial-qr pattern
    echo "   Removing QR codes with test-initial-qr pattern..."
    DELETED_2=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "WITH deleted AS (DELETE FROM qr_codes WHERE content LIKE '%test-initial-qr%' RETURNING *) SELECT COUNT(*) FROM deleted;" | tr -d ' \r\n')
    echo "   Deleted: $DELETED_2 QR codes"
    
    # 3. Clean up QR codes with test-new-qr pattern
    echo "   Removing QR codes with test-new-qr pattern..."
    DELETED_3=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "WITH deleted AS (DELETE FROM qr_codes WHERE content LIKE '%test-new-qr%' RETURNING *) SELECT COUNT(*) FROM deleted;" | tr -d ' \r\n')
    echo "   Deleted: $DELETED_3 QR codes"
    
    # 4. Clean up error-level-test QR codes
    echo "   Removing error-level-test QR codes..."
    DELETED_4=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "WITH deleted AS (DELETE FROM qr_codes WHERE content LIKE '%error-level-test%' RETURNING *) SELECT COUNT(*) FROM deleted;" | tr -d ' \r\n')
    echo "   Deleted: $DELETED_4 QR codes"
    
    # 5. Clean up accessibility-test QR codes
    echo "   Removing accessibility-test QR codes..."
    DELETED_5=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "WITH deleted AS (DELETE FROM qr_codes WHERE content LIKE '%accessibility-test%' RETURNING *) SELECT COUNT(*) FROM deleted;" | tr -d ' \r\n')
    echo "   Deleted: $DELETED_5 QR codes"
    
    # 6. Clean up QR codes with "Test Static QR" titles
    echo "   Removing QR codes with 'Test Static QR' titles..."
    DELETED_6=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "WITH deleted AS (DELETE FROM qr_codes WHERE title LIKE '%Test Static QR%' RETURNING *) SELECT COUNT(*) FROM deleted;" | tr -d ' \r\n')
    echo "   Deleted: $DELETED_6 QR codes"
    
    # 7. Clean up QR codes with "Test Dynamic QR" titles
    echo "   Removing QR codes with 'Test Dynamic QR' titles..."
    DELETED_7=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "WITH deleted AS (DELETE FROM qr_codes WHERE title LIKE '%Test Dynamic QR%' RETURNING *) SELECT COUNT(*) FROM deleted;" | tr -d ' \r\n')
    echo "   Deleted: $DELETED_7 QR codes"
    
    # 8. Clean up QR codes created by test scripts
    echo "   Removing QR codes created by test scripts..."
    DELETED_8=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "WITH deleted AS (DELETE FROM qr_codes WHERE description LIKE '%Created by test script%' RETURNING *) SELECT COUNT(*) FROM deleted;" | tr -d ' \r\n')
    echo "   Deleted: $DELETED_8 QR codes"
    
    # 9. Clean up QR codes with various test patterns in content
    echo "   Removing QR codes with test patterns in content..."
    DELETED_9=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "WITH deleted AS (DELETE FROM qr_codes WHERE content LIKE '%user-agent-test%' OR content LIKE '%background-task-test%' OR content LIKE '%service-test%' OR content LIKE '%rate-limit-test%' RETURNING *) SELECT COUNT(*) FROM deleted;" | tr -d ' \r\n')
    echo "   Deleted: $DELETED_9 QR codes"
    
    # 10. Clean up QR codes with empty titles and descriptions (likely test-generated)
    echo "   Removing QR codes with empty titles and descriptions..."
    DELETED_10=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "WITH deleted AS (DELETE FROM qr_codes WHERE (title IS NULL OR title = '') AND (description IS NULL OR description = '') RETURNING *) SELECT COUNT(*) FROM deleted;" | tr -d ' \r\n')
    echo "   Deleted: $DELETED_10 QR codes"
    
    # Calculate total deleted
    TOTAL_DELETED=$((DELETED_1 + DELETED_2 + DELETED_3 + DELETED_4 + DELETED_5 + DELETED_6 + DELETED_7 + DELETED_8 + DELETED_9 + DELETED_10))
    echo -e "${GREEN}   Total deleted: $TOTAL_DELETED QR codes${NC}"
}

# Function to get final counts
get_final_counts() {
    echo -e "${YELLOW}📊 Getting final database state...${NC}"
    
    TOTAL_AFTER=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM qr_codes;" | tr -d ' \r\n')
    REMAINING_TEST=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM qr_codes WHERE title LIKE '%Test%' OR title LIKE '%test%' OR description LIKE '%test%' OR description LIKE '%Test%' OR content LIKE '%test%' OR content LIKE '%Test%';" | tr -d ' \r\n')
    
    echo "   Total QR codes after cleanup: $TOTAL_AFTER"
    echo "   Remaining QR codes with test patterns: $REMAINING_TEST"
    echo "   QR codes removed: $((TOTAL_BEFORE - TOTAL_AFTER))"
}

# Function to validate database after cleanup
validate_database() {
    echo -e "${YELLOW}✅ Validating database after cleanup...${NC}"
    
    if docker-compose exec api python /app/scripts/manage_db.py --validate; then
        echo -e "${GREEN}✅ Database validation passed${NC}"
    else
        echo -e "${RED}❌ Database validation failed${NC}"
        echo "   Consider restoring from the safety backup: $BACKUP_FILE"
        exit 1
    fi
}

# Main execution
main() {
    echo -e "${YELLOW}Starting QR code database cleanup...${NC}"
    echo ""
    
    # Get initial state
    get_initial_counts
    echo ""
    
    # Create safety backup
    create_safety_backup
    echo ""
    
    # Confirm cleanup
    echo -e "${YELLOW}⚠️  WARNING: This will permanently delete test-generated QR codes!${NC}"
    echo "   Safety backup created: $BACKUP_FILE"
    echo "   Estimated QR codes to be deleted: ~$TEST_PATTERNS"
    echo ""
    read -p "Do you want to proceed with cleanup? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Cleanup cancelled by user${NC}"
        exit 0
    fi
    
    # Perform cleanup
    cleanup_test_patterns
    echo ""
    
    # Get final state
    get_final_counts
    echo ""
    
    # Validate database
    validate_database
    echo ""
    
    echo -e "${GREEN}🎉 QR Code Database Cleanup Completed Successfully!${NC}"
    echo "   Safety backup available: $BACKUP_FILE"
    echo "   Database validated and operational"
}

# Execute main function
main "$@" 