"""
Health check Pydantic models.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SystemMetrics(BaseModel):
    """System metrics for health check."""

    cpu_usage: float
    memory_usage: float
    disk_usage: float
    uptime_seconds: float = Field(0.0, description="System uptime in seconds")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

    @field_validator("uptime_seconds", mode="before")
    @classmethod
    def validate_uptime(cls, value, info):
        """Allow uptime to be passed as uptime or uptime_seconds."""
        if value == 0.0 and "uptime" in info.data:
            return info.data["uptime"]
        return value


class ServiceCheck(BaseModel):
    """Service check result."""

    name: str = ""
    status: str
    latency: float = 0.0
    message: Optional[str] = None
    last_check: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

    @field_validator("latency", mode="before")
    @classmethod
    def validate_latency(cls, value, info):
        """Allow latency to be passed as latency or latency_ms."""
        if value == 0.0 and "latency_ms" in info.data:
            return info.data["latency_ms"]
        return value

    @field_validator("last_check", mode="before")
    @classmethod
    def validate_last_check(cls, value, info):
        """Allow last_check to be passed as last_check or last_checked."""
        if value == datetime.now() and "last_checked" in info.data:
            return info.data["last_checked"]
        return value


class ServiceStatus(str, Enum):
    """Enumeration of possible service check statuses."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class HealthStatus(str, Enum):
    """Enumeration of possible overall health check statuses."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    version: str
    environment: str = Field(default="development")
    timestamp: datetime = datetime.now()
    uptime_seconds: float = Field(default=0.0, description="Service uptime in seconds")
    system_metrics: Optional[SystemMetrics] = None
    services: Optional[Dict[str, ServiceStatus]] = None
    checks: Optional[Dict[str, ServiceCheck]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "environment": "production",
                "timestamp": "2023-01-01T00:00:00",
                "system": {
                    "cpu_usage": 10.5,
                    "memory_usage": 45.2,
                    "disk_usage": 68.3,
                    "uptime": 3600.5
                },
                "services": {
                    "database": {
                        "name": "PostgreSQL",
                        "version": "14.1",
                        "uptime": 3600.5,
                        "environment": "production"
                    }
                },
                "checks": [
                    {
                        "name": "database_connection",
                        "status": "pass",
                        "latency": 0.05,
                        "message": "Connected successfully",
                        "last_check": "2023-01-01T00:00:00"
                    }
                ]
            }
        }
    ) 