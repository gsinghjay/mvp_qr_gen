#!/bin/bash

# Supplementary QR Code Cleanup Script
# Removes remaining specific test QR codes from the database

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

echo -e "${BLUE}🧹 Supplementary QR Code Cleanup Script${NC}"
echo "=================================================="

# Function to show remaining test QR codes
show_remaining_test_qr_codes() {
    echo -e "${YELLOW}📊 Remaining test QR codes in database:${NC}"
    
    REMAINING_COUNT=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM qr_codes WHERE title LIKE '%Test%' OR title LIKE '%test%' OR description LIKE '%test%' OR description LIKE '%Test%' OR content LIKE '%test%' OR content LIKE '%Test%';" | tr -d ' \r\n')
    echo "   Total remaining test QR codes: $REMAINING_COUNT"
    echo ""
    
    echo -e "${YELLOW}Sample of remaining test QR codes:${NC}"
    docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT title, description, LEFT(content, 50) as content_preview FROM qr_codes WHERE title LIKE '%Test%' OR title LIKE '%test%' OR description LIKE '%test%' OR description LIKE '%Test%' OR content LIKE '%test%' OR content LIKE '%Test%' ORDER BY created_at DESC LIMIT 15;" | cat
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

# Function to clean up remaining specific test patterns
cleanup_remaining_test_patterns() {
    echo -e "${YELLOW}🗑️  Cleaning up remaining specific test QR codes...${NC}"
    
    # 1. Clean up QR codes with specific test titles
    echo "   Removing QR codes with specific test titles..."
    DELETED_1=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "WITH deleted AS (DELETE FROM qr_codes WHERE title LIKE '%Rate Limit Test%' OR title LIKE '%Performance Test%' OR title LIKE '%Background Task%' OR title LIKE '%User Agent%' OR title LIKE '%Case Test%' OR title LIKE '%Restore Test%' RETURNING *) SELECT COUNT(*) FROM deleted;" | tr -d ' \r\n')
    echo "   Deleted: $DELETED_1 QR codes"
    
    # 2. Clean up QR codes with test descriptions
    echo "   Removing QR codes with test descriptions..."
    DELETED_2=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "WITH deleted AS (DELETE FROM qr_codes WHERE description LIKE '%Testing%' OR description LIKE '%test%' OR description LIKE '%Test%' RETURNING *) SELECT COUNT(*) FROM deleted;" | tr -d ' \r\n')
    echo "   Deleted: $DELETED_2 QR codes"
    
    # 3. Clean up QR codes with "Test" in title (case insensitive)
    echo "   Removing remaining QR codes with 'Test' in title..."
    DELETED_3=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "WITH deleted AS (DELETE FROM qr_codes WHERE title ILIKE '%test%' RETURNING *) SELECT COUNT(*) FROM deleted;" | tr -d ' \r\n')
    echo "   Deleted: $DELETED_3 QR codes"
    
    # 4. Clean up QR codes with test content patterns
    echo "   Removing QR codes with test content patterns..."
    DELETED_4=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "WITH deleted AS (DELETE FROM qr_codes WHERE content LIKE '%Test%' OR content LIKE '%test%' RETURNING *) SELECT COUNT(*) FROM deleted;" | tr -d ' \r\n')
    echo "   Deleted: $DELETED_4 QR codes"
    
    # Calculate total deleted
    TOTAL_DELETED=$((DELETED_1 + DELETED_2 + DELETED_3 + DELETED_4))
    echo -e "${GREEN}   Total deleted: $TOTAL_DELETED QR codes${NC}"
}

# Function to get final counts
get_final_counts() {
    echo -e "${YELLOW}📊 Getting final database state...${NC}"
    
    TOTAL_AFTER=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM qr_codes;" | tr -d ' \r\n')
    REMAINING_TEST=$(docker-compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM qr_codes WHERE title LIKE '%Test%' OR title LIKE '%test%' OR description LIKE '%test%' OR description LIKE '%Test%' OR content LIKE '%test%' OR content LIKE '%Test%';" | tr -d ' \r\n')
    
    echo "   Total QR codes after cleanup: $TOTAL_AFTER"
    echo "   Remaining QR codes with test patterns: $REMAINING_TEST"
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
    echo -e "${YELLOW}Starting supplementary QR code database cleanup...${NC}"
    echo ""
    
    # Show what we're working with
    show_remaining_test_qr_codes
    echo ""
    
    # Create safety backup
    create_safety_backup
    echo ""
    
    # Confirm cleanup
    echo -e "${YELLOW}⚠️  WARNING: This will delete the remaining test QR codes shown above!${NC}"
    echo "   Safety backup created: $BACKUP_FILE"
    echo ""
    read -p "Do you want to proceed with cleanup? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Cleanup cancelled by user${NC}"
        exit 0
    fi
    
    # Perform cleanup
    cleanup_remaining_test_patterns
    echo ""
    
    # Get final state
    get_final_counts
    echo ""
    
    # Validate database
    validate_database
    echo ""
    
    echo -e "${GREEN}🎉 Supplementary QR Code Cleanup Completed Successfully!${NC}"
    echo "   Safety backup available: $BACKUP_FILE"
    echo "   Database validated and operational"
}

# Execute main function
main "$@" 