# API Endpoint Testing Script

## Prerequisites

- Docker
- Docker Compose
- `curl`
- `jq`
- `bc` (for floating-point calculations)
- Your QR Code Generator application running via Docker Compose

## Usage

1. Ensure your Docker services are running:
   ```bash
   docker-compose up -d
   ```

2. Make the script executable:
   ```bash
   chmod +x app/scripts/test_api_script.sh
   ```

3. Run the tests:
   ```bash
   ./app/scripts/test_api_script.sh
   ```

## Authentication

The script uses Basic Authentication to access the API endpoints:
- Username and Password are configurable in the `.env` file.

## Host Header Requirement

The script adds a `Host: web.hccc.edu` header to all requests that interact with the `/r/` endpoints. This is necessary because:

- Traefik routing is configured to use host-based rules for the QR redirect endpoints
- The router configuration requires the host header to match either `web.hccc.edu` or `130.156.44.52`
- Without the correct host header, Traefik might route the request to a different handler that requires authentication

If you're running tests in a different environment, you may need to modify the host header to match your configuration.

## What the Script Tests

The script performs comprehensive testing of your QR Code Generator API endpoints:

1. Docker Container Status
2. Health Endpoint
3. QR Code Listing
4. Static QR Code Creation
5. Dynamic QR Code Creation
6. Get QR Code by ID
7. Update Dynamic QR Code
8. QR Code Redirection
9. QR Code with Logo Generation
10. Error Correction Levels
11. SVG Accessibility Features
12. Enhanced User Agent Tracking

## Error Correction Levels

The script tests all four error correction levels supported by the QR code standard:

- **Low (L)**: 7% of data can be restored
- **Medium (M)**: 15% of data can be restored
- **Quartile (Q)**: 25% of data can be restored
- **High (H)**: 30% of data can be restored

For each level, the script:
1. Creates a QR code with the specified error level
2. Verifies the error level is correctly saved in the database
3. Downloads the QR code image with the appropriate error level

## SVG Accessibility Features

For SVG format QR codes, the script tests the accessibility features:

1. Title attribute: Adds a descriptive title to the SVG for screen readers
2. Description attribute: Adds a more detailed description to the SVG
3. Verifies these attributes are correctly included in the generated SVG

These features improve accessibility for users with visual impairments when QR codes are delivered in SVG format.

## Enhanced User Agent Tracking

The script tests the advanced scan tracking features:

1. **Genuine Scan Detection**:
   - Tests if the system correctly differentiates between direct URL access and genuine QR scans
   - Uses the `scan_ref=qr` parameter to simulate genuine QR scans
   - Verifies that only genuine scans increment the genuine scan counter

2. **User Agent Analysis**:
   - Tests different user agents (Desktop, iPhone, Android) to ensure proper device detection
   - Verifies that user agent strings are correctly parsed and device information is tracked
   - Confirms that device-specific metadata is stored with scan logs

3. **Scan Statistics**:
   - Verifies that both total and genuine scan counters are updated correctly
   - Tests that first and last genuine scan timestamps are properly recorded
   - Ensures that scan history is maintained for analytics purposes

## FastAPI Optimization Task Verification

The script also verifies the implementation of completed optimization tasks:

### Task 1: Service-Based Dependency Injection
- Tests that the service layer correctly processes QR code creation
- Verifies proper handling of custom parameters (fill_color)
- Ensures consistent data structure in responses with proper timestamps
- **Implementation Status**: ✅ COMPLETE
- **Test Results**: All tests pass, confirming that the service layer is properly handling parameters and returning consistent data structures.

### Task 2: Background Tasks for Scan Statistics
- Measures redirection response time to verify non-blocking behavior
- Verifies scan count is updated correctly after redirection
- Confirms last_scanned_at timestamp is updated properly
- Tests the asynchronous nature of scan statistic updates
- **Implementation Status**: ✅ COMPLETE
- **Test Results**: All tests pass with very fast response times (typically < 0.02s), confirming that background tasks are being used for scan statistics updates.

### Task 3: Enhanced User Agent Tracking
- Tests the differentiation between genuine QR scans and direct URL access
- Verifies that scan_ref parameter is correctly processed
- Confirms that user agent strings are properly parsed into device information
- Tests separate counters for total scans vs. genuine QR scans
- Validates timestamp recording for first and last genuine scans
- **Implementation Status**: ✅ COMPLETE
- **Test Results**: All tests pass, confirming that the system correctly tracks and differentiates scan types while extracting detailed device information.

## Implementation Details

### Service-Based Dependency Injection
- The application successfully uses a service layer for QR code operations
- Custom parameters like `fill_color` are properly processed
- The service returns consistent data structures with proper timestamps
- Response times are fast, indicating efficient service implementation

### Background Tasks for Scan Statistics
- Redirection is extremely fast (typically < 0.02s), confirming non-blocking behavior
- Scan counts are properly updated in the background
- Timestamp updates are handled correctly
- The implementation successfully separates the user-facing redirection from the statistics tracking

### Error Correction Levels
- The application correctly implements all four error correction levels
- The database schema includes an error_level column to store the selected level
- QR codes are generated with the appropriate error correction level
- Default level (Medium) is used when not explicitly specified

### SVG Accessibility Features
- The application properly implements title and description attributes in SVG output
- These attributes are correctly embedded in the SVG for screen reader compatibility
- URL encoding is handled properly for special characters in titles and descriptions

### Enhanced User Agent Tracking
- The system correctly distinguishes between direct URL access and genuine QR scans using the scan_ref parameter
- User agent strings are properly parsed to extract device, OS, and browser information
- The database schema includes separate counters for total accesses vs. genuine QR scans
- Timestamp recording for first and last genuine scans provides valuable analytics data
- Device-specific data (mobile/tablet/PC/bot detection) enhances scan analytics capabilities

## Requirements

- The application must be running via Docker Compose
- Authentication is required for all API endpoints
- `jq` is used for JSON parsing and validation
- `bc` is used for floating-point calculations in response time tests

## Cleanup

After running all tests, the script automatically cleans up:
- Removes downloaded QR code image files (PNG, SVG)
- Removes any other temporary files created during testing

## Troubleshooting

- Ensure Docker services are running
- Check that your application is accessible at the configured URL
- Make sure `curl`, `jq`, and `bc` are installed
- If authentication fails, verify the credentials in the script
- If redirection tests fail with 401 errors, check that:
  - The Host header is correctly set to match Traefik router rules
  - The API_URL is properly configured
  - Your Traefik configuration is routing `/r/` paths correctly
- If SVG tests fail, check that your segno library is properly configured
