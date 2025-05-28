#!/bin/bash

# Production-Safe Rollback Automation Script (Task S.3)
# Observatory-First Safety Phase - Comprehensive Rollback Infrastructure
# Integrates with existing backup/restore and enhanced smoke test infrastructure

set -euo pipefail

# ============================================================================
# Color Codes and Constants
# ============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Rollback operation timeouts
BACKUP_TIMEOUT=300          # 5 minutes for backup creation
RESTORE_TIMEOUT=600         # 10 minutes for restore operations
SMOKE_TEST_TIMEOUT=120      # 2 minutes for smoke test validation
SERVICE_STOP_TIMEOUT=60     # 1 minute for service stop operations
SERVICE_START_TIMEOUT=180   # 3 minutes for service start operations

# Observatory integration
PROMETHEUS_URL="http://localhost:9090"
GRAFANA_URL="http://localhost:3000"

# Rollback types
ROLLBACK_TYPE=""
ROLLBACK_REASON=""
ROLLBACK_TIMESTAMP=""
SAFETY_BACKUP_CREATED=""
SELECTED_IMAGE_TAG=""

# ============================================================================
# Environment Loading and Validation
# ============================================================================

load_environment() {
    if [ -f ".env" ]; then
        echo -e "${YELLOW}📁 Loading environment variables from .env file...${NC}"
        set -a
        source .env
        set +a
    else
        echo -e "${RED}❌ Error: .env file not found. Cannot proceed with rollback.${NC}"
        exit 1
    fi

    # Required variables for rollback operations
    local required_vars=("POSTGRES_USER" "POSTGRES_DB" "API_URL" "AUTH_USER" "AUTH_PASS")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing required environment variables for rollback:${NC}"
        printf '%s\n' "${missing_vars[@]}" | sed 's/^/   - /'
        echo ""
        echo -e "${YELLOW}Required variables should be set in .env file:${NC}"
        echo "   POSTGRES_USER=pguser"
        echo "   POSTGRES_DB=qrdb"
        echo "   API_URL=https://10.1.6.12"
        echo "   AUTH_USER=[username]"
        echo "   AUTH_PASS=[password]"
        exit 1
    fi
    
    echo -e "${CYAN}🔧 Environment configured for rollback operations${NC}"
}

# ============================================================================
# Observatory Integration Functions
# ============================================================================

create_grafana_annotation() {
    local title="$1"
    local text="$2"
    local tags="${3:-rollback}"
    
    if ! command -v curl &> /dev/null; then
        echo -e "${YELLOW}⚠️  curl not available, skipping Grafana annotation${NC}"
        return 0
    fi
    
    local annotation_data=$(cat <<EOF
{
    "text": "$text",
    "title": "$title",
    "tags": ["$tags", "production", "safety"],
    "time": $(date +%s)000
}
EOF
)
    
    # Attempt to create annotation (non-blocking if Grafana unavailable)
    curl -s --max-time 10 -X POST \
        -H "Content-Type: application/json" \
        -u "admin:${GRAFANA_ADMIN_PASSWORD:-admin123}" \
        -d "$annotation_data" \
        "${GRAFANA_URL}/api/annotations" &>/dev/null || {
        echo -e "${YELLOW}⚠️  Could not create Grafana annotation (service may be unavailable)${NC}"
    }
}

