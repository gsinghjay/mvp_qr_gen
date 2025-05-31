import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings # For templates directory
from app.services.qr_retrieval_service import QRRetrievalService # New dependency
from app.dependencies import get_qr_retrieval_service # New dependency getter

# Using Annotated for dependencies as in other route files
QRRetrievalServiceDep = Annotated[QRRetrievalService, Depends(get_qr_retrieval_service)]

# Configure templates
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))
logger = logging.getLogger("app.dashboard_pages")

router = APIRouter(
    tags=["Pages - Dashboard"], # Updated tag
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, qr_retrieval_service: QRRetrievalServiceDep):
    """
    Render the home page template with dynamic data.
    (Moved from pages.py)
    """
    try:
        # Get dashboard data using the retrieval service
        # Assuming get_dashboard_data in QRRetrievalService is now async
        dashboard_data = await qr_retrieval_service.get_dashboard_data(current_user_id=0) # User ID 0 for now, adjust if needed

        return templates.TemplateResponse(
            name="pages/dashboard.html", # Ensure this template exists and path is correct
            context={
                "request": request, # Explicitly passing request
                "total_qr_codes": dashboard_data["total_qr_codes"],
                "recent_qr_codes": dashboard_data["recent_qr_codes"],
            },
        )
    except Exception as e: # Catching generic Exception, consider more specific ones if known
        logger.error("Error in home page (dashboard_page_router)", extra={"error": str(e)})
        # Fallback context for template rendering in case of error
        return templates.TemplateResponse(
            name="pages/dashboard.html",
            context={
                "request": request, # Explicitly passing request
                "total_qr_codes": 0,
                "recent_qr_codes": [],
                "error": "Unable to load QR code data",
            },
            status_code=500,
        )
