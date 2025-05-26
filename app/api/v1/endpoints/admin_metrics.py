"""
Admin metrics and service status API endpoints.

This module provides secured admin endpoints for monitoring feature flags,
service status, and operational metrics in the Observatory-First architecture.
"""

import logging
import os
from datetime import UTC, datetime
from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={
        200: {"description": "Admin operation successful"},
        403: {"description": "Access forbidden"},
    },
)


class ServiceStatusResponse(BaseModel):
    """Response model for service status endpoint."""
    
    timestamp: datetime
    application_info: Dict[str, Any]
    feature_flags: Dict[str, Any]
    canary_settings: Dict[str, Any]
    environment_info: Dict[str, Any]


@router.get(
    "/service-status",
    response_model=ServiceStatusResponse,
    summary="Service Status",
    description="Get current feature flag statuses, canary settings, and application info",
)
def get_service_status(
    settings: Annotated[Settings, Depends(get_settings)]
) -> ServiceStatusResponse:
    """
    Get comprehensive service status including feature flags and settings.
    
    This endpoint is secured by Traefik middleware (IP whitelist + basic auth).
    
    Args:
        settings: Application settings dependency
        
    Returns:
        ServiceStatusResponse: Current service status and configuration
    """
    logger.info("Admin service status requested")
    
    # Application information
    app_info = {
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "base_url": settings.BASE_URL,
    }
    
    # Feature flags - Phase 0 Observatory-First flags
    feature_flags = {
        "USE_NEW_QR_GENERATION_SERVICE": settings.USE_NEW_QR_GENERATION_SERVICE,
        "USE_NEW_ANALYTICS_SERVICE": settings.USE_NEW_ANALYTICS_SERVICE,
        "USE_NEW_VALIDATION_SERVICE": settings.USE_NEW_VALIDATION_SERVICE,
        # Legacy feature flags
        "FEATURE_NEW_QR_SERVICE_ENABLED": settings.FEATURE_NEW_QR_SERVICE_ENABLED,
        "FEATURE_ENHANCED_VALIDATION_ENABLED": settings.FEATURE_ENHANCED_VALIDATION_ENABLED,
        "FEATURE_PERFORMANCE_OPTIMIZATION_ENABLED": settings.FEATURE_PERFORMANCE_OPTIMIZATION_ENABLED,
        "FEATURE_DEBUG_MODE_ENABLED": settings.FEATURE_DEBUG_MODE_ENABLED,
    }
    
    # Canary testing configuration
    canary_settings = {
        "CANARY_TESTING_ENABLED": settings.CANARY_TESTING_ENABLED,
        "CANARY_PERCENTAGE": settings.CANARY_PERCENTAGE,
        "canary_description": f"{'Active' if settings.CANARY_TESTING_ENABLED else 'Inactive'} - {settings.CANARY_PERCENTAGE}% of requests routed to new services"
    }
    
    # Environment information
    env_info = {
        "cors_origins": settings.CORS_ORIGINS,
        "trusted_hosts": settings.TRUSTED_HOSTS,
        "allowed_redirect_domains": settings.ALLOWED_REDIRECT_DOMAINS,
        "log_level": settings.LOG_LEVEL,
        "metrics_enabled": settings.ENABLE_METRICS,
        "gzip_enabled": settings.ENABLE_GZIP,
    }
    
    response = ServiceStatusResponse(
        timestamp=datetime.now(UTC),
        application_info=app_info,
        feature_flags=feature_flags,
        canary_settings=canary_settings,
        environment_info=env_info,
    )
    
    logger.info("Admin service status response generated successfully")
    return response


@router.get(
    "/feature-flags",
    summary="Feature Flags Status", 
    description="Get current feature flag statuses only",
)
def get_feature_flags_status(
    settings: Annotated[Settings, Depends(get_settings)]
) -> Dict[str, Any]:
    """
    Get only the feature flags status.
    
    Args:
        settings: Application settings dependency
        
    Returns:
        Dictionary of current feature flag values
    """
    logger.info("Admin feature flags status requested")
    
    flags = {
        "timestamp": datetime.now(UTC).isoformat(),
        "observatory_first_flags": {
            "USE_NEW_QR_GENERATION_SERVICE": settings.USE_NEW_QR_GENERATION_SERVICE,
            "USE_NEW_ANALYTICS_SERVICE": settings.USE_NEW_ANALYTICS_SERVICE,
            "USE_NEW_VALIDATION_SERVICE": settings.USE_NEW_VALIDATION_SERVICE,
        },
        "canary_testing": {
            "CANARY_TESTING_ENABLED": settings.CANARY_TESTING_ENABLED,
            "CANARY_PERCENTAGE": settings.CANARY_PERCENTAGE,
        },
        "legacy_flags": {
            "FEATURE_NEW_QR_SERVICE_ENABLED": settings.FEATURE_NEW_QR_SERVICE_ENABLED,
            "FEATURE_ENHANCED_VALIDATION_ENABLED": settings.FEATURE_ENHANCED_VALIDATION_ENABLED,
            "FEATURE_PERFORMANCE_OPTIMIZATION_ENABLED": settings.FEATURE_PERFORMANCE_OPTIMIZATION_ENABLED,
            "FEATURE_DEBUG_MODE_ENABLED": settings.FEATURE_DEBUG_MODE_ENABLED,
        }
    }
    
    logger.info("Admin feature flags response generated successfully")
    return flags 