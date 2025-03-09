"""
Health check service for monitoring system and service health.
"""

import os
import time
import psutil
import sqlite3
from datetime import datetime, UTC
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.engine import Engine

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
    def _get_sqlite_file_path(db: Session) -> str:
        """
        Get the file path for the SQLite database from the session.

        Args:
            db: Database session

        Returns:
            str: Path to the SQLite database file or empty string if not SQLite
        """
        try:
            engine = db.get_bind()
            if 'sqlite' in engine.dialect.name:
                # Extract the database path from the connection URL
                url = str(engine.url)
                if url.startswith('sqlite:///'):
                    # Absolute path
                    return url[10:]
                elif url.startswith('sqlite://'):
                    # In-memory or relative path
                    return url[9:] if url[9:] else ':memory:'
            return ""
        except Exception:
            return ""

    @staticmethod
    def check_database(db: Session) -> ServiceCheck:
        """
        Check database connectivity and performance with SQLite-specific checks.

        Args:
            db: Database session

        Returns:
            ServiceCheck: Database health check results
        """
        start_time = time.time()
        try:
            # Basic connectivity check - works for any database
            result = db.execute(text("SELECT 1")).scalar()
            if result != 1:
                raise ValueError(f"Expected 1, got {result}")
            
            # Get database details
            engine = db.get_bind()
            is_sqlite = 'sqlite' in engine.dialect.name
            
            # SQLite-specific health checks
            sqlite_details = {}
            if is_sqlite:
                sqlite_file = HealthService._get_sqlite_file_path(db)
                
                # Skip detailed checks for in-memory databases
                if sqlite_file and sqlite_file != ':memory:':
                    # Check file status
                    db_file = Path(sqlite_file)
                    if not db_file.exists():
                        raise FileNotFoundError(f"SQLite database file not found: {sqlite_file}")
                    
                    # Get file metadata
                    sqlite_details = {
                        "file_size_mb": round(db_file.stat().st_size / (1024 * 1024), 2),
                        "writable": os.access(sqlite_file, os.W_OK),
                        "file_path": sqlite_file
                    }
                    
                    # Run integrity checks
                    # Quick check is faster but less thorough
                    quick_check = db.execute(text("PRAGMA quick_check")).scalar()
                    sqlite_details["quick_check"] = quick_check
                    
                    # Check journal mode
                    journal_mode = db.execute(text("PRAGMA journal_mode")).scalar()
                    sqlite_details["journal_mode"] = journal_mode
                    
                    # Check if WAL mode is in use and get WAL file size if it exists
                    if journal_mode == 'wal':
                        wal_file = Path(f"{sqlite_file}-wal")
                        if wal_file.exists():
                            sqlite_details["wal_size_mb"] = round(wal_file.stat().st_size / (1024 * 1024), 2)
                    
                    # Get page size and cache size
                    sqlite_details["page_size"] = db.execute(text("PRAGMA page_size")).scalar()
                    sqlite_details["cache_size"] = db.execute(text("PRAGMA cache_size")).scalar()
                
                # Always include database type and version in details
                sqlite_details["type"] = "SQLite"
                try:
                    sqlite_details["version"] = sqlite3.sqlite_version
                except Exception:
                    sqlite_details["version"] = "unknown"
            
            latency = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            message = "Database connection successful"
            if is_sqlite:
                message = f"SQLite database operational: {sqlite_details.get('quick_check', 'ok')}"
                if 'writable' in sqlite_details and not sqlite_details['writable']:
                    message = "SQLite database is read-only"
            
            return ServiceCheck(
                status=ServiceStatus.PASS,
                latency_ms=latency,
                message=message,
                last_checked=datetime.now(UTC),
                details=sqlite_details if is_sqlite else None
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
            uptime_seconds=time.time() - START_TIME,
            system_metrics=metrics,
            checks={
                "database": db_check,
            },
        ) 