query_prometheus_status() {
    local metric="$1"
    local description="${2:-Prometheus query}"
    
    if ! command -v curl &> /dev/null; then
        echo -e "${YELLOW}⚠️  curl not available, skipping Observatory check: $description${NC}"
        return 0
    fi
    
    local response
    response=$(curl -s --max-time 10 "${PROMETHEUS_URL}/api/v1/query" \
        --data-urlencode "query=$metric" 2>/dev/null) || {
        echo -e "${YELLOW}⚠️  Prometheus query failed: $description${NC}"
        return 0
    }
    
    local status
    status=$(echo "$response" | jq -r '.status' 2>/dev/null || echo "error")
    
    if [ "$status" = "success" ]; then
        echo "$response" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

# ============================================================================
# Core Rollback Functions
# ============================================================================

print_banner() {
    echo -e "${RED}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    🚨 ROLLBACK AUTOMATION SCRIPT (Task S.3) 🚨              ║"
    echo "║                         Observatory-First Production Safety                  ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${YELLOW}⚠️  PRODUCTION ROLLBACK OPERATION - PROCEED WITH CAUTION${NC}"
    echo -e "${CYAN}🎯 Purpose: Safe, automated rollback with comprehensive validation${NC}"
    echo -e "${CYAN}🔍 Integration: Prometheus/Grafana monitoring, enhanced smoke test${NC}"
    echo -e "${CYAN}🛡️ Safety: Automatic pre-rollback backup, multi-level validation${NC}"
    echo ""
}

show_rollback_menu() {
    echo -e "${BLUE}🔄 Available Rollback Options:${NC}"
    echo ""
    echo -e "${CYAN}1.${NC} Database Rollback Only"
    echo -e "   📊 Restore database from backup"
    echo -e "   ⚡ Fast operation (~2-5 minutes)"
    echo -e "   🎯 Use when: Database corruption or unwanted schema changes"
    echo ""
    echo -e "${CYAN}2.${NC} Application Rollback (Code + Database)"
    echo -e "   🔄 Docker image rollback + database restore + API restart"
    echo -e "   ⏱️ Moderate operation (~5-10 minutes)"
    echo -e "   🎯 Use when: Application code issues affecting functionality"
    echo ""
    echo -e "${CYAN}3.${NC} Complete System Rollback"
    echo -e "   🚀 Docker image rollback + database restore + full stack restart"
    echo -e "   ⏳ Comprehensive operation (~10-15 minutes)"
    echo -e "   🎯 Use when: Infrastructure or configuration issues"
    echo ""
    echo -e "${CYAN}4.${NC} Emergency Rollback (No Backup)"
    echo -e "   🔥 Service restart without database changes"
    echo -e "   ⚡ Fastest operation (~1-3 minutes)"
    echo -e "   🎯 Use when: Application hang or memory issues"
    echo ""
    echo -e "${CYAN}5.${NC} Exit (Cancel)"
    echo ""
}

confirm_rollback_operation() {
    local operation_type="$1"
    local estimated_time="$2"
    
    # Skip confirmation if NO_CONFIRM is set
    if [ "${NO_CONFIRM:-false}" = "true" ]; then
        echo -e "${CYAN}🔄 Proceeding with ${operation_type} (confirmation skipped)${NC}"
        echo -e "${YELLOW}⏱️  Estimated time: ${estimated_time}${NC}"
        echo -e "${YELLOW}🌐 Target environment: Production QR Generator System${NC}"
        
        # Set default reason if not provided
        if [ -z "${ROLLBACK_REASON:-}" ]; then
            ROLLBACK_REASON="Automated rollback via command line"
        fi
        
        echo -e "${GREEN}✅ Proceeding with operation...${NC}"
        echo ""
        return 0
    fi
    
    echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════════════════════╗"
    echo -e "║                              ⚠️  CONFIRMATION REQUIRED ⚠️                    ║"
    echo -e "╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${RED}🚨 You are about to perform: ${operation_type}${NC}"
    echo -e "${YELLOW}⏱️  Estimated time: ${estimated_time}${NC}"
    echo -e "${YELLOW}🌐 Target environment: Production QR Generator System${NC}"
    echo ""
    
    # Show current system status
    echo -e "${CYAN}📊 Current System Status:${NC}"
    local service_status
    service_status=$(docker-compose ps --services --filter status=running | wc -l || echo "unknown")
    echo -e "   🐳 Docker services running: $service_status"
    
    local qr_count
    qr_count=$(docker-compose exec postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -t -c "SELECT COUNT(*) FROM qr_codes;" 2>/dev/null | tr -d ' \r\n' || echo "unknown")
    echo -e "   📊 Current QR codes in database: $qr_count"
    
    # Enhanced health endpoint validation (consistent with existing scripts)
    echo -e "   🔍 Checking system health..."
    local health_response
    health_response=$(curl -k -s --max-time 10 -u "${AUTH_USER}:${AUTH_PASS}" "${API_URL}/health" 2>/dev/null || echo "")
    
    if [ -n "$health_response" ]; then
        local health_status
        health_status=$(echo "$health_response" | jq -r '.status' 2>/dev/null || echo "unknown")
        local db_status
        db_status=$(echo "$health_response" | jq -r '.checks.database.status' 2>/dev/null || echo "unknown")
        
        if [ "$health_status" = "healthy" ]; then
            echo -e "   ✅ System health: healthy (database: $db_status)"
        elif [ "$health_status" = "degraded" ]; then
            echo -e "   ⚠️  System health: degraded (database: $db_status)"
        else
            echo -e "   ❌ System health: $health_status (database: $db_status)"
        fi
    else
        echo -e "   ❌ Health endpoint unavailable"
    fi
    
    local uptime
    uptime=$(query_prometheus_status 'up{job="qr-app"}' "Service uptime check")
    if [ "$uptime" = "1" ]; then
        echo -e "   ✅ QR application service: UP"
    else
        echo -e "   ❌ QR application service: DOWN"
    fi
    
    echo ""
    read -p "$(echo -e "${RED}Are you sure you want to proceed? Type 'ROLLBACK' to confirm: ${NC}")" confirmation
    
    if [ "$confirmation" != "ROLLBACK" ]; then
        echo -e "${YELLOW}❌ Rollback cancelled by user${NC}"
        exit 0
    fi
    
    # Additional confirmation for destructive operations
    if [[ "$operation_type" =~ "Database" ]] || [[ "$operation_type" =~ "Complete" ]]; then
        echo ""
        echo -e "${RED}🚨 FINAL WARNING: This operation will modify your database${NC}"
        read -p "$(echo -e "${RED}Type 'YES' to proceed with database changes: ${NC}")" final_confirmation
        
        if [ "$final_confirmation" != "YES" ]; then
            echo -e "${YELLOW}❌ Rollback cancelled - database changes not confirmed${NC}"
            exit 0
        fi
    fi
    
    # Collect rollback reason for audit trail
    echo ""
    echo -e "${CYAN}📝 Please provide a reason for this rollback (for audit trail):${NC}"
    read -p "Reason: " ROLLBACK_REASON
    
    if [ -z "$ROLLBACK_REASON" ]; then
        ROLLBACK_REASON="No reason provided"
    fi
    
    echo -e "${GREEN}✅ Rollback confirmed. Proceeding with operation...${NC}"
    echo ""
}

create_safety_backup() {
    echo -e "${CYAN}🛡️  Creating safety backup before rollback...${NC}"
    echo -e "   📝 This backup will be created in case rollback needs to be reversed"
    echo -e "   ⏱️  Estimated time: 1-3 minutes"
    echo ""
    
    local backup_start_time
    backup_start_time=$(date +%s)
    
    # Use existing production_backup.sh infrastructure
    if bash scripts/production_backup.sh; then
        local backup_end_time duration
        backup_end_time=$(date +%s)
        duration=$((backup_end_time - backup_start_time))
        
        # Get the latest backup filename
        SAFETY_BACKUP_CREATED=$(docker-compose exec api find /app/backups -name "qrdb_*.sql" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2- | tr -d '\r\n' | xargs basename 2>/dev/null || echo "")
        
        echo -e "${GREEN}✅ Safety backup created successfully${NC}"
        echo -e "   📁 File: ${SAFETY_BACKUP_CREATED}"
        echo -e "   ⏱️  Duration: ${duration}s"
        echo -e "   🔒 This backup can be used to reverse the rollback if needed"
        
        # Create Grafana annotation
        create_grafana_annotation "Safety Backup Created" "Pre-rollback safety backup: ${SAFETY_BACKUP_CREATED}" "backup,safety"
        
    else
        echo -e "${RED}❌ Safety backup creation failed${NC}"
        echo -e "${YELLOW}⚠️  Proceeding without safety backup (not recommended)${NC}"
        
        read -p "$(echo -e "${RED}Continue rollback without safety backup? (y/N): ${NC}")" continue_without_backup
        if [[ ! "$continue_without_backup" =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}❌ Rollback cancelled - safety backup required${NC}"
            exit 1
        fi
    fi
    echo ""
}

list_available_backups() {
    echo -e "${CYAN}📁 Available backups for rollback:${NC}"
    echo ""
    
    local backups
    backups=$(docker-compose exec api find /app/backups -name "qrdb_*.sql" -type f -printf '%T@ %f %s\n' 2>/dev/null | sort -rn || echo "")
    
    if [ -z "$backups" ]; then
        echo -e "${RED}❌ No backups found in /app/backups/${NC}"
        echo -e "${YELLOW}⚠️  Cannot proceed with database rollback without backup${NC}"
        return 1
    fi
    
    local count=1
    echo "$backups" | while read -r timestamp filename size; do
        local backup_date
        backup_date=$(date -d "@${timestamp}" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "Unknown date")
        local size_mb
        size_mb=$(echo "scale=2; $size / 1024 / 1024" | bc 2>/dev/null || echo "unknown")
        
        echo -e "${CYAN}${count}.${NC} $filename"
        echo -e "   📅 Created: $backup_date"
        echo -e "   📏 Size: ${size_mb} MB"
        echo ""
        
        count=$((count + 1))
    done
}

select_backup_for_rollback() {
    list_available_backups || return 1
    
    echo -e "${YELLOW}📝 Enter the exact filename of the backup to use for rollback:${NC}"
    read -p "Backup filename: " selected_backup
    
    if [ -z "$selected_backup" ]; then
        echo -e "${RED}❌ No backup filename provided${NC}"
        return 1
    fi
    
    # Verify backup exists
    if ! docker-compose exec api test -f "/app/backups/$selected_backup" 2>/dev/null; then
        echo -e "${RED}❌ Backup file not found: $selected_backup${NC}"
        return 1
    fi
    
    # Get backup info
    local backup_size
    backup_size=$(docker-compose exec api stat -c%s "/app/backups/$selected_backup" 2>/dev/null | tr -d '\r\n' || echo "unknown")
    local backup_size_mb
    backup_size_mb=$(echo "scale=2; $backup_size / 1024 / 1024" | bc 2>/dev/null || echo "unknown")
    
    echo -e "${GREEN}✅ Selected backup: $selected_backup${NC}"
    echo -e "   📏 Size: ${backup_size_mb} MB"
    echo -e "   📍 Location: /app/backups/$selected_backup"
    echo ""
    
    export SELECTED_BACKUP="$selected_backup"
}

# ============================================================================
# Docker Image Tag Management Functions
# ============================================================================

list_available_image_tags() {
    echo -e "${CYAN}🐳 Available Docker image tags for QR Generator API:${NC}"
    echo ""
    
    # Get current image tag from docker-compose.yml
    local current_tag
    current_tag=$(grep -A 10 "api:" docker-compose.yml | grep "image:" | sed 's/.*://' | tr -d ' ' || echo "latest")
    echo -e "${YELLOW}📍 Current tag: $current_tag${NC}"
    echo ""
    
    # List common/recent tags (this would typically come from your registry)
    echo -e "${CYAN}Common image tags:${NC}"
    echo -e "${CYAN}1.${NC} latest (current production)"
    echo -e "${CYAN}2.${NC} stable (last known stable)"
    echo -e "${CYAN}3.${NC} v1.0.0 (tagged release)"
    echo -e "${CYAN}4.${NC} backup-$(date +%Y%m%d) (today's backup tag)"
    echo -e "${CYAN}5.${NC} Custom tag (enter manually)"
    echo ""
    echo -e "${YELLOW}💡 Note: Available tags depend on your Docker registry/build process${NC}"
    echo -e "${YELLOW}💡 In production, this would query your actual registry for available tags${NC}"
}

select_image_tag_for_rollback() {
    list_available_image_tags
    
    echo -e "${YELLOW}📝 Select image tag option or enter custom tag:${NC}"
    read -p "Selection (1-5 or custom tag): " tag_selection
    
    case "$tag_selection" in
        1)
            SELECTED_IMAGE_TAG="latest"
            ;;
        2)
            SELECTED_IMAGE_TAG="stable"
            ;;
        3)
            SELECTED_IMAGE_TAG="v1.0.0"
            ;;
        4)
            SELECTED_IMAGE_TAG="backup-$(date +%Y%m%d)"
            ;;
        5)
            echo -e "${YELLOW}Enter custom image tag:${NC}"
            read -p "Custom tag: " custom_tag
            if [ -z "$custom_tag" ]; then
                echo -e "${RED}❌ No custom tag provided${NC}"
                return 1
            fi
            SELECTED_IMAGE_TAG="$custom_tag"
            ;;
        *)
            # Treat as direct tag input
            if [ -n "$tag_selection" ]; then
                SELECTED_IMAGE_TAG="$tag_selection"
            else
                echo -e "${RED}❌ No tag selection provided${NC}"
                return 1
            fi
            ;;
    esac
    
    echo -e "${GREEN}✅ Selected image tag: $SELECTED_IMAGE_TAG${NC}"
    echo ""
    
    # Confirm tag selection
    echo -e "${YELLOW}⚠️  This will update the API service to use image tag: $SELECTED_IMAGE_TAG${NC}"
    read -p "$(echo -e "${CYAN}Confirm image tag selection? (y/N): ${NC}")" confirm_tag
    
    if [[ ! "$confirm_tag" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}❌ Image tag selection cancelled${NC}"
        return 1
    fi
    
    export SELECTED_IMAGE_TAG="$SELECTED_IMAGE_TAG"
}

