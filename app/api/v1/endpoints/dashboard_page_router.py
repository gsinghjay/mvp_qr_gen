import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request, Header, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

from app.core.config import settings # For templates directory
from app.core.exceptions import DatabaseError
from app.services.qr_retrieval_service import QRRetrievalService # New dependency
from app.dependencies import get_qr_retrieval_service # New dependency getter

# Using Annotated for dependencies as in other route files
QRRetrievalServiceDep = Annotated[QRRetrievalService, Depends(get_qr_retrieval_service)]

# Configure templates
def get_base_template_context(request: Request) -> dict:
    request.scope["scheme"] = "https"
    return {
        "request": request,
        "app_version": "1.0.0", # Example, consider centralizing if needed
        "environment": settings.ENVIRONMENT,
        "current_year": datetime.now().year,
        "api_base_url": "/api/v1",
    }

templates = Jinja2Templates(
    directory=str(settings.TEMPLATES_DIR),
    context_processors=[get_base_template_context],
)
logger = logging.getLogger("app.dashboard_pages")

router = APIRouter(
    tags=["Pages - Dashboard"], # Updated tag
    responses={404: {"description": "Not found"}},
)

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, qr_retrieval_service: QRRetrievalServiceDep):
    """ Render the dashboard page. (Moved from pages.py) """
    try:
        dashboard_data = await qr_retrieval_service.get_dashboard_data(current_user_id=0) # UserID 0 for now
        return templates.TemplateResponse(
            name="pages/dashboard.html",
            context={"request": request, "dashboard_data": dashboard_data, "is_authenticated": True},
        )
    except DatabaseError as e:
        logger.error("Database error in dashboard page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="pages/dashboard.html",
            context={"request": request, "dashboard_data": {}, "error": "Unable to load dashboard data", "is_authenticated": True},
            status_code=500,
        )
