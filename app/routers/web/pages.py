"""
Router for web page endpoints.
"""

import os
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ...database import get_db_with_logging
from ...models import QRCode
from ..qr.common import logger
from ...auth.sso import get_optional_user, User
from typing import Optional


# Configure templates with context processors
def get_base_template_context(request: Request) -> dict:
    """
    Get base context for all templates.
    Includes common data like app version, environment info, etc.
    """
    from ...core.config import settings

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
TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates"
)
templates = Jinja2Templates(
    directory=TEMPLATES_DIR,
    context_processors=[get_base_template_context],
)

router = APIRouter(
    tags=["pages"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db_with_logging)):
    """
    Render the home page template with dynamic data.
    """
    try:
        # Get total QR code count for the dashboard
        total_qr_codes = db.query(QRCode).count()
        recent_qr_codes = db.query(QRCode).order_by(QRCode.created_at.desc()).limit(5).all()

        return templates.TemplateResponse(
            name="dashboard.html",
            context={
                "request": request,  # Required by Jinja2Templates
                "total_qr_codes": total_qr_codes,
                "recent_qr_codes": recent_qr_codes,
            },
        )
    except SQLAlchemyError as e:
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
async def qr_list(request: Request, db: Session = Depends(get_db_with_logging)):
    """
    Render the QR code list page with filtering and sorting options.
    """
    try:
        # Get total QR code count
        total_qr_codes = db.query(QRCode).count()
        
        return templates.TemplateResponse(
            name="qr_list.html",
            context={
                "request": request,
                "total_qr_codes": total_qr_codes,
            },
        )
    except SQLAlchemyError as e:
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
async def qr_create(request: Request, current_user: Optional[User] = Depends(get_optional_user)):
    """
    Render the QR code creation page.
    
    This endpoint displays a form for creating both static and dynamic QR codes,
    with a live preview and download options.
    
    Args:
        request: The FastAPI request object.
        current_user: The current authenticated user (if any).
        
    Returns:
        HTMLResponse: The rendered QR code creation page.
    """
    try:
        return templates.TemplateResponse(
            name="qr_create.html",
            context={
                "request": request,
                "current_user": current_user,
                "is_authenticated": current_user is not None,
            },
        )
    except Exception as e:
        logger.error("Error in QR creation page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="qr_create.html",
            context={
                "request": request,
                "current_user": current_user,
                "is_authenticated": current_user is not None,
                "error": "An error occurred while loading the QR creation page",
            },
            status_code=500,
        )


@router.get("/qr-detail/{qr_id}", response_class=HTMLResponse)
async def qr_detail(
    request: Request, 
    qr_id: str, 
    db: Session = Depends(get_db_with_logging),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Render the QR code detail page.
    
    This endpoint displays detailed information about a specific QR code,
    including its metadata, statistics, and management options.
    
    Args:
        request: The FastAPI request object.
        qr_id: The ID of the QR code to display.
        db: The database session.
        current_user: The current authenticated user (if any).
        
    Returns:
        HTMLResponse: The rendered QR code detail page.
    """
    try:
        # Get the QR code from the database
        qr_code = db.query(QRCode).filter(QRCode.id == qr_id).first()
        
        if not qr_code:
            logger.warning(f"QR code not found: {qr_id}")
            return templates.TemplateResponse(
                name="qr_detail.html",
                context={
                    "request": request,
                    "current_user": current_user,
                    "is_authenticated": current_user is not None,
                    "error": "QR code not found",
                    "qr_id": qr_id,
                },
                status_code=404,
            )
        
        # Convert the QR code model to a dictionary for the template
        qr_data = qr_code.to_dict()
        
        # Add the base URL for the short URL display
        from ...core.config import settings
        base_url = f"{settings.BASE_URL}/r/"
        
        return templates.TemplateResponse(
            name="qr_detail.html",
            context={
                "request": request,
                "current_user": current_user,
                "is_authenticated": current_user is not None,
                "qr": qr_data,
                "base_url": base_url,
            },
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error in QR detail page for QR ID: {qr_id}", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="qr_detail.html",
            context={
                "request": request,
                "current_user": current_user,
                "is_authenticated": current_user is not None,
                "error": "Unable to load QR code data",
                "qr_id": qr_id,
            },
            status_code=500,
        )
    except Exception as e:
        logger.error(f"Error in QR detail page for QR ID: {qr_id}", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="qr_detail.html",
            context={
                "request": request,
                "current_user": current_user,
                "is_authenticated": current_user is not None,
                "error": "An error occurred while loading the QR code details",
                "qr_id": qr_id,
            },
            status_code=500,
        )


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request, user: Optional[User] = Depends(get_optional_user)):
    """
    Render login page.
    """
    return templates.TemplateResponse(
        name="portal-login.html",
        context={
            "request": request,
            "is_authenticated": user is not None,
            "current_user": user,
        },
    )


@router.get("/portal-login", response_class=HTMLResponse)
async def portal_login(
    request: Request, 
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Render the portal login page.
    
    This endpoint displays login options for students and faculty.
    If the user is already authenticated, their information will be included in the context.
    
    Args:
        request: The FastAPI request object.
        current_user: The current authenticated user (if any).
        
    Returns:
        HTMLResponse: The rendered portal login page.
    """
    try:
        return templates.TemplateResponse(
            name="portal-login.html",
            context={
                "request": request,  # Required by Jinja2Templates
                "current_user": current_user,
                "is_authenticated": current_user is not None,
            },
        )
    except Exception as e:
        logger.error("Error in portal login page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="portal-login.html",
            context={
                "request": request,  # Required by Jinja2Templates
                "error": "An error occurred while loading the login page",
            },
            status_code=500,
        )
