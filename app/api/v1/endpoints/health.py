"""
Health check API endpoints.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import HTTPError
from app.schemas.health import HealthResponse
from app.services.health import HealthService
from app.types import DbSessionDep
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/health",
    responses={
        200: {"description": "Service is healthy"},
        503: {"description": "Service is unhealthy"},
    },
)


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health Check",
    description="Comprehensive health check endpoint that monitors system metrics, database connectivity, and service status",
    responses={
        500: {"model": HTTPError, "description": "Internal server error"},
        503: {"model": HTTPError, "description": "Service unavailable"},
    },
)
def health_check(
    db: DbSessionDep,
    settings: Annotated[Settings, Depends(get_settings)]
) -> HealthResponse:
    """
    Perform a comprehensive health check of the API service.

    Args:
        db: Database session dependency
        settings: Application settings dependency

    Returns:
        HealthResponse: The current health status of the service with detailed metrics

    Raises:
        HTTPException: If the service is unhealthy or degraded
    """
    health_status = HealthService.get_health_status(db, settings)

    if health_status.status == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is currently unhealthy. Please check the logs for more details.",
        )

    return health_status 