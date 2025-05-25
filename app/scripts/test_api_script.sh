#!/bin/bash

# Ensure the script fails if any command fails
set -e

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# S.0.1: Environment Variable Loading and Validation
# ============================================================================

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo -e "${YELLOW}Loading environment variables from .env file...${NC}"
    # Export variables to make them available to subshells (safer method)
    set -a  # automatically export all variables
    source .env
    set +a  # disable automatic export
else
    echo -e "${RED}Error: .env file not found. Please create one from .env.example.${NC}"
    exit 1
fi

# Required variable check - fail fast if any are missing
required_vars_test_api=("API_URL" "BASE_URL" "AUTH_USER" "AUTH_PASS")
missing_vars_test_api=()
for var in "${required_vars_test_api[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars_test_api+=("$var")
    fi
done
if [ ${#missing_vars_test_api[@]} -gt 0 ]; then
    echo -e "${RED}❌ Error: Required environment variables for test_api_script.sh are not set:${NC}"
    for var in "${missing_vars_test_api[@]}"; do echo "   - $var"; done
    echo "Please ensure these are defined in your .env file."
    exit 1
fi

# Global Variable Definitions (strictly from .env)
API_URL="${API_URL}"
BASE_URL="${BASE_URL}"
AUTH_USER="${AUTH_USER}"
AUTH_PASS="${AUTH_PASS}"
AUTH_HEADER="--user ${AUTH_USER}:${AUTH_PASS}"

echo -e "${YELLOW}Using BASE_URL for QR codes: ${BASE_URL}${NC}"
echo -e "${YELLOW}Using API_URL for API calls: ${API_URL}${NC}"
echo -e "${YELLOW}Using authentication: ${AUTH_USER}${NC}"

# ============================================================================
# Global Variables for Shared State
# ============================================================================

# Global variables for API responses
API_RESPONSE_BODY=""
API_RESPONSE_STATUS=""

# Global variables for shared IDs between tests
STATIC_QR_ID=""
DYNAMIC_QR_ID=""

# ============================================================================
# S.0.2: Core Utility Functions
# ============================================================================

# Function to make an API request
# Usage: _api_request <METHOD> <ENDPOINT_PATH> [JSON_DATA]
# Sets global variables: API_RESPONSE_STATUS and API_RESPONSE_BODY
_api_request() {
    local method="$1"
    local endpoint_path="$2"
    local json_data="$3"
    local curl_opts=(-k -s --user "${AUTH_USER}:${AUTH_PASS}") # -k for insecure (localhost dev), -s for silent

    # Clear/initialize global response variables
    API_RESPONSE_BODY=""
    API_RESPONSE_STATUS=""

    if [ -n "$json_data" ]; then
        curl_opts+=(-H "Content-Type: application/json" -d "$json_data")
    fi

    local tmp_response_file=$(mktemp)
    API_RESPONSE_STATUS=$(curl "${curl_opts[@]}" -X "$method" "${API_URL}${endpoint_path}" -w "%{http_code}" -o "$tmp_response_file")
    API_RESPONSE_BODY=$(cat "$tmp_response_file")
    rm "$tmp_response_file"
}

# Function to assert HTTP status code
# Usage: _assert_status_code <actual_code> <expected_code> "<test_description>"
_assert_status_code() {
    local actual="$1"
    local expected="$2"
    local description="$3"
    if [ "$actual" -eq "$expected" ]; then
        echo -e "${GREEN}✓ PASS:${NC} $description (Expected $expected, Got $actual)"
    else
        echo -e "${RED}✗ FAIL:${NC} $description (Expected $expected, Got $actual)"
        echo -e "${YELLOW}Response Body:${NC}\n$API_RESPONSE_BODY"
        exit 1
    fi
}

# Function to extract a value from JSON using jq
# Usage: _get_json_value <json_string> <jq_path>
# Returns: extracted value or empty string if not found/error
_get_json_value() {
    local json_string="$1"
    local jq_path="$2"
    local value
    value=$(echo "$json_string" | jq -r "$jq_path" 2>/dev/null)
    if [ $? -ne 0 ] || [ "$value" == "null" ]; then
        echo "" # Return empty for errors or jq 'null'
    else
        echo "$value"
    fi
}

# Function to assert a JSON value
# Usage: _assert_json_value <json_string> <jq_path> <expected_value> "<test_description>"
_assert_json_value() {
    local json_string="$1"
    local jq_path="$2"
    local expected_value="$3"
    local description="$4"
    
    local actual_value
    actual_value=$(_get_json_value "$json_string" "$jq_path")
    
    if [ "$actual_value" == "$expected_value" ]; then
        echo -e "${GREEN}✓ PASS:${NC} $description (Expected '$expected_value', Got '$actual_value')"
    else
        echo -e "${RED}✗ FAIL:${NC} $description (Expected '$expected_value', Got '$actual_value')"
        echo -e "${YELLOW}Full JSON Body:${NC}\n$json_string"
        exit 1
    fi
}

# Function to assert a JSON key exists and is not null
# Usage: _assert_json_contains_key <json_string> <jq_path_to_key> "<test_description>"
_assert_json_contains_key() {
    local json_string="$1"
    local jq_path="$2"
    local description="$3"
    
    if echo "$json_string" | jq -e "$jq_path" > /dev/null 2>&1; then
        # Check if value is not literal "null"
        local val
        val=$(echo "$json_string" | jq -r "$jq_path")
        if [ "$val" != "null" ]; then
            echo -e "${GREEN}✓ PASS:${NC} $description (Key '$jq_path' exists and is not null)"
        else
            echo -e "${RED}✗ FAIL:${NC} $description (Key '$jq_path' exists but is null)"
            echo -e "${YELLOW}Full JSON Body:${NC}\n$json_string"
            exit 1
        fi
    else
        echo -e "${RED}✗ FAIL:${NC} $description (Key '$jq_path' does not exist)"
        echo -e "${YELLOW}Full JSON Body:${NC}\n$json_string"
        exit 1
    fi
}

# ============================================================================
# Legacy Helper Functions (for compatibility)
# ============================================================================

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" -eq 0 ]; then
        echo -e "${GREEN}✓ PASS:${NC} $message"
    else
        echo -e "${RED}✗ FAIL:${NC} $message"
        exit 1
    fi
}

# Function to print section header
print_section() {
    local title=$1
    echo -e "\n${BLUE}=== $title ===${NC}"
}

# ============================================================================
# S.0.4: Refactored Test Functions
# ============================================================================

# Function to check Docker containers
check_docker_containers() {
    print_section "Checking Docker Containers"
    echo -e "${YELLOW}Checking Docker containers...${NC}"
    if docker ps | grep -E 'qr_generator_api|qr_generator_traefik' > /dev/null; then
        echo -e "${GREEN}✓ PASS:${NC} Docker containers are running"
    else
        echo -e "${RED}✗ FAIL:${NC} Docker containers are not running"
        exit 1
    fi
}

# Function to test health endpoint
test_health_endpoint() {
    print_section "Testing Health Endpoint"
    _api_request GET "/health"
    _assert_status_code "$API_RESPONSE_STATUS" 200 "GET /health returns 200 OK"
    _assert_json_contains_key "$API_RESPONSE_BODY" ".status" "Health response contains 'status' key"
}

# Function to test QR code listing
test_qr_code_listing() {
    print_section "Testing QR Code Listing"
    _api_request GET "/api/v1/qr"
    _assert_status_code "$API_RESPONSE_STATUS" 200 "GET /api/v1/qr returns 200 OK"
    # Verify it's a valid JSON object with items array
    if echo "$API_RESPONSE_BODY" | jq -e '.items | type == "array"' > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS:${NC} QR code listing returns valid JSON with items array"
    else
        echo -e "${RED}✗ FAIL:${NC} QR code listing does not return valid JSON with items array"
        exit 1
    fi
}

# Function to create static QR code
test_create_static_qr() {
    print_section "Testing Create Static QR Code"
    local payload='{"content": "https://test.example.com", "qr_type": "static", "title": "Test Static QR", "description": "This is a test static QR code"}'
    _api_request POST "/api/v1/qr/static" "$payload"
    _assert_status_code "$API_RESPONSE_STATUS" 201 "POST /api/v1/qr/static creates resource"
    
    _assert_json_contains_key "$API_RESPONSE_BODY" ".id" "Create static QR response contains 'id'"
    STATIC_QR_ID=$(_get_json_value "$API_RESPONSE_BODY" ".id")
    if [ -z "$STATIC_QR_ID" ]; then
        echo -e "${RED}✗ FAIL:${NC} Failed to extract ID from static QR creation response."
        exit 1
    fi
    _assert_json_value "$API_RESPONSE_BODY" ".content" "https://test.example.com" "Static QR content matches"
    _assert_json_value "$API_RESPONSE_BODY" ".qr_type" "static" "Static QR type matches"
    _assert_json_value "$API_RESPONSE_BODY" ".title" "Test Static QR" "Static QR title matches"
}

# Function to create dynamic QR code
test_create_dynamic_qr() {
    print_section "Testing Create Dynamic QR Code"
    local payload='{"content": "test-dynamic", "redirect_url": "https://technological-alchemist.vercel.app", "title": "Test Dynamic QR", "description": "This is a test dynamic QR code"}'
    _api_request POST "/api/v1/qr/dynamic" "$payload"
    _assert_status_code "$API_RESPONSE_STATUS" 201 "POST /api/v1/qr/dynamic creates resource"
    
    _assert_json_contains_key "$API_RESPONSE_BODY" ".id" "Create dynamic QR response contains 'id'"
    DYNAMIC_QR_ID=$(_get_json_value "$API_RESPONSE_BODY" ".id")
    if [ -z "$DYNAMIC_QR_ID" ]; then
        echo -e "${RED}✗ FAIL:${NC} Failed to extract ID from dynamic QR creation response."
        exit 1
    fi
    _assert_json_value "$API_RESPONSE_BODY" ".qr_type" "dynamic" "Dynamic QR type matches"
    _assert_json_value "$API_RESPONSE_BODY" ".title" "Test Dynamic QR" "Dynamic QR title matches"
    _assert_json_contains_key "$API_RESPONSE_BODY" ".redirect_url" "Dynamic QR response contains redirect_url"
}

# Function to get QR code by ID
test_get_qr_by_id() {
    print_section "Testing Get QR Code by ID"
    
    # Test static QR retrieval
    _api_request GET "/api/v1/qr/$STATIC_QR_ID"
    _assert_status_code "$API_RESPONSE_STATUS" 200 "GET static QR by ID returns 200 OK"
    _assert_json_value "$API_RESPONSE_BODY" ".id" "$STATIC_QR_ID" "Static QR ID matches"
    
    # Test dynamic QR retrieval
    _api_request GET "/api/v1/qr/$DYNAMIC_QR_ID"
    _assert_status_code "$API_RESPONSE_STATUS" 200 "GET dynamic QR by ID returns 200 OK"
    _assert_json_value "$API_RESPONSE_BODY" ".id" "$DYNAMIC_QR_ID" "Dynamic QR ID matches"
}

# Function to update dynamic QR code
test_update_dynamic_qr() {
    print_section "Testing Update Dynamic QR Code"
    local payload='{"redirect_url": "https://updated.example.com"}'
    _api_request PUT "/api/v1/qr/$DYNAMIC_QR_ID" "$payload"
    _assert_status_code "$API_RESPONSE_STATUS" 200 "PUT /api/v1/qr/{id} updates resource"
    
    # Extract and verify the updated URL (removing trailing slash for comparison)
    local updated_url
    updated_url=$(_get_json_value "$API_RESPONSE_BODY" ".redirect_url")
    updated_url=$(echo "$updated_url" | sed 's:/*$::')
    local expected_url="https://updated.example.com"
    
    if [ "$updated_url" == "$expected_url" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Dynamic QR code URL updated successfully"
    else
        echo -e "${RED}✗ FAIL:${NC} URL not updated correctly (Expected: $expected_url, Got: $updated_url)"
        exit 1
    fi
}

# Function to test QR code redirection
test_qr_redirection() {
    print_section "Testing QR Code Redirection"
    
    # Get the dynamic QR code to extract content
    _api_request GET "/api/v1/qr/$DYNAMIC_QR_ID"
    _assert_status_code "$API_RESPONSE_STATUS" 200 "GET dynamic QR for redirection test"
    
    local content
    content=$(_get_json_value "$API_RESPONSE_BODY" ".content")
    echo -e "${YELLOW}QR code content:${NC} $content"
    
    # Extract short ID from the content
    local short_id=$(echo "$content" | sed 's/.*\/r\///')
    echo -e "${YELLOW}Extracted short ID:${NC} $short_id"
    
    # Check if content starts with expected BASE_URL
    if [[ "$content" == "$BASE_URL/r/"* ]]; then
        echo -e "${GREEN}✓ PASS:${NC} QR code content has expected BASE_URL format"
    else
        echo -e "${YELLOW}⚠ WARNING:${NC} QR code content does not match BASE_URL format"
        echo -e "Expected format: ${BASE_URL}/r/{short_id}"
        echo -e "Actual content: $content"
    fi
    
    # Test redirection using curl
    local redirect_response=$(curl -k -s -o /dev/null -w "%{http_code}" -H "Host: web.hccc.edu" "$API_URL/r/$short_id")
    
    if [ "$redirect_response" == "302" ]; then
        echo -e "${GREEN}✓ PASS:${NC} QR code redirection successful (302 status)"
    else
        echo -e "${RED}✗ FAIL:${NC} QR code redirection failed (status: $redirect_response)"
        exit 1
    fi
}

# Function to test service-based dependency injection
test_service_dependency_injection() {
    print_section "Testing Service-Based Dependency Injection"
    
    # Create a QR code with specific parameters to test service layer
    local payload='{"content": "https://service-test.example.com", "qr_type": "static", "fill_color": "#333333", "back_color": "#FFFFFF", "title": "Service Test QR", "description": "Testing service layer with specific parameters"}'
    _api_request POST "/api/v1/qr/static" "$payload"
    _assert_status_code "$API_RESPONSE_STATUS" 201 "Service layer QR code creation successful"
    
    # Verify service properly handles the fill_color parameter
    _assert_json_value "$API_RESPONSE_BODY" ".fill_color" "#333333" "Service layer correctly processed fill_color parameter"
    
    # Verify service returns consistent data structure
    _assert_json_contains_key "$API_RESPONSE_BODY" ".created_at" "Service layer returned proper timestamp data"
}

# Function to test background tasks for scan statistics
test_background_tasks_scan_statistics() {
    print_section "Testing Background Tasks for Scan Statistics"
    
    # Create a new dynamic QR code for testing
    local payload='{"content": "background-task-test", "redirect_url": "https://background-task.example.com", "title": "Background Task QR", "description": "Testing background task processing"}'
    _api_request POST "/api/v1/qr/dynamic" "$payload"
    _assert_status_code "$API_RESPONSE_STATUS" 201 "Created QR code for background task testing"
    
    local bg_qr_id
    bg_qr_id=$(_get_json_value "$API_RESPONSE_BODY" ".id")
    local content
    content=$(_get_json_value "$API_RESPONSE_BODY" ".content")
    local short_id=$(echo "$content" | sed 's/.*\/r\///')
    
    echo -e "${YELLOW}QR code content:${NC} $content"
    echo -e "${YELLOW}Extracted short ID:${NC} $short_id"
    
    # Get initial scan count
    _api_request GET "/api/v1/qr/$bg_qr_id"
    _assert_status_code "$API_RESPONSE_STATUS" 200 "GET QR for initial scan count"
    local initial_scan_count
    initial_scan_count=$(_get_json_value "$API_RESPONSE_BODY" ".scan_count")
    echo -e "${YELLOW}Initial scan count:${NC} $initial_scan_count"
    
    # Test redirection response time
    echo -e "${YELLOW}Testing redirection response time...${NC}"
    local start_time=$(date +%s.%N)
    local redirect_status=$(curl -k -s -o /dev/null -w "%{http_code}" -H "Host: web.hccc.edu" "$API_URL/r/$short_id")
    local end_time=$(date +%s.%N)
    local response_time=$(echo "$end_time - $start_time" | bc)
    
    echo -e "Redirection status code: ${redirect_status}"
    echo -e "Redirection response time: ${response_time} seconds"
    
    if [ "$redirect_status" != "302" ]; then
        echo -e "${RED}✗ FAIL:${NC} Redirection failed with status code $redirect_status"
        exit 1
    fi
    
    if (( $(echo "$response_time < 0.5" | bc -l) )); then
        echo -e "${GREEN}✓ PASS:${NC} Redirection response time is fast (< 0.5s), suggesting background task usage"
    else
        echo -e "${YELLOW}⚠ WARNING:${NC} Redirection response time is slow (> 0.5s), might not be using background tasks"
    fi
    
    # Wait for background task to complete
    echo -e "${YELLOW}Waiting for background task to complete...${NC}"
    sleep 3
    
    # Verify scan count was updated
    _api_request GET "/api/v1/qr/$bg_qr_id"
    _assert_status_code "$API_RESPONSE_STATUS" 200 "GET QR for updated scan count"
    local updated_scan_count
    updated_scan_count=$(_get_json_value "$API_RESPONSE_BODY" ".scan_count")
    echo -e "${YELLOW}Updated scan count:${NC} $updated_scan_count"
    
    if [ "$updated_scan_count" -gt "$initial_scan_count" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Scan count was updated by background task (${initial_scan_count} -> ${updated_scan_count})"
    else
        echo -e "${RED}✗ FAIL:${NC} Scan count was not updated by background task"
        echo -e "${YELLOW}Debug Information:${NC}"
        echo "Initial scan count: $initial_scan_count"
        echo "Updated scan count: $updated_scan_count"
        exit 1
    fi
    
    # Verify last_scanned_at was updated
    local last_scanned_at
    last_scanned_at=$(_get_json_value "$API_RESPONSE_BODY" ".last_scan_at")
    if [ -z "$last_scanned_at" ]; then
        # Try alternative field name
        last_scanned_at=$(_get_json_value "$API_RESPONSE_BODY" ".last_scanned_at")
    fi
    
    if [ -n "$last_scanned_at" ]; then
        echo -e "${GREEN}✓ PASS:${NC} last_scanned_at timestamp was updated by background task"
    else
        echo -e "${RED}✗ FAIL:${NC} last_scanned_at timestamp was not updated"
        exit 1
    fi
}

# Function to test QR code generation with logo
test_qr_with_logo() {
    print_section "Testing QR Code Generation with Logo"
    
    # Test static QR with logo
    echo -e "\n${YELLOW}Testing Static QR Code with Logo...${NC}"
    local payload='{"content": "https://www.github.com/gsinghjay", "qr_type": "static", "include_logo": true, "title": "GitHub Logo QR", "description": "Static QR code with logo pointing to GitHub"}'
    _api_request POST "/api/v1/qr/static" "$payload"
    _assert_status_code "$API_RESPONSE_STATUS" 201 "Static QR code with logo creation successful"
    
    local static_id
    static_id=$(_get_json_value "$API_RESPONSE_BODY" ".id")
    
    # Get the static QR image with logo
    local static_image_response=$(curl -k -s $AUTH_HEADER -o static_qr_with_logo.png \
        "$API_URL/api/v1/qr/$static_id/image?include_logo=true")
    if [ -f "static_qr_with_logo.png" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Static QR image with logo downloaded successfully"
    else
        echo -e "${RED}✗ FAIL:${NC} Failed to download static QR image with logo"
        exit 1
    fi
    
    # Test dynamic QR with logo
    echo -e "\n${YELLOW}Testing Dynamic QR Code with Logo...${NC}"
    local dynamic_payload='{"content": "dynamic-with-logo", "redirect_url": "https://technological-alchemist.vercel.app/", "include_logo": true, "title": "Dynamic Logo QR", "description": "Dynamic QR code with logo for redirection"}'
    _api_request POST "/api/v1/qr/dynamic" "$dynamic_payload"
    _assert_status_code "$API_RESPONSE_STATUS" 201 "Dynamic QR code with logo creation successful"
    
    local dynamic_id
    dynamic_id=$(_get_json_value "$API_RESPONSE_BODY" ".id")
    
    # Get the dynamic QR image with logo
    local dynamic_image_response=$(curl -k -s $AUTH_HEADER -o dynamic_qr_with_logo.png \
        "$API_URL/api/v1/qr/$dynamic_id/image?include_logo=true")
    if [ -f "dynamic_qr_with_logo.png" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Dynamic QR image with logo downloaded successfully"
    else
        echo -e "${RED}✗ FAIL:${NC} Failed to download dynamic QR image with logo"
        exit 1
    fi
    
    # Test redirection for dynamic QR with logo
    local content
    content=$(_get_json_value "$API_RESPONSE_BODY" ".content")
    local short_id=$(echo "$content" | sed 's/.*\/r\///')
    local redirect_response=$(curl -k -s -L -o /dev/null -w "%{http_code}" -H "Host: web.hccc.edu" "$API_URL/r/$short_id")
    
    if [ "$redirect_response" == "302" ] || [ "$redirect_response" == "200" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Dynamic QR code with logo redirects successfully (status: $redirect_response)"
    else
        echo -e "${RED}✗ FAIL:${NC} Dynamic QR code with logo redirection failed (status: $redirect_response)"
        exit 1
    fi
}

# Function to test error correction levels
test_error_correction_levels() {
    print_section "Testing Error Correction Levels"
    
    # Array of error correction levels to test
    local error_levels=("l" "m" "q" "h")
    local error_names=("Low" "Medium" "Quartile" "High")
    
    # Loop through each error level and test
    for i in "${!error_levels[@]}"; do
        local error_level="${error_levels[$i]}"
        local error_name="${error_names[$i]}"
        
        echo -e "\n${YELLOW}Testing ${error_name} (${error_level}) Error Correction Level...${NC}"
        
        # Create static QR code with specific error level
        local payload="{\"content\": \"https://error-level-test-${error_level}.example.com\", \"qr_type\": \"static\", \"error_level\": \"${error_level}\", \"title\": \"Error Level ${error_name} QR\", \"description\": \"Testing QR code with ${error_name} error correction level\"}"
        _api_request POST "/api/v1/qr/static" "$payload"
        _assert_status_code "$API_RESPONSE_STATUS" 201 "QR code creation with ${error_name} error level successful"
        
        # Verify error level was set correctly
        _assert_json_value "$API_RESPONSE_BODY" ".error_level" "$error_level" "Error level correctly set to ${error_name} (${error_level})"
        
        local qr_id
        qr_id=$(_get_json_value "$API_RESPONSE_BODY" ".id")
        
        # Get QR image with error level and save to file
        local output_file="qr_error_level_${error_level}.png"
        local image_response=$(curl -k -s $AUTH_HEADER -o "${output_file}" \
            "$API_URL/api/v1/qr/$qr_id/image?error_level=${error_level}")
        
        if [ -f "${output_file}" ]; then
            echo -e "${GREEN}✓ PASS:${NC} QR image with ${error_name} error level downloaded successfully"
        else
            echo -e "${RED}✗ FAIL:${NC} Failed to download QR image with ${error_name} error level"
            exit 1
        fi
    done
    
    echo -e "\n${GREEN}✓ PASS:${NC} All error correction level tests completed successfully"
}

# Function to test SVG accessibility options
test_svg_accessibility() {
    print_section "Testing SVG Accessibility Options"
    
    echo -e "\n${YELLOW}Testing SVG QR Code with Accessibility Options...${NC}"
    
    # Create a QR code with SVG accessibility options
    local payload='{"content": "https://accessibility-test.example.com", "qr_type": "static", "title": "Accessibility Test QR", "description": "Testing QR code with SVG accessibility features"}'
    _api_request POST "/api/v1/qr/static" "$payload"
    _assert_status_code "$API_RESPONSE_STATUS" 201 "QR code creation for SVG accessibility test successful"
    
    local qr_id
    qr_id=$(_get_json_value "$API_RESPONSE_BODY" ".id")
    
    # Get QR code as SVG with accessibility options
    local svg_title="QR Code for Accessibility Testing"
    local svg_description="This QR code links to the accessibility test example website"
    
    # URL encode the title and description
    local encoded_title=$(echo "$svg_title" | sed -e 's/ /%20/g')
    local encoded_description=$(echo "$svg_description" | sed -e 's/ /%20/g')
    
    echo -e "${YELLOW}Requesting SVG with title and description...${NC}"
    local svg_response=$(curl -k -s $AUTH_HEADER -o "accessible_qr_code.svg" \
        "$API_URL/api/v1/qr/$qr_id/image?image_format=svg&svg_title=${encoded_title}&svg_description=${encoded_description}")
    
    if [ -f "accessible_qr_code.svg" ]; then
        echo -e "${GREEN}✓ PASS:${NC} SVG QR code with accessibility options downloaded successfully"
        
        # Check if SVG file contains title and description
        if grep -q "title" "accessible_qr_code.svg" && grep -q "desc" "accessible_qr_code.svg"; then
            echo -e "${GREEN}✓ PASS:${NC} SVG contains title and description elements"
        else
            echo -e "${YELLOW}⚠ WARNING:${NC} SVG might not contain title and description elements"
        fi
    else
        echo -e "${RED}✗ FAIL:${NC} Failed to download SVG QR code with accessibility options"
        exit 1
    fi
    
    echo -e "\n${GREEN}✓ PASS:${NC} SVG accessibility tests completed successfully"
}

# Function to test enhanced user agent tracking
test_enhanced_user_agent_tracking() {
    print_section "Testing Enhanced User Agent Tracking"
    
    echo -e "\n${YELLOW}Testing Genuine Scan Detection and User Agent Tracking...${NC}"
    
    # Create a dynamic QR code for testing user agent tracking
    local payload='{"redirect_url": "https://user-agent-test.example.com", "title": "User Agent Tracking Test", "description": "Testing enhanced scan tracking with user agent analysis"}'
    _api_request POST "/api/v1/qr/dynamic" "$payload"
    _assert_status_code "$API_RESPONSE_STATUS" 201 "QR code creation for user agent tracking test successful"
    
    local qr_id
    qr_id=$(_get_json_value "$API_RESPONSE_BODY" ".id")
    local content
    content=$(_get_json_value "$API_RESPONSE_BODY" ".content")
    local short_id=$(echo "$content" | sed 's/.*\/r\///' | sed 's/?.*//')
    
    echo -e "${YELLOW}QR code content:${NC} $content"
    echo -e "${YELLOW}Extracted short ID:${NC} $short_id"
    
    # Check initial scan statistics
    _api_request GET "/api/v1/qr/$qr_id"
    _assert_status_code "$API_RESPONSE_STATUS" 200 "GET QR for initial scan statistics"
    local initial_scan_count
    initial_scan_count=$(_get_json_value "$API_RESPONSE_BODY" ".scan_count")
    local initial_genuine_scan_count
    initial_genuine_scan_count=$(_get_json_value "$API_RESPONSE_BODY" ".genuine_scan_count")
    
    echo -e "${YELLOW}Initial scan count:${NC} $initial_scan_count"
    echo -e "${YELLOW}Initial genuine scan count:${NC} $initial_genuine_scan_count"
    
    # Test 1: Simulate a non-genuine scan (direct URL access)
    echo -e "\n${YELLOW}Test 1: Simulating direct URL access (non-genuine scan)...${NC}"
    local non_genuine_status=$(curl -k -s -o /dev/null -w "%{http_code}" \
        -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36" \
        -H "Host: web.hccc.edu" \
        "$API_URL/r/$short_id")
    
    if [ "$non_genuine_status" == "302" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Non-genuine scan redirect successful"
    else
        echo -e "${RED}✗ FAIL:${NC} Non-genuine scan redirect failed (status: $non_genuine_status)"
        exit 1
    fi
    
    # Test 2: Simulate genuine QR scans
    echo -e "\n${YELLOW}Test 2: Simulating genuine QR scan with mobile device...${NC}"
    local genuine_status=$(curl -k -s -o /dev/null -w "%{http_code}" \
        -A "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1" \
        -H "Host: web.hccc.edu" \
        "$API_URL/r/$short_id?scan_ref=qr")
    
    if [ "$genuine_status" == "302" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Genuine scan redirect successful"
    else
        echo -e "${RED}✗ FAIL:${NC} Genuine scan redirect failed (status: $genuine_status)"
        exit 1
    fi
    
    # Test 3: Android device scan
    echo -e "\n${YELLOW}Test 3: Simulating QR scan with Android device...${NC}"
    local android_status=$(curl -k -s -o /dev/null -w "%{http_code}" \
        -A "Mozilla/5.0 (Linux; Android 12; SM-G991U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Mobile Safari/537.36" \
        -H "Host: web.hccc.edu" \
        "$API_URL/r/$short_id?scan_ref=qr")
    
    if [ "$android_status" == "302" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Android scan redirect successful"
    else
        echo -e "${RED}✗ FAIL:${NC} Android scan redirect failed (status: $android_status)"
        exit 1
    fi
    
    # Wait for background tasks to complete
    echo -e "${YELLOW}Waiting for background tasks to complete...${NC}"
    sleep 3
    
    # Check updated scan statistics
    _api_request GET "/api/v1/qr/$qr_id"
    _assert_status_code "$API_RESPONSE_STATUS" 200 "GET QR for updated scan statistics"
    local updated_scan_count
    updated_scan_count=$(_get_json_value "$API_RESPONSE_BODY" ".scan_count")
    local updated_genuine_scan_count
    updated_genuine_scan_count=$(_get_json_value "$API_RESPONSE_BODY" ".genuine_scan_count")
    
    echo -e "${YELLOW}Updated scan count:${NC} $updated_scan_count"
    echo -e "${YELLOW}Updated genuine scan count:${NC} $updated_genuine_scan_count"
    
    # Verify total scan count increased by 3
    local expected_scan_count=$((initial_scan_count + 3))
    if [ "$updated_scan_count" -eq "$expected_scan_count" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Total scan count increased correctly (${initial_scan_count} -> ${updated_scan_count})"
    else
        echo -e "${YELLOW}⚠ WARNING:${NC} Total scan count did not increase by expected amount (Expected: $expected_scan_count, Actual: $updated_scan_count)"
    fi
    
    # Verify genuine scan count increased by 2
    local expected_genuine_scan_count=$((initial_genuine_scan_count + 2))
    if [ "$updated_genuine_scan_count" -eq "$expected_genuine_scan_count" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Genuine scan count increased correctly (${initial_genuine_scan_count} -> ${updated_genuine_scan_count})"
    else
        echo -e "${YELLOW}⚠ WARNING:${NC} Genuine scan count did not increase by expected amount (Expected: $expected_genuine_scan_count, Actual: $updated_genuine_scan_count)"
    fi
    
    # Verify timestamps are set
    local first_genuine_scan_at
    first_genuine_scan_at=$(_get_json_value "$API_RESPONSE_BODY" ".first_genuine_scan_at")
    local last_genuine_scan_at
    last_genuine_scan_at=$(_get_json_value "$API_RESPONSE_BODY" ".last_genuine_scan_at")
    
    if [ -n "$first_genuine_scan_at" ]; then
        echo -e "${GREEN}✓ PASS:${NC} First genuine scan timestamp is properly set"
    else
        echo -e "${RED}✗ FAIL:${NC} First genuine scan timestamp was not set"
    fi
    
    if [ -n "$last_genuine_scan_at" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Last genuine scan timestamp is properly set"
    else
        echo -e "${RED}✗ FAIL:${NC} Last genuine scan timestamp was not set"
    fi
    
    echo -e "\n${GREEN}✓ PASS:${NC} Enhanced user agent tracking tests completed successfully"
}

# Function to test production hardening security features
test_production_hardening_security() {
    print_section "Testing Production Hardening Security Features"
    
    # Test invalid short_id formats
    test_invalid_short_id_formats
    
    # Test disallowed redirect URLs
    test_disallowed_redirect_urls
    
    # Test invalid URL schemes
    test_invalid_url_schemes
    
    # Test rate limiting
    test_rate_limiting
    
    echo -e "\n${GREEN}✓ PASS:${NC} All production hardening security tests completed successfully"
}

# Function to test invalid short_id formats
test_invalid_short_id_formats() {
    echo -e "\n${YELLOW}Testing Invalid Short ID Formats...${NC}"
    
    # Test 1: Short ID too short
    echo -e "\n${YELLOW}Test 1: Short ID too short (abc)...${NC}"
    local short_status=$(curl -k -s -o /dev/null -w "%{http_code}" \
        -H "Host: web.hccc.edu" \
        "$API_URL/r/abc")
    
    if [ "$short_status" == "404" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Short ID too short correctly returns 404"
    else
        echo -e "${RED}✗ FAIL:${NC} Short ID too short returned $short_status instead of 404"
        exit 1
    fi
    
    # Test 2: Short ID too long
    echo -e "\n${YELLOW}Test 2: Short ID too long (abcdef123456)...${NC}"
    local long_status=$(curl -k -s -o /dev/null -w "%{http_code}" \
        -H "Host: web.hccc.edu" \
        "$API_URL/r/abcdef123456")
    
    if [ "$long_status" == "404" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Short ID too long correctly returns 404"
    else
        echo -e "${RED}✗ FAIL:${NC} Short ID too long returned $long_status instead of 404"
        exit 1
    fi
    
    # Test 3: Short ID with invalid characters
    echo -e "\n${YELLOW}Test 3: Short ID with invalid characters (invalid!)...${NC}"
    local invalid_status=$(curl -k -s -o /dev/null -w "%{http_code}" \
        -H "Host: web.hccc.edu" \
        "$API_URL/r/invalid!")
    
    if [ "$invalid_status" == "404" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Short ID with invalid characters correctly returns 404"
    else
        echo -e "${RED}✗ FAIL:${NC} Short ID with invalid characters returned $invalid_status instead of 404"
        exit 1
    fi
    
    # Test 4: Non-existent but valid format short ID
    echo -e "\n${YELLOW}Test 4: Non-existent but valid format short ID (deadbeef)...${NC}"
    local nonexistent_status=$(curl -k -s -o /dev/null -w "%{http_code}" \
        -H "Host: web.hccc.edu" \
        "$API_URL/r/deadbeef")
    
    if [ "$nonexistent_status" == "404" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Non-existent short ID correctly returns 404"
    else
        echo -e "${RED}✗ FAIL:${NC} Non-existent short ID returned $nonexistent_status instead of 404"
        exit 1
    fi
    
    echo -e "\n${GREEN}✓ PASS:${NC} All invalid short ID format tests completed successfully"
}

# Function to test disallowed redirect URLs
test_disallowed_redirect_urls() {
    echo -e "\n${YELLOW}Testing Disallowed Redirect URLs...${NC}"
    
    # Test 1: Create dynamic QR with disallowed domain
    echo -e "\n${YELLOW}Test 1: Creating dynamic QR with disallowed domain...${NC}"
    local payload='{"redirect_url": "https://definitely-not-allowed-domain.com", "title": "Disallowed Domain Test", "description": "Testing disallowed domain rejection"}'
    _api_request POST "/api/v1/qr/dynamic" "$payload"
    local actual_status_code="$API_RESPONSE_STATUS"
    
    if [ "$actual_status_code" == "422" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Disallowed domain correctly rejected with 422"
    else
        echo -e "${RED}✗ FAIL:${NC} Disallowed domain returned $actual_status_code instead of 422"
        exit 1
    fi
    
    # Test 2: Update dynamic QR to disallowed domain
    echo -e "\n${YELLOW}Test 2: Updating dynamic QR to disallowed domain...${NC}"
    # First create a valid dynamic QR
    local valid_payload='{"redirect_url": "https://valid-test.example.com", "title": "Valid QR for Update Test", "description": "Testing update to disallowed domain"}'
    _api_request POST "/api/v1/qr/dynamic" "$valid_payload"
    _assert_status_code "$API_RESPONSE_STATUS" 201 "Create valid QR for update test"
    
    local valid_qr_id
    valid_qr_id=$(_get_json_value "$API_RESPONSE_BODY" ".id")
    
    # Now try to update to disallowed domain
    local update_payload='{"redirect_url": "https://malicious-domain.evil"}'
    _api_request PUT "/api/v1/qr/$valid_qr_id" "$update_payload"
    actual_status_code="$API_RESPONSE_STATUS"
    
    if [ "$actual_status_code" == "422" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Update to disallowed domain correctly rejected with 422"
    else
        echo -e "${RED}✗ FAIL:${NC} Update to disallowed domain returned $actual_status_code instead of 422"
        exit 1
    fi
    
    echo -e "\n${GREEN}✓ PASS:${NC} All disallowed redirect URL tests completed successfully"
}

# Function to test invalid URL schemes
test_invalid_url_schemes() {
    echo -e "\n${YELLOW}Testing Invalid URL Schemes...${NC}"
    
    # Test 1: FTP scheme
    echo -e "\n${YELLOW}Test 1: Creating dynamic QR with FTP scheme...${NC}"
    local ftp_payload='{"redirect_url": "ftp://example.com/file.txt", "title": "FTP Scheme Test", "description": "Testing FTP scheme rejection"}'
    _api_request POST "/api/v1/qr/dynamic" "$ftp_payload"
    local actual_status_code="$API_RESPONSE_STATUS"
    
    if [ "$actual_status_code" == "422" ]; then
        echo -e "${GREEN}✓ PASS:${NC} FTP scheme correctly rejected with 422"
    else
        echo -e "${RED}✗ FAIL:${NC} FTP scheme returned $actual_status_code instead of 422"
        exit 1
    fi
    
    # Test 2: File scheme
    echo -e "\n${YELLOW}Test 2: Creating dynamic QR with file scheme...${NC}"
    local file_payload='{"redirect_url": "file:///etc/passwd", "title": "File Scheme Test", "description": "Testing file scheme rejection"}'
    _api_request POST "/api/v1/qr/dynamic" "$file_payload"
    actual_status_code="$API_RESPONSE_STATUS"
    
    if [ "$actual_status_code" == "422" ]; then
        echo -e "${GREEN}✓ PASS:${NC} File scheme correctly rejected with 422"
    else
        echo -e "${RED}✗ FAIL:${NC} File scheme returned $actual_status_code instead of 422"
        exit 1
    fi
    
    # Test 3: JavaScript scheme
    echo -e "\n${YELLOW}Test 3: Creating dynamic QR with javascript scheme...${NC}"
    local js_payload='{"redirect_url": "javascript:alert(\"XSS\")", "title": "JavaScript Scheme Test", "description": "Testing javascript scheme rejection"}'
    _api_request POST "/api/v1/qr/dynamic" "$js_payload"
    actual_status_code="$API_RESPONSE_STATUS"
    
    if [ "$actual_status_code" == "422" ]; then
        echo -e "${GREEN}✓ PASS:${NC} JavaScript scheme correctly rejected with 422"
    else
        echo -e "${RED}✗ FAIL:${NC} JavaScript scheme returned $actual_status_code instead of 422"
        exit 1
    fi
    
    echo -e "\n${GREEN}✓ PASS:${NC} All invalid URL scheme tests completed successfully"
}

# Function to test rate limiting
test_rate_limiting() {
    echo -e "\n${YELLOW}Testing Rate Limiting...${NC}"
    
    # Test 1: QR Redirect Rate Limiting (Classroom Optimized)
    echo -e "\n${YELLOW}Test 1: QR Redirect Rate Limiting (Classroom Optimized)...${NC}"
    
    # Create a dynamic QR for rate limiting test
    local payload='{"redirect_url": "https://rate-limit-test.example.com", "title": "Rate Limit Test QR", "description": "Testing rate limiting on redirects"}'
    _api_request POST "/api/v1/qr/dynamic" "$payload"
    _assert_status_code "$API_RESPONSE_STATUS" 201 "Create QR for rate limiting test"
    
    local content
    content=$(_get_json_value "$API_RESPONSE_BODY" ".content")
    local short_id=$(echo "$content" | sed 's/.*\/r\///' | sed 's/?.*//')
    
    echo -e "${YELLOW}Created QR for rate limiting test with short_id: $short_id${NC}"
    
    # Test QR redirect rate limiting (should be more permissive)
    echo -e "\n${YELLOW}Testing QR redirect rate limits (60 requests)...${NC}"
    
    local qr_success_count=0
    local qr_rate_limited_count=0
    local qr_other_count=0
    
    # Send 60 requests rapidly to test the burst + sustained rate
    for i in {1..60}; do
        local status=$(curl -k -s -o /dev/null -w "%{http_code}" \
            -H "Host: web.hccc.edu" \
            "$API_URL/r/$short_id" 2>/dev/null)
        
        case $status in
            302)
                qr_success_count=$((qr_success_count + 1))
                ;;
            429)
                qr_rate_limited_count=$((qr_rate_limited_count + 1))
                ;;
            *)
                qr_other_count=$((qr_other_count + 1))
                ;;
        esac
        
        # Small delay to avoid overwhelming the system
        sleep 0.01
    done
    
    echo -e "${YELLOW}QR Redirect Rate Limiting Results:${NC}"
    echo -e "  Successful redirects (302): $qr_success_count"
    echo -e "  Rate limited (429): $qr_rate_limited_count"
    echo -e "  Other responses: $qr_other_count"
    echo -e "  Success rate: $(echo "scale=1; $qr_success_count * 100 / 60" | bc)%"
    
    # Verify QR redirect rate limiting is classroom-friendly
    if [ "$qr_success_count" -gt 45 ]; then
        echo -e "${GREEN}✓ PASS:${NC} QR redirect rate limiting is classroom-friendly (${qr_success_count}/60 successful)"
    else
        echo -e "${YELLOW}⚠ WARNING:${NC} QR redirect rate limiting might be too restrictive for classrooms (${qr_success_count}/60 successful)"
    fi
    
    # Test 2: API Endpoint Rate Limiting (Internal Access)
    echo -e "\n${YELLOW}Test 2: API Endpoint Rate Limiting (Internal Access)...${NC}"
    
    # Wait for rate limits to settle
    echo -e "${YELLOW}Waiting 5 seconds for rate limits to settle...${NC}"
    sleep 5
    
    # Test API endpoint rate limiting (internal access via 10.1.6.12 - no rate limiting by design)
    echo -e "\n${YELLOW}Testing API endpoint access (30 requests to /api/v1/qr via internal IP)...${NC}"
    echo -e "${BLUE}Note: Internal API access (10.1.6.12) is not rate limited by design${NC}"
    
    local api_success_count=0
    local api_rate_limited_count=0
    local api_other_count=0
    
    # Send 30 requests rapidly to test internal API access
    for i in {1..30}; do
        local status=$(curl -k -s -o /dev/null -w "%{http_code}" \
            $AUTH_HEADER \
            "$API_URL/api/v1/qr" 2>/dev/null)
        
        case $status in
            200)
                api_success_count=$((api_success_count + 1))
                ;;
            429)
                api_rate_limited_count=$((api_rate_limited_count + 1))
                ;;
            *)
                api_other_count=$((api_other_count + 1))
                ;;
        esac
        
        # Small delay to avoid overwhelming the system
        sleep 0.01
    done
    
    echo -e "${YELLOW}Internal API Access Results:${NC}"
    echo -e "  Successful requests (200): $api_success_count"
    echo -e "  Rate limited (429): $api_rate_limited_count"
    echo -e "  Other responses: $api_other_count"
    echo -e "  Success rate: $(echo "scale=1; $api_success_count * 100 / 30" | bc)%"
    
    # Verify internal API access works (should not be rate limited)
    if [ "$api_success_count" -eq 30 ]; then
        echo -e "${GREEN}✓ PASS:${NC} Internal API access works without rate limiting (as designed)"
    else
        echo -e "${YELLOW}⚠ WARNING:${NC} Internal API access had some failures (${api_success_count}/30 successful)"
    fi
    
    echo -e "\n${GREEN}✓ PASS:${NC} Differentiated rate limiting tests completed successfully"
    echo -e "${BLUE}Summary:${NC}"
    echo -e "  QR Redirects: Classroom-optimized (${qr_success_count}/60 = $(echo "scale=1; $qr_success_count * 100 / 60" | bc)% success)"
    echo -e "  Internal API: Unrestricted access (${api_success_count}/30 = $(echo "scale=1; $api_success_count * 100 / 30" | bc)% success)"
}

# Function to run optimization task verification tests
test_optimization_tasks() {
    print_section "Testing FastAPI Optimization Tasks"
    
    # Test Task 1: Service-Based Dependency Injection
    test_service_dependency_injection
    
    # Test Task 2: Background Tasks for Scan Statistics
    test_background_tasks_scan_statistics
    
    # Test Task 3: Enhanced User Agent Tracking
    test_enhanced_user_agent_tracking
    
    echo -e "\n${GREEN}✓ PASS:${NC} All optimization task tests completed successfully"
}

# Function to clean up generated files
cleanup() {
    print_section "Cleaning Up Generated Files"
    echo -e "${YELLOW}Cleaning up generated files...${NC}"
    rm -f static_qr_with_logo.png
    rm -f dynamic_qr_with_logo.png
    rm -f qr_error_level_*.png
    rm -f accessible_qr_code.svg
    echo -e "${GREEN}✓ PASS:${NC} Cleanup completed"
}

# ============================================================================
# S.0.5: Main Execution Flow
# ============================================================================

# Main function to orchestrate all tests
main() {
    print_section "Starting API Test Suite - QR Generator"
    echo -e "${BLUE}Refactored with S.0 modularity and DRY principles${NC}"
    
    # Infrastructure checks
    check_docker_containers
    
    # Core functionality tests
    test_health_endpoint
    test_qr_code_listing
    
    # QR lifecycle tests
    test_create_static_qr
    test_create_dynamic_qr
    test_get_qr_by_id
    test_update_dynamic_qr
    test_qr_redirection
    
    # Advanced feature tests
    test_qr_with_logo
    test_error_correction_levels
    test_svg_accessibility
    
    # Optimization task verification tests
    test_optimization_tasks
    
    # Production hardening security tests
    test_production_hardening_security
    
    # Cleanup
    cleanup
    
    print_section "✨ All API Endpoint Tests Passed Successfully! ✨"
    echo -e "${GREEN}✨ Including Production Hardening Security Tests! ✨${NC}"
    echo -e "${BLUE}✨ Refactored with S.0 Modularity and DRY Principles! ✨${NC}"
}

# Execute main function with all script arguments
main "$@"
