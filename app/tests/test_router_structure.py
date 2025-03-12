"""
Tests for router structure and path accessibility.

This test module ensures that all routes are accessible after router restructuring.
It compares path operations before and after refactoring to verify compatibility.
"""

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app


def get_all_routes(app: FastAPI):
    """
    Extract all routes from a FastAPI application.

    Args:
        app: FastAPI application

    Returns:
        A dictionary of paths mapped to HTTP methods
    """
    routes = {}

    for route in app.routes:
        if isinstance(route, APIRoute):
            path = route.path
            if path not in routes:
                routes[path] = []

            routes[path].extend(route.methods)

    return routes


def test_api_endpoints_exist():
    """Verify key API endpoints exist and are accessible."""
    client = TestClient(app)

    # Test API documentation endpoints
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/redoc")
    assert response.status_code == 200

    response = client.get("/openapi.json")
    assert response.status_code == 200

    # Test health check endpoint
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"


def test_qr_api_endpoints():
    """Verify QR API endpoints exist and return expected responses."""
    # Print all available routes for debugging
    routes = get_all_routes(app)
    api_routes = [path for path in routes.keys() if path.startswith("/api")]
    print("\nAvailable API routes:")
    for route in sorted(api_routes):
        print(f"  {route}: {routes[route]}")

    client = TestClient(app)

    # List QR codes endpoint
    response = client.get("/api/v1/qr")
    assert response.status_code == 200
    assert "items" in response.json()
    assert "total" in response.json()

    # QR creation endpoints should return validation error without data
    # but the endpoints should exist
    response = client.post("/api/v1/qr/static")
    assert response.status_code == 422

    response = client.post("/api/v1/qr/dynamic")
    assert response.status_code == 422


def test_route_mapping_consistency():
    """Ensure all routes are mapped consistently and prefix patterns are followed."""
    routes = get_all_routes(app)

    # Print all available routes for debugging
    print("\nAll available routes:")
    for route in sorted(routes.keys()):
        print(f"  {route}: {routes[route]}")

    # API endpoints should have consistent prefixes
    api_routes = [path for path in routes.keys() if path.startswith("/api")]
    assert any(path.startswith("/api/v1/qr") for path in api_routes)

    # QR redirect endpoints should start with /r/
    assert any(path.startswith("/r/") for path in routes.keys())

    # Health endpoint should exist
    assert "/health" in routes

    # Static and dynamic QR endpoints should exist with new structured paths
    assert any(
        path == "/api/v1/qr/static" or path.startswith("/api/v1/qr/static/") for path in api_routes
    )
    assert any(
        path == "/api/v1/qr/dynamic" or path.startswith("/api/v1/qr/dynamic/")
        for path in api_routes
    )


def test_route_tag_consistency():
    """Verify that routes are properly tagged for OpenAPI documentation."""
    openapi_schema = app.openapi()
    paths = openapi_schema["paths"]

    # Check that API endpoints have expected tags
    api_endpoint_paths = [path for path in paths.keys() if path.startswith("/api")]

    for path in api_endpoint_paths:
        for method, operation in paths[path].items():
            if method.lower() != "options":  # Skip OPTIONS methods
                assert "tags" in operation, f"Missing tags for {method} {path}"
                assert len(operation["tags"]) > 0, f"Empty tags for {method} {path}"
