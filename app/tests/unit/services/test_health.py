"""
Unit tests for health service.

These tests use mocking to test the health service in isolation.
"""

import pytest
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from fastapi import HTTPException, status

from app.services.health import HealthService
from app.schemas.health.models import HealthStatus, ServiceCheck, ServiceStatus, SystemMetrics


class TestHealthService:
    """Test suite for health service."""

    @patch("app.services.health.psutil")
    def test_get_system_metrics(self, mock_psutil):
        """Test that system metrics are correctly retrieved."""
        # Mock psutil responses
        mock_psutil.cpu_percent.return_value = 25.5
        mock_psutil.virtual_memory.return_value.percent = 45.3
        mock_psutil.disk_usage.return_value.percent = 65.7

        # Get system metrics
        metrics = HealthService.get_system_metrics()

        # Validate system metrics
        assert metrics.cpu_usage == 25.5
        assert metrics.memory_usage == 45.3
        assert metrics.disk_usage == 65.7

        # Verify psutil was called correctly
        mock_psutil.cpu_percent.assert_called_once()
        mock_psutil.virtual_memory.assert_called_once()
        mock_psutil.disk_usage.assert_called_once_with("/")

    def test_check_database_success(self):
        """Test that database check works correctly when database is healthy."""
        # Mock database session
        mock_db = MagicMock()
        mock_db.execute.side_effect = [
            MagicMock(scalar=lambda: 1),  # SELECT 1
            MagicMock(scalar=lambda: "14.8"),  # server_version
            MagicMock(scalar=lambda: 5),  # connection count
            MagicMock(scalar=lambda: 0),  # long running queries
            MagicMock(scalar=lambda: "150 MB")  # database size
        ]
        mock_db.get_bind.return_value = MagicMock()

        # Perform database check
        result = HealthService.check_database(mock_db)

        # Validate result
        assert result.status == ServiceStatus.PASS
        assert result.message == "PostgreSQL database operational"
        assert "latency_ms" in result.model_dump()
        assert result.details["type"] == "PostgreSQL"
        assert result.details["version"] == "14.8"
        assert result.details["active_connections"] == 5
        assert result.details["long_running_queries"] == 0
        assert result.details["database_size"] == "150 MB"

    def test_check_database_with_long_running_queries(self):
        """Test that database check includes warning when there are long-running queries."""
        # Mock database session
        mock_db = MagicMock()
        mock_db.execute.side_effect = [
            MagicMock(scalar=lambda: 1),  # SELECT 1
            MagicMock(scalar=lambda: "14.8"),  # server_version
            MagicMock(scalar=lambda: 10),  # connection count
            MagicMock(scalar=lambda: 3),  # long running queries (> 0)
            MagicMock(scalar=lambda: "150 MB")  # database size
        ]
        mock_db.get_bind.return_value = MagicMock()

        # Perform database check
        result = HealthService.check_database(mock_db)

        # Validate result
        assert result.status == ServiceStatus.PASS
        assert "3 long-running queries" in result.message
        assert result.details["long_running_queries"] == 3

    def test_check_database_failure(self):
        """Test that database check handles failure correctly."""
        # Mock database session that raises an exception
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("Database connection error")

        # Perform database check
        result = HealthService.check_database(mock_db)

        # Validate result
        assert result.status == ServiceStatus.FAIL
        assert "Database connection failed" in result.message
        assert result.latency == 0.0

    @patch("app.services.health.HealthService.get_system_metrics")
    @patch("app.services.health.HealthService.check_database")
    def test_get_health_status_healthy(self, mock_check_db, mock_get_metrics):
        """Test that health status is healthy when all checks pass."""
        # Mock dependencies
        mock_get_metrics.return_value = SystemMetrics(
            cpu_usage=25.0,
            memory_usage=40.0,
            disk_usage=60.0
        )
        mock_check_db.return_value = ServiceCheck(
            status=ServiceStatus.PASS,
            latency_ms=2.5,
            message="PostgreSQL database operational",
            last_checked=datetime.now(UTC),
            details={"type": "PostgreSQL", "version": "14.8"}
        )
        mock_db = MagicMock()

        # Get health status
        health_status = HealthService.get_health_status(mock_db)

        # Validate health status
        assert health_status.status == HealthStatus.HEALTHY
        assert "version" in health_status.model_dump()
        assert "environment" in health_status.model_dump()
        assert "uptime_seconds" in health_status.model_dump()
        assert health_status.system_metrics.cpu_usage == 25.0
        assert "database" in health_status.checks

    @patch("app.services.health.HealthService.get_system_metrics")
    @patch("app.services.health.HealthService.check_database")
    def test_get_health_status_degraded_high_resource(self, mock_check_db, mock_get_metrics):
        """Test that health status is degraded when system metrics are high."""
        # Mock dependencies with high CPU usage
        mock_get_metrics.return_value = SystemMetrics(
            cpu_usage=95.0,  # High CPU usage
            memory_usage=60.0,
            disk_usage=70.0
        )
        mock_check_db.return_value = ServiceCheck(
            status=ServiceStatus.PASS,
            latency_ms=2.5,
            message="PostgreSQL database operational",
            last_checked=datetime.now(UTC),
            details={"type": "PostgreSQL", "version": "14.8"}
        )
        mock_db = MagicMock()

        # Get health status
        health_status = HealthService.get_health_status(mock_db)

        # Validate health status
        assert health_status.status == HealthStatus.DEGRADED
        assert health_status.system_metrics.cpu_usage == 95.0

    @patch("app.services.health.HealthService.get_system_metrics")
    @patch("app.services.health.HealthService.check_database")
    def test_get_health_status_degraded_warning(self, mock_check_db, mock_get_metrics):
        """Test that health status is degraded when a service check has a warning."""
        # Mock dependencies with database warning
        mock_get_metrics.return_value = SystemMetrics(
            cpu_usage=25.0,
            memory_usage=40.0,
            disk_usage=60.0
        )
        mock_check_db.return_value = ServiceCheck(
            status=ServiceStatus.WARN,
            latency_ms=50.0,  # High latency
            message="PostgreSQL database operational but with high latency",
            last_checked=datetime.now(UTC),
            details={"type": "PostgreSQL", "version": "14.8"}
        )
        mock_db = MagicMock()

        # Get health status
        health_status = HealthService.get_health_status(mock_db)

        # Validate health status
        assert health_status.status == HealthStatus.DEGRADED

    @patch("app.services.health.HealthService.get_system_metrics")
    @patch("app.services.health.HealthService.check_database")
    def test_get_health_status_unhealthy(self, mock_check_db, mock_get_metrics):
        """Test that health status is unhealthy when a critical service check fails."""
        # Mock dependencies with database failure
        mock_get_metrics.return_value = SystemMetrics(
            cpu_usage=25.0,
            memory_usage=40.0,
            disk_usage=60.0
        )
        mock_check_db.return_value = ServiceCheck(
            status=ServiceStatus.FAIL,
            latency_ms=0.0,
            message="Database connection failed",
            last_checked=datetime.now(UTC)
        )
        mock_db = MagicMock()

        # Get health status
        health_status = HealthService.get_health_status(mock_db)

        # Validate health status
        assert health_status.status == HealthStatus.UNHEALTHY 