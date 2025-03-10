"""
Tests for FastAPI middleware components.

These tests verify:
1. Each middleware functions as expected
2. Middleware execution order is correct
3. Conditional middleware activation works
4. Performance impact is reasonable
"""

import json
import os
import pytest
import time
from unittest.mock import patch, MagicMock

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.main import create_app
from app.middleware.logging import LoggingMiddleware
from app.middleware.metrics import MetricsMiddleware
from app.middleware.security import create_security_headers_middleware
from app.core.config import settings


class MockMiddleware(BaseHTTPMiddleware):
    """Mock middleware for testing execution order."""
    
    def __init__(self, app, name):
        super().__init__(app)
        self.name = name
        self.order = []
        
    async def dispatch(self, request, call_next):
        # Add to the request state to track middleware execution order
        if not hasattr(request.state, "middleware_order"):
            request.state.middleware_order = []
        
        # Record entry
        request.state.middleware_order.append(f"{self.name}_enter")
        
        # Call the next middleware or endpoint
        response = await call_next(request)
        
        # Record exit
        if hasattr(request.state, "middleware_order"):
            request.state.middleware_order.append(f"{self.name}_exit")
            # Copy middleware_order from state to response header for testing
            response.headers["X-Middleware-Order"] = ",".join(request.state.middleware_order)
        
        # Add a header to show this middleware was executed
        response.headers[f"X-Middleware-{self.name}"] = "executed"
        
        return response


@pytest.fixture
def test_app():
    """Create a test FastAPI app with configurable middleware."""
    app = FastAPI()
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "Test endpoint"}
    
    @app.get("/middleware-order")
    def middleware_order_endpoint(request: Request):
        # Return the middleware execution order from the request state
        return {"order": request.state.middleware_order}
    
    return app


def test_all_middleware_direct_application(test_app):
    """Test that all middleware can be applied directly using FastAPI's add_middleware."""
    # Apply middleware directly
    test_app.add_middleware(GZipMiddleware, minimum_size=1000)
    test_app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
    test_app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, 
                          allow_methods=["*"], allow_headers=["*"])
    create_security_headers_middleware(test_app)
    test_app.add_middleware(MetricsMiddleware)
    test_app.add_middleware(LoggingMiddleware)
    
    client = TestClient(test_app)
    response = client.get("/test")
    
    assert response.status_code == 200
    assert response.json() == {"message": "Test endpoint"}
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "X-XSS-Protection" in response.headers


def test_middleware_execution_order(test_app):
    """Test that middleware is executed in the correct order."""
    # Add middlewares in reverse order (last added is first executed)
    test_app.add_middleware(MockMiddleware, name="last")
    test_app.add_middleware(MockMiddleware, name="middle")
    test_app.add_middleware(MockMiddleware, name="first")
    
    client = TestClient(test_app)
    response = client.get("/middleware-order")
    
    assert response.status_code == 200
    
    # Get the middleware order from the response header
    if "X-Middleware-Order" in response.headers:
        order = response.headers["X-Middleware-Order"].split(",")
    else:
        order = response.json().get("order", [])
    
    # Check that middlewares are executed in the correct order (LIFO for entry)
    assert "first_enter" in order
    assert "middle_enter" in order
    assert "last_enter" in order
    
    # The entry order should be first, middle, last
    first_idx = order.index("first_enter")
    middle_idx = order.index("middle_enter")
    last_idx = order.index("last_enter")
    assert first_idx < middle_idx < last_idx, "Middleware entry order should be first, middle, last"
    
    # Check headers to verify all middleware executed
    assert response.headers["X-Middleware-first"] == "executed"
    assert response.headers["X-Middleware-middle"] == "executed"
    assert response.headers["X-Middleware-last"] == "executed"