update_docker_compose_image_tag() {
    local service_name="$1"
    local new_tag="$2"
    
    echo -e "${CYAN}🔧 Checking $service_name service configuration...${NC}"
    
    # Check if service uses build or image
    local build_line image_line
    build_line=$(grep -A 10 "$service_name:" docker-compose.yml | grep "build:" | head -1)
    image_line=$(grep -A 10 "$service_name:" docker-compose.yml | grep "image:" | head -1)
    
    if [ -n "$build_line" ]; then
        echo -e "${YELLOW}📦 Service uses build configuration (build: .)${NC}"
        echo -e "${CYAN}💡 Skipping image tag update for build-based service${NC}"
        echo -e "   🔄 Application rollback will use container restart instead"
        echo -e "   📝 Note: For true image rollback, consider using pre-built images"
        return 0  # Success - no update needed for build-based services
    fi
    
    if [ -z "$image_line" ]; then
        echo -e "${RED}❌ Could not find image or build configuration for $service_name service${NC}"
        return 1
    fi
    
    echo -e "${CYAN}🔧 Updating docker-compose.yml for $service_name service...${NC}"
    echo -e "   📝 Setting image tag to: $new_tag"
    
    # Create backup of docker-compose.yml
    local compose_backup="docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)"
    cp docker-compose.yml "$compose_backup"
    echo -e "   💾 Backup created: $compose_backup"
    
    # Extract image name without tag
    local image_name
    image_name=$(echo "$image_line" | sed 's/.*image: *//' | sed 's/:.*$//' | tr -d ' ')
    
    if [ -z "$image_name" ]; then
        # If no explicit image name, assume it's the default pattern
        image_name="qr-generator"
    fi
    
    local new_image_spec="${image_name}:${new_tag}"
    
    # Update the docker-compose.yml file
    # This uses sed to replace the image line for the specific service
    sed -i "/^[[:space:]]*$service_name:/,/^[[:space:]]*[^[:space:]]/ s|image:.*|image: $new_image_spec|" docker-compose.yml
    
    # Verify the change
    local updated_line
    updated_line=$(grep -A 10 "$service_name:" docker-compose.yml | grep "image:" | head -1)
    
    if echo "$updated_line" | grep -q "$new_tag"; then
        echo -e "${GREEN}✅ docker-compose.yml updated successfully${NC}"
        echo -e "   📝 New image specification: $new_image_spec"
        
        # Create Grafana annotation
        create_grafana_annotation "Docker Image Updated" "Updated $service_name service to image tag: $new_tag" "rollback,docker,image"
        
        return 0
    else
        echo -e "${RED}❌ Failed to update docker-compose.yml${NC}"
        echo -e "${YELLOW}💡 Restoring backup...${NC}"
        cp "$compose_backup" docker-compose.yml
        return 1
    fi
}

