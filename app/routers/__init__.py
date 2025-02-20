"""
Router initialization and configuration.
"""

from .api.v1 import router as api_v1_router
from .qr.dynamic import router as dynamic_qr_router
from .qr.redirect import router as redirect_router
from .qr.static import router as static_qr_router
from .web.pages import router as pages_router

# Create a list of all routers to be included in the application
routers = [
    api_v1_router,
    dynamic_qr_router,
    redirect_router,
    static_qr_router,
    pages_router,
]

__all__ = ["routers"]
