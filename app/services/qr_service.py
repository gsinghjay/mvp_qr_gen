"""
QR code service layer for the QR code generator application.
"""

import logging
import uuid
from datetime import UTC, datetime
from io import BytesIO
from zoneinfo import ZoneInfo
from typing import Optional, Union, List, Tuple, Dict

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from ..core.exceptions import (
    DatabaseError,
    InvalidQRTypeError,
    QRCodeNotFoundError,
    QRCodeValidationError,
    RedirectURLError,
)
from ..core.config import settings
from ..models.qr import QRCode
from ..repositories.qr_repository import QRCodeRepository
from ..schemas.common import QRType
from ..schemas.qr.models import QRCodeCreate
from ..schemas.qr.parameters import (
    DynamicQRCreateParameters,
    QRUpdateParameters,
    StaticQRCreateParameters,
)
from ..utils.qr_imaging import generate_qr_image as qr_imaging_util, generate_qr_response

# Configure UTC timezone
UTC = ZoneInfo("UTC")

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
    """Service class for QR code operations."""

    def __init__(self, repository: QRCodeRepository):
        """
        Initialize the QR code service with a repository.

        Args:
            repository: QRCodeRepository for database operations
        """
        self.repository = repository

    def get_qr_by_id(self, qr_id: str) -> QRCode:
        """
        Get a QR code by its ID.

        Args:
            qr_id: The ID of the QR code to retrieve

        Returns:
            The QR code object

        Raises:
            QRCodeNotFoundError: If the QR code is not found
            DatabaseError: If a database error occurs
        """
        qr = self.repository.get_by_id(qr_id)
        if not qr:
            raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found")
        return qr

    def create_static_qr(self, data: StaticQRCreateParameters) -> QRCode:
        """
        Create a new static QR code.

        Args:
            data: Parameters for creating a static QR code

        Returns:
            The created QR code object

        Raises:
            QRCodeValidationError: If the QR code data is invalid
            DatabaseError: If a database error occurs
        """
        try:
            # Create QR code data
            qr_data = QRCodeCreate(
                id=str(uuid.uuid4()),
                content=data.content,
                qr_type=QRType.STATIC,
                fill_color=data.fill_color,
                back_color=data.back_color,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            # Validate QR code data
            self.validate_qr_code(qr_data)

            # Create QR code using repository
            qr = self.repository.create(qr_data.model_dump())

            logger.info(f"Created static QR code with ID {qr.id}")
            return qr
        except ValidationError as e:
            logger.error(f"Validation error creating static QR code: {str(e)}")
            raise QRCodeValidationError(detail=e.errors())
        except DatabaseError:
            # Let repository exceptions propagate up
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating static QR code: {str(e)}")
            raise DatabaseError(f"Unexpected error while creating QR code: {str(e)}")

    def create_dynamic_qr(self, data: DynamicQRCreateParameters) -> QRCode:
        """
        Create a dynamic QR code.

        Args:
            data: Parameters for creating a dynamic QR code

        Returns:
            The created QR code object

        Raises:
            QRCodeValidationError: If the QR code data is invalid
            RedirectURLError: If the redirect URL is invalid
            DatabaseError: If a database error occurs
        """
        try:
            # Generate a short unique identifier for the redirect path
            short_id = str(uuid.uuid4())[:8]
            
            # Create full URL with BASE_URL
            full_url = f"{settings.BASE_URL}/r/{short_id}"

            # Create QR code data
            qr_data = QRCodeCreate(
                id=str(uuid.uuid4()),
                content=full_url,
                qr_type=QRType.DYNAMIC,
                redirect_url=str(data.redirect_url),  # Explicitly convert to string
                fill_color=data.fill_color,
                back_color=data.back_color,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            # Validate QR code data
            self.validate_qr_code(qr_data)

            # Create QR code using repository - ensure model_dump() converts HttpUrl to string
            model_data = qr_data.model_dump()
            # Double check that redirect_url is a string
            if "redirect_url" in model_data and not isinstance(model_data["redirect_url"], str):
                model_data["redirect_url"] = str(model_data["redirect_url"])

            qr = self.repository.create(model_data)

            logger.info(f"Created dynamic QR code with ID {qr.id} and redirect path {qr.content}")
            return qr
        except ValidationError as e:
            logger.error(f"Validation error creating dynamic QR code: {str(e)}")
            raise QRCodeValidationError(detail=e.errors())
        except ValueError as e:
            if "URL" in str(e):
                logger.error(f"Invalid redirect URL: {str(e)}")
                raise RedirectURLError(f"Invalid redirect URL: {str(e)}")
            logger.error(f"Validation error creating dynamic QR code: {str(e)}")
            raise QRCodeValidationError(str(e))
        except DatabaseError:
            # Let repository exceptions propagate up
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating dynamic QR code: {str(e)}")
            raise DatabaseError(f"Unexpected error while creating QR code: {str(e)}")

    def update_dynamic_qr(self, qr_id: str, data: QRUpdateParameters) -> QRCode:
        """
        Update a dynamic QR code.

        Args:
            qr_id: The ID of the QR code to update
            data: Parameters for updating the QR code

        Returns:
            The updated QR code object

        Raises:
            QRCodeNotFoundError: If the QR code is not found
            QRCodeValidationError: If the QR code data is invalid
            RedirectURLError: If the redirect URL is invalid
            DatabaseError: If a database error occurs
        """
        try:
            # Get the QR code
            qr = self.get_qr_by_id(qr_id)

            # Verify it's a dynamic QR code
            if qr.qr_type != QRType.DYNAMIC.value:
                raise QRCodeValidationError(f"Cannot update non-dynamic QR code: {qr_id}")

            # Update the QR code using repository
            update_data = {}
            if data.redirect_url:
                # Ensure redirect_url is a string
                update_data["redirect_url"] = str(data.redirect_url)
                update_data["updated_at"] = datetime.now(UTC)

            # Update the QR code in the database using repository
            updated_qr = self.repository.update_qr(qr_id, update_data)
            if not updated_qr:
                raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found")

            logger.info(f"Updated dynamic QR code with ID {updated_qr.id}")
            return updated_qr
        except ValidationError as e:
            logger.error(f"Validation error updating QR code {qr_id}: {str(e)}")
            raise QRCodeValidationError(detail=e.errors())
        except ValueError as e:
            if "URL" in str(e):
                logger.error(f"Invalid redirect URL: {str(e)}")
                raise RedirectURLError(f"Invalid redirect URL: {str(e)}")
            logger.error(f"Validation error updating QR code {qr_id}: {str(e)}")
            raise QRCodeValidationError(str(e))
        except (QRCodeNotFoundError, QRCodeValidationError, RedirectURLError, DatabaseError):
            # Let these exceptions propagate up
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating QR code {qr_id}: {str(e)}")
            raise DatabaseError(f"Unexpected error while updating QR code: {str(e)}")

    def update_scan_count(self, qr_id: str, timestamp: datetime | None = None) -> None:
        """
        Update the scan count for a QR code.

        Args:
            qr_id: The ID of the QR code to update
            timestamp: The timestamp of the scan, defaults to current time

        Raises:
            QRCodeNotFoundError: If the QR code is not found
            DatabaseError: If a database error occurs
        """
        # Delegate to repository
        self.repository.update_scan_count(qr_id, timestamp)

    def update_scan_statistics(
        self,
        qr_id: str,
        timestamp: datetime | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Update scan statistics for a QR code.
        
        This method updates the scan count, last scan timestamp, and other
        statistics for a QR code. It is designed to be run as a background
        task to avoid blocking the redirect response.
        
        Args:
            qr_id: The ID of the QR code to update
            timestamp: The timestamp of the scan, defaults to current time
            client_ip: The IP address of the client that scanned the QR code
            user_agent: The user agent of the client that scanned the QR code
            
        Raises:
            QRCodeNotFoundError: If the QR code is not found
            DatabaseError: If a database error occurs
        """
        # Use repository method to update scan statistics
        self.repository.update_scan_statistics(qr_id, timestamp, client_ip, user_agent)

    def validate_qr_code(self, qr_data: QRCodeCreate) -> None:
        """
        Validate QR code data.

        Args:
            qr_data: The QR code data to validate

        Raises:
            QRCodeValidationError: If the QR code data is invalid
            RedirectURLError: If the redirect URL is invalid
        """
        # Validate content
        if not qr_data.content:
            raise QRCodeValidationError("QR code content cannot be empty")

        # Validate redirect URL for dynamic QR codes
        if qr_data.qr_type == QRType.DYNAMIC and not qr_data.redirect_url:
            raise RedirectURLError("Redirect URL is required for dynamic QR codes")

        # Validate colors
        try:
            # Simple validation for hex color format
            if not qr_data.fill_color.startswith("#") or len(qr_data.fill_color) != 7:
                raise QRCodeValidationError(f"Invalid fill color format: {qr_data.fill_color}")
            if not qr_data.back_color.startswith("#") or len(qr_data.back_color) != 7:
                raise QRCodeValidationError(
                    f"Invalid background color format: {qr_data.back_color}"
                )
        except Exception as e:
            raise QRCodeValidationError(f"Color validation error: {str(e)}")

    def generate_qr_image(
        self,
        content: str,
        fill_color: str = "#000000",
        back_color: str = "#FFFFFF",
        box_size: int = 10,
        border: int = 4,
        image_format: str = "PNG",
        logo_path: Optional[Union[str, bool]] = None,
    ) -> BytesIO:
        """
        Generate a QR code image.

        Args:
            content: The content to encode in the QR code
            fill_color: The color of the QR code (foreground)
            back_color: The background color of the QR code
            box_size: The size of each box/module in the QR code
            border: The size of the border around the QR code
            image_format: The format of the image (PNG, JPEG, etc.)
            logo_path: Optional path to a logo image to embed in the QR code
                - If None, no logo is added
                - If True, the default logo is used
                - If a string, it's used as the path to the logo

        Returns:
            A BytesIO object containing the image data

        Raises:
            Exception: If there is an error generating the QR code image
        """
        try:
            # Calculate the approximate size based on box_size
            size = box_size * 25  # Rough estimate based on typical QR code size
            
            # Generate the QR code using the utility function
            img_bytes = qr_imaging_util(
                content=content,
                image_format=image_format.lower(),
                size=size,
                fill_color=fill_color,
                back_color=back_color,
                border=border,
                logo_path=logo_path
            )
            
            # Create a BytesIO object from the bytes
            img_buffer = BytesIO(img_bytes)
            img_buffer.seek(0)
            
            return img_buffer
        except Exception as e:
            logger.error(f"Error generating QR code image: {e}")
            raise

    def generate_qr(
        self,
        data: str,
        size: int = 10,
        border: int = 4,
        fill_color: str = "black",
        back_color: str = "white",
        error_correction: int = None,  # Remove qrcode.constants.ERROR_CORRECT_H
        image_format: str = "png",
        image_quality: int | None = None,
        include_logo: bool = False,  # Add include_logo parameter
    ) -> StreamingResponse:
        """
        Generate a QR code with the given parameters.

        Args:
            data: Content to encode in the QR code
            size: Size of the QR code image in pixels (approximate)
            border: Border size around the QR code
            fill_color: Color of the QR code pattern
            back_color: Background color
            error_correction: Error correction level (not used with segno)
            image_format: Output image format (png, jpeg, svg, webp)
            image_quality: Quality for lossy formats (1-100)
            include_logo: Whether to include the default logo

        Returns:
            StreamingResponse: FastAPI response containing the QR code image

        Raises:
            HTTPException: If the image format is not supported or conversion fails
        """
        # Calculate the approximate size based on size parameter
        # For segno, we use the total image size rather than box_size
        pixel_size = size * 25  # Rough estimate based on typical QR code size
        
        return generate_qr_response(
            content=data,
            image_format=image_format,
            size=pixel_size,
            fill_color=fill_color,
            back_color=back_color,
            border=border,
            image_quality=image_quality,
            logo_path=True if include_logo else None  # Pass logo_path based on include_logo
        )

    def list_qr_codes(
        self,
        skip: int = 0,
        limit: int = 100,
        qr_type: str | None = None,
        search: str | None = None,
        sort_by: str | None = None,
        sort_desc: bool = False,
    ) -> Tuple[List[QRCode], int]:
        """
        List QR codes with pagination and optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            qr_type: Optional QR code type to filter by
            search: Optional search term for filtering content or redirect URL
            sort_by: Optional field to sort by
            sort_desc: Sort in descending order if true

        Returns:
            A tuple of (list of QR codes, total count)

        Raises:
            InvalidQRTypeError: If an invalid QR type is specified
            DatabaseError: If a database error occurs
        """
        # Validate QR type if specified
        if qr_type and qr_type not in [QRType.STATIC.value, QRType.DYNAMIC.value]:
            raise InvalidQRTypeError(f"Invalid QR type: {qr_type}")
        
        # Delegate to repository
        return self.repository.list_qr_codes(skip, limit, qr_type, search, sort_by, sort_desc)

    def delete_qr(self, qr_id: str) -> None:
        """
        Delete a QR code by ID.

        Args:
            qr_id: The ID of the QR code to delete

        Raises:
            QRCodeNotFoundError: If the QR code is not found
            DatabaseError: If a database error occurs
        """
        # Delete QR code using repository
        deleted = self.repository.delete(qr_id)
        if not deleted:
            raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found")
        logger.info(f"Deleted QR code with ID {qr_id}")

    def get_dashboard_data(self) -> Dict[str, Union[int, List[QRCode]]]:
        """
        Get data for the dashboard, including total QR code count and recent QR codes.
        
        Returns:
            Dictionary containing total_qr_codes and recent_qr_codes
            
        Raises:
            DatabaseError: If a database error occurs
        """
        try:
            # Get count of all QR codes
            total_qr_codes = self.repository.count()
            
            # Get recent QR codes
            recent_qr_codes, _ = self.repository.list_qr_codes(
                skip=0,
                limit=5,
                sort_by="created_at",
                sort_desc=True
            )
            
            return {
                "total_qr_codes": total_qr_codes,
                "recent_qr_codes": recent_qr_codes
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving dashboard data: {str(e)}")
            raise DatabaseError(f"Database error retrieving dashboard data: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving dashboard data: {str(e)}")
            raise DatabaseError(f"Unexpected error retrieving dashboard data: {str(e)}")
    
    def get_qr_by_short_id(self, short_id: str) -> QRCode:
        """
        Get a QR code by short ID used in redirect URLs.
        
        This method handles different content formats for backward compatibility:
        - Full URL: "{BASE_URL}/r/{short_id}"
        - Relative path: "/r/{short_id}"
        - Just the short ID itself
        
        Args:
            short_id: The short ID from the QR code URL
            
        Returns:
            The QR code object
            
        Raises:
            QRCodeNotFoundError: If the QR code is not found
            DatabaseError: If a database error occurs
        """
        try:
            # The short path that would be in old QR codes
            relative_path = f"/r/{short_id}"
            
            # The full URL that would be in new QR codes
            full_url = f"{settings.BASE_URL}/r/{short_id}"
            
            # Try to find QR code by content matching any of the possible formats
            qr = self.repository.find_by_pattern([
                relative_path,
                full_url,
                short_id,
                f"%/r/{short_id}"  # Pattern for partial match (backward compatibility)
            ])
            
            if not qr:
                raise QRCodeNotFoundError(f"QR code with short ID {short_id} not found")
                
            return qr
        except QRCodeNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error finding QR code by short ID {short_id}: {str(e)}")
            raise DatabaseError(f"Database error finding QR code by short ID: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error finding QR code by short ID {short_id}: {str(e)}")
            raise DatabaseError(f"Unexpected error finding QR code by short ID: {str(e)}")
