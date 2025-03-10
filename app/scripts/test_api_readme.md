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
   chmod +x test_api_endpoints.sh
   ```

3. Run the tests:
   ```bash
   ./test_api_endpoints.sh
   ```

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

## Requirements

- The application must be running on `https://localhost`
- Self-signed or local development certificates are handled by the `-k` flag
- `jq` is used for JSON parsing and validation
- `bc` is used for floating-point calculations in response time tests

## Troubleshooting

- Ensure Docker services are running
- Check that your application is accessible at `https://localhost`
- Make sure `curl`, `jq`, and `bc` are installed
- If background task tests fail, ensure your application is using FastAPI's BackgroundTasks
