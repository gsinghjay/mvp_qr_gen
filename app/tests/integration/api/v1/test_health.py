"""
Integration tests for health check API endpoints.
"""

import pytest
from fastapi import status

from app.schemas.health.models import HealthStatus, ServiceStatus


class TestHealthEndpoints:
    """Test suite for health check API endpoints."""

    def test_health_check_success(self, client):
        """Test that health check returns 200 when all systems are healthy."""
        # Make request to health endpoint
        response = client.get("/health")
        
        # Assert status code and response structure
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Validate response structure
        assert "status" in data
        assert "version" in data
        assert "environment" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "system_metrics" in data
        assert "checks" in data
        
        # Validate health status is healthy
        assert data["status"] == HealthStatus.HEALTHY
        
        # Validate system metrics
        system_metrics = data["system_metrics"]
        assert "cpu_usage" in system_metrics
        assert "memory_usage" in system_metrics
        assert "disk_usage" in system_metrics
        
        # Validate database check
        assert "database" in data["checks"]
        db_check = data["checks"]["database"]
        assert db_check["status"] == ServiceStatus.PASS 