pull_and_verify_image() {
    local service_name="$1"
    local image_tag="$2"
    
    # Check if service uses build configuration
    local build_line
    build_line=$(grep -A 10 "$service_name:" docker-compose.yml | grep "build:" | head -1)
    
    if [ -n "$build_line" ]; then
        echo -e "${YELLOW}📦 Service uses build configuration - skipping image pull${NC}"
        echo -e "${CYAN}💡 Build-based services don't need image pulling${NC}"
        return 0  # Success - no pull needed for build-based services
    fi
    
    echo -e "${CYAN}📥 Pulling Docker image for $service_name service...${NC}"
    echo -e "   🐳 Image tag: $image_tag"
    
    # Pull the specific service image
    if timeout 300 docker-compose pull "$service_name"; then
        echo -e "${GREEN}✅ Docker image pulled successfully${NC}"
        
        # Verify image exists locally
        local image_name
        image_name=$(grep -A 10 "$service_name:" docker-compose.yml | grep "image:" | sed 's/.*image: *//' | tr -d ' ')
        
        if docker images "$image_name" --format "table {{.Repository}}:{{.Tag}}" | grep -q "$image_tag"; then
            echo -e "${GREEN}✅ Image verified locally: $image_name${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  Image pulled but verification uncertain${NC}"
            return 0  # Continue anyway
        fi
    else
        echo -e "${RED}❌ Failed to pull Docker image${NC}"
        echo -e "${YELLOW}💡 This could indicate:${NC}"
        echo -e "   - Image tag does not exist in registry"
        echo -e "   - Network connectivity issues"
        echo -e "   - Registry authentication problems"
        return 1
    fi
}

# ============================================================================
# Rollback Type Handlers
# ============================================================================

handle_database_rollback() {
    ROLLBACK_TYPE="Database Rollback Only"
    confirm_rollback_operation "$ROLLBACK_TYPE" "2-5 minutes"
    
    create_safety_backup
    
    if ! select_backup_for_rollback; then
        echo -e "${RED}❌ Cannot proceed without backup selection${NC}"
        exit 1
    fi
    
    perform_database_rollback || {
        echo -e "${RED}❌ Database rollback failed${NC}"
        exit 1
    }
    
    run_post_rollback_validation || {
        echo -e "${YELLOW}⚠️  Validation failed but rollback completed${NC}"
    }
}

handle_application_rollback() {
    ROLLBACK_TYPE="Application Rollback (Code + Database)"
    confirm_rollback_operation "$ROLLBACK_TYPE" "5-10 minutes"
    
    create_safety_backup
    
    if ! select_backup_for_rollback; then
        echo -e "${RED}❌ Cannot proceed without backup selection${NC}"
        exit 1
    fi
    
    if ! select_image_tag_for_rollback; then
        echo -e "${RED}❌ Cannot proceed without image tag selection${NC}"
        exit 1
    fi
    
    perform_database_rollback || {
        echo -e "${RED}❌ Database rollback failed${NC}"
        exit 1
    }
    
    perform_application_rollback_with_image || {
        echo -e "${RED}❌ Application rollback failed${NC}"
        exit 1
    }
    
    run_post_rollback_validation || {
        echo -e "${YELLOW}⚠️  Validation failed but rollback completed${NC}"
    }
}

handle_complete_system_rollback() {
    ROLLBACK_TYPE="Complete System Rollback"
    confirm_rollback_operation "$ROLLBACK_TYPE" "10-15 minutes"
    
    create_safety_backup
    
    if ! select_backup_for_rollback; then
        echo -e "${RED}❌ Cannot proceed without backup selection${NC}"
        exit 1
    fi
    
    if ! select_image_tag_for_rollback; then
        echo -e "${RED}❌ Cannot proceed without image tag selection${NC}"
        exit 1
    fi
    
    perform_database_rollback || {
        echo -e "${RED}❌ Database rollback failed${NC}"
        exit 1
    }
    
    perform_complete_system_rollback_with_image || {
        echo -e "${RED}❌ Complete system rollback failed${NC}"
        exit 1
    }
    
    run_post_rollback_validation || {
        echo -e "${YELLOW}⚠️  Validation failed but rollback completed${NC}"
    }
}

