"""
Common utilities and dependencies for QR code routes.
"""

import logging

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ...models import QRCode

# Configure logger for QR code routes
logger = logging.getLogger("app.qr")


def get_qr_by_id(qr_id: str, db: Session) -> QRCode:
    """
    Legacy function to get a QR code by ID directly from the database.

    Note: This function is maintained for backward compatibility but should be
    replaced with QRCodeService.get_qr_by_id in new code.

    Args:
        qr_id: The ID of the QR code to retrieve
        db: The database session

    Returns:
        The QR code if found

    Raises:
        HTTPException: If the QR code is not found or there is a database error
    """
    try:
        qr = db.query(QRCode).filter(QRCode.id == qr_id).first()
        if not qr:
            raise HTTPException(status_code=404, detail=f"QR code {qr_id} not found")
        return qr
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving QR code {qr_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error while retrieving QR code")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving QR code {qr_id}: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error while retrieving QR code")
