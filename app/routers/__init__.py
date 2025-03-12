"""
Router initialization and configuration.

This module organizes routers into a hierarchical structure with parent routers
that handle prefixes and tags for related endpoints.
"""

from fastapi import APIRouter

# Import individual routers
from .api.v1 import router as api_v1_router
from .auth import router as auth_router
from .health import router as health_router
from .qr.dynamic import router as dynamic_qr_router
from .qr.redirect import router as redirect_router
from .qr.static import router as static_qr_router
from .web.pages import router as pages_router

# Create parent routers for logical grouping
api_router = APIRouter(prefix="/api")
qr_router = APIRouter(prefix="/v1/qr")

# Include child routers in their parent routers
api_router.include_router(api_v1_router)

# Include QR routers under the parent QR router
qr_router.include_router(dynamic_qr_router)
qr_router.include_router(static_qr_router)

# Include QR router under the API router
api_router.include_router(qr_router)

# Create a list of all routers to be included in the application
routers = [
    # Top-level routers
    api_router,
    auth_router,  # Authentication router
    redirect_router,  # /r prefix (handled in the router itself)
    pages_router,  # Web pages
    health_router,  # Health check
]

__all__ = ["routers"]
