"""
Health check service for monitoring system and service health.
"""

import os
import time
from datetime import timezone, datetime # Changed UTC import

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
from app.core.config import settings, Settings

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
                last_checked=datetime.now(timezone.utc), # Changed UTC
                details=db_details,
            )
        except Exception as e:
            return ServiceCheck(
                status=ServiceStatus.FAIL,
                latency_ms=0.0,
                message=f"Database connection failed: {str(e)}",
                last_checked=datetime.now(timezone.utc), # Changed UTC
            )

    @staticmethod
    def check_new_qr_generation_service() -> ServiceCheck:
        """
        Check new QR generation service health.

        Returns:
            ServiceCheck: New QR generation service health check results
        """
        start_time = time.time()
        try:
            # Try to instantiate the service via dependency injection
            from app.dependencies import get_new_qr_generation_service, get_segno_qr_generator, get_pillow_qr_formatter
            
            generator = get_segno_qr_generator()
            formatter = get_pillow_qr_formatter()
            service = get_new_qr_generation_service(generator, formatter)
            
            if service is None:
                raise ValueError("Service instantiation returned None")
                
            latency = (time.time() - start_time) * 1000
            
            return ServiceCheck(
                status=ServiceStatus.PASS,
                latency_ms=latency,
                message="New QR Generation Service operational",
                last_checked=datetime.now(timezone.utc), # Changed UTC
                details={"service_type": "NewQRGenerationService", "adapter": "Segno+Pillow"}
            )
            
        except Exception as e:
            return ServiceCheck(
                status=ServiceStatus.FAIL,
                latency_ms=0.0,
                message=f"New QR Generation Service check failed: {str(e)}",
                last_checked=datetime.now(timezone.utc), # Changed UTC
            )

    @staticmethod  
    def check_new_analytics_service() -> ServiceCheck:
        """
        Check new analytics service health.

        Returns:
            ServiceCheck: New analytics service health check results
        """
        start_time = time.time()
        try:
            # Try to instantiate the service via dependency injection
            from app.dependencies import get_new_analytics_service
            
            service = get_new_analytics_service()
            
            # Note: Currently returns None as placeholder
            if service is None:
                return ServiceCheck(
                    status=ServiceStatus.WARN,
                    latency_ms=0.0,
                    message="New Analytics Service not yet implemented (placeholder)",
                    last_checked=datetime.now(timezone.utc), # Changed UTC
                    details={"service_type": "NewAnalyticsService", "status": "placeholder"}
                )
                
            latency = (time.time() - start_time) * 1000
            
            return ServiceCheck(
                status=ServiceStatus.PASS,
                latency_ms=latency,
                message="New Analytics Service operational",
                last_checked=datetime.now(timezone.utc), # Changed UTC
                details={"service_type": "NewAnalyticsService"}
            )
            
        except Exception as e:
            return ServiceCheck(
                status=ServiceStatus.FAIL,
                latency_ms=0.0,
                message=f"New Analytics Service check failed: {str(e)}",
                last_checked=datetime.now(timezone.utc), # Changed UTC
            )

    @staticmethod
    def check_new_validation_service() -> ServiceCheck:
        """
        Check new validation service health.

        Returns:
            ServiceCheck: New validation service health check results
        """
        start_time = time.time()
        try:
            # Try to instantiate the service via dependency injection
            from app.dependencies import get_new_validation_service
            
            service = get_new_validation_service()
            
            # Note: Currently returns None as placeholder
            if service is None:
                return ServiceCheck(
                    status=ServiceStatus.WARN,
                    latency_ms=0.0,
                    message="New Validation Service not yet implemented (placeholder)",
                    last_checked=datetime.now(timezone.utc), # Changed UTC
                    details={"service_type": "NewValidationService", "status": "placeholder"}
                )
                
            latency = (time.time() - start_time) * 1000
            
            return ServiceCheck(
                status=ServiceStatus.PASS,
                latency_ms=latency,
                message="New Validation Service operational",
                last_checked=datetime.now(timezone.utc), # Changed UTC
                details={"service_type": "NewValidationService"}
            )
            
        except Exception as e:
            return ServiceCheck(
                status=ServiceStatus.FAIL,
                latency_ms=0.0,
                message=f"New Validation Service check failed: {str(e)}",
                last_checked=datetime.now(timezone.utc), # Changed UTC
            )

    @classmethod
    def get_health_status(cls, db: Session, app_settings: Settings = None) -> HealthResponse:
        """
        Get comprehensive health status of the service.

        Args:
            db: Database session
            app_settings: Application settings (optional, defaults to global settings)

        Returns:
            HealthResponse: Complete health status
        """
        if app_settings is None:
            app_settings = settings
            
        # Get system metrics
        metrics = cls.get_system_metrics()

        # Perform service checks
        checks = {"database": cls.check_database(db)}
        
        # Add new service checks based on feature flags
        if app_settings.USE_NEW_QR_GENERATION_SERVICE:
            checks["new_qr_generation"] = cls.check_new_qr_generation_service()
            
        if app_settings.USE_NEW_ANALYTICS_SERVICE:
            checks["new_analytics"] = cls.check_new_analytics_service()
            
        if app_settings.USE_NEW_VALIDATION_SERVICE:
            checks["new_validation"] = cls.check_new_validation_service()

        # Determine overall health status
        status = HealthStatus.HEALTHY
        
        # Check for any failed services
        failed_services = [name for name, check in checks.items() if check.status == ServiceStatus.FAIL]
        if failed_services:
            status = HealthStatus.UNHEALTHY
        else:
            # Check for degraded conditions
            warned_services = [name for name, check in checks.items() if check.status == ServiceStatus.WARN]
            if (
                metrics.cpu_usage > 90
                or metrics.memory_usage > 90
                or metrics.disk_usage > 90
                or warned_services
            ):
                status = HealthStatus.DEGRADED

        return HealthResponse(
            status=status,
            version=os.getenv("APP_VERSION", "1.0.0"),
            environment=app_settings.ENVIRONMENT,
            uptime_seconds=time.time() - START_TIME,
            system_metrics=metrics,
            checks=checks,
        )