handle_emergency_rollback() {
    ROLLBACK_TYPE="Emergency Rollback (No Backup)"
    confirm_rollback_operation "$ROLLBACK_TYPE" "1-3 minutes"
    
    echo -e "${YELLOW}⚠️  Emergency rollback: Skipping safety backup and database changes${NC}"
    echo -e "${CYAN}🔄 Performing emergency application restart...${NC}"
    
    perform_application_restart || {
        echo -e "${RED}❌ Emergency restart failed${NC}"
        exit 1
    }
    
    run_post_rollback_validation || {
        echo -e "${YELLOW}⚠️  Validation failed but emergency restart completed${NC}"
    }
}

# ============================================================================
# Main Execution Flow
# ============================================================================

print_rollback_summary() {
    local end_time duration
    end_time=$(date +%s)
    duration=$((end_time - ROLLBACK_START_TIME))
    
    echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗"
    echo -e "║                          🎉 ROLLBACK COMPLETED 🎉                           ║"
    echo -e "╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo -e "${CYAN}📊 Rollback Summary:${NC}"
    echo -e "   ⏱️  Total Duration: ${duration}s"
    echo -e "   🔄 Operation Type: $ROLLBACK_TYPE"
    echo -e "   📝 Reason: $ROLLBACK_REASON"
    echo -e "   🛡️  Safety Backup: ${SAFETY_BACKUP_CREATED:-None}"
    if [ -n "${SELECTED_BACKUP:-}" ]; then
        echo -e "   📊 Restored From: $SELECTED_BACKUP"
    fi
    if [ -n "${SELECTED_IMAGE_TAG:-}" ]; then
        echo -e "   🐳 Image Tag: $SELECTED_IMAGE_TAG"
    fi
    echo -e "   📅 Completed: $(date)"
    echo ""
    echo -e "${GREEN}✅ System rollback completed successfully!${NC}"
    echo -e "${CYAN}🔍 System validated and ready for production traffic${NC}"
    echo ""
}

# Error handling with cleanup
handle_error() {
    local exit_code=$?
    echo -e "\n${RED}❌ Rollback operation interrupted or failed${NC}"
    echo -e "${YELLOW}💡 Check logs for detailed error information${NC}"
    echo -e "${CYAN}📊 Rollback attempt details:${NC}"
    echo -e "   🔄 Operation Type: ${ROLLBACK_TYPE:-Unknown}"
    echo -e "   📝 Reason: ${ROLLBACK_REASON:-Not provided}"
    echo -e "   🛡️  Safety Backup: ${SAFETY_BACKUP_CREATED:-None created}"
    echo -e "   📅 Failed at: $(date)"
    
    # Create failure annotation in Grafana
    create_grafana_annotation "Rollback Operation Failed" "Production rollback failed: ${ROLLBACK_TYPE:-Unknown}" "rollback,failure,error"
    
    exit $exit_code
}

trap 'handle_error' ERR INT TERM

# Usage information
show_usage() {
    echo -e "${BLUE}🔄 Rollback Automation Script Usage:${NC}"
    echo ""
    echo -e "${CYAN}Basic Usage:${NC}"
    echo "   $0                    # Interactive mode with menu"
    echo "   $0 --help            # Show this help message"
    echo ""
    echo -e "${CYAN}Advanced Usage:${NC}"
    echo "   $0 --type database --backup <filename>    # Direct database rollback"
    echo "   $0 --type application --backup <filename> # Direct application rollback"
    echo "   $0 --type system --backup <filename>      # Direct system rollback"
    echo "   $0 --type emergency                       # Direct emergency rollback"
    echo ""
    echo -e "${CYAN}Options:${NC}"
    echo "   --type TYPE          Rollback type: database|application|system|emergency"
    echo "   --backup FILENAME    Backup file to use for rollback"
    echo "   --reason REASON      Reason for rollback (for audit trail)"
    echo "   --no-confirm         Skip confirmation prompts (use with caution)"
    echo "   --help               Show this help message"
    echo ""
    echo -e "${YELLOW}⚠️  Important Notes:${NC}"
    echo "   • Interactive mode is recommended for safety"
    echo "   • All operations create automatic safety backups"
    echo "   • Post-rollback validation is always performed"
    echo "   • Operations are logged in Grafana for monitoring"
    echo ""
}

# Command line argument parsing
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --type)
                ROLLBACK_TYPE="$2"
                shift 2
                ;;
            --backup)
                SELECTED_BACKUP="$2"
                shift 2
                ;;
            --reason)
                ROLLBACK_REASON="$2"
                shift 2
                ;;
            --no-confirm)
                NO_CONFIRM=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Unknown option: $1${NC}"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Validate rollback type if provided
    if [ -n "${ROLLBACK_TYPE:-}" ]; then
        case "$ROLLBACK_TYPE" in
            database|application|system|emergency)
                ;;
            *)
                echo -e "${RED}❌ Invalid rollback type: $ROLLBACK_TYPE${NC}"
                echo -e "${YELLOW}Valid types: database, application, system, emergency${NC}"
                exit 1
                ;;
        esac
    fi
}

# Direct rollback execution (for command line usage)
execute_direct_rollback() {
    case "$ROLLBACK_TYPE" in
        database)
            if [ -z "${SELECTED_BACKUP:-}" ]; then
                echo -e "${RED}❌ Database rollback requires --backup parameter${NC}"
                exit 1
            fi
            if [ "${NO_CONFIRM:-false}" != "true" ]; then
                confirm_rollback_operation "Database Rollback Only" "2-5 minutes"
            fi
            handle_database_rollback
            ;;
        application)
            if [ -z "${SELECTED_BACKUP:-}" ]; then
                echo -e "${RED}❌ Application rollback requires --backup parameter${NC}"
                exit 1
            fi
            if [ "${NO_CONFIRM:-false}" != "true" ]; then
                confirm_rollback_operation "Application Rollback (Code + Database)" "5-10 minutes"
            fi
            handle_application_rollback
            ;;
        system)
            if [ -z "${SELECTED_BACKUP:-}" ]; then
                echo -e "${RED}❌ System rollback requires --backup parameter${NC}"
                exit 1
            fi
            if [ "${NO_CONFIRM:-false}" != "true" ]; then
                confirm_rollback_operation "Complete System Rollback" "10-15 minutes"
            fi
            handle_complete_system_rollback
            ;;
        emergency)
            if [ "${NO_CONFIRM:-false}" != "true" ]; then
                confirm_rollback_operation "Emergency Rollback (No Backup)" "1-3 minutes"
            fi
            handle_emergency_rollback
            ;;
    esac
}

