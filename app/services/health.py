"""
Health check service for monitoring system and service health.
"""

import os
import time
from datetime import UTC, datetime

import psutil
from sqlalchemy import text
from sqlalchemy.orm import Session

# We'll define these schemas in schemas.py later
from app.schemas.health.models import (
    HealthResponse,
    HealthStatus,
    ServiceCheck,
    ServiceStatus,
    SystemMetrics,
)
from app.core.config import settings

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
        Check PostgreSQL database connectivity and performance.

        Args:
            db: Database session

        Returns:
            ServiceCheck: Database health check results
        """
        start_time = time.time()
        try:
            # Basic connectivity check
            result = db.execute(text("SELECT 1")).scalar()
            if result != 1:
                raise ValueError(f"Expected 1, got {result}")

            # Get database details
            engine = db.get_bind()
            
            # Get PostgreSQL version and connection info
            pg_version = db.execute(text("SHOW server_version")).scalar()
            pg_connections = db.execute(text("SELECT count(*) FROM pg_stat_activity")).scalar()
            
            # Database details
            db_details = {
                "type": "PostgreSQL",
                "version": pg_version,
                "active_connections": pg_connections,
            }
            
            # Check for long-running queries (potentially problematic)
            long_running_queries = db.execute(
                text("""
                SELECT count(*) FROM pg_stat_activity 
                WHERE state = 'active' 
                AND (now() - query_start) > interval '5 minutes'
                """)
            ).scalar()
            
            db_details["long_running_queries"] = long_running_queries
            
            # Check database size
            db_size = db.execute(
                text("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
                """)
            ).scalar()
            
            db_details["database_size"] = db_size

            latency = (time.time() - start_time) * 1000  # Convert to milliseconds

            message = "PostgreSQL database operational"
            if long_running_queries > 0:
                message = f"PostgreSQL database operational, but has {long_running_queries} long-running queries"

            return ServiceCheck(
                status=ServiceStatus.PASS,
                latency_ms=latency,
                message=message,
                last_checked=datetime.now(UTC),
                details=db_details,
            )
        except Exception as e:
            return ServiceCheck(
                status=ServiceStatus.FAIL,
                latency_ms=0.0,
                message=f"Database connection failed: {str(e)}",
                last_checked=datetime.now(UTC),
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
            environment=settings.ENVIRONMENT,
            uptime_seconds=time.time() - START_TIME,
            system_metrics=metrics,
            checks={
                "database": db_check,
            },
        )