def test_conditional_middleware_activation():
    """Test that middleware can be conditionally activated."""
    # Test with environment variable
    with patch.dict(os.environ, {"ENABLE_LOGGING": "False"}):
        with patch("app.core.config.settings.ENABLE_LOGGING", False):
            # Create app with mocked settings
            app = create_app()
            
            # Now we'll inspect the app middleware stack
            # In FastAPI, middleware is stored in app.user_middleware
            middleware_classes = [m.cls for m in app.user_middleware]
            
            # LoggingMiddleware should not be in the middleware stack
            assert LoggingMiddleware not in middleware_classes, "LoggingMiddleware should not be added when ENABLE_LOGGING is False"
            
    # Test with logging enabled
    with patch.dict(os.environ, {"ENABLE_LOGGING": "True"}):
        with patch("app.core.config.settings.ENABLE_LOGGING", True):
            # Create app with mocked settings
            app = create_app()
            
            # Inspect middleware stack
            middleware_classes = [m.cls for m in app.user_middleware]
            
            # LoggingMiddleware should be in the middleware stack
            assert LoggingMiddleware in middleware_classes, "LoggingMiddleware should be added when ENABLE_LOGGING is True"


def test_security_headers_middleware():
    """Test that security headers middleware adds the correct headers."""
    app = FastAPI()
    create_security_headers_middleware(app)
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "Test endpoint"}
    
    # Test in development mode
    with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert "Strict-Transport-Security" not in response.headers
    
    # Test in production mode
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"


def test_metrics_middleware():
    """Test that metrics middleware correctly handles the metrics endpoint and records metrics."""
    app = FastAPI()
    app.add_middleware(MetricsMiddleware)
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "Test endpoint"}
    
    client = TestClient(app)
    
    # Test normal endpoint
    response = client.get("/test")
    assert response.status_code == 200
    
    # Test metrics endpoint
    response = client.get(settings.METRICS_ENDPOINT)
    assert response.status_code == 200
    assert "app_http_requests_total" in response.text
    assert "app_http_request_duration_seconds" in response.text


def test_logging_middleware():
    """Test that logging middleware logs requests and responses correctly."""
    app = FastAPI()
    
    # For a proper test, we need to inspect the actual logging calls
    # Create a test endpoint
    @app.get("/test")
    def test_endpoint():
        return {"message": "Test endpoint"}
    
    @app.get("/error")
    def error_endpoint():
        raise ValueError("Test error")
    
    # Set up logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Use a test client
    client = TestClient(app)
    
    # Test successful request with actual logging
    with patch("logging.Logger.info") as mock_info:
        response = client.get("/test")
        assert response.status_code == 200
        # Verify logging was called
        assert mock_info.call_count > 0, "Logger.info should be called"
    
    # Test error request with actual logging
    with patch("logging.Logger.error") as mock_error:
        try:
            client.get("/error")
        except ValueError:
            pass
        # Verify error logging was called
        assert mock_error.call_count > 0, "Logger.error should be called"


def test_middleware_performance():
    """Test the performance impact of middleware."""
    base_app = FastAPI()
    
    @base_app.get("/test")
    def test_endpoint():
        return {"message": "Test endpoint"}
    
    # Test without middleware
    base_client = TestClient(base_app)
    
    start_time = time.time()
    for _ in range(100):
        base_client.get("/test")
    base_time = time.time() - start_time
    
    # Test with all middleware
    full_app = FastAPI()
    
    @full_app.get("/test")
    def full_test_endpoint():
        return {"message": "Test endpoint"}
    
    full_app.add_middleware(GZipMiddleware, minimum_size=1000)
    full_app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
    full_app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                          allow_methods=["*"], allow_headers=["*"])
    create_security_headers_middleware(full_app)
    full_app.add_middleware(MetricsMiddleware)
    full_app.add_middleware(LoggingMiddleware)
    
    full_client = TestClient(full_app)
    
    start_time = time.time()
    for _ in range(100):
        full_client.get("/test")
    full_time = time.time() - start_time
    
    # Performance impact should be reasonable
    # Note: This is a basic check and might need adjustment based on actual perf requirements
    overhead_ratio = full_time / base_time
    assert overhead_ratio < 10, f"Middleware overhead ratio: {overhead_ratio}" 