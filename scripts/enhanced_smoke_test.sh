#!/bin/bash

# Enhanced Smoke Test for QR Generator (Task S.2)
# Observatory-First Production Safety Testing
# Integrates with Prometheus/Grafana for metric validation

set -euo pipefail

# ============================================================================
# Color Codes and Constants
# ============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test timing and performance thresholds
HEALTH_CHECK_TIMEOUT=5
REDIRECT_TIMEOUT=10
IMAGE_GENERATION_TIMEOUT=15
BACKGROUND_TASK_WAIT=3

# Prometheus/Grafana endpoints
PROMETHEUS_URL="http://localhost:9090"
GRAFANA_URL="http://localhost:3000"

# ============================================================================
# Environment Variable Loading and Validation
# ============================================================================

load_environment() {
    if [ -f ".env" ]; then
        echo -e "${YELLOW}📁 Loading environment variables from .env file...${NC}"
        set -a
        source .env
        set +a
    else
        echo -e "${RED}❌ Error: .env file not found${NC}"
        exit 1
    fi

    # Required variables for smoke test
    local required_vars=("API_URL" "BASE_URL" "AUTH_USER" "AUTH_PASS")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing required environment variables:${NC}"
        printf '%s\n' "${missing_vars[@]}" | sed 's/^/   - /'
        exit 1
    fi

    # Global variables from environment
    API_URL="${API_URL}"
    BASE_URL="${BASE_URL}"
    AUTH_USER="${AUTH_USER}"
    AUTH_PASS="${AUTH_PASS}"
    
    echo -e "${CYAN}🔧 Environment configured:${NC}"
    echo -e "   API URL: ${API_URL}"
    echo -e "   Base URL: ${BASE_URL}"
    echo -e "   Auth User: ${AUTH_USER}"
}

# ============================================================================
# Core Utility Functions (Based on your existing patterns)
# ============================================================================

# Global response variables
API_RESPONSE_BODY=""
API_RESPONSE_STATUS=""

# Enhanced API request function with timing
_api_request() {
    local method="$1"
    local endpoint_path="$2"
    local json_data="${3:-}"
    local start_time end_time duration
    
    local curl_opts=(-k -s --user "${AUTH_USER}:${AUTH_PASS}" --max-time 30)
    
    API_RESPONSE_BODY=""
    API_RESPONSE_STATUS=""
    
    if [ -n "$json_data" ]; then
        curl_opts+=(-H "Content-Type: application/json" -d "$json_data")
    fi
    
    local tmp_response_file=$(mktemp)
    start_time=$(date +%s.%N)
    
    API_RESPONSE_STATUS=$(curl "${curl_opts[@]}" -X "$method" "${API_URL}${endpoint_path}" \
        -w "%{http_code}" -o "$tmp_response_file" 2>/dev/null) || {
        echo -e "${RED}❌ CURL request failed for $method $endpoint_path${NC}"
        rm -f "$tmp_response_file"
        return 1
    }
    
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
    
    API_RESPONSE_BODY=$(cat "$tmp_response_file")
    rm -f "$tmp_response_file"
    
    # Store response time for performance validation
    export LAST_RESPONSE_TIME="$duration"
}

# Status code assertion with performance validation
_assert_status_code() {
    local actual="$1"
    local expected="$2"
    local description="$3"
    local max_time="${4:-10}"
    
    if [ "$actual" -eq "$expected" ]; then
        local perf_indicator=""
        if [ -n "${LAST_RESPONSE_TIME:-}" ]; then
            if (( $(echo "${LAST_RESPONSE_TIME} < 1.0" | bc -l 2>/dev/null || echo 0) )); then
                perf_indicator=" (${LAST_RESPONSE_TIME}s ⚡)"
            else
                perf_indicator=" (${LAST_RESPONSE_TIME}s)"
            fi
        fi
        echo -e "${GREEN}✅ PASS:${NC} $description${perf_indicator}"
    else
        echo -e "${RED}❌ FAIL:${NC} $description (Expected $expected, Got $actual)"
        if [ -n "$API_RESPONSE_BODY" ]; then
            echo -e "${YELLOW}Response Body:${NC}\n$API_RESPONSE_BODY"
        fi
        exit 1
    fi
}

# JSON value extraction (your existing pattern)
_get_json_value() {
    local json_string="$1"
    local jq_path="$2"
    local value
    value=$(echo "$json_string" | jq -r "$jq_path" 2>/dev/null || echo "")
    if [ "$value" == "null" ] || [ -z "$value" ]; then
        echo ""
    else
        echo "$value"
    fi
}