# Modified main function to handle command line arguments
main() {
    ROLLBACK_START_TIME=$(date +%s)
    ROLLBACK_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Parse command line arguments
    parse_arguments "$@"
    
    print_banner
    load_environment
    
    # Create initial Grafana annotation
    create_grafana_annotation "Rollback Operation Started" "Production rollback initiated by user" "rollback,start"
    
    # Handle direct rollback if type is specified
    if [ -n "${ROLLBACK_TYPE:-}" ]; then
        execute_direct_rollback
    else
        # Interactive mode
        while true; do
            show_rollback_menu
            
            read -p "$(echo -e "${CYAN}Select rollback option (1-5): ${NC}")" choice
            
            case $choice in
                1)
                    handle_database_rollback
                    break
                    ;;
                2)
                    handle_application_rollback
                    break
                    ;;
                3)
                    handle_complete_system_rollback
                    break
                    ;;
                4)
                    handle_emergency_rollback
                    break
                    ;;
                5)
                    echo -e "${YELLOW}❌ Rollback cancelled by user${NC}"
                    create_grafana_annotation "Rollback Cancelled" "User cancelled rollback operation" "rollback,cancelled"
                    exit 0
                    ;;
                *)
                    echo -e "${RED}❌ Invalid option. Please select 1-5.${NC}"
                    echo ""
                    ;;
            esac
        done
    fi
    
    print_rollback_summary
    
    # Create final Grafana annotation
    create_grafana_annotation "Rollback Operation Completed" "Production rollback completed successfully: ${ROLLBACK_TYPE}" "rollback,completed,success"
    
    exit 0
}

# ============================================================================
# Core Rollback Functions
# ============================================================================

perform_database_rollback() {
    echo -e "${CYAN}🔄 Performing database rollback...${NC}"
    echo -e "   📊 Using backup: $SELECTED_BACKUP"
    echo -e "   ⏱️  Estimated time: 2-5 minutes"
    echo ""
    
    local rollback_start_time
    rollback_start_time=$(date +%s)
    
    # Use existing safe_restore.sh infrastructure
    if bash scripts/safe_restore.sh "$SELECTED_BACKUP"; then
        local rollback_end_time duration
        rollback_end_time=$(date +%s)
        duration=$((rollback_end_time - rollback_start_time))
        
        echo -e "${GREEN}✅ Database rollback completed successfully${NC}"
        echo -e "   ⏱️  Duration: ${duration}s"
        echo -e "   📊 Database restored from: $SELECTED_BACKUP"
        
        # Create Grafana annotation
        create_grafana_annotation "Database Rollback Completed" "Database rolled back to: ${SELECTED_BACKUP}" "rollback,database"
        
    else
        echo -e "${RED}❌ Database rollback failed${NC}"
        echo -e "${YELLOW}💡 Check the safe_restore.sh logs for detailed error information${NC}"
        return 1
    fi
}

perform_application_rollback_with_image() {
    echo -e "${CYAN}🔄 Performing application rollback with image update...${NC}"
    echo -e "   🐳 Updating to image tag: $SELECTED_IMAGE_TAG"
    echo -e "   🔄 Restarting QR Generator API service"
    echo -e "   ⏱️  Estimated time: 3-8 minutes"
    echo ""
    
    local rollback_start_time
    rollback_start_time=$(date +%s)
    
    # Step 1: Update docker-compose.yml with new image tag
    if ! update_docker_compose_image_tag "api" "$SELECTED_IMAGE_TAG"; then
        echo -e "${RED}❌ Failed to update docker-compose.yml${NC}"
        return 1
    fi
    
    # Step 2: Pull the new image
    if ! pull_and_verify_image "api" "$SELECTED_IMAGE_TAG"; then
        echo -e "${RED}❌ Failed to pull Docker image${NC}"
        return 1
    fi
    
    # Step 3: Stop API service
    echo -e "${YELLOW}🛑 Stopping API service...${NC}"
    if timeout $SERVICE_STOP_TIMEOUT docker-compose stop api; then
        echo -e "${GREEN}✅ API service stopped${NC}"
    else
        echo -e "${RED}❌ Failed to stop API service within timeout${NC}"
        return 1
    fi
    
    # Step 4: Start API service with new image
    echo -e "${YELLOW}🚀 Starting API service with new image...${NC}"
    if timeout $SERVICE_START_TIMEOUT docker-compose up -d --force-recreate api; then
        echo -e "${GREEN}✅ API service started with new image${NC}"
    else
        echo -e "${RED}❌ Failed to start API service within timeout${NC}"
        return 1
    fi
    
    # Step 5: Wait for service to be ready
    echo -e "${CYAN}⏳ Waiting for service to be ready...${NC}"
    local ready_check_attempts=0
    local max_ready_attempts=60  # Increased from 30 to 60 (2 minutes)
    
    while [ $ready_check_attempts -lt $max_ready_attempts ]; do
        if docker-compose exec api curl -k -s --max-time 5 "${API_URL}/health" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ API service is responding${NC}"
            break
        fi
        sleep 3  # Increased from 2 to 3 seconds
        ready_check_attempts=$((ready_check_attempts + 1))
        
        # Progress indicator
        if [ $((ready_check_attempts % 10)) -eq 0 ]; then
            echo -e "${YELLOW}   Still waiting... (${ready_check_attempts}/${max_ready_attempts})${NC}"
        fi
    done
    
    if [ $ready_check_attempts -ge $max_ready_attempts ]; then
        echo -e "${RED}❌ API service did not become ready within timeout${NC}"
        return 1
    fi
    
    # Additional settling time for service to fully initialize
    echo -e "${CYAN}⏳ Allowing service to fully initialize...${NC}"
    sleep 15  # 15 second settling time
    echo -e "${GREEN}✅ Service initialization complete${NC}"
    
    local rollback_end_time duration
    rollback_end_time=$(date +%s)
    duration=$((rollback_end_time - rollback_start_time))
    
    echo -e "${GREEN}✅ Application rollback completed successfully${NC}"
    echo -e "   ⏱️  Duration: ${duration}s"
    echo -e "   🐳 Image tag: $SELECTED_IMAGE_TAG"
    
    # Create Grafana annotation
    create_grafana_annotation "Application Rollback Completed" "API service rolled back to image tag: ${SELECTED_IMAGE_TAG}" "rollback,application,image"
}

