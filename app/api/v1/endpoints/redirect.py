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
from app.core.metrics_logger import MetricsLogger

# Configure logger
import logging
logger = logging.getLogger("app.qr.redirect")

# Regex pattern for valid short_id format (8 hexadecimal characters)
SHORT_ID_PATTERN = re.compile(r"^[a-f0-9]{8}$")

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
        # Validate and normalize short_id format
        normalized_short_id = short_id.lower()
        if not SHORT_ID_PATTERN.match(normalized_short_id):
            logger.warning(f"Invalid short_id format: {short_id}")
            raise HTTPException(status_code=404, detail="QR code not found")

        # Get the QR code using the service with normalized short_id
        qr = qr_service.get_qr_by_short_id(normalized_short_id)

        # Validate QR code type and redirect URL
        if qr.qr_type != "dynamic" or not qr.redirect_url or not qr.redirect_url.startswith(('http://', 'https://')):
            logger.error(f"QR code not configured for redirects: {qr.id} (type: {qr.qr_type}, redirect_url: {qr.redirect_url})")
            raise HTTPException(status_code=400, detail="QR code not configured for redirects")

        # Defense-in-depth: validate redirect URL safety
        if not qr_service._is_safe_redirect_url(qr.redirect_url):
            logger.warning(f"Unsafe redirect URL detected for QR {qr.id}: {qr.redirect_url}")
            raise HTTPException(status_code=400, detail="Redirect not permitted")

        # Get redirect URL before any background tasks run
        redirect_url = qr.redirect_url

        # Update scan statistics in a background task to improve response time
        timestamp = datetime.now(UTC)

        # Get client information for analytics - robust IP extraction
        client_ip = (
            request.headers.get("X-Real-IP")
            or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or (request.client.host if request.client else "unknown")
        )
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Extract the scan_ref parameter from the query string
        scan_ref = request.query_params.get("scan_ref")
        is_genuine_scan = scan_ref == "qr"
        
        # Log whether this is a genuine scan or direct access
        scan_type = "genuine QR scan" if is_genuine_scan else "direct URL access"
        logger.info(f"Processing {scan_type} for QR {qr.id} with short_id {normalized_short_id}")

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

        # Log successful redirect processing
        MetricsLogger.log_redirect_processed('success')
        
        # Redirect to the target URL
        return RedirectResponse(url=redirect_url, status_code=302)

    except QRCodeNotFoundError as e:
        logger.info(f"QR code not found: {normalized_short_id if 'normalized_short_id' in locals() else short_id}")
        MetricsLogger.log_redirect_processed('not_found')
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException as http_e:
        # Re-raise HTTPExceptions (including our 400 errors above)
        # Log based on status code
        if http_e.status_code == 400:
            MetricsLogger.log_redirect_processed('invalid')
        else:
            MetricsLogger.log_redirect_processed('error')
        raise
    except DatabaseError as e:
        logger.error(f"Database error processing QR code redirect: {str(e)}")
        MetricsLogger.log_redirect_processed('error')
        raise HTTPException(
            status_code=503, 
            detail="Service temporarily unavailable",
            headers={"Retry-After": "30"}
        )
    except Exception as e:
        logger.exception(f"Unexpected error processing QR code redirect: {str(e)}")
        MetricsLogger.log_redirect_processed('error')
        raise HTTPException(status_code=500, detail="Internal server error")