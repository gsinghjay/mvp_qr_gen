"""
Unit tests for health check API endpoint.

These tests use mocking to test the health endpoint in isolation.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, status

from app.api.v1.endpoints.health import health_check
from app.schemas.health.models import HealthResponse, HealthStatus, ServiceCheck, ServiceStatus, SystemMetrics


class TestHealthEndpoint:
    """Test suite for health endpoint."""

    @patch("app.api.v1.endpoints.health.HealthService")
    def test_health_check_healthy(self, mock_health_service):
        """Test that health check returns correct response when healthy."""
        # Mock the health service response
        mock_health_response = HealthResponse(
            status=HealthStatus.HEALTHY,
            version="1.0.0",
            environment="test",
            uptime_seconds=3600.0,
            system_metrics=SystemMetrics(
                cpu_usage=25.0,
                memory_usage=40.0,
                disk_usage=60.0
            ),
            checks={
                "database": ServiceCheck(
                    status=ServiceStatus.PASS,
                    latency=5.0,
                    message="PostgreSQL database operational",
                )
            }
        )
        mock_health_service.get_health_status.return_value = mock_health_response
        
        # Call the endpoint function
        mock_db = MagicMock()
        response = health_check(mock_db)
        
        # Verify the response
        assert response == mock_health_response
        assert response.status == HealthStatus.HEALTHY
        mock_health_service.get_health_status.assert_called_once_with(mock_db)

    @patch("app.api.v1.endpoints.health.HealthService")
    def test_health_check_unhealthy(self, mock_health_service):
        """Test that health check raises HTTPException when unhealthy."""
        # Mock the health service response
        mock_health_response = HealthResponse(
            status=HealthStatus.UNHEALTHY,
            version="1.0.0",
            environment="test",
            uptime_seconds=3600.0,
            system_metrics=SystemMetrics(
                cpu_usage=25.0,
                memory_usage=40.0,
                disk_usage=60.0
            ),
            checks={
                "database": ServiceCheck(
                    status=ServiceStatus.FAIL,
                    latency=0.0,
                    message="Database connection failed",
                )
            }
        )
        mock_health_service.get_health_status.return_value = mock_health_response
        
        # Call the endpoint function and expect an exception
        mock_db = MagicMock()
        with pytest.raises(HTTPException) as excinfo:
            health_check(mock_db)
        
        # Verify the exception
        assert excinfo.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Service is currently unhealthy" in excinfo.value.detail
        mock_health_service.get_health_status.assert_called_once_with(mock_db)

    @patch("app.api.v1.endpoints.health.HealthService")
    def test_health_check_degraded(self, mock_health_service):
        """Test that health check returns correct response when degraded."""
        # Mock the health service response
        mock_health_response = HealthResponse(
            status=HealthStatus.DEGRADED,
            version="1.0.0",
            environment="test",
            uptime_seconds=3600.0,
            system_metrics=SystemMetrics(
                cpu_usage=95.0,
                memory_usage=40.0,
                disk_usage=60.0
            ),
            checks={
                "database": ServiceCheck(
                    status=ServiceStatus.PASS,
                    latency=5.0,
                    message="PostgreSQL database operational",
                )
            }
        )
        mock_health_service.get_health_status.return_value = mock_health_response
        
        # Call the endpoint function
        mock_db = MagicMock()
        response = health_check(mock_db)
        
        # Verify the response
        assert response == mock_health_response
        assert response.status == HealthStatus.DEGRADED
        mock_health_service.get_health_status.assert_called_once_with(mock_db) 