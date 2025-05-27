#!/bin/bash

# Test Script for NewQRGenerationService Features
# Validates advanced Segno adapter capabilities via API calls.

set -euo pipefail

# ============================================================================
# Color Codes and Constants (borrowed from your existing scripts)
# ============================================================================
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================================
# Environment Variable Loading and Validation
# ============================================================================
echo -e "${YELLOW}📁 Loading environment variables...${NC}"
if [ -f ".env" ]; then
    set -a
    # shellcheck source=.env
    source .env
    set +a
else
    echo -e "${RED}❌ Error: .env file not found.${NC}"
    exit 1
fi

required_vars=("API_URL" "AUTH_USER" "AUTH_PASS" "PROMETHEUS_URL" \
               "USE_NEW_QR_GENERATION_SERVICE" "CANARY_TESTING_ENABLED" "CANARY_PERCENTAGE")
missing_vars=()
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

# Ensure new service path is forced for these tests
if [ "${USE_NEW_QR_GENERATION_SERVICE}" != "true" ] || \
   ([ "${CANARY_TESTING_ENABLED}" == "true" ] && [ "${CANARY_PERCENTAGE}" != "100" ]); then
    echo -e "${RED}❌ Configuration Error for New Service Testing:${NC}"
    echo "   Please set the following in .env to force the new path for these tests:"
    echo "   USE_NEW_QR_GENERATION_SERVICE=true"
    echo "   CANARY_TESTING_ENABLED=false (or CANARY_PERCENTAGE=100 if enabled)"
    exit 1
fi
echo -e "${GREEN}✅ New QR Generation Service path will be used for these tests.${NC}"

API_URL="${API_URL}"
AUTH_HEADER="--user ${AUTH_USER}:${AUTH_PASS}"
PROMETHEUS_URL="${PROMETHEUS_URL}"

# Global API response variables
API_RESPONSE_BODY=""
API_RESPONSE_STATUS=""
IMAGE_OUTPUT_DIR="test_new_qr_images"
mkdir -p "$IMAGE_OUTPUT_DIR"

# ============================================================================
# Utility Functions (borrowed and adapted)
# ============================================================================
_api_request_image() {
    local qr_id="$1"
    local query_params="$2"
    local output_filename="$3"
    local expected_content_type="$4"
    local description="$5"

    echo -e "${CYAN}🔄 Requesting: $description ($output_filename)...${NC}"
    local start_time response_code content_type response_headers
    start_time=$(date +%s.%N)

    # Create a temp file to store headers
    local headers_file=$(mktemp)
    
    # Use a single request to get both response code and content type
    response_code=$(curl -k -s $AUTH_HEADER \
        -D "$headers_file" \
        -w "%{http_code}" -o "${IMAGE_OUTPUT_DIR}/${output_filename}" \
        "${API_URL}/api/v1/qr/${qr_id}/image?${query_params}")
    
    # Extract content type from the headers file - specifically look for Content-Type
    content_type=$(grep -i '^Content-Type:' "$headers_file" | awk '{print $2}' | tr -d '\r')
    
    # Print the headers for debugging
    echo -e "${CYAN}   Response headers:${NC}"
    cat "$headers_file"
    
    rm "$headers_file"  # Clean up the temporary file

    local end_time duration
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")

    if [ "$response_code" -eq 200 ]; then
        if [[ "$content_type" == *"$expected_content_type"* ]]; then
            if [ -s "${IMAGE_OUTPUT_DIR}/${output_filename}" ]; then
                echo -e "${GREEN}✅ PASS:${NC} $description downloaded (${duration}s, Type: $content_type)."
                echo "   File: ${IMAGE_OUTPUT_DIR}/${output_filename}"
            else
                echo -e "${RED}❌ FAIL:${NC} $description - Output file is empty."
                exit 1
            fi
        else
            echo -e "${RED}❌ FAIL:${NC} $description - Incorrect Content-Type (Expected: *$expected_content_type*, Got: $content_type)."
            exit 1
        fi
    else
        echo -e "${RED}❌ FAIL:${NC} $description - API Request Failed (Status: $response_code)."
        cat "${IMAGE_OUTPUT_DIR}/${output_filename}" # Print error body if any
        exit 1
    fi
}

