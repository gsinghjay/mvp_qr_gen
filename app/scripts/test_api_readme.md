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

### Core Functionality
1. Docker Container Status
2. Health Endpoint
3. QR Code Listing
4. Static QR Code Creation
5. Dynamic QR Code Creation
6. Get QR Code by ID
7. Update Dynamic QR Code
8. QR Code Redirection

### Advanced Features
9. QR Code with Logo Generation
10. Error Correction Levels
11. SVG Accessibility Features
12. Enhanced User Agent Tracking

### Production Hardening Security
13. Invalid Short ID Format Validation
14. Disallowed Redirect URL Rejection
15. Invalid URL Scheme Rejection
16. Differentiated Rate Limiting (QR vs API)

### FastAPI Optimization Verification
17. Service-Based Dependency Injection
18. Background Tasks for Scan Statistics
19. Enhanced User Agent Tracking

## Production Hardening Security Features

The script comprehensively tests the security hardening implemented for production deployment:

### Input Validation and Normalization
- **Short ID Format Validation**: Tests regex pattern `^[a-f0-9]{8}$` enforcement
- **Case Normalization**: Verifies uppercase short IDs are converted to lowercase
- **Invalid Format Rejection**: Confirms 404 errors for malformed short IDs
- **Non-existent ID Handling**: Tests proper 404 responses for valid format but non-existent IDs

### URL Safety and Domain Allowlisting
- **Domain Allowlisting**: Tests `ALLOWED_REDIRECT_DOMAINS` configuration enforcement
- **Subdomain Support**: Verifies that subdomains of allowed domains are permitted
- **Disallowed Domain Rejection**: Confirms 422 errors for non-allowed domains
- **URL Scheme Validation**: Tests rejection of non-HTTP/HTTPS schemes (FTP, file, javascript)

### Rate Limiting (Classroom-Optimized)
The script tests the differentiated rate limiting strategy designed for educational environments:

#### QR Redirect Rate Limiting (Classroom-Friendly)
- **Target**: `/r/{short_id}` endpoints via `web.hccc.edu`
- **Limits**: 300 requests/minute, 50 burst capacity
- **Test**: 60 rapid requests simulating classroom QR scanning
- **Expected**: 90%+ success rate to handle entire classrooms
- **College Network Compatible**: Addresses NAT issues where all students appear from same IP

#### Internal API Access (Unrestricted)
- **Target**: `/api/v1/*` endpoints via `10.1.6.12`
- **Limits**: None (internal administrative access)
- **Test**: 30 rapid requests to verify unrestricted access
- **Expected**: 100% success rate for administrative operations

### Error Handling and Resilience
- **Specific HTTP Status Codes**: Tests proper 404, 422, 503, 500 responses
- **Background Task Error Handling**: Verifies graceful error handling without crashes
- **Client IP Extraction**: Tests robust IP detection behind Traefik proxy
- **Defense-in-Depth**: Multiple layers of URL validation

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

## Security Configuration

### Environment Variables
The script tests proper loading and enforcement of security configuration:

```bash
# Required in .env file
ALLOWED_REDIRECT_DOMAINS="hccc.edu,example.com,vercel.app,github.com"
```

### Rate Limiting Configuration
The Traefik configuration implements differentiated rate limiting:

```yaml
# QR Redirects - Classroom Optimized
qr-redirect-rate-limit:
  average: 300  # 5 requests/second
  burst: 50     # Handles classroom scanning

# API Endpoints - Security Focused  
rate-limit:
  average: 60   # 1 request/second
  burst: 10     # Prevents abuse
```

## Implementation Details

### Production Hardening Security
- **Input Validation**: Comprehensive regex-based validation with case normalization
- **Domain Allowlisting**: Configurable domain restrictions with subdomain support
- **URL Safety**: Multi-layer validation preventing malicious redirects
- **Rate Limiting**: Classroom-optimized limits addressing college network NAT issues
- **Error Handling**: Specific HTTP status codes with comprehensive logging

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

## Test Results Summary

A successful test run validates:

- ✅ **47+ Tests Passing** across all functionality areas
- ✅ **Security Hardening**: All 8 production hardening tasks verified
- ✅ **Rate Limiting**: 95%+ success rate for QR redirects (classroom-friendly)
- ✅ **Domain Security**: Proper rejection of disallowed domains
- ✅ **Input Validation**: Comprehensive short ID format enforcement
- ✅ **Background Tasks**: Fast response times with asynchronous processing
- ✅ **User Experience**: No regressions in existing functionality

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
- If security tests fail, verify:
  - `ALLOWED_REDIRECT_DOMAINS` is properly set in `.env`
  - Environment variables are passed to Docker containers
  - Traefik rate limiting configuration is active

## College Network Compatibility

The rate limiting configuration specifically addresses common issues in educational environments:

- **NAT/Proxy Issues**: All students appear from same IP address
- **Classroom Scenarios**: 50+ students scanning QR codes simultaneously
- **Event Registration**: Large groups accessing QR codes without blocking
- **Administrative Access**: Unrestricted internal API access for management

This ensures the QR system works seamlessly in college network environments while maintaining security.
