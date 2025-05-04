"""
Router for web page endpoints.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.types import DbSessionDep, QRServiceDep
from app.core.exceptions import DatabaseError
from app.models import QRCode

# Configure logger
import logging
logger = logging.getLogger("app.web.pages")

# Configure templates with context processors
def get_base_template_context(request: Request) -> dict:
    """
    Get base context for all templates.
    Includes common data like app version, environment info, etc.
    """
    from app.core.config import settings

    # Force HTTPS for all URLs
    request.scope["scheme"] = "https"

    return {
        "request": request,  # Required by Jinja2Templates
        "app_version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "current_year": datetime.now().year,
        "api_base_url": "/api/v1",
    }

# Configure templates directory
# First try using Docker container path (templates are in /app/app/templates in the container)
TEMPLATES_DIR = "/app/app/templates"
if not os.path.exists(TEMPLATES_DIR):
    # Fall back to relative path for development
    TEMPLATES_DIR = Path(__file__).parents[4] / "templates"

templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR),
    context_processors=[get_base_template_context],
)

router = APIRouter(
    tags=["pages"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, qr_service: QRServiceDep):
    """
    Render the home page template with dynamic data.
    """
    try:
        # Get dashboard data using the service
        dashboard_data = qr_service.get_dashboard_data()
        
        return templates.TemplateResponse(
            name="dashboard.html",
            context={
                "request": request,  # Required by Jinja2Templates
                "total_qr_codes": dashboard_data["total_qr_codes"],
                "recent_qr_codes": dashboard_data["recent_qr_codes"],
            },
        )
    except DatabaseError as e:
        logger.error("Database error in home page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="dashboard.html",
            context={
                "request": request,  # Required by Jinja2Templates
                "total_qr_codes": 0,
                "recent_qr_codes": [],
                "error": "Unable to load QR code data",
            },
            status_code=500,
        )


@router.get("/qr-list", response_class=HTMLResponse)
async def qr_list(request: Request, qr_service: QRServiceDep):
    """
    Render the QR code list page with filtering and sorting options.
    """
    try:
        # Get dashboard data using the service to get the total count
        dashboard_data = qr_service.get_dashboard_data()
        
        return templates.TemplateResponse(
            name="qr_list.html",
            context={
                "request": request,
                "total_qr_codes": dashboard_data["total_qr_codes"],
            },
        )
    except DatabaseError as e:
        logger.error("Database error in QR list page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="qr_list.html",
            context={
                "request": request,
                "total_qr_codes": 0,
                "error": "Unable to load QR code data",
            },
            status_code=500,
        )


@router.get("/qr-create", response_class=HTMLResponse)
async def qr_create(request: Request):
    """
    Render the QR code creation page.
    
    This endpoint displays a form for creating both static and dynamic QR codes,
    with a live preview and download options.
    
    Args:
        request: The FastAPI request object.
        
    Returns:
        HTMLResponse: The rendered QR code creation page.
    """
    try:
        return templates.TemplateResponse(
            name="qr_create.html",
            context={
                "request": request,
                "is_authenticated": True,  # Network-level authentication is now used
            },
        )
    except Exception as e:
        logger.error("Error in QR creation page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="qr_create.html",
            context={
                "request": request,
                "is_authenticated": True,  # Network-level authentication is now used
                "error": "An error occurred while loading the QR creation page",
            },
            status_code=500,
        )


@router.get("/qr-detail/{qr_id}", response_class=HTMLResponse)
async def qr_detail(
    request: Request, 
    qr_id: str, 
    qr_service: QRServiceDep
):
    """
    Render the QR code detail page.
    
    This endpoint displays detailed information about a specific QR code,
    including its metadata, statistics, and management options.
    
    Args:
        request: The FastAPI request object.
        qr_id: The ID of the QR code to display.
        qr_service: The QR code service.
        
    Returns:
        HTMLResponse: The rendered QR code detail page.
    """
    try:
        # Get the QR code using the service
        qr_code = qr_service.get_qr_by_id(qr_id)
        
        # Convert the QR code model to a dictionary for the template
        qr_data = qr_code.to_dict()
        
        # Add the base URL for the short URL display
        from app.core.config import settings
        base_url = f"{settings.BASE_URL}/r/"
        
        return templates.TemplateResponse(
            name="qr_detail.html",
            context={
                "request": request,
                "is_authenticated": True,  # Network-level authentication is now used
                "qr": qr_data,
                "base_url": base_url,
            },
        )
    except DatabaseError as e:
        logger.error(f"Database error in QR detail page for {qr_id}", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="qr_detail.html",
            context={
                "request": request,
                "is_authenticated": True,  # Network-level authentication is now used
                "error": "An error occurred while loading the QR code details",
                "qr_id": qr_id,
            },
            status_code=500,
        )
    except Exception as e:
        logger.error(f"Error in QR detail page for {qr_id}", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="qr_detail.html",
            context={
                "request": request,
                "is_authenticated": True,  # Network-level authentication is now used
                "error": "QR code not found",
                "qr_id": qr_id,
            },
            status_code=404,
        ) 