# E2E Testing for QR Code Generator

This directory contains end-to-end tests for the QR Code Generator application, specifically focused on testing the parallel implementation paths and circuit breaker functionality.

## Prerequisites

- Docker Compose environment running
- Application and Traefik accessible
- Grafana dashboards operational
- Python with `httpx` installed

## Configuration

Set the API base URL as an environment variable:

```bash
export E2E_API_BASE_URL=https://10.1.6.12  # With Traefik TLS
```

For self-signed certificates, uncomment the client initialization with `verify=False` in the test scripts.

## Test Files

- `test_qr_paths.py` - Basic QR code creation and image generation tests
- `test_paths_metrics.py` - Tests for path-specific metrics (old vs new implementation)
- `test_circuit_breaker.py` - Tests for circuit breaker functionality
- `check_health.sh` - Simple health check script

## Running Tests

### Basic Tests

```bash
# Run from inside the API container
docker-compose exec api python -m tests.e2e.test_qr_paths
```

### Path-Specific Metrics Tests

First, configure the correct feature flags in your `.env` file:

For new path:
```
USE_NEW_QR_GENERATION_SERVICE=True
CANARY_TESTING_ENABLED=True  # If using canary
CANARY_PERCENTAGE=100  # For full traffic to new implementation
```

For old path:
```
USE_NEW_QR_GENERATION_SERVICE=False
CANARY_TESTING_ENABLED=False
```

Then restart the API container and run the tests:
```bash
docker-compose restart api
docker-compose exec api python -m tests.e2e.test_paths_metrics
```

Uncomment the specific test functions you want to run in the main section based on your current configuration.

### Circuit Breaker Tests

For details on circuit breaker testing, see the instructions in `test_circuit_breaker.py`. This requires temporarily modifying the `NewQRGenerationService` to force failures for testing.

## Metrics Verification

After running tests, verify the metrics in Grafana using the `qr-refactoring-detailed.json` and `qr-circuit-breaker-monitoring.json` dashboards to check:

- Request counts for each path
- Duration metrics for performance comparison
- Success rates for both implementations
- Circuit breaker states and transitions

## Health Check

Use the health check script to verify API availability:

```bash
./check_health.sh
``` 