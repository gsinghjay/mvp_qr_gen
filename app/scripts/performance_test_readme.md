# Performance Testing for QR Code Generator

This directory contains tools for measuring and monitoring the performance of the QR Code Generator application, with a particular focus on first-request performance and initialization optimizations.

## Performance Test Script

The `performance_test.sh` script is designed to measure the difference between cold-start (first request) and warm (subsequent) request times for key endpoints in the application. This is particularly useful for verifying the effectiveness of initialization optimizations like FastAPI's lifespan context manager.

### Usage

```bash
./performance_test.sh [options]
```

Options:
- `-u, --url URL`: Base URL to test (default: https://10.1.6.12)
- `-i, --iterations N`: Number of warm requests to make per endpoint (default: 3)
- `-o, --output FILE`: Output file for CSV results (default: performance_results.csv)
- `-h, --help`: Show the help message
- `-v, --verbose`: Show more detailed output and log historical data

Example:
```bash
./performance_test.sh --url https://web.hccc.edu --iterations 5
```

### Key Metrics

The script collects the following metrics:
- **Cold Start Time**: Time taken for the first request to an endpoint after application startup
- **Warm Request Time**: Average time for subsequent requests to the same endpoint
- **Cold/Warm Ratio**: Ratio between cold start and warm request times

A ratio close to 1.0 indicates minimal cold-start penalty, suggesting effective initialization.

## Recent Performance Results

Our latest performance testing results (as of Apr 30, 2025) show the following:

| Endpoint      | Path                | Cold Start (s) | Warm Average (s) | Cold/Warm Ratio |
|---------------|---------------------|----------------|------------------|-----------------|
| Health Check  | /health            | 0.016412236    | 0.01735          | 0.94x           |
| QR Listing    | /api/v1/qr?limit=1 | 0.017958024    | 0.01744          | 1.02x           |
| Home Page     | /                  | 0.033270984    | 0.02002          | 1.66x           |
| QR Redirect   | /r/{short_id}      | 0.016688552    | 0.01737          | 0.96x           |

**Overall Metrics**:
- Average cold start time: 0.0210824 seconds
- Average warm request time: 0.018045 seconds
- Overall cold/warm ratio: 1.16x

These excellent results were achieved by:
1. Moving imports to module level in key service files
2. Enhancing FastAPI's lifespan context manager to pre-initialize key dependencies
3. Removing redundant script-based warmup mechanisms

## Performance Optimization Approach

Our approach to optimizing first-request performance includes:

1. **Module-Level Imports**: Ensuring imports occur at module level rather than inside functions, allowing Python to load dependencies during application startup.

2. **FastAPI Lifespan Initialization**: Using FastAPI's lifespan context manager to pre-initialize key dependencies:
   ```python
   @asynccontextmanager
   async def lifespan(app: FastAPI):
       # Start up - initialize key dependencies
       db = next(get_db_with_logging())
       qr_repo = QRCodeRepository(db)
       qr_service = QRCodeService(qr_repo)
       # Initialize code paths by performing minimal operations
       total = qr_repo.count()
       yield  # Application runs here
       # Shutdown
   ```

3. **Performance Monitoring**: Regular testing to verify initialization improvements maintain their effectiveness.

## Best Practices

For maintaining good first-request performance:

1. **Keep imports at module level** unless there's a specific reason for delayed importing (e.g., circular dependencies).

2. **Use the lifespan context manager** to initialize key dependencies during application startup.

3. **Regularly test performance** using the provided script to catch regressions.

4. **Document performance implications** when making architectural changes that could affect startup or first-request times. 