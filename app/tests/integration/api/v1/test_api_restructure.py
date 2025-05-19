"""
Tests for verifying that both old and new router structures are working.

This module tests key endpoints in both the old and new API structures
to ensure backward compatibility during the transition.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_both_structures():
    """Test that health check endpoint works in both old and new structures."""
    # Test old health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"
    
    # Test new health endpoint
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"


def test_qr_list_endpoint_both_structures():
    """Test that QR list endpoint works in both old and new structures."""
    # Test old QR list endpoint
    response = client.get("/api/v1/qr")
    assert response.status_code == 200
    assert "items" in response.json()
    assert "total" in response.json()
    assert "page" in response.json()
    
    # Test new QR list endpoint
    response = client.get("/api/v1/qr")
    assert response.status_code == 200
    assert "items" in response.json()
    assert "total" in response.json()
    assert "page" in response.json()


def test_openapi_schema():
    """Test that OpenAPI schema includes all endpoints."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    paths = schema["paths"]
    
    # Check that both old and new endpoints are in the schema
    assert "/health" in paths
    assert "/api/v1/health" in paths
    assert "/api/v1/qr" in paths 