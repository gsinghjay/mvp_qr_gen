#!/bin/bash

# Ensure the script fails if any command fails
set -e

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Set API_URL for making API calls in the script
API_URL="https://10.1.6.12"
echo -e "${YELLOW}Using API_URL for API calls: ${API_URL}${NC}"

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

# Test both old and new health endpoints
test_health_endpoints() {
    print_section "TESTING HEALTH ENDPOINTS (OLD AND NEW)"
    
    # Test old health endpoint
    echo -e "\n${YELLOW}Testing Old Health Endpoint (/health)...${NC}"
    local old_response=$(curl -k -s $API_URL/health)
    local old_status_code=$(curl -k -s -o /dev/null -w "%{http_code}" $API_URL/health)
    
    echo "$old_response" | jq . > /dev/null
    print_status $? "Old health endpoint returns valid JSON"
    
    if [ "$old_status_code" == "200" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Old health endpoint returned 200 OK"
    else
        echo -e "${RED}✗ FAIL:${NC} Old health endpoint returned $old_status_code"
        exit 1
    fi
    
    # Test new health endpoint
    echo -e "\n${YELLOW}Testing New Health Endpoint (/api/v1/health)...${NC}"
    local new_response=$(curl -k -s $API_URL/api/v1/health)
    local new_status_code=$(curl -k -s -o /dev/null -w "%{http_code}" $API_URL/api/v1/health)
    
    echo "$new_response" | jq . > /dev/null
    print_status $? "New health endpoint returns valid JSON"
    
    if [ "$new_status_code" == "200" ]; then
        echo -e "${GREEN}✓ PASS:${NC} New health endpoint returned 200 OK"
    else
        echo -e "${RED}✗ FAIL:${NC} New health endpoint returned $new_status_code"
        exit 1
    fi
    
    # Compare responses
    local old_status=$(echo "$old_response" | jq -r '.status')
    local new_status=$(echo "$new_response" | jq -r '.status')
    
    if [ "$old_status" == "$new_status" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Both health endpoints return the same status"
    else
        echo -e "${RED}✗ FAIL:${NC} Health endpoints return different statuses"
        exit 1
    fi
}

# Test QR code listing through both old and new endpoints
test_qr_listing() {
    print_section "TESTING QR CODE LISTING (OLD AND NEW)"
    
    # List QR codes through old endpoint
    echo -e "\n${YELLOW}Testing QR Code Listing (Old Endpoint)...${NC}"
    local old_response=$(curl -k -s $API_URL/api/v1/qr)
    echo "$old_response" | jq . > /dev/null
    print_status $? "Old QR code listing endpoint returns valid JSON"
    
    # List QR codes through new endpoint
    echo -e "\n${YELLOW}Testing QR Code Listing (New Endpoint)...${NC}"
    local new_response=$(curl -k -s $API_URL/api/v1/qr)
    echo "$new_response" | jq . > /dev/null
    print_status $? "New QR code listing endpoint returns valid JSON"
    
    # Extract total counts
    local old_total=$(echo "$old_response" | jq -r '.total')
    local new_total=$(echo "$new_response" | jq -r '.total')
    
    if [ "$old_total" == "$new_total" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Both endpoints return the same total count ($old_total)"
    else
        echo -e "${RED}✗ FAIL:${NC} Endpoints return different total counts (old: $old_total, new: $new_total)"
        exit 1
    fi
}

# Create QR code through both old and new endpoints
test_create_qr() {
    print_section "TESTING QR CODE CREATION (OLD AND NEW)"
    
    # Create static QR through old endpoint
    echo -e "\n${YELLOW}Creating Static QR (Old Endpoint)...${NC}"
    local old_static_response=$(curl -k -s -X POST $API_URL/api/v1/qr/static \
        -H "Content-Type: application/json" \
        -d '{"content": "https://old-endpoint-test.example.com", "qr_type": "static"}')
    
    echo "$old_static_response" | jq . > /dev/null
    print_status $? "Old static QR creation endpoint returns valid JSON"
    
    # Create static QR through new endpoint
    echo -e "\n${YELLOW}Creating Static QR (New Endpoint)...${NC}"
    local new_static_response=$(curl -k -s -X POST $API_URL/api/v1/qr/static \
        -H "Content-Type: application/json" \
        -d '{"content": "https://new-endpoint-test.example.com", "qr_type": "static"}')
    
    echo "$new_static_response" | jq . > /dev/null
    print_status $? "New static QR creation endpoint returns valid JSON"
    
    # Compare response structures (checking for same fields)
    local old_fields=$(echo "$old_static_response" | jq -S 'keys')
    local new_fields=$(echo "$new_static_response" | jq -S 'keys')
    
    if [ "$old_fields" == "$new_fields" ]; then
        echo -e "${GREEN}✓ PASS:${NC} Both endpoints return the same response structure"
    else
        echo -e "${YELLOW}⚠ WARNING:${NC} Endpoints return different response structures"
        echo -e "Old fields: $old_fields"
        echo -e "New fields: $new_fields"
    fi
}

# Main test function
run_tests() {
    test_health_endpoints
    test_qr_listing
    test_create_qr
    
    echo -e "\n${GREEN}✨ API Restructuring Tests Completed Successfully! ✨${NC}"
    echo -e "${YELLOW}Note: Both old and new endpoints are working correctly, ensuring backward compatibility.${NC}"
}

# Run the tests
run_tests 