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

from ...models import QRCode
from ..qr.common import get_db_with_logging, logger


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
            name="index.html",
            context={
                "request": request,  # Required by Jinja2Templates
                "total_qr_codes": total_qr_codes,
                "recent_qr_codes": recent_qr_codes,
            },
        )
    except SQLAlchemyError as e:
        logger.error("Database error in home page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="index.html",
            context={
                "request": request,  # Required by Jinja2Templates
                "total_qr_codes": 0,
                "recent_qr_codes": [],
                "error": "Unable to load QR code data",
            },
            status_code=500,
        )
