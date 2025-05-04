#!/bin/bash
#
# QR App Performance Test Script
# Version: 1.0
# Created: $(date +%Y-%m-%d)
#
# This script tests the performance of key endpoints in the QR Code Generator application,
# focusing on measuring the difference between cold start (first request) and warm (subsequent)
# request times. This is particularly useful for verifying the effectiveness of
# initialization optimizations like FastAPI's lifespan context manager.
#
# Usage:
#   ./performance_test.sh [options]
#
# Options:
#   -u, --url URL       Base URL to test (default: https://10.1.6.12)
#   -i, --iterations N  Number of warm requests to make per endpoint (default: 3)
#   -o, --output FILE   Output file for CSV results (default: performance_results.csv)
#   -h, --help          Show this help message
#   -v, --verbose       Show more detailed output
#
# Example:
#   ./performance_test.sh --url https://web.hccc.edu --iterations 5
#
set -e

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
API_URL="https://10.1.6.12"
ITERATIONS=3
WAIT_TIME=1
OUTPUT_FILE="performance_results.csv"
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -u|--url)
            API_URL="$2"
            shift 2
            ;;
        -i|--iterations)
            ITERATIONS="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo
            echo "Options:"
            echo "  -u, --url URL       Base URL to test (default: https://10.1.6.12)"
            echo "  -i, --iterations N  Number of warm requests per endpoint (default: 3)"
            echo "  -o, --output FILE   Output file for CSV results (default: performance_results.csv)"
            echo "  -h, --help          Show this help message"
            echo "  -v, --verbose       Show more detailed output"
            echo
            echo "Example:"
            echo "  $0 --url https://web.hccc.edu --iterations 5"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
done

echo -e "${BLUE}=== QR App Performance Test ===${NC}"
echo -e "${YELLOW}Testing API URL: ${API_URL}${NC}"
echo -e "Date/Time: $(date)"
echo -e "Iterations per endpoint: ${ITERATIONS}"
echo -e "Output file: ${OUTPUT_FILE}"

# Function to test endpoint performance
test_endpoint_performance() {
    local endpoint=$1
    local description=$2
    
    echo -e "\n${BLUE}=== Testing Endpoint: ${description} (${endpoint}) ===${NC}"
    
    # First request (cold start)
    echo -e "${YELLOW}First request (cold start):${NC}"
    local start_time=$(date +%s.%N)
    local status_code=$(curl -k -s -o /dev/null -w "%{http_code}" "${API_URL}${endpoint}")
    local end_time=$(date +%s.%N)
    local first_request_time=$(echo "$end_time - $start_time" | bc)
    
    echo -e "Status code: ${status_code}"
    echo -e "Response time: ${first_request_time} seconds"
    
    # Warm requests
    echo -e "\n${YELLOW}Subsequent requests (warm):${NC}"
    local total_warm_time=0
    
    for (( i=1; i<=$ITERATIONS; i++ )); do
        sleep $WAIT_TIME
        local warm_start_time=$(date +%s.%N)
        local warm_status_code=$(curl -k -s -o /dev/null -w "%{http_code}" "${API_URL}${endpoint}")
        local warm_end_time=$(date +%s.%N)
        local warm_request_time=$(echo "$warm_end_time - $warm_start_time" | bc)
        
        echo -e "Request $i - Status: ${warm_status_code}, Time: ${warm_request_time} seconds"
        total_warm_time=$(echo "$total_warm_time + $warm_request_time" | bc)
    done
    
    local avg_warm_time=$(echo "scale=5; $total_warm_time / $ITERATIONS" | bc)
    local cold_vs_warm_ratio=$(echo "scale=2; $first_request_time / $avg_warm_time" | bc)
    
    echo -e "\n${GREEN}Performance Summary for ${description}:${NC}"
    echo -e "Cold start time: ${first_request_time}s"
    echo -e "Average warm time: ${avg_warm_time}s"
    echo -e "Cold/Warm ratio: ${cold_vs_warm_ratio}x"
    
    # Save results for final report
    echo "${description},${endpoint},${first_request_time},${avg_warm_time},${cold_vs_warm_ratio}" >> $OUTPUT_FILE
}

