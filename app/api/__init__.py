"""
API router initialization and configuration.

This module serves as the main entry point for the API router hierarchy.
"""

from fastapi import APIRouter

from .v1 import api_router as api_v1_router
from .v1 import web_router, health_router
from .v1.endpoints.redirect import router as redirect_router
from .v1.endpoints.test_format import router as test_format_router

# Create the main API router that includes versioned routers
api_router = APIRouter(prefix="/api")

# Include versioned routers
api_router.include_router(api_v1_router)

# Create non-API routers without prefixes
redirect_router_no_prefix = redirect_router  # Already has /r prefix
web_router_no_prefix = web_router  # No prefix
health_router_no_prefix = health_router  # No prefix
test_format_router_no_prefix = test_format_router  # Already has /test prefix 