"""
Common utilities and dependencies for QR code routes.
"""

import logging

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ...models import QRCode
from ...qr_service import QRCodeService

logger = logging.getLogger(__name__)

qr_service = QRCodeService()


def get_qr_by_id(qr_id: str, db: Session) -> QRCode:
    """Get QR code by ID with proper error handling."""
    try:
        qr = db.query(QRCode).filter(QRCode.id == qr_id).first()
        if not qr:
            raise HTTPException(status_code=404, detail=f"QR code with ID {qr_id} not found")
        return qr
    except SQLAlchemyError as e:
        logger.error(f"Database error getting QR code {qr_id}", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail="Database error occurred while retrieving QR code"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting QR code {qr_id}", extra={"error": str(e)})
        raise HTTPException(
            status_code=500, detail="Unexpected error occurred while retrieving QR code"
        )