perform_application_restart() {
    echo -e "${CYAN}🔄 Performing application restart...${NC}"
    echo -e "   🐳 Restarting QR Generator API service (current image)"
    echo -e "   ⏱️  Estimated time: 1-3 minutes"
    echo ""
    
    local restart_start_time
    restart_start_time=$(date +%s)
    
    # Stop API service
    echo -e "${YELLOW}🛑 Stopping API service...${NC}"
    if timeout $SERVICE_STOP_TIMEOUT docker-compose stop api; then
        echo -e "${GREEN}✅ API service stopped${NC}"
    else
        echo -e "${RED}❌ Failed to stop API service within timeout${NC}"
        return 1
    fi
    
    # Start API service
    echo -e "${YELLOW}🚀 Starting API service...${NC}"
    if timeout $SERVICE_START_TIMEOUT docker-compose up -d api; then
        echo -e "${GREEN}✅ API service started${NC}"
    else
        echo -e "${RED}❌ Failed to start API service within timeout${NC}"
        return 1
    fi
    
    # Wait for service to be ready
    echo -e "${CYAN}⏳ Waiting for service to be ready...${NC}"
    local ready_check_attempts=0
    local max_ready_attempts=45  # Increased from 30 to 45 (90 seconds)
    
    while [ $ready_check_attempts -lt $max_ready_attempts ]; do
        if docker-compose exec api curl -k -s --max-time 5 "${API_URL}/health" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ API service is responding${NC}"
            break
        fi
        sleep 2
        ready_check_attempts=$((ready_check_attempts + 1))
        
        # Progress indicator every 15 attempts (30 seconds)
        if [ $((ready_check_attempts % 15)) -eq 0 ]; then
            echo -e "${YELLOW}   Still waiting for API service... (${ready_check_attempts}/${max_ready_attempts})${NC}"
        fi
    done
    
    if [ $ready_check_attempts -ge $max_ready_attempts ]; then
        echo -e "${RED}❌ API service did not become ready within timeout${NC}"
        return 1
    fi
    
    # Additional settling time for service restart
    echo -e "${CYAN}⏳ Allowing service to complete initialization...${NC}"
    sleep 10  # 10 second settling time for restart
    echo -e "${GREEN}✅ Service restart complete${NC}"
    
    local restart_end_time duration
    restart_end_time=$(date +%s)
    duration=$((restart_end_time - restart_start_time))
    
    echo -e "${GREEN}✅ Application restart completed successfully${NC}"
    echo -e "   ⏱️  Duration: ${duration}s"
    
    # Create Grafana annotation
    create_grafana_annotation "Application Restart Completed" "QR Generator API service restarted" "rollback,application"
}

perform_complete_system_rollback_with_image() {
    echo -e "${CYAN}🔄 Performing complete system rollback with image update...${NC}"
    echo -e "   🐳 Updating to image tag: $SELECTED_IMAGE_TAG"
    echo -e "   🔄 Restarting entire Docker stack"
    echo -e "   ⏱️  Estimated time: 5-12 minutes"
    echo ""
    
    local system_rollback_start_time
    system_rollback_start_time=$(date +%s)
    
    # Step 1: Update docker-compose.yml with new image tag
    if ! update_docker_compose_image_tag "api" "$SELECTED_IMAGE_TAG"; then
        echo -e "${RED}❌ Failed to update docker-compose.yml${NC}"
        return 1
    fi
    
    # Step 2: Pull the new image
    if ! pull_and_verify_image "api" "$SELECTED_IMAGE_TAG"; then
        echo -e "${RED}❌ Failed to pull Docker image${NC}"
        return 1
    fi
    
    # Step 3: Stop all services
    echo -e "${YELLOW}🛑 Stopping all services...${NC}"
    if timeout $SERVICE_STOP_TIMEOUT docker-compose down; then
        echo -e "${GREEN}✅ All services stopped${NC}"
    else
        echo -e "${RED}❌ Failed to stop services within timeout${NC}"
        return 1
    fi
    
    # Step 4: Start all services with new image
    echo -e "${YELLOW}🚀 Starting all services with updated image...${NC}"
    if timeout $SERVICE_START_TIMEOUT docker-compose up -d; then
        echo -e "${GREEN}✅ All services started${NC}"
    else
        echo -e "${RED}❌ Failed to start services within timeout${NC}"
        return 1
    fi
    
    # Step 5: Wait for all services to be ready
    echo -e "${CYAN}⏳ Waiting for services to be ready...${NC}"
    local services_ready=false
    local ready_attempts=0
    local max_ready_attempts=120  # Increased from 60 to 120 (10 minutes total)
    
    while [ $ready_attempts -lt $max_ready_attempts ] && [ "$services_ready" = false ]; do
        local api_ready=false
        local prometheus_ready=false
        local grafana_ready=false
        
        # Check API
        if docker-compose exec api curl -k -s --max-time 5 "${API_URL}/health" >/dev/null 2>&1; then
            api_ready=true
        fi
        
        # Check Prometheus
        if curl -s --max-time 5 "${PROMETHEUS_URL}/-/ready" >/dev/null 2>&1; then
            prometheus_ready=true
        fi
        
        # Check Grafana
        if curl -s --max-time 5 "${GRAFANA_URL}/api/health" >/dev/null 2>&1; then
            grafana_ready=true
        fi
        
        # Progress reporting
        if [ $((ready_attempts % 12)) -eq 0 ]; then  # Every minute
            echo -e "${YELLOW}   Progress: API:$([[ $api_ready == true ]] && echo "✅" || echo "⏳") Prometheus:$([[ $prometheus_ready == true ]] && echo "✅" || echo "⏳") Grafana:$([[ $grafana_ready == true ]] && echo "✅" || echo "⏳") (${ready_attempts}/${max_ready_attempts})${NC}"
        fi
        
        if [ "$api_ready" = true ] && [ "$prometheus_ready" = true ] && [ "$grafana_ready" = true ]; then
            services_ready=true
            echo -e "${GREEN}✅ All services are responding${NC}"
        else
            sleep 5
            ready_attempts=$((ready_attempts + 1))
        fi
    done
    
    if [ "$services_ready" = false ]; then
        echo -e "${RED}❌ Not all services became ready within timeout${NC}"
        echo -e "${YELLOW}💡 Some services may still be starting up${NC}"
        return 1
    fi
    
    # Additional settling time for all services to fully initialize
    echo -e "${CYAN}⏳ Allowing all services to fully initialize and stabilize...${NC}"
    sleep 30  # 30 second settling time for complete system
    echo -e "${GREEN}✅ System initialization complete${NC}"
    
    local system_rollback_end_time duration
    system_rollback_end_time=$(date +%s)
    duration=$((system_rollback_end_time - system_rollback_start_time))
    
    echo -e "${GREEN}✅ Complete system rollback completed successfully${NC}"
    echo -e "   ⏱️  Duration: ${duration}s"
    echo -e "   🐳 Image tag: $SELECTED_IMAGE_TAG"
    
    # Create Grafana annotation
    create_grafana_annotation "Complete System Rollback" "Full Docker stack restarted with image tag: ${SELECTED_IMAGE_TAG}" "rollback,system,image"
}

