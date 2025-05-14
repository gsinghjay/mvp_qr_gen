"""
Router for QR code redirects.
"""

from datetime import UTC, datetime
import re
from typing import Annotated
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select, or_
from sqlalchemy.exc import SQLAlchemyError

from app.types import DbSessionDep, QRServiceDep
from app.models.qr import QRCode
from app.services.qr_service import QRCodeService
from app.core.config import settings
from app.core.exceptions import QRCodeNotFoundError, DatabaseError

# Configure logger
import logging
logger = logging.getLogger("app.qr.redirect")

router = APIRouter(
    prefix="/r",
    tags=["QR Redirects"],
    responses={
        302: {"description": "Redirect to target URL"},
        404: {"description": "QR code not found"},
        500: {"description": "Internal server error"},
    },
)


@router.get(
    "/{short_id}",
    status_code=status.HTTP_302_FOUND,
    response_class=RedirectResponse,
    responses={
        302: {"description": "Redirect to target URL"},
        404: {"description": "QR code not found"},
        500: {"description": "Internal server error"},
    },
)
async def redirect_qr(
    short_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    qr_service: QRServiceDep,
):
    """
    Redirect a QR code scan to the target URL.

    Args:
        short_id: The short ID from the QR code
        request: The FastAPI request object
        background_tasks: FastAPI background tasks
        qr_service: The QR code service (injected)

    Returns:
        A redirect response to the target URL
    """
    try:
        # Get the QR code using the service
        qr = qr_service.get_qr_by_short_id(short_id)

        # Validate QR code type and redirect URL
        if qr.qr_type != "dynamic" or not qr.redirect_url:
            logger.error(f"Invalid QR code type or missing redirect URL: {qr.id}")
            raise HTTPException(status_code=400, detail="Invalid QR code")

        # Get redirect URL before any background tasks run
        redirect_url = qr.redirect_url

        # Update scan statistics in a background task to improve response time
        timestamp = datetime.now(UTC)

        # Get client information for analytics
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Extract the scan_ref parameter from the query string
        scan_ref = request.query_params.get("scan_ref")
        is_genuine_scan = scan_ref == "qr"
        
        # Log whether this is a genuine scan or direct access
        scan_type = "genuine QR scan" if is_genuine_scan else "direct URL access"
        logger.info(f"Processing {scan_type} for QR {qr.id} with short_id {short_id}")

        # Add the background task to update scan statistics with client info and genuine scan signal
        background_tasks.add_task(
            qr_service.update_scan_statistics, 
            qr.id, 
            timestamp, 
            client_ip, 
            user_agent,
            is_genuine_scan
        )

        # Log the scan event
        logger.info(
            f"QR code scan: {qr.id}",
            extra={
                "qr_id": qr.id,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "timestamp": timestamp.isoformat(),
                "is_genuine_scan": is_genuine_scan,
                "scan_ref": scan_ref,
            },
        )

        # Redirect to the target URL
        return RedirectResponse(url=redirect_url, status_code=302)

    except QRCodeNotFoundError as e:
        logger.warning(f"QR code not found: {short_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        logger.error(f"Database error processing QR code redirect: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing QR code redirect: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing QR code redirect")