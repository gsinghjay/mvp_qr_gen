#!/bin/bash

# Ensure the script fails if any command fails
set -e

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Function to check Docker containers
check_docker_containers() {
    echo -e "\n${YELLOW}Checking Docker containers...${NC}"
    docker ps | grep -E 'qr_generator_api|qr_generator_traefik'
    print_status $? "Docker containers are running"
}

# Function to test health endpoint
test_health_endpoint() {
    echo -e "\n${YELLOW}Testing Health Endpoint...${NC}"
    local response=$(curl -k -s https://localhost/health)
    local status_code=$(curl -k -s -o /dev/null -w "%{http_code}" https://localhost/health)
    
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
    local response=$(curl -k -s https://localhost/api/v1/qr)
    echo "$response" | jq . > /dev/null
    print_status $? "QR code listing endpoint returns valid JSON"
}

# Function to create static QR code
test_create_static_qr() {
    echo -e "\n${YELLOW}Testing Create Static QR Code...${NC}"
    local response=$(curl -k -s -X POST https://localhost/api/v1/qr/static \
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
    local response=$(curl -k -s -X POST https://localhost/api/v1/qr/dynamic \
        -H "Content-Type: application/json" \
        -d '{"content": "test-dynamic", "redirect_url": "https://test-dynamic.example.com"}')
    
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
    local static_response=$(curl -k -s https://localhost/api/v1/qr/$STATIC_QR_ID)
    local dynamic_response=$(curl -k -s https://localhost/api/v1/qr/$DYNAMIC_QR_ID)
    
    echo "$static_response" | jq . > /dev/null
    print_status $? "Get static QR code by ID successful"
    
    echo "$dynamic_response" | jq . > /dev/null
    print_status $? "Get dynamic QR code by ID successful"
}

# Function to update dynamic QR code
test_update_dynamic_qr() {
    echo -e "\n${YELLOW}Testing Update Dynamic QR Code...${NC}"
    local response=$(curl -k -X PUT https://localhost/api/v1/qr/$DYNAMIC_QR_ID -H "Content-Type: application/json" -d '{"redirect_url": "https://updated-example.com"}' | jq)
    
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
    # Extract short ID from the dynamic QR code's content
    local SHORT_ID=$(curl -k -s https://localhost/api/v1/qr/$DYNAMIC_QR_ID | jq -r '.content' | sed 's/\/r\///')
    
    # Check redirection
    local redirect_response=$(curl -k -s -L -o /dev/null -w "%{http_code}" https://localhost/r/$SHORT_ID)
    
    if [ "$redirect_response" == "302" ]; then
        echo -e "${GREEN}✓ PASS:${NC} QR code redirection successful (302 status)"
    else
        echo -e "${RED}✗ FAIL:${NC} QR code redirection failed (status: $redirect_response)"
        exit 1
    fi
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
    
    echo -e "\n${GREEN}✨ All API Endpoint Tests Passed Successfully! ✨${NC}"
}

# Run the tests
run_tests