_api_request_json() {
    local method="$1"
    local endpoint_path="$2"
    local json_data="$3"
    local curl_opts=(-k -s --user "${AUTH_USER}:${AUTH_PASS}")

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

_assert_status_code() {
    local actual="$1"
    local expected="$2"
    local description="$3"
    if [ "$actual" -eq "$expected" ]; then
        echo -e "${GREEN}✅ PASS:${NC} $description (Expected $expected, Got $actual)"
    else
        echo -e "${RED}❌ FAIL:${NC} $description (Expected $expected, Got $actual)"
        echo -e "${YELLOW}Response Body:${NC}\n$API_RESPONSE_BODY"
        exit 1
    fi
}

_get_json_value() {
    echo "$1" | jq -r "$2" 2>/dev/null || echo ""
}

query_prometheus_metric_path_new() {
    local metric_name="$1"
    local operation="$2"
    local query="${metric_name}_count{path=\"new\", operation=\"${operation}\"}"
    
    echo -e "${CYAN}📊 Querying Prometheus: ${query}${NC}"
    local response
    response=$(curl -s -G "${PROMETHEUS_URL}/api/v1/query" --data-urlencode "query=$query" 2>/dev/null)
    
    if echo "$response" | jq -e '.data.result[0].value[1]' > /dev/null; then
        local value
        value=$(echo "$response" | jq -r '.data.result[0].value[1]')
        echo -e "${GREEN}   Prometheus metric ${metric_name}{path=\"new\", operation=\"${operation}\"} value: $value${NC}"
        echo "$value"
    else
        echo -e "${YELLOW}   Prometheus metric ${metric_name}{path=\"new\", operation=\"${operation}\"} not found or no data.${NC}"
        echo "0" # Return 0 if metric not found or no data
    fi
}

print_section() {
    echo -e "\n${BLUE}🧪 === $1 ===${NC}"
}

# ============================================================================
# Test Functions
# ============================================================================

# Global ID for a test QR code
TEST_QR_ID=""

setup_test_qr() {
    print_section "Setup: Creating a Test QR Code"
    local payload='{"content": "Test content for new features", "qr_type": "static", "title": "New Features Test QR"}'
    _api_request_json POST "/api/v1/qr/static" "$payload"
    _assert_status_code "$API_RESPONSE_STATUS" 201 "Test QR creation"
    TEST_QR_ID=$(_get_json_value "$API_RESPONSE_BODY" ".id")
    if [ -z "$TEST_QR_ID" ]; then
        echo -e "${RED}❌ FAIL: Could not create Test QR ID.${NC}"
        exit 1
    fi
    echo -e "${GREEN}   Test QR ID: $TEST_QR_ID${NC}"
}

test_advanced_color_control() {
    print_section "Advanced Color Control (Data Dark/Light)"
    # PNG with data_dark_color (OrangeRed) and data_light_color (LightCyan, should be ignored due to PNG transparency)
    _api_request_image "$TEST_QR_ID" "format=png&data_dark_color=%23FF4500&data_light_color=%23E0FFFF" \
        "qr_advanced_color.png" "image/png" "PNG with Data Dark/Light Colors"
    
    # SVG with data_dark_color (DarkSlateBlue) and data_light_color (PaleGoldenRod)
    _api_request_image "$TEST_QR_ID" "format=svg&data_dark_color=%23483D8B&data_light_color=%23EEE8AA" \
        "qr_advanced_color.svg" "image/svg+xml" "SVG with Data Dark/Light Colors"
    
    # Verify SVG content for specific fill attributes if possible (complex, manual check recommended for actual color)
    if grep -q 'fill="#483D8B"' "${IMAGE_OUTPUT_DIR}/qr_advanced_color.svg"; then
        echo -e "${GREEN}   SVG fill for data_dark_color found.${NC}"
    else
        echo -e "${YELLOW}   WARN: data_dark_color fill not explicitly found in SVG, manual check recommended.${NC}"
    fi
}

test_logo_embedding() {
    print_section "Logo Embedding"
    # PNG with logo
    _api_request_image "$TEST_QR_ID" "format=png&include_logo=true" \
        "qr_with_logo.png" "image/png" "PNG with Default Logo"
    
    # JPEG with logo (should handle transparency by pasting on white)
    _api_request_image "$TEST_QR_ID" "format=jpeg&include_logo=true" \
        "qr_with_logo.jpg" "image/jpeg" "JPEG with Default Logo"

    # SVG with logo (note in refactor.md mentions SVG logo support is basic/experimental for Segno direct)
    # Our PillowQRImageFormatter does not directly embed logos into SVG via Segno's artistic path.
    # It would use qr_data.to_pil() then add logo, then save as SVG if that path existed.
    # Currently, it saves SVG directly. So `include_logo=true` for SVG will effectively be ignored by the new path,
    # or result in an SVG without a logo if Segno doesn't embed it directly.
    echo -e "${YELLOW}   Testing SVG with include_logo=true (logo embedding for SVG via Pillow is not a primary feature of PillowQRImageFormatter's SVG path). Expecting a standard SVG.${NC}"
    _api_request_image "$TEST_QR_ID" "format=svg&include_logo=true" \
        "qr_with_logo_attempt.svg" "image/svg+xml" "SVG with include_logo=true (Expect no logo)"

    if ! grep -q 'image' "${IMAGE_OUTPUT_DIR}/qr_with_logo_attempt.svg"; then # Basic check for embedded image tag
        echo -e "${GREEN}   As expected, SVG does not contain an embedded image tag for the logo.${NC}"
    else
        echo -e "${YELLOW}   WARN: SVG unexpectedly contains an image tag. Manual check required.${NC}"
    fi
}

test_svg_accessibility_features() {
    print_section "SVG Accessibility (Title & Description)"
    local svg_title="Test&%20SVG&%20Title" # URL encoded space
    local svg_desc="A&%20test&%20description&%20for&%20SVG&%20accessibility."
    _api_request_image "$TEST_QR_ID" "format=svg&svg_title=${svg_title}&svg_description=${svg_desc}" \
        "qr_accessible.svg" "image/svg+xml" "SVG with Accessibility Title/Description"

    if grep -q '<title>Test SVG Title</title>' "${IMAGE_OUTPUT_DIR}/qr_accessible.svg" && \
       grep -q '<desc>A test description for SVG accessibility.</desc>' "${IMAGE_OUTPUT_DIR}/qr_accessible.svg"; then
        echo -e "${GREEN}   SVG contains correct title and description elements.${NC}"
    else
        echo -e "${RED}❌ FAIL: SVG does not contain correct title and/or description elements.${NC}"
        echo "   Content of ${IMAGE_OUTPUT_DIR}/qr_accessible.svg:"
        cat "${IMAGE_OUTPUT_DIR}/qr_accessible.svg"
        exit 1
    fi
}

test_physical_dimensions() {
    print_section "Physical Dimensions (SVG & Raster)"
    # SVG with physical dimensions (inches)
    _api_request_image "$TEST_QR_ID" "format=svg&physical_size=2&physical_unit=in&dpi=300" \
        "qr_physical_2in_300dpi.svg" "image/svg+xml" "SVG 2 inches @ 300 DPI"
    
    if grep -q 'width="2in"' "${IMAGE_OUTPUT_DIR}/qr_physical_2in_300dpi.svg" && \
       grep -q 'height="2in"' "${IMAGE_OUTPUT_DIR}/qr_physical_2in_300dpi.svg"; then
        echo -e "${GREEN}   SVG contains correct physical width/height attributes.${NC}"
    else
        echo -e "${RED}❌ FAIL: SVG does not contain correct physical width/height attributes.${NC}"
        exit 1
    fi

    # PNG with physical dimensions (cm)
    # This will influence the `scale` used by Segno, and Pillow will resize to target pixels.
    # Exact pixel validation is complex here; we're mostly testing the API accepts params.
    _api_request_image "$TEST_QR_ID" "format=png&physical_size=5&physical_unit=cm&dpi=150" \
        "qr_physical_5cm_150dpi.png" "image/png" "PNG 5cm @ 150 DPI"

    # PNG with pixel-based sizing (using `size` parameter directly)
    # The `size` parameter is interpreted as `modules * 25px` by the adapter for precise control.
    # A size of 10 -> 250px. Let's test size=8 -> 200px.
    _api_request_image "$TEST_QR_ID" "format=png&size=8" \
        "qr_pixel_size_8_approx_200px.png" "image/png" "PNG with size=8 (target ~200px)"
    # We'd need an image info tool to verify exact dimensions of the output PNG.
    # For now, we check if the file is created.
}

test_error_correction_impact_on_logo() {
    print_section "Error Correction and Logo Interaction"
    # When include_logo=true, error_level should default to 'h' or be respected if 'h'
    _api_request_image "$TEST_QR_ID" "format=png&include_logo=true&error_level=m" \
        "qr_logo_error_m_becomes_h.png" "image/png" "PNG with Logo (error_level=m should become h)"
    # Verification here would ideally involve checking the QR code's actual error correction level
    # from the image, which is non-trivial. We rely on the adapter logic.
    echo -e "${YELLOW}   NOTE: Verifying actual error level in output image is complex. Test confirms API processes request.${NC}"

     _api_request_image "$TEST_QR_ID" "format=png&include_logo=true&error_level=h" \
        "qr_logo_error_h.png" "image/png" "PNG with Logo (error_level=h specified)"
}

validate_prometheus_metrics() {
    print_section "Prometheus Metrics Validation for New Path"
    local initial_count_generate current_count_generate
    
    # Get initial count for "generate_image" on "new" path
    initial_count_generate=$(query_prometheus_metric_path_new "qr_generation_path_total" "generate_image")

    # Perform an operation that should hit the "new" path "generate_image"
    _api_request_image "$TEST_QR_ID" "format=png" "metric_test.png" "image/png" "Metric Test PNG"
    
    # Wait a bit for Prometheus to scrape
    echo -e "${CYAN}   Waiting 10s for Prometheus to scrape metrics...${NC}"
    sleep 10

    # Get current count
    current_count_generate=$(query_prometheus_metric_path_new "qr_generation_path_total" "generate_image")

    if [ "$current_count_generate" -gt "$initial_count_generate" ]; then
        echo -e "${GREEN}✅ PASS: Prometheus metric 'qr_generation_path_total{path=\"new\", operation=\"generate_image\"}' incremented.${NC}"
    else
        echo -e "${RED}❌ FAIL: Prometheus metric 'qr_generation_path_total{path=\"new\", operation=\"generate_image\"}' did NOT increment. Initial: $initial_count_generate, Current: $current_count_generate${NC}"
        exit 1
    fi
    # Similar checks can be added for qr_generation_path_duration_seconds if needed (more complex to assert specific values)
}

cleanup_test_qr() {
    print_section "Cleanup: Deleting Test QR Code"
    if [ -n "$TEST_QR_ID" ]; then
        _api_request_json DELETE "/api/v1/qr/$TEST_QR_ID" ""
        _assert_status_code "$API_RESPONSE_STATUS" 204 "Test QR deletion"
        echo -e "${GREEN}   Test QR ID: $TEST_QR_ID deleted.${NC}"
    else
        echo -e "${YELLOW}   No Test QR ID to delete.${NC}"
    fi
    rm -rf "$IMAGE_OUTPUT_DIR"
    echo -e "${GREEN}   Cleaned up ${IMAGE_OUTPUT_DIR}.${NC}"
}

# ============================================================================
# Main Execution
# ============================================================================
main() {
    echo -e "${BLUE}🚀 Starting New QR Generation Service Feature Tests...${NC}"
    
    setup_test_qr
    test_advanced_color_control
    test_logo_embedding
    test_svg_accessibility_features
    test_physical_dimensions
    test_error_correction_impact_on_logo
    validate_prometheus_metrics # This test needs to run *after* some image generations

    echo -e "\n${GREEN}🎉 All New QR Generation Service feature tests PASSED!${NC}"
}

# Trap errors and ensure cleanup
trap 'echo -e "\n${RED}❌ Test script failed prematurely!${NC}"; cleanup_test_qr; exit 1' ERR INT TERM

# Run main and then cleanup
main
cleanup_test_qr