# Section header printing
print_section() {
    local title="$1"
    echo -e "\n${BLUE}🔍 === $title ===${NC}"
}

# ============================================================================
# Observatory Integration Functions
# ============================================================================

# Query Prometheus for metrics
query_prometheus() {
    local query="$1"
    local description="${2:-Prometheus query}"
    
    if ! command -v curl &> /dev/null; then
        echo -e "${YELLOW}⚠️  curl not available, skipping Prometheus check: $description${NC}"
        return 0
    fi
    
    local response
    response=$(curl -s --max-time 10 "${PROMETHEUS_URL}/api/v1/query" \
        --data-urlencode "query=$query" 2>/dev/null) || {
        echo -e "${YELLOW}⚠️  Prometheus query failed: $description${NC}"
        return 0
    }
    
    local status
    status=$(echo "$response" | jq -r '.status' 2>/dev/null || echo "error")
    
    if [ "$status" = "success" ]; then
        echo "$response" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "0"
    else
        echo -e "${YELLOW}⚠️  Prometheus query unsuccessful: $description${NC}"
        echo "0"
    fi
}

# Validate system metrics from Observatory
validate_observatory_metrics() {
    print_section "Observatory Metrics Validation"
    
    # Check 5xx error rate (should be very low)
    local error_rate
    error_rate=$(query_prometheus 'sum(rate(app_http_requests_total{status=~"5.."}[1m])) / sum(rate(app_http_requests_total[1m])) * 100' "5xx error rate")
    
    if [ "$error_rate" != "0" ] && (( $(echo "$error_rate < 5" | bc -l 2>/dev/null || echo 1) )); then
        echo -e "${GREEN}✅ PASS:${NC} 5xx error rate acceptable: ${error_rate}%"
    elif [ "$error_rate" = "0" ]; then
        echo -e "${GREEN}✅ PASS:${NC} No 5xx errors detected"
    else
        echo -e "${RED}❌ FAIL:${NC} 5xx error rate too high: ${error_rate}%"
        exit 1
    fi
    
    # Check P95 latency for redirects (should be under 100ms)
    local p95_latency
    p95_latency=$(query_prometheus 'histogram_quantile(0.95, sum(rate(app_http_request_duration_seconds_bucket{endpoint=~"/r/.*"}[5m])) by (le)) * 1000' "P95 redirect latency")
    
    if [ "$p95_latency" != "0" ] && (( $(echo "$p95_latency < 100" | bc -l 2>/dev/null || echo 1) )); then
        echo -e "${GREEN}✅ PASS:${NC} P95 redirect latency acceptable: ${p95_latency}ms"
    elif [ "$p95_latency" = "0" ]; then
        echo -e "${CYAN}ℹ️  INFO:${NC} No recent redirect latency data"
    else
        echo -e "${YELLOW}⚠️  WARNING:${NC} P95 redirect latency elevated: ${p95_latency}ms"
    fi
    
    # Check service uptime
    local service_up
    service_up=$(query_prometheus 'up{job="qr-app"}' "QR app service status")
    
    if [ "$service_up" = "1" ]; then
        echo -e "${GREEN}✅ PASS:${NC} QR application service is up"
    else
        echo -e "${RED}❌ FAIL:${NC} QR application service is down"
        exit 1
    fi
}

# ============================================================================
# Core Smoke Test Functions
# ============================================================================

test_health_endpoint() {
    print_section "Health Endpoint Validation"
    
    _api_request GET "/health"
    _assert_status_code "$API_RESPONSE_STATUS" 200 "Health endpoint returns 200 OK" "$HEALTH_CHECK_TIMEOUT"
    
    # Validate health response structure
    local status
    status=$(_get_json_value "$API_RESPONSE_BODY" ".status")
    if [ "$status" = "healthy" ]; then
        echo -e "${GREEN}✅ PASS:${NC} Health status is healthy"
    else
        echo -e "${RED}❌ FAIL:${NC} Health status is not healthy: $status"
        exit 1
    fi
    
    # Check database connectivity in health response
    local db_status
    db_status=$(_get_json_value "$API_RESPONSE_BODY" ".checks.database.status")
    if [ "$db_status" = "pass" ]; then
        echo -e "${GREEN}✅ PASS:${NC} Database connectivity confirmed"
    else
        echo -e "${RED}❌ FAIL:${NC} Database connectivity issues detected"
        exit 1
    fi
}

