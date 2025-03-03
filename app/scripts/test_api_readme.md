# API Endpoint Testing Script

## Prerequisites

- Docker
- Docker Compose
- `curl`
- `jq`
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

## Requirements

- The application must be running on `https://localhost`
- Self-signed or local development certificates are handled by the `-k` flag
- `jq` is used for JSON parsing and validation

## Troubleshooting

- Ensure Docker services are running
- Check that your application is accessible at `https://localhost`
- Make sure `curl` and `jq` are installed
