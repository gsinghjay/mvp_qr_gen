"""
Enhanced metrics middleware for FastAPI application.
Implements Prometheus metrics collection for monitoring.
Note: Works alongside Traefik's metrics. While Traefik collects edge-level metrics,
this middleware provides application-level insights.
"""

import time
from collections.abc import Callable

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import settings

# Define application-level metrics (complementing Traefik's edge metrics)
REQUEST_COUNT = Counter(
    "app_http_requests_total",  # Prefixed with 'app_' to distinguish from Traefik metrics
    "Application-level HTTP request count",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "app_http_request_duration_seconds",  # Prefixed with 'app_' to distinguish from Traefik metrics
    "Application-level HTTP request duration in seconds",
    ["method", "endpoint"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Handle metrics endpoint
        if request.url.path == settings.METRICS_ENDPOINT:
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

        # Start timer for request duration using perf_counter for more precision
        start_time = time.perf_counter()

        try:
            # Process request
            response = await call_next(request)

            # Record metrics
            duration = time.perf_counter() - start_time
            REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(
                duration
            )

            REQUEST_COUNT.labels(
                method=request.method, endpoint=request.url.path, status=response.status_code
            ).inc()

            return response

        except Exception:
            # Record error metrics
            duration = time.perf_counter() - start_time
            REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(
                duration
            )

            REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=500).inc()

            raise