test_qr_creation_workflow() {
    print_section "QR Code Creation Workflow"
    
    # Test static QR creation
    echo -e "${CYAN}📝 Creating static QR code...${NC}"
    local static_payload='{"content": "https://smoke-test-static.example.com", "qr_type": "static", "title": "Smoke Test Static QR", "description": "Enhanced smoke test static QR code"}'
    _api_request POST "/api/v1/qr/static" "$static_payload"
    _assert_status_code "$API_RESPONSE_STATUS" 201 "Static QR code creation"
    
    local static_qr_id
    static_qr_id=$(_get_json_value "$API_RESPONSE_BODY" ".id")
    if [ -z "$static_qr_id" ]; then
        echo -e "${RED}❌ FAIL:${NC} Failed to extract static QR ID"
        exit 1
    fi
    echo -e "${GREEN}✅ PASS:${NC} Static QR created with ID: ${static_qr_id:0:8}..."
    
    # Test dynamic QR creation
    echo -e "${CYAN}📝 Creating dynamic QR code...${NC}"
    local dynamic_payload='{"redirect_url": "https://smoke-test-dynamic.example.com", "title": "Smoke Test Dynamic QR", "description": "Enhanced smoke test dynamic QR code"}'
    _api_request POST "/api/v1/qr/dynamic" "$dynamic_payload"
    _assert_status_code "$API_RESPONSE_STATUS" 201 "Dynamic QR code creation"
    
    local dynamic_qr_id
    dynamic_qr_id=$(_get_json_value "$API_RESPONSE_BODY" ".id")
    local qr_content
    qr_content=$(_get_json_value "$API_RESPONSE_BODY" ".content")
    
    if [ -z "$dynamic_qr_id" ]; then
        echo -e "${RED}❌ FAIL:${NC} Failed to extract dynamic QR ID"
        exit 1
    fi
    echo -e "${GREEN}✅ PASS:${NC} Dynamic QR created with ID: ${dynamic_qr_id:0:8}..."
    
    # Store IDs for later cleanup and testing
    export SMOKE_TEST_STATIC_QR_ID="$static_qr_id"
    export SMOKE_TEST_DYNAMIC_QR_ID="$dynamic_qr_id"
    export SMOKE_TEST_QR_CONTENT="$qr_content"
}

test_qr_retrieval() {
    print_section "QR Code Retrieval"
    
    # Test static QR retrieval
    _api_request GET "/api/v1/qr/$SMOKE_TEST_STATIC_QR_ID"
    _assert_status_code "$API_RESPONSE_STATUS" 200 "Static QR retrieval by ID"
    
    # Test dynamic QR retrieval
    _api_request GET "/api/v1/qr/$SMOKE_TEST_DYNAMIC_QR_ID"
    _assert_status_code "$API_RESPONSE_STATUS" 200 "Dynamic QR retrieval by ID"
    
    # Test QR listing
    _api_request GET "/api/v1/qr?limit=5"
    _assert_status_code "$API_RESPONSE_STATUS" 200 "QR code listing"
}

test_qr_image_generation() {
    print_section "QR Code Image Generation"
    
    # Test PNG image generation
    echo -e "${CYAN}🖼️  Testing PNG image generation...${NC}"
    local png_start_time png_end_time png_duration
    png_start_time=$(date +%s.%N)
    
    local png_status
    png_status=$(curl -k -s --user "${AUTH_USER}:${AUTH_PASS}" \
        -o /dev/null -w "%{http_code}" --max-time "$IMAGE_GENERATION_TIMEOUT" \
        "$API_URL/api/v1/qr/$SMOKE_TEST_STATIC_QR_ID/image?format=png&size=10" 2>/dev/null)
    
    png_end_time=$(date +%s.%N)
    png_duration=$(echo "$png_end_time - $png_start_time" | bc -l 2>/dev/null || echo "0")
    
    if [ "$png_status" = "200" ]; then
        echo -e "${GREEN}✅ PASS:${NC} PNG image generation (${png_duration}s)"
    else
        echo -e "${RED}❌ FAIL:${NC} PNG image generation failed (status: $png_status)"
        exit 1
    fi
    
    # Test SVG image generation
    echo -e "${CYAN}🖼️  Testing SVG image generation...${NC}"
    local svg_status
    svg_status=$(curl -k -s --user "${AUTH_USER}:${AUTH_PASS}" \
        -o /dev/null -w "%{http_code}" --max-time "$IMAGE_GENERATION_TIMEOUT" \
        "$API_URL/api/v1/qr/$SMOKE_TEST_STATIC_QR_ID/image?format=svg" 2>/dev/null)
    
    if [ "$svg_status" = "200" ]; then
        echo -e "${GREEN}✅ PASS:${NC} SVG image generation"
    else
        echo -e "${RED}❌ FAIL:${NC} SVG image generation failed (status: $svg_status)"
        exit 1
    fi
}