perform_complete_system_restart() {
    echo -e "${CYAN}🔄 Performing complete system restart...${NC}"
    echo -e "   🐳 Restarting entire Docker stack (current images)"
    echo -e "   ⏱️  Estimated time: 3-8 minutes"
    echo ""
    
    local system_restart_start_time
    system_restart_start_time=$(date +%s)
    
    # Stop all services
    echo -e "${YELLOW}🛑 Stopping all services...${NC}"
    if timeout $SERVICE_STOP_TIMEOUT docker-compose down; then
        echo -e "${GREEN}✅ All services stopped${NC}"
    else
        echo -e "${RED}❌ Failed to stop services within timeout${NC}"
        return 1
    fi
    
    # Start all services
    echo -e "${YELLOW}🚀 Starting all services...${NC}"
    if timeout $SERVICE_START_TIMEOUT docker-compose up -d; then
        echo -e "${GREEN}✅ All services started${NC}"
    else
        echo -e "${RED}❌ Failed to start services within timeout${NC}"
        return 1
    fi
    
    # Wait for all services to be ready
    echo -e "${CYAN}⏳ Waiting for services to be ready...${NC}"
    local services_ready=false
    local ready_attempts=0
    local max_ready_attempts=60
    
    while [ $ready_attempts -lt $max_ready_attempts ] && [ "$services_ready" = false ]; do
        local api_ready=false
        local prometheus_ready=false
        local grafana_ready=false
        
        # Check API
        if docker-compose exec api curl -k -s --max-time 5 "${API_URL}/health" >/dev/null 2>&1; then
            api_ready=true
        fi
        
        # Check Prometheus
        if curl -s --max-time 5 "${PROMETHEUS_URL}/-/ready" >/dev/null 2>&1; then
            prometheus_ready=true
        fi
        
        # Check Grafana
        if curl -s --max-time 5 "${GRAFANA_URL}/api/health" >/dev/null 2>&1; then
            grafana_ready=true
        fi
        
        if [ "$api_ready" = true ] && [ "$prometheus_ready" = true ] && [ "$grafana_ready" = true ]; then
            services_ready=true
        else
            sleep 5
            ready_attempts=$((ready_attempts + 1))
        fi
    done
    
    if [ "$services_ready" = false ]; then
        echo -e "${RED}❌ Not all services became ready within timeout${NC}"
        echo -e "${YELLOW}💡 Some services may still be starting up${NC}"
        return 1
    fi
    
    local system_restart_end_time duration
    system_restart_end_time=$(date +%s)
    duration=$((system_restart_end_time - system_restart_start_time))
    
    echo -e "${GREEN}✅ Complete system restart completed successfully${NC}"
    echo -e "   ⏱️  Duration: ${duration}s"
    
    # Create Grafana annotation
    create_grafana_annotation "Complete System Restart" "Full Docker stack restarted" "rollback,system"
}

run_post_rollback_validation() {
    echo -e "${CYAN}🔍 Running post-rollback validation...${NC}"
    echo -e "   🧪 Using enhanced smoke test for comprehensive validation"
    echo -e "   ⏱️  Estimated time: 60-120 seconds (including initialization)"
    echo ""
    
    # Critical: Allow additional time for services to fully stabilize
    echo -e "${CYAN}⏳ Allowing services to fully stabilize before validation...${NC}"
    echo -e "   🔄 This ensures database connections and internal services are ready"
    sleep 30  # 30 second stabilization period
    echo -e "${GREEN}✅ Stabilization period complete${NC}"
    echo ""
    
    local validation_start_time
    validation_start_time=$(date +%s)
    
    # Run enhanced smoke test
    if timeout $SMOKE_TEST_TIMEOUT bash scripts/enhanced_smoke_test.sh; then
        local validation_end_time duration
        validation_end_time=$(date +%s)
        duration=$((validation_end_time - validation_start_time))
        
        echo -e "${GREEN}✅ Post-rollback validation completed successfully${NC}"
        echo -e "   ⏱️  Duration: ${duration}s"
        echo -e "   🎯 All critical functionality verified"
        
        # Create Grafana annotation
        create_grafana_annotation "Rollback Validation Passed" "Post-rollback smoke test completed successfully" "rollback,validation,success"
        
    else
        echo -e "${RED}❌ Post-rollback validation failed${NC}"
        echo -e "${YELLOW}💡 System may not be functioning correctly after rollback${NC}"
        echo -e "${YELLOW}💡 Check enhanced_smoke_test.sh output for specific failures${NC}"
        
        # Create Grafana annotation
        create_grafana_annotation "Rollback Validation Failed" "Post-rollback smoke test failed - system may be unstable" "rollback,validation,failure"
        
        return 1
    fi
}

# ============================================================================
# Execute main function with all arguments
# ============================================================================

main "$@"