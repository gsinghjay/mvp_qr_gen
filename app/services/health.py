"""
Health check service for monitoring system and service health.
"""

import os
import time
import psutil
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings

# We'll define these schemas in schemas.py later
from app.schemas.health.models import (
    HealthResponse,
    HealthStatus,
    ServiceStatus,
    SystemMetrics,
    ServiceCheck,
)

START_TIME = time.time()


class HealthService:
    """Service for performing health checks."""

    @staticmethod
    def get_system_metrics() -> SystemMetrics:
        """
        Get current system resource metrics.

        Returns:
            SystemMetrics: Current system resource usage
        """
        return SystemMetrics(
            cpu_usage=psutil.cpu_percent(),
            memory_usage=psutil.virtual_memory().percent,
            disk_usage=psutil.disk_usage("/").percent,
        )

    @staticmethod
    def check_database(db: Session) -> ServiceCheck:
        """
        Check database connectivity and performance.

        Args:
            db: Database session

        Returns:
            ServiceCheck: Database health check results
        """
        start_time = time.time()
        try:
            # Execute a simple query to check database connectivity
            db.execute(text("SELECT 1"))
            latency = (time.time() - start_time) * 1000  # Convert to milliseconds

            return ServiceCheck(
                status=ServiceStatus.PASS,
                latency_ms=latency,
                message="Database connection successful",
                last_checked=datetime.utcnow(),
            )
        except Exception as e:
            return ServiceCheck(
                status=ServiceStatus.FAIL,
                latency_ms=0.0,
                message=f"Database connection failed: {str(e)}",
                last_checked=datetime.utcnow(),
            )

    @classmethod
    def get_health_status(cls, db: Session) -> HealthResponse:
        """
        Get comprehensive health status of the service.

        Args:
            db: Database session

        Returns:
            HealthResponse: Complete health status
        """
        # Get system metrics
        metrics = cls.get_system_metrics()

        # Perform service checks
        db_check = cls.check_database(db)

        # Determine overall health status
        status = HealthStatus.HEALTHY
        if db_check.status == ServiceStatus.FAIL:
            status = HealthStatus.UNHEALTHY
        elif (
            metrics.cpu_usage > 90
            or metrics.memory_usage > 90
            or metrics.disk_usage > 90
            or db_check.status == ServiceStatus.WARN
        ):
            status = HealthStatus.DEGRADED

        return HealthResponse(
            status=status,
            version=os.getenv("APP_VERSION", "1.0.0"),
            uptime_seconds=time.time() - START_TIME,
            system_metrics=metrics,
            checks={
                "database": db_check,
            },
        ) 