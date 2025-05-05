"""
API v1 router initialization and configuration.

This module organizes all v1 API endpoints under a single router.
"""

from fastapi import APIRouter

from .endpoints import health, qr, pages, fragments

# Create the v1 API router
api_router = APIRouter(prefix="/v1")

# Include endpoint routers
api_router.include_router(qr.router, prefix="/qr", tags=["QR Codes"])
api_router.include_router(fragments.router)  # No prefix needed - router has its own prefix

# Create the health router (no prefix under API router)
health_router = APIRouter()
health_router.include_router(health.router, tags=["Health Check"])

# Include web page routers (no prefix)
web_router = APIRouter()
web_router.include_router(pages.router) 