# Set up results file
echo "Endpoint,Path,Cold Start (s),Warm Average (s),Cold/Warm Ratio" > $OUTPUT_FILE

# Wait for application to be fully available
echo -e "${YELLOW}Waiting for application to be ready...${NC}"
ready=false
max_attempts=15
attempt=1

while [ $attempt -le $max_attempts ] && [ "$ready" = false ]; do
    echo "Attempt $attempt of $max_attempts..."
    health_status=$(curl -k -s -o /dev/null -w "%{http_code}" "${API_URL}/health" || echo "000")
    
    if [ "$health_status" = "200" ]; then
        echo -e "${GREEN}Application is ready!${NC}"
        ready=true
    else
        echo -e "${YELLOW}Application not ready yet (status: $health_status), waiting...${NC}"
        sleep 2
        ((attempt++))
    fi
done

if [ "$ready" = false ]; then
    echo -e "${RED}Could not confirm application readiness after $max_attempts attempts.${NC}"
    exit 1
fi

# Test key endpoints
test_endpoint_performance "/health" "Health Check"
test_endpoint_performance "/api/v1/qr?limit=1" "QR Listing"
test_endpoint_performance "/" "Home Page"

# Need to find a valid short_id for testing redirect
echo -e "\n${YELLOW}Creating a test dynamic QR code for redirect testing...${NC}"
REDIRECT_RESPONSE=$(curl -k -s -X POST "${API_URL}/api/v1/qr/dynamic" \
    -H "Content-Type: application/json" \
    -d '{"content": "perf-test", "redirect_url": "https://example.com"}')

QR_ID=$(echo "$REDIRECT_RESPONSE" | grep -o '"id":"[^"]*' | sed 's/"id":"//g')
CONTENT=$(curl -k -s "${API_URL}/api/v1/qr/$QR_ID" | grep -o '"content":"[^"]*' | sed 's/"content":"//g')
SHORT_ID=$(echo "$CONTENT" | sed 's/.*\/r\///')

if [ -n "$SHORT_ID" ]; then
    echo -e "${GREEN}Created test QR with short ID: $SHORT_ID${NC}"
    test_endpoint_performance "/r/$SHORT_ID" "QR Redirect"
else
    echo -e "${RED}Failed to create test QR code for redirect testing${NC}"
fi

# Generate final report
echo -e "\n${BLUE}=== PERFORMANCE TEST SUMMARY ===${NC}"
echo -e "${YELLOW}Date:${NC} $(date)"

# Calculate overall improvement metrics
COLD_AVG=$(awk -F, 'NR>1 {sum+=$3; count++} END {print sum/count}' $OUTPUT_FILE)
WARM_AVG=$(awk -F, 'NR>1 {sum+=$4; count++} END {print sum/count}' $OUTPUT_FILE)
OVERALL_RATIO=$(echo "scale=2; $COLD_AVG / $WARM_AVG" | bc)

echo -e "\n${BLUE}Overall Performance Metrics:${NC}"
echo -e "Average cold start time: ${COLD_AVG}s"
echo -e "Average warm request time: ${WARM_AVG}s"
echo -e "Average cold/warm ratio: ${OVERALL_RATIO}x"

# Show detailed results
echo -e "\n${BLUE}Detailed Results:${NC}"
column -t -s, $OUTPUT_FILE

echo -e "\n${GREEN}Performance test completed! Results saved to $OUTPUT_FILE${NC}"

# Append results to a historical log file if verbose is enabled
if [ "$VERBOSE" = true ]; then
    HISTORY_FILE="performance_history.log"
    echo "$(date +%Y-%m-%d_%H:%M:%S),${API_URL},${COLD_AVG},${WARM_AVG},${OVERALL_RATIO}" >> $HISTORY_FILE
    echo -e "${BLUE}Historical data appended to $HISTORY_FILE${NC}"
fi 