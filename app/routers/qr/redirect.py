"""
Router for QR code redirects.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from ...dependencies import get_qr_service
from ...services.qr_service import QRCodeService
from .common import logger

router = APIRouter(
    prefix="/r",
    tags=["redirects"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{short_id}")
async def redirect_qr(
    short_id: str,
    request: Request,
    qr_service: QRCodeService = Depends(get_qr_service),
):
    """
    Redirect a QR code scan to the target URL.

    Args:
        short_id: The short ID from the QR code
        request: The FastAPI request object
        qr_service: The QR code service (injected)

    Returns:
        A redirect response to the target URL
    """
    try:
        # The full path that would be in the QR code content
        full_path = f"/r/{short_id}"

        # Query all QR codes to find the one with matching content
        qr_codes, _ = qr_service.list_qr_codes(limit=1000)
        matching_qr_codes = [qr for qr in qr_codes if qr.content == full_path]

        if not matching_qr_codes:
            logger.warning(f"QR code not found for path: {full_path}")
            raise HTTPException(status_code=404, detail="QR code not found")

        qr = matching_qr_codes[0]

        # Validate QR code type and redirect URL
        if qr.qr_type != "dynamic" or not qr.redirect_url:
            logger.error(f"Invalid QR code type or missing redirect URL: {qr.id}")
            raise HTTPException(status_code=400, detail="Invalid QR code")

        # Update scan statistics in the background
        timestamp = datetime.now(UTC)
        try:
            qr_service.update_scan_count(qr.id, timestamp)
        except Exception as e:
            # Log the error but don't fail the redirect
            logger.error(f"Error updating scan count: {str(e)}")

        # Log the scan event
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        logger.info(
            f"QR code scan: {qr.id}",
            extra={
                "qr_id": qr.id,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "timestamp": timestamp.isoformat(),
            },
        )

        # Redirect to the target URL
        return RedirectResponse(url=qr.redirect_url, status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing QR code redirect: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing QR code redirect")
