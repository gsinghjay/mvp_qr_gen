"""
API v1 router initialization and configuration.

This module organizes all v1 API endpoints under a single router.
"""

from fastapi import APIRouter

from .endpoints import health, qr, admin_metrics # pages and fragments removed
from .endpoints import dashboard_page_router, auth_page_router
from .endpoints import qr_management_page_router, portal_page_router
from .endpoints import portal_router # New dynamic portal router
from .endpoints import qr_list_fragments_router, qr_form_fragments_router
from .endpoints import qr_analytics_fragments_router # Import new analytics fragment router

# Create the v1 API router
api_router = APIRouter(prefix="/v1")

# Include endpoint routers
api_router.include_router(qr.router, prefix="/qr", tags=["QR Codes"])
# api_router.include_router(fragments.router)  # fragments.router removed
api_router.include_router(admin_metrics.router)  # No prefix needed - router has its own /admin prefix

# Create the health router (no prefix under API router)
health_router = APIRouter()
health_router.include_router(health.router, tags=["Health Check"])

# Include web page routers (no prefix)
web_router = APIRouter()
# web_router.include_router(pages.router) # pages.router removed
web_router.include_router(dashboard_page_router.router)
web_router.include_router(auth_page_router.router)
web_router.include_router(qr_management_page_router.router)
web_router.include_router(portal_page_router.router)

# Include dynamic portal router under API
api_router.include_router(portal_router.router)

# Include new fragment routers (these typically have their own /fragments prefix)
api_router.include_router(qr_list_fragments_router.router)
api_router.include_router(qr_form_fragments_router.router)
api_router.include_router(qr_analytics_fragments_router.router) # Add new analytics fragment router