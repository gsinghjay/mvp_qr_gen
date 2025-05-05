#!/bin/bash

# Ensure the script fails if any command fails
set -e

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}Loading environment variables from .env file...${NC}"
    source .env
fi

# Set BASE_URL for QR code content (what users will scan)
BASE_URL=${BASE_URL:-"https://web.hccc.edu"}
# Set API_URL for making API calls in the script
API_URL=${API_URL:-"https://10.1.6.12"}
# Auth credentials
AUTH_USER=${AUTH_USER:-"admin_user"}
AUTH_PASS=${AUTH_PASS:-"strong"}
AUTH_HEADER="--user ${AUTH_USER}:${AUTH_PASS}"

echo -e "${YELLOW}Using BASE_URL for QR codes: ${BASE_URL}${NC}"
echo -e "${YELLOW}Using API_URL for API calls: ${API_URL}${NC}"
echo -e "${YELLOW}Using authentication: ${AUTH_USER}${NC}"

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

# Function to check Docker containers
check_docker_containers() {
    echo -e "\n${YELLOW}Checking Docker containers...${NC}"
    docker ps | grep -E 'qr_generator_api|qr_generator_traefik'
    print_status $? "Docker containers are running"
}

# Function to test health endpoint
test_health_endpoint() {
    echo -e "\n${YELLOW}Testing Health Endpoint...${NC}"
    local response=$(curl -k -s $AUTH_HEADER $API_URL/health)
    local status_code=$(curl -k -s $AUTH_HEADER -o /dev/null -w "%{http_code}" $API_URL/health)
    
    echo "$response" | jq . > /dev/null
    print_status $? "Health endpoint returns valid JSON"
    
    if [ "$status_code" == "200" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Health endpoint returned 200 OK"
    else
        echo -e "${RED}✗ FAIL:${NC} Health endpoint returned $status_code"
        exit 1
    fi
}

# Function to test QR code listing
test_qr_code_listing() {
    echo -e "\n${YELLOW}Testing QR Code Listing...${NC}"
    local response=$(curl -k -s $AUTH_HEADER $API_URL/api/v1/qr)
    echo "$response" | jq . > /dev/null
    print_status $? "QR code listing endpoint returns valid JSON"
}

# Function to create static QR code
test_create_static_qr() {
    echo -e "\n${YELLOW}Testing Create Static QR Code...${NC}"
    local response=$(curl -k -s $AUTH_HEADER -X POST $API_URL/api/v1/qr/static \
        -H "Content-Type: application/json" \
        -d '{"content": "https://test.example.com", "qr_type": "static"}')
    
    STATIC_QR_ID=$(echo "$response" | jq -r '.id')
    echo "$response" | jq . > /dev/null
    print_status $? "Static QR code creation successful"
    
    if [ -z "$STATIC_QR_ID" ] || [ "$STATIC_QR_ID" == "null" ]; then
        echo -e "${RED}✗ FAIL:${NC} No valid QR code ID received"
        exit 1
    fi
}

# Function to create dynamic QR code
test_create_dynamic_qr() {
    echo -e "\n${YELLOW}Testing Create Dynamic QR Code...${NC}"
    local response=$(curl -k -s $AUTH_HEADER -X POST $API_URL/api/v1/qr/dynamic \
        -H "Content-Type: application/json" \
        -d '{"content": "test-dynamic", "redirect_url": "https://technological-alchemist.vercel.app"}')
    
    DYNAMIC_QR_ID=$(echo "$response" | jq -r '.id')
    echo "$response" | jq . > /dev/null
    print_status $? "Dynamic QR code creation successful"
    
    if [ -z "$DYNAMIC_QR_ID" ] || [ "$DYNAMIC_QR_ID" == "null" ]; then
        echo -e "${RED}✗ FAIL:${NC} No valid QR code ID received"
        exit 1
    fi
}

# Function to get QR code by ID
test_get_qr_by_id() {
    echo -e "\n${YELLOW}Testing Get QR Code by ID...${NC}"
    local static_response=$(curl -k -s $AUTH_HEADER $API_URL/api/v1/qr/$STATIC_QR_ID)
    local dynamic_response=$(curl -k -s $AUTH_HEADER $API_URL/api/v1/qr/$DYNAMIC_QR_ID)
    
    echo "$static_response" | jq . > /dev/null
    print_status $? "Get static QR code by ID successful"
    
    echo "$dynamic_response" | jq . > /dev/null
    print_status $? "Get dynamic QR code by ID successful"
}

# Function to update dynamic QR code
test_update_dynamic_qr() {
    echo -e "\n${YELLOW}Testing Update Dynamic QR Code...${NC}"
    local response=$(curl -k $AUTH_HEADER -X PUT $API_URL/api/v1/qr/$DYNAMIC_QR_ID -H "Content-Type: application/json" -d '{"redirect_url": "https://updated-example.com"}' -s | jq)
    
    # Check if jq parsing was successful
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ FAIL:${NC} Invalid JSON response"
        exit 1
    fi
    
    # Extract the redirect URL from the response and remove trailing slash
    local updated_url=$(echo "$response" | jq -r '.redirect_url' | sed 's:/*$::')
    local expected_url="https://updated-example.com"
    
    # Debugging output
    echo -e "${YELLOW}Full Response:${NC}"
    echo "$response"
    
    echo -e "\n${YELLOW}Updated URL:${NC} $updated_url"
    
    # Check if the URL was updated correctly (ignoring trailing slash)
    if [ "$updated_url" != "$expected_url" ]; then
        echo -e "${RED}✗ FAIL:${NC} URL not updated correctly"
        echo -e "${YELLOW}Debug Information:${NC}"
        echo "Expected URL: $expected_url"
        echo "Actual URL:   $updated_url"
        exit 1
    fi
    
    echo -e "${GREEN}✓ PASS:${NC} Dynamic QR code URL updated successfully"
}

# Function to test QR code redirection
test_qr_redirection() {
    echo -e "\n${YELLOW}Testing QR Code Redirection...${NC}"
    
    # Get the full content of the dynamic QR code
    local CONTENT=$(curl -k -s $AUTH_HEADER $API_URL/api/v1/qr/$DYNAMIC_QR_ID | jq -r '.content')
    echo -e "${YELLOW}QR code content:${NC} $CONTENT"
    
    # Extract short ID from the dynamic QR code's content
    local SHORT_ID=$(echo "$CONTENT" | sed 's/.*\/r\///')
    echo -e "${YELLOW}Extracted short ID:${NC} $SHORT_ID"
    
    # Check if content starts with expected BASE_URL
    if [[ "$CONTENT" == "$BASE_URL/r/"* ]]; then
        echo -e "${GREEN}✓ PASS:${NC} QR code content has expected BASE_URL format"
    else
        echo -e "${YELLOW}⚠ WARNING:${NC} QR code content does not match BASE_URL format"
        echo -e "Expected format: ${BASE_URL}/r/{short_id}"
        echo -e "Actual content: $CONTENT"
    fi
    
    # Check redirection
    local redirect_response=$(curl -k -s -L -o /dev/null -w "%{http_code}" $API_URL/r/$SHORT_ID)
    
    if [ "$redirect_response" == "302" ]; then
        echo -e "${GREEN}✓ PASS:${NC} QR code redirection successful (302 status)"
    else
        echo -e "${RED}✗ FAIL:${NC} QR code redirection failed (status: $redirect_response)"
        exit 1
    fi
}

# Function to test service-based dependency injection (Task 1)
test_service_dependency_injection() {
    echo -e "\n${YELLOW}Testing Service-Based Dependency Injection (Task 1)...${NC}"
    
    # Test 1: Create a QR code with specific parameters to test service layer
    local response=$(curl -k -s $AUTH_HEADER -X POST $API_URL/api/v1/qr/static \
        -H "Content-Type: application/json" \
        -d '{"content": "https://service-test.example.com", "qr_type": "static", "fill_color": "#333333", "back_color": "#FFFFFF"}')
    
    local service_qr_id=$(echo "$response" | jq -r '.id')
    echo "$response" | jq . > /dev/null
    print_status $? "Service layer QR code creation successful"
    
    # Test 2: Verify service properly handles the fill_color parameter
    local fill_color=$(echo "$response" | jq -r '.fill_color')
    if [ "$fill_color" == "#333333" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Service layer correctly processed fill_color parameter"
    else
        echo -e "${RED}✗ FAIL:${NC} Service layer did not process fill_color parameter correctly"
        echo -e "${YELLOW}Debug Information:${NC}"
        echo "Expected fill_color: #333333"
        echo "Actual fill_color:   $fill_color"
        exit 1
    fi
    
    # Test 3: Verify service returns consistent data structure
    local created_at=$(echo "$response" | jq -r '.created_at')
    if [ -z "$created_at" ] || [ "$created_at" == "null" ]; then
        echo -e "${RED}✗ FAIL:${NC} Service layer did not return created_at timestamp"
        exit 1
    else
        echo -e "${GREEN}✓ PASS:${NC} Service layer returned proper timestamp data"
    fi
}

# Function to test background tasks for scan statistics (Task 2)
test_background_tasks_scan_statistics() {
    echo -e "\n${YELLOW}Testing Background Tasks for Scan Statistics (Task 2)...${NC}"
    
    # Create a new dynamic QR code for testing
    local response=$(curl -k -s $AUTH_HEADER -X POST $API_URL/api/v1/qr/dynamic \
        -H "Content-Type: application/json" \
        -d '{"content": "background-task-test", "redirect_url": "https://background-task.example.com"}')
    
    local bg_qr_id=$(echo "$response" | jq -r '.id')
    echo "$response" | jq . > /dev/null
    print_status $? "Created QR code for background task testing"
    
    # Get the full content of the dynamic QR code
    local CONTENT=$(echo "$response" | jq -r '.content')
    echo -e "${YELLOW}QR code content:${NC} $CONTENT"
    
    # Extract short ID from the dynamic QR code's content
    local SHORT_ID=$(echo "$CONTENT" | sed 's/.*\/r\///')
    echo -e "${YELLOW}Extracted short ID:${NC} $SHORT_ID"
    
    # Check if content starts with expected BASE_URL
    if [[ "$CONTENT" == "$BASE_URL/r/"* ]]; then
        echo -e "${GREEN}✓ PASS:${NC} QR code content has expected BASE_URL format"
    else
        echo -e "${YELLOW}⚠ WARNING:${NC} QR code content does not match BASE_URL format"
        echo -e "Expected format: ${BASE_URL}/r/{short_id}"
        echo -e "Actual content: $CONTENT"
    fi
    
    # Get initial scan count
    local initial_response=$(curl -k -s $AUTH_HEADER $API_URL/api/v1/qr/$bg_qr_id)
    local initial_scan_count=$(echo "$initial_response" | jq -r '.scan_count')
    echo -e "${YELLOW}Initial scan count:${NC} $initial_scan_count"
    
    # Test 1: Measure response time for redirection (should be fast if using background tasks)
    echo -e "${YELLOW}Testing redirection response time...${NC}"
    local start_time=$(date +%s.%N)
    local redirect_status=$(curl -k -s -o /dev/null -w "%{http_code}" $API_URL/r/$SHORT_ID)
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
    
    # Test 2: Wait a moment for background task to complete
    echo -e "${YELLOW}Waiting for background task to complete...${NC}"
    sleep 3
    
    # Test 3: Verify scan count was updated
    local updated_response=$(curl -k -s $AUTH_HEADER $API_URL/api/v1/qr/$bg_qr_id)
    local updated_scan_count=$(echo "$updated_response" | jq -r '.scan_count')
    echo -e "${YELLOW}Updated scan count:${NC} $updated_scan_count"
    
    if [ "$updated_scan_count" -gt "$initial_scan_count" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Scan count was updated by background task (${initial_scan_count} -> ${updated_scan_count})"
    else
        echo -e "${RED}✗ FAIL:${NC} Scan count was not updated by background task"
        echo -e "${YELLOW}Debug Information:${NC}"
        echo "Initial scan count: $initial_scan_count"
        echo "Updated scan count: $updated_scan_count"
        echo "Full response:"
        echo "$updated_response" | jq .
        exit 1
    fi
    
    # Test 4: Verify last_scanned_at was updated
    local last_scanned_at=$(echo "$updated_response" | jq -r '.last_scan_at')
    echo -e "${YELLOW}Last scanned at:${NC} $last_scanned_at"
    
    if [ -z "$last_scanned_at" ] || [ "$last_scanned_at" == "null" ]; then
        # Try alternative field name
        last_scanned_at=$(echo "$updated_response" | jq -r '.last_scanned_at')
        echo -e "${YELLOW}Trying alternative field name - Last scanned at:${NC} $last_scanned_at"
        
        if [ -z "$last_scanned_at" ] || [ "$last_scanned_at" == "null" ]; then
            echo -e "${RED}✗ FAIL:${NC} last_scanned_at timestamp was not updated"
            echo -e "${YELLOW}Full response:${NC}"
            echo "$updated_response" | jq .
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✓ PASS:${NC} last_scanned_at timestamp was updated by background task"
}

# Function to test QR code generation with logo
test_qr_with_logo() {
    print_section "TESTING QR CODE GENERATION WITH LOGO"
    
    # Test static QR with logo
    echo -e "\n${YELLOW}Testing Static QR Code with Logo...${NC}"
    local static_response=$(curl -k -s $AUTH_HEADER -X POST $API_URL/api/v1/qr/static \
        -H "Content-Type: application/json" \
        -d '{
            "content": "https://www.github.com/gsinghjay",
            "qr_type": "static",
            "include_logo": true
        }')
    
    local static_id=$(echo "$static_response" | jq -r '.id')
    echo "$static_response" | jq . > /dev/null
    print_status $? "Static QR code with logo creation successful"
    
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
    local dynamic_response=$(curl -k -s $AUTH_HEADER -X POST $API_URL/api/v1/qr/dynamic \
        -H "Content-Type: application/json" \
        -d '{
            "content": "dynamic-with-logo",
            "redirect_url": "https://technological-alchemist.vercel.app/",
            "include_logo": true
        }')
    
    local dynamic_id=$(echo "$dynamic_response" | jq -r '.id')
    echo "$dynamic_response" | jq . > /dev/null
    print_status $? "Dynamic QR code with logo creation successful"
    
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
    local CONTENT=$(echo "$dynamic_response" | jq -r '.content')
    local SHORT_ID=$(echo "$CONTENT" | sed 's/.*\/r\///')
    local redirect_response=$(curl -k -s -L -o /dev/null -w "%{http_code}" $API_URL/r/$SHORT_ID)
    
    if [ "$redirect_response" == "302" ] || [ "$redirect_response" == "200" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Dynamic QR code with logo redirects successfully (status: $redirect_response)"
    else
        echo -e "${RED}✗ FAIL:${NC} Dynamic QR code with logo redirection failed (status: $redirect_response)"
        exit 1
    fi
}

# Function to test error correction levels
test_error_correction_levels() {
    print_section "TESTING ERROR CORRECTION LEVELS"
    
    # Test QR code with different error correction levels
    echo -e "\n${YELLOW}Testing QR Codes with Different Error Correction Levels...${NC}"
    
    # Array of error correction levels to test
    local error_levels=("l" "m" "q" "h")
    local error_names=("Low" "Medium" "Quartile" "High")
    
    # Loop through each error level and test
    for i in "${!error_levels[@]}"; do
        local error_level="${error_levels[$i]}"
        local error_name="${error_names[$i]}"
        
        echo -e "\n${YELLOW}Testing ${error_name} (${error_level}) Error Correction Level...${NC}"
        
        # Create static QR code with specific error level
        local response=$(curl -k -s $AUTH_HEADER -X POST $API_URL/api/v1/qr/static \
            -H "Content-Type: application/json" \
            -d "{
                \"content\": \"https://error-level-test-${error_level}.example.com\",
                \"qr_type\": \"static\",
                \"error_level\": \"${error_level}\"
            }")
        
        local qr_id=$(echo "$response" | jq -r '.id')
        echo "$response" | jq . > /dev/null
        print_status $? "QR code creation with ${error_name} error level successful"
        
        # Verify error level was set correctly in the response
        local stored_error_level=$(echo "$response" | jq -r '.error_level')
        if [ "$stored_error_level" == "$error_level" ]; then
            echo -e "${GREEN}✓ PASS:${NC} Error level correctly set to ${error_name} (${error_level})"
        else
            echo -e "${RED}✗ FAIL:${NC} Error level not set correctly"
            echo -e "${YELLOW}Debug Information:${NC}"
            echo "Expected error level: ${error_level}"
            echo "Actual error level:   ${stored_error_level}"
            exit 1
        fi
        
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
    print_section "TESTING SVG ACCESSIBILITY OPTIONS"
    
    echo -e "\n${YELLOW}Testing SVG QR Code with Accessibility Options...${NC}"
    
    # Create a QR code with SVG accessibility options
    local response=$(curl -k -s $AUTH_HEADER -X POST $API_URL/api/v1/qr/static \
        -H "Content-Type: application/json" \
        -d '{
            "content": "https://accessibility-test.example.com",
            "qr_type": "static"
        }')
    
    local qr_id=$(echo "$response" | jq -r '.id')
    echo "$response" | jq . > /dev/null
    print_status $? "QR code creation for SVG accessibility test successful"
    
    # Get QR code as SVG with accessibility options - URL encode parameters
    local svg_title="QR Code for Accessibility Testing"
    local svg_description="This QR code links to the accessibility test example website"
    
    # URL encode the title and description to handle spaces and special characters
    local encoded_title=$(echo "$svg_title" | sed -e 's/ /%20/g')
    local encoded_description=$(echo "$svg_description" | sed -e 's/ /%20/g')
    
    echo -e "${YELLOW}Requesting SVG with title and description...${NC}"
    local svg_response=$(curl -k -v $AUTH_HEADER -o "accessible_qr_code.svg" \
        "$API_URL/api/v1/qr/$qr_id/image?image_format=svg&svg_title=${encoded_title}&svg_description=${encoded_description}" 2>&1)
    
    # Output curl verbose info for debugging
    echo -e "${YELLOW}Curl response:${NC}"
    echo "$svg_response" | tail -20
    
    if [ -f "accessible_qr_code.svg" ]; then
        echo -e "${GREEN}✓ PASS:${NC} SVG QR code with accessibility options downloaded successfully"
        
        # Check if SVG file contains title and description
        if grep -q "title" "accessible_qr_code.svg" && grep -q "desc" "accessible_qr_code.svg"; then
            echo -e "${GREEN}✓ PASS:${NC} SVG contains title and description elements"
            
            # Further check if our specific title and description are included
            if grep -q "$svg_title" "accessible_qr_code.svg" || grep -q "$svg_description" "accessible_qr_code.svg"; then
                echo -e "${GREEN}✓ PASS:${NC} SVG contains the title or description text"
            else
                echo -e "${YELLOW}⚠ WARNING:${NC} SVG may not contain the exact title/description text provided"
                echo -e "Expected title: $svg_title"
                echo -e "Expected description: $svg_description"
                echo -e "SVG file content:"
                cat accessible_qr_code.svg | head -20
            fi
        else
            echo -e "${YELLOW}⚠ WARNING:${NC} SVG might not contain title and description elements"
            echo -e "SVG file content:"
            cat accessible_qr_code.svg | head -20
        fi
    else
        echo -e "${RED}✗ FAIL:${NC} Failed to download SVG QR code with accessibility options"
        exit 1
    fi
    
    echo -e "\n${GREEN}✓ PASS:${NC} SVG accessibility tests completed successfully"
}

# Function to run optimization task verification tests
test_optimization_tasks() {
    print_section "TESTING FASTAPI OPTIMIZATION TASKS"
    
    # Test Task 1: Service-Based Dependency Injection
    test_service_dependency_injection
    
    # Test Task 2: Background Tasks for Scan Statistics
    test_background_tasks_scan_statistics
    
    echo -e "\n${GREEN}✓ PASS:${NC} All optimization task tests completed successfully"
}

# Function to clean up generated files
cleanup() {
    echo -e "\n${YELLOW}Cleaning up generated files...${NC}"
    rm -f static_qr_with_logo.png
    rm -f dynamic_qr_with_logo.png
    rm -f qr_error_level_*.png
    rm -f accessible_qr_code.svg
    echo -e "${GREEN}✓ PASS:${NC} Cleanup completed"
}

# Main test function
run_tests() {
    check_docker_containers
    test_health_endpoint
    test_qr_code_listing
    test_create_static_qr
    test_create_dynamic_qr
    test_get_qr_by_id
    test_update_dynamic_qr
    test_qr_redirection
    test_qr_with_logo
    
    # Run new tests for error correction and SVG accessibility
    test_error_correction_levels
    test_svg_accessibility
    
    # Run optimization task verification tests
    test_optimization_tasks
    
    # Clean up generated files
    cleanup
    
    echo -e "\n${GREEN}✨ All API Endpoint Tests Passed Successfully! ✨${NC}"
}

# Run the tests
run_tests
