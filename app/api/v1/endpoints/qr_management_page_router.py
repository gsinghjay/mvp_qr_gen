import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
# Import specific service dependencies needed
from app.services.qr_retrieval_service import QRRetrievalService
from app.dependencies import get_qr_retrieval_service
# Potentially others like QRDeletionService, QRUpdateService if actions are embedded or linked from these pages.
# For now, focusing on what's directly used to render the page.

QRRetrievalServiceDep = Annotated[QRRetrievalService, Depends(get_qr_retrieval_service)]

templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))
logger = logging.getLogger("app.qr_management_pages")

router = APIRouter(
    tags=["Pages - QR Management"],
    responses={404: {"description": "Not found"}},
from app.core.exceptions import DatabaseError # For error handling
from app.models import QRCode # For type hinting if needed by original code
from app.dependencies import QRServiceDep # Temporarily, will change to specific ones
from fastapi import status # For redirect

# Context processor similar to pages.py
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

@router.get("/qr-list", response_class=HTMLResponse)
async def qr_list_page(request: Request, qr_retrieval_service: QRRetrievalServiceDep): # Changed to QRRetrievalServiceDep
    """ Render the QR code list page. (Moved from pages.py) """
    try:
        dashboard_data = await qr_retrieval_service.get_dashboard_data(current_user_id=0) # UserID 0 for now
        return templates.TemplateResponse(
            name="pages/qr_list.html",
            context={"total_qr_codes": dashboard_data["total_qr_codes"]},
        )
    except DatabaseError as e:
        logger.error("Database error in QR list page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="pages/qr_list.html",
            context={"total_qr_codes": 0, "error": "Unable to load QR code data"},
            status_code=500,
        )

@router.get("/qr-create", response_class=HTMLResponse)
async def qr_create_page(request: Request): # Renamed from qr_create
    """ Render the QR code creation page. (Moved from pages.py) """
    try:
        return templates.TemplateResponse(
            name="pages/qr_create.html",
            context={"is_authenticated": True}, # Assuming auth, request already in context_processor
        )
    except Exception as e:
        logger.error("Error in QR creation page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="pages/qr_create.html",
            context={"is_authenticated": True, "error": "An error occurred while loading the QR creation page"},
            status_code=500,
        )

@router.get("/qr-detail/{qr_id}", response_class=HTMLResponse)
async def qr_detail_page(request: Request, qr_id: str, qr_retrieval_service: QRRetrievalServiceDep): # Renamed & Changed
    """ Render the QR code detail page. (Moved from pages.py) """
    try:
        qr_code = await qr_retrieval_service.get_qr_by_id(qr_id)
        qr_data = qr_code.to_dict()
        base_url = f"{settings.BASE_URL}/r/"
        return templates.TemplateResponse(
            name="pages/qr_detail.html",
            context={"is_authenticated": True, "qr": qr_data, "base_url": base_url},
        )
    except DatabaseError as e: # More specific error
        logger.error(f"Database error in QR detail page for {qr_id}", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="pages/qr_detail.html",
            context={"is_authenticated": True, "error": "An error occurred while loading the QR code details", "qr_id": qr_id},
            status_code=500,
        )
    except Exception as e: # Catch QRCodeNotFoundError specifically if it's not a DatabaseError
        logger.error(f"Error in QR detail page for {qr_id}", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="pages/qr_detail.html",
            context={"is_authenticated": True, "error": "QR code not found", "qr_id": qr_id},
            status_code=404,
        )

@router.get("/qr/{qr_id}/analytics", response_class=HTMLResponse)
async def qr_analytics_display_page(request: Request, qr_id: str, qr_retrieval_service: QRRetrievalServiceDep): # Renamed & Changed
    """ Render the QR code analytics page. (Moved from pages.py) """
    try:
        qr_code = await qr_retrieval_service.get_qr_by_id(qr_id)
        qr_data = qr_code.to_dict()
        base_url = f"{settings.BASE_URL}/r/"
        return templates.TemplateResponse(
            name="pages/qr_analytics.html",
            context={
                "is_authenticated": True,
                "qr": qr_data,
                "base_url": base_url,
                "page_title": f"Analytics for {qr_data.get('title', 'QR Code')}",
            },
        )
    except DatabaseError as e:
        logger.error(f"Database error in QR analytics page for {qr_id}", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="pages/qr_analytics.html",
            context={"is_authenticated": True, "error": "An error occurred while loading the QR code analytics", "qr_id": qr_id},
            status_code=500,
        )
    except Exception as e:
        logger.error(f"Error in QR analytics page for {qr_id}", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="pages/qr_analytics.html",
            context={"is_authenticated": True, "error": "QR code not found", "qr_id": qr_id},
            status_code=404,
        )

@router.get("/qr", response_class=HTMLResponse, include_in_schema=False) # Changed to HTMLResponse for consistency, was RedirectResponse
async def redirect_qr_to_qr_list_page(): # Renamed
    """ Redirects general /qr path to the main QR list page. (Moved from pages.py) """
    # Original was RedirectResponse, but HTMLResponse with a meta refresh or JS redirect might be better for HTMX context
    # For now, keeping it simple, but this might need adjustment depending on how it's used.
    # Let's stick to RedirectResponse as it's a server-side redirect.
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/qr-list", status_code=status.HTTP_301_MOVED_PERMANENTLY)
