"""
Router for dynamic QR code operations.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ...models import QRCode
from ...schemas import QRCodeCreate, QRCodeResponse, QRCodeUpdate
from .common import get_db_with_logging, get_qr_by_id, logger

router = APIRouter(
    prefix="/api/v1/qr/dynamic",
    tags=["dynamic-qr"],
    responses={404: {"description": "Not found"}},
)


@router.post("", response_model=QRCodeResponse)
async def create_dynamic_qr(data: QRCodeCreate, db: Session = Depends(get_db_with_logging)):
    """Create a new dynamic QR code."""
    try:
        if not data.redirect_url:
            raise HTTPException(status_code=422, detail="Dynamic QR codes must have a redirect URL")

        # Generate a short unique identifier for the redirect path
        short_id = str(uuid.uuid4())[:8]
        qr = QRCode(
            content=f"/r/{short_id}",
            qr_type="dynamic",
            redirect_url=str(data.redirect_url),
            fill_color=data.fill_color,
            back_color=data.back_color,
            size=data.size,
            border=data.border,
            created_at=datetime.now(UTC),
        )
        db.add(qr)
        db.commit()
        db.refresh(qr)

        logger.info("Created dynamic QR code", extra={"qr_id": qr.id})
        return qr
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("Database error creating dynamic QR code", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Error creating QR code: database error")
    except Exception:
        db.rollback()
        logger.exception("Unexpected error creating dynamic QR code")
        raise HTTPException(status_code=500, detail="Error creating QR code: unexpected error")


@router.put("/{qr_id}", response_model=QRCodeResponse)
async def update_dynamic_qr(
    qr_id: str, data: QRCodeUpdate, db: Session = Depends(get_db_with_logging)
):
    """Update a dynamic QR code's redirect URL."""
    try:
        qr = get_qr_by_id(qr_id, db)

        if qr.qr_type != "dynamic":
            raise HTTPException(status_code=400, detail="Cannot update static QR code")

        # Validate and update the redirect URL
        if not data.redirect_url:
            raise HTTPException(status_code=422, detail="Redirect URL is required")

        try:
            qr.redirect_url = str(data.redirect_url)
            qr.last_scan_at = datetime.now(UTC)
            db.add(qr)
            db.commit()
            db.refresh(qr)

            logger.info(f"Updated QR code {qr_id} with new redirect URL")
            return qr

        except Exception as e:
            db.rollback()
            logger.error(f"Database error updating QR code: {str(e)}")
            raise HTTPException(status_code=500, detail="Database error while updating QR code")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating QR code: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error while updating QR code")
