"""
API router initialization and configuration.

This module serves as the main entry point for the API router hierarchy.
"""

from fastapi import APIRouter

from .v1 import api_router as api_v1_router
from .v1 import web_router, health_router
from .v1.endpoints.qr import router as qr_router
from .v1.endpoints.health import router as health_router
from .v1.endpoints.redirect import router as redirect_router
from .v1.endpoints.admin_metrics import router as admin_router

# Create the main API router that includes versioned routers
api_router = APIRouter(prefix="/api")

# Include versioned routers
api_router.include_router(api_v1_router)

# Create non-API routers without prefixes
redirect_router_no_prefix = redirect_router  # Already has /r prefix
web_router_no_prefix = web_router  # No prefix
health_router_no_prefix = health_router  # No prefix
qr_router_no_prefix = qr_router  # Already has /v1 prefix
admin_router_no_prefix = admin_router  # Already has /v1 prefix 