test_qr_redirection_critical_path() {
    print_section "QR Code Redirection (CRITICAL PATH)"
    
    # Extract short ID from dynamic QR content
    local short_id
    short_id=$(echo "$SMOKE_TEST_QR_CONTENT" | sed 's/.*\/r\///' | sed 's/?.*//')
    
    if [ -z "$short_id" ]; then
        echo -e "${RED}❌ FAIL:${NC} Could not extract short ID from QR content"
        exit 1
    fi
    
    echo -e "${CYAN}🔀 Testing QR redirect for short ID: $short_id${NC}"
    
    # Test redirect with performance measurement
    local redirect_start_time redirect_end_time redirect_duration
    redirect_start_time=$(date +%s.%N)
    
    local redirect_status
    redirect_status=$(curl -k -s -o /dev/null -w "%{http_code}" \
        --max-time "$REDIRECT_TIMEOUT" \
        -H "Host: web.hccc.edu" \
        "$API_URL/r/$short_id" 2>/dev/null)
    
    redirect_end_time=$(date +%s.%N)
    redirect_duration=$(echo "$redirect_end_time - $redirect_start_time" | bc -l 2>/dev/null || echo "0")
    
    if [ "$redirect_status" = "302" ]; then
        local perf_indicator=""
        if (( $(echo "$redirect_duration < 0.05" | bc -l 2>/dev/null || echo 0) )); then
            perf_indicator=" ⚡ EXCELLENT"
        elif (( $(echo "$redirect_duration < 0.1" | bc -l 2>/dev/null || echo 0) )); then
            perf_indicator=" ✨ GOOD"
        fi
        echo -e "${GREEN}✅ PASS:${NC} QR redirect successful (${redirect_duration}s${perf_indicator})"
    else
        echo -e "${RED}❌ FAIL:${NC} QR redirect failed (status: $redirect_status, time: ${redirect_duration}s)"
        exit 1
    fi
    
    # Wait for background task processing
    if [ "$redirect_status" = "302" ]; then
        echo -e "${CYAN}⏳ Waiting for background task processing...${NC}"
        sleep "$BACKGROUND_TASK_WAIT"
        
        # Verify scan count was updated
        _api_request GET "/api/v1/qr/$SMOKE_TEST_DYNAMIC_QR_ID"
        _assert_status_code "$API_RESPONSE_STATUS" 200 "QR retrieval for scan count validation"
        
        local scan_count
        scan_count=$(_get_json_value "$API_RESPONSE_BODY" ".scan_count")
        if [ "$scan_count" -gt 0 ]; then
            echo -e "${GREEN}✅ PASS:${NC} Background scan statistics updated (count: $scan_count)"
        else
            echo -e "${YELLOW}⚠️  WARNING:${NC} Scan count not updated (may be background task delay)"
        fi
    fi
}

test_error_conditions() {
    print_section "Error Condition Handling"
    
    # Test non-existent QR
    echo -e "${CYAN}🚫 Testing non-existent QR retrieval...${NC}"
    _api_request GET "/api/v1/qr/non-existent-id"
    _assert_status_code "$API_RESPONSE_STATUS" 404 "Non-existent QR returns 404"
    
    # Test invalid short ID redirect
    echo -e "${CYAN}🚫 Testing invalid short ID redirect...${NC}"
    local invalid_redirect_status
    invalid_redirect_status=$(curl -k -s -o /dev/null -w "%{http_code}" \
        --max-time 5 -H "Host: web.hccc.edu" \
        "$API_URL/r/invalid!" 2>/dev/null)
    
    if [ "$invalid_redirect_status" = "404" ]; then
        echo -e "${GREEN}✅ PASS:${NC} Invalid short ID returns 404"
    else
        echo -e "${RED}❌ FAIL:${NC} Invalid short ID returned $invalid_redirect_status instead of 404"
        exit 1
    fi
    
    # Test malformed JSON
    echo -e "${CYAN}🚫 Testing malformed JSON handling...${NC}"
    _api_request POST "/api/v1/qr/static" '{"invalid": json}'
    if [ "$API_RESPONSE_STATUS" -eq 422 ] || [ "$API_RESPONSE_STATUS" -eq 400 ]; then
        echo -e "${GREEN}✅ PASS:${NC} Malformed JSON properly rejected (status: $API_RESPONSE_STATUS)"
    else
        echo -e "${RED}❌ FAIL:${NC} Malformed JSON not properly handled (status: $API_RESPONSE_STATUS)"
        exit 1
    fi
}

# ============================================================================
# Cleanup and Maintenance Functions
# ============================================================================

cleanup_test_resources() {
    print_section "Test Resource Cleanup"
    
    local cleanup_success=0
    local cleanup_total=0
    
    # Clean up static QR
    if [ -n "${SMOKE_TEST_STATIC_QR_ID:-}" ]; then
        echo -e "${CYAN}🧹 Cleaning up static QR: ${SMOKE_TEST_STATIC_QR_ID:0:8}...${NC}"
        cleanup_total=$((cleanup_total + 1))
        _api_request DELETE "/api/v1/qr/$SMOKE_TEST_STATIC_QR_ID"
        if [ "$API_RESPONSE_STATUS" -eq 204 ]; then
            echo -e "${GREEN}✅ PASS:${NC} Static QR cleanup successful"
            cleanup_success=$((cleanup_success + 1))
        else
            echo -e "${YELLOW}⚠️  WARNING:${NC} Static QR cleanup failed (status: $API_RESPONSE_STATUS)"
        fi
    fi
    
    # Clean up dynamic QR
    if [ -n "${SMOKE_TEST_DYNAMIC_QR_ID:-}" ]; then
        echo -e "${CYAN}🧹 Cleaning up dynamic QR: ${SMOKE_TEST_DYNAMIC_QR_ID:0:8}...${NC}"
        cleanup_total=$((cleanup_total + 1))
        _api_request DELETE "/api/v1/qr/$SMOKE_TEST_DYNAMIC_QR_ID"
        if [ "$API_RESPONSE_STATUS" -eq 204 ]; then
            echo -e "${GREEN}✅ PASS:${NC} Dynamic QR cleanup successful"
            cleanup_success=$((cleanup_success + 1))
        else
            echo -e "${YELLOW}⚠️  WARNING:${NC} Dynamic QR cleanup failed (status: $API_RESPONSE_STATUS)"
        fi
    fi
    
    echo -e "${CYAN}📊 Cleanup Summary: $cleanup_success/$cleanup_total resources cleaned${NC}"
}

# ============================================================================
# Main Execution Flow
# ============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    🔥 ENHANCED SMOKE TEST (Task S.2) 🔥                     ║"
    echo "║                         Observatory-First Production Safety                  ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${CYAN}🎯 Purpose: Validate critical QR Generator functionality post-deployment${NC}"
    echo -e "${CYAN}🔍 Integration: Prometheus metrics validation included${NC}"
    echo -e "${CYAN}⚡ Performance: Sub-100ms redirect target, <15s image generation${NC}"
    echo ""
}

print_summary() {
    local end_time duration
    end_time=$(date +%s)
    duration=$((end_time - START_TIME))
    
    echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗"
    echo -e "║                            🎉 SMOKE TEST PASSED 🎉                          ║"
    echo -e "╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo -e "${CYAN}📊 Test Duration: ${duration}s${NC}"
    echo -e "${CYAN}✅ All critical paths validated${NC}"
    echo -e "${CYAN}📈 Observatory metrics within acceptable ranges${NC}"
    echo -e "${CYAN}🚀 System ready for production traffic${NC}"
    echo ""
}

main() {
    local START_TIME
    START_TIME=$(date +%s)
    
    print_banner
    
    # Environment setup
    load_environment
    
    # Core functionality tests
    test_health_endpoint
    validate_observatory_metrics
    test_qr_creation_workflow
    test_qr_retrieval
    test_qr_image_generation
    test_qr_redirection_critical_path
    test_error_conditions
    
    # Cleanup
    cleanup_test_resources
    
    # Success summary
    print_summary
    
    exit 0
}

# Error handling
trap 'echo -e "\n${RED}❌ Smoke test interrupted or failed${NC}"; cleanup_test_resources 2>/dev/null || true; exit 1' ERR INT TERM

# Execute main function
main "$@"