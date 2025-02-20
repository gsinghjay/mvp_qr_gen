"""
QR code generation service for the QR code generator application.
"""

import logging
from datetime import UTC, datetime
from io import BytesIO

import qrcode
import qrcode.image.svg
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import update
from sqlalchemy.orm import Session

from . import schemas
from .models import QRCode

# Configure logger
logger = logging.getLogger(__name__)

# Define supported image formats and their media types
IMAGE_FORMATS = {
    "png": "image/png",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "svg": "image/svg+xml",
    "webp": "image/webp",
}


class QRCodeService:
    """Service class for QR code generation and customization."""

    @staticmethod
    def generate_qr(
        data: str,
        size: int = 10,
        border: int = 4,
        fill_color: str = "black",
        back_color: str = "white",
        error_correction: int = qrcode.constants.ERROR_CORRECT_H,
        image_format: str = "png",
        image_quality: int | None = None,
    ) -> StreamingResponse:
        """
        Generate a QR code with the given parameters.

        Args:
            data (str): Content to encode in the QR code
            size (int): Size of each box in the QR code
            border (int): Border size around the QR code
            fill_color (str): Color of the QR code pattern
            back_color (str): Background color
            error_correction (int): Error correction level
            image_format (str): Output image format (png, jpeg, svg, webp)
            image_quality (int, optional): Quality for lossy formats (1-100)

        Returns:
            StreamingResponse: FastAPI response containing the QR code image

        Raises:
            HTTPException: If the image format is not supported or conversion fails
        """
        # Validate image format
        image_format = image_format.lower()
        if image_format not in IMAGE_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image format. Supported formats: {', '.join(IMAGE_FORMATS.keys())}",
            )

        try:
            # Handle SVG format separately as it requires different processing
            if image_format == "svg":
                # Use the proper SVG factory that supports styling
                factory = qrcode.image.svg.SvgPathImage
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=error_correction,
                    box_size=size,
                    border=border,
                    image_factory=factory,
                )
                qr.add_data(data)
                qr.make(fit=True)
                # Generate SVG with proper styling
                img = qr.make_image(
                    fill_color=fill_color,
                    back_color=back_color,
                    attrib={"style": f"background-color:{back_color}"},
                )
                # Update the SVG path fill color
                img._img.find("path").set("fill", fill_color)
            else:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=error_correction,
                    box_size=size,
                    border=border,
                )
                qr.add_data(data)
                qr.make(fit=True)
                # Generate image with specified colors
                img = qr.make_image(fill_color=fill_color, back_color=back_color)

            # Convert to final format
            buf = BytesIO()
            save_kwargs = {}
            if image_format in ["jpeg", "jpg", "webp"] and image_quality is not None:
                save_kwargs["quality"] = max(1, min(100, image_quality))
            if image_format == "webp":
                save_kwargs["lossless"] = image_quality is None

            if image_format != "svg":
                img.save(buf, format=image_format.upper(), **save_kwargs)
            else:
                img.save(buf)
            buf.seek(0)

            return StreamingResponse(
                buf,
                media_type=IMAGE_FORMATS[image_format],
                headers={"Content-Disposition": f'inline; filename="qr.{image_format}"'},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating QR code: {str(e)}")

    @staticmethod
    def generate_qr_image(
        content: str,
        fill_color: str = "#000000",
        back_color: str = "#FFFFFF",
        box_size: int = 10,
        border: int = 4,
        image_format: str = "PNG",
    ) -> BytesIO:
        """Generate a QR code image."""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=box_size,
                border=border,
            )
            qr.add_data(content)
            qr.make(fit=True)

            img = qr.make_image(fill_color=fill_color, back_color=back_color)

            img_buffer = BytesIO()
            img.save(img_buffer, format=image_format)
            img_buffer.seek(0)

            return img_buffer

        except Exception as e:
            logger.error(f"Error generating QR code image: {e}")
            raise

    @staticmethod
    def update_scan_count(db: Session, qr_id: str, timestamp: datetime | None = None) -> None:
        """Update the scan count and last scan timestamp for a QR code."""
        try:
            if timestamp is None:
                timestamp = datetime.now(UTC)

            stmt = (
                update(QRCode)
                .where(QRCode.id == qr_id)
                .values(scan_count=QRCode.scan_count + 1, last_scan_at=timestamp)
            )
            db.execute(stmt)
            db.commit()

        except Exception as e:
            logger.error(f"Error updating scan count: {e}")
            db.rollback()
            raise

    @staticmethod
    def validate_qr_code(qr_data: schemas.QRCodeCreate) -> None:
        """Validate QR code data."""
        if qr_data.qr_type == schemas.QRType.DYNAMIC and not qr_data.redirect_url:
            raise ValueError("Dynamic QR codes require a redirect URL")

        if qr_data.qr_type == schemas.QRType.STATIC and qr_data.redirect_url:
            raise ValueError("Static QR codes cannot have a redirect URL")

        if qr_data.fill_color == qr_data.back_color:
            raise ValueError("Fill color and background color must be different")
