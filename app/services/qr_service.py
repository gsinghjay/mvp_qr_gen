"""
QR code service layer for the QR code generator application.
"""

import logging
import uuid
from datetime import UTC, datetime
from io import BytesIO
from zoneinfo import ZoneInfo
from typing import Optional, Union, List, Tuple, Dict, Any

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from user_agents import parse as parse_user_agent

from ..core.exceptions import (
    DatabaseError,
    InvalidQRTypeError,
    QRCodeNotFoundError,
    QRCodeValidationError,
    RedirectURLError,
)
from ..core.config import settings
from ..models.qr import QRCode
from ..models.scan_log import ScanLog
from ..repositories import QRCodeRepository, ScanLogRepository
from ..schemas.common import QRType, ErrorCorrectionLevel
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

    def __init__(
        self, 
        qr_code_repo: QRCodeRepository,
        scan_log_repo: ScanLogRepository
    ):
        """
        Initialize the QR code service with repositories.

        Args:
            qr_code_repo: Specialized QRCodeRepository for QR code operations
            scan_log_repo: ScanLogRepository for scan log operations
        """
        self.qr_code_repo = qr_code_repo
        self.scan_log_repo = scan_log_repo

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
        qr = self.qr_code_repo.get_by_id(qr_id)
            
        if not qr:
            raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found")
        return qr

    def get_qr_by_short_id(self, short_id: str) -> QRCode:
        """
        Get a QR code by its short ID (used for redirects).

        Args:
            short_id: The short ID of the QR code to retrieve

        Returns:
            The QR code object

        Raises:
            QRCodeNotFoundError: If the QR code is not found
            InvalidQRTypeError: If the QR code is not of type 'dynamic'
            DatabaseError: If a database error occurs
        """
        # Look up QR code directly by short_id
        qr = self.qr_code_repo.get_by_short_id(short_id)

        if not qr:
            logger.warning(f"QR code with short ID {short_id} not found")
            raise QRCodeNotFoundError(f"QR code with short ID {short_id} not found")

        # Ensure the QR code is of type 'dynamic' for redirects
        if qr.qr_type != 'dynamic':
            logger.warning(f"QR code with short ID {short_id} is not dynamic (type: {qr.qr_type})")
            raise InvalidQRTypeError(f"QR code with short ID {short_id} is not dynamic")

        return qr

    def list_qr_codes(
        self,
        skip: int = 0,
        limit: int = 100,
        qr_type: Union[QRType, str, None] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
    ) -> Tuple[List[QRCode], int]:
        """
        List QR codes with optional filtering and sorting.

        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            qr_type: QR code type to filter by
            search: Search term for filtering
            sort_by: Field to sort by
            sort_desc: Sort in descending order if true

        Returns:
            Tuple of (list of QR codes, total count)

        Raises:
            DatabaseError: If a database error occurs
        """
        # Convert enum to value if it's an enum
        qr_type_str = None
        if qr_type is not None:
            if isinstance(qr_type, QRType):
                qr_type_str = qr_type.value
            else:
                qr_type_str = qr_type

        return self.qr_code_repo.list_qr_codes(
            skip=skip,
            limit=limit,
            qr_type=qr_type_str,
            search=search,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

    def create_static_qr(self, data: StaticQRCreateParameters) -> QRCode:
        """
        Create a static QR code with the provided content.

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
                title=data.title,
                description=data.description,
                fill_color=data.fill_color,
                back_color=data.back_color,
                size=data.size,
                border=data.border,
                error_level=data.error_level.value,
                created_at=datetime.now(UTC),
            )

            # Validate QR code data
            self.validate_qr_code(qr_data)

            # Create QR code using repository
            qr = self.qr_code_repo.create(qr_data.model_dump())

            logger.info(f"Created static QR code with ID {qr.id}")
            return qr
        except ValidationError as e:
            # Handle validation errors
            logger.error(f"Validation error creating static QR code: {str(e)}")
            raise QRCodeValidationError(detail=e.errors())
        except ValueError as e:
            # Handle value errors like color validation
            logger.error(f"Validation error creating static QR code: {str(e)}")
            raise QRCodeValidationError(str(e))

    def create_dynamic_qr(self, data: DynamicQRCreateParameters) -> QRCode:
        """
        Create a dynamic QR code with the provided data.

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
            
            # Create full URL with BASE_URL and tracking parameter
            full_url = f"{settings.BASE_URL}/r/{short_id}?scan_ref=qr"

            # Create QR code data
            qr_data = QRCodeCreate(
                id=str(uuid.uuid4()),
                content=full_url,
                qr_type=QRType.DYNAMIC,
                redirect_url=str(data.redirect_url),  # Explicitly convert to string
                title=data.title,
                description=data.description,
                fill_color=data.fill_color,
                back_color=data.back_color,
                size=data.size,
                border=data.border,
                error_level=data.error_level.value,
                created_at=datetime.now(UTC),
                short_id=short_id,  # Store the short_id in the database
            )

            # Validate QR code data
            self.validate_qr_code(qr_data)

            # Create QR code using repository - ensure model_dump() converts HttpUrl to string
            model_data = qr_data.model_dump()
            # Double check that redirect_url is a string
            if "redirect_url" in model_data and not isinstance(model_data["redirect_url"], str):
                model_data["redirect_url"] = str(model_data["redirect_url"])

            qr = self.qr_code_repo.create(model_data)

            logger.info(f"Created dynamic QR code with ID {qr.id} and redirect path {qr.content}, short_id: {short_id}")
            return qr
        except ValidationError as e:
            # Only catch and translate validation errors
            logger.error(f"Validation error creating dynamic QR code: {str(e)}")
            raise QRCodeValidationError(detail=e.errors())
        except ValueError as e:
            # Handle URL validation errors
            if "URL" in str(e):
                logger.error(f"Invalid redirect URL: {str(e)}")
                raise RedirectURLError(f"Invalid redirect URL: {str(e)}")
            # Other value errors are validation errors
            logger.error(f"Validation error creating dynamic QR code: {str(e)}")
            raise QRCodeValidationError(str(e))

    def _parse_user_agent_data(self, ua_string: str | None) -> Dict[str, any]:
        """
        Parse a user agent string into structured data for scan log entries.
        
        Args:
            ua_string: Raw user agent string to parse
            
        Returns:
            Dictionary with parsed user agent data
        """
        if not ua_string:
            return {
                "device_family": "Unknown",
                "os_family": "Unknown",
                "os_version": "Unknown",
                "browser_family": "Unknown",
                "browser_version": "Unknown",
                "is_mobile": False,
                "is_tablet": False,
                "is_pc": True,  # Default to PC if unknown
                "is_bot": False
            }
        
        try:
            # Parse the user agent string
            user_agent = parse_user_agent(ua_string)
            
            # Extract device information
            is_mobile = user_agent.is_mobile
            is_tablet = user_agent.is_tablet
            is_pc = not (is_mobile or is_tablet)
            is_bot = user_agent.is_bot
            
            # Create structured data dictionary
            return {
                "device_family": user_agent.device.family or "Unknown",
                "os_family": user_agent.os.family or "Unknown",
                "os_version": f"{user_agent.os.version_string}" if user_agent.os.version_string else "Unknown",
                "browser_family": user_agent.browser.family or "Unknown",
                "browser_version": f"{user_agent.browser.version_string}" if user_agent.browser.version_string else "Unknown",
                "is_mobile": is_mobile,
                "is_tablet": is_tablet,
                "is_pc": is_pc,
                "is_bot": is_bot
            }
        except Exception as e:
            # Log the error but return default values rather than failing
            logger.error(f"Error parsing user agent string: {str(e)}")
            return {
                "device_family": "Parse Error",
                "os_family": "Unknown",
                "os_version": "Unknown",
                "browser_family": "Unknown",
                "browser_version": "Unknown",
                "is_mobile": False,
                "is_tablet": False,
                "is_pc": False,
                "is_bot": False
            }

    def update_qr(self, qr_id: str, data: QRUpdateParameters) -> QRCode:
        """
        Update a QR code with the provided data.

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

            # Build update data dictionary
            update_data = {}
            
            # Handle title update
            if data.title is not None:
                update_data["title"] = data.title
                
            # Handle description update
            if data.description is not None:
                update_data["description"] = data.description
                
            # Handle redirect_url update (only for dynamic QR codes)
            if data.redirect_url is not None:
                # Verify it's a dynamic QR code
                if qr.qr_type != QRType.DYNAMIC.value:
                    raise QRCodeValidationError(f"Cannot update redirect URL for non-dynamic QR code: {qr_id}")
                # Ensure redirect_url is a string
                update_data["redirect_url"] = str(data.redirect_url)
            
            # Only set updated_at if we're actually updating something
            if update_data:
                update_data["updated_at"] = datetime.now(UTC)
            else:
                # No fields to update - return the existing QR code
                return qr

            # Update the QR code in the database using repository
            updated_qr = self.qr_code_repo.update_qr(qr_id, update_data)
            if not updated_qr:
                raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found")

            logger.info(f"Updated QR code with ID {updated_qr.id}")
            return updated_qr
        except ValidationError as e:
            # Only catch and translate validation errors
            logger.error(f"Validation error updating QR code {qr_id}: {str(e)}")
            raise QRCodeValidationError(detail=e.errors())
        except ValueError as e:
            # Handle URL validation errors
            if "URL" in str(e):
                logger.error(f"Invalid redirect URL: {str(e)}")
                raise RedirectURLError(f"Invalid redirect URL: {str(e)}")
            # Other value errors are validation errors
            logger.error(f"Validation error updating QR code {qr_id}: {str(e)}")
            raise QRCodeValidationError(str(e))
    
    # Keep the update_dynamic_qr method for backwards compatibility
    def update_dynamic_qr(self, qr_id: str, data: QRUpdateParameters) -> QRCode:
        """
        Update a dynamic QR code.

        This method is maintained for backwards compatibility and delegates to update_qr.

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
        return self.update_qr(qr_id, data)

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
        if timestamp is None:
            timestamp = datetime.now(UTC)
            
        # Delegate to repository
        self.qr_code_repo.update_scan_count(qr_id, timestamp, is_genuine_scan_signal=False)

    def update_scan_statistics(
        self,
        qr_id: str,
        timestamp: datetime | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
        is_genuine_scan_signal: bool = False,
    ) -> None:
        """
        Update scan statistics for a QR code.
        
        This method updates the scan count, last scan timestamp, and other
        statistics for a QR code. It is designed to be run as a background
        task to avoid blocking the redirect response.
        
        This implementation orchestrates between QRCodeRepository and ScanLogRepository
        to update QR code statistics and create scan log entries, respectively.
        
        Args:
            qr_id: The ID of the QR code to update
            timestamp: The timestamp of the scan, defaults to current time
            client_ip: The IP address of the client that scanned the QR code
            user_agent: The user agent of the client that scanned the QR code
            is_genuine_scan_signal: Whether this is a genuine QR scan (vs. direct URL access)
            
        Raises:
            QRCodeNotFoundError: If the QR code is not found
            DatabaseError: If a database error occurs
        """
        if timestamp is None:
            timestamp = datetime.now(UTC)

        # Parse user agent data
        parsed_ua_data = self._parse_user_agent_data(user_agent)
        
        # 1. Update QR code scan statistics (scan_count, genuine_scan_count, etc.)
        updated_qr = self.qr_code_repo.update_scan_count(qr_id, timestamp, is_genuine_scan_signal)
        if not updated_qr:
            logger.warning(f"Failed to update scan count for QR ID {qr_id}.")
            return  # Or raise appropriate error
            
        # 2. Create scan log entry
        self.scan_log_repo.create_scan_log(
            qr_id=qr_id,
            timestamp=timestamp,
            ip_address=client_ip,
            raw_user_agent=user_agent,
            parsed_ua_data=parsed_ua_data,
            is_genuine_scan_signal=is_genuine_scan_signal
        )
        logger.info(f"Scan statistics and log updated for QR ID {qr_id}")

    def validate_qr_code(self, qr_data: QRCodeCreate) -> None:
        """
        Validate QR code data.

        Args:
            qr_data: The QR code data to validate

        Raises:
            QRCodeValidationError: If the QR code data is invalid
            RedirectURLError: If the redirect URL is invalid
        """
        # Check for required content in static QR codes
        if qr_data.qr_type == QRType.STATIC and not qr_data.content:
            raise QRCodeValidationError("Static QR codes must have content")

        # Check for required redirect_url in dynamic QR codes
        if qr_data.qr_type == QRType.DYNAMIC and not qr_data.redirect_url:
            raise RedirectURLError("Dynamic QR codes must have a redirect URL")

        # Color format validation is handled by Pydantic schemas

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
            QRCodeValidationError: If there is an validation error with the QR parameters
            ValueError: If there are issues with the QR generation parameters
            IOError: If there are problems with file operations
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
        except ValueError as e:
            # Handle parameter validation errors
            logger.error(f"Parameter validation error generating QR code image: {e}")
            raise QRCodeValidationError(f"Invalid parameters for QR generation: {str(e)}")
        except IOError as e:
            # Handle file/IO errors (e.g., logo file not found)
            logger.error(f"IO error generating QR code image: {e}")
            raise QRCodeValidationError(f"Error processing QR code image: {str(e)}")

    def generate_qr(
        self,
        data: str,
        size: int = 10,
        border: int = 4,
        fill_color: str = "black",
        back_color: str = "white",
        error_level: str | None = None,
        image_format: str = "png",
        image_quality: int | None = None,
        include_logo: bool = False,
        svg_title: str | None = None,
        svg_description: str | None = None,
        physical_size: float | None = None,
        physical_unit: str | None = None,
        dpi: int | None = None,
    ) -> StreamingResponse:
        """
        Generate a QR code with the given parameters.

        Args:
            data: Content to encode in the QR code
            size: Size of the QR code image in pixels (approximate)
            border: Border size around the QR code
            fill_color: Color of the QR code pattern
            back_color: Background color
            error_level: Error correction level (l, m, q, h)
            image_format: Output image format (png, jpeg, svg, webp)
            image_quality: Quality for lossy formats (1-100)
            include_logo: Whether to include the default logo
            svg_title: Optional title for SVG format (improves accessibility)
            svg_description: Optional description for SVG format (improves accessibility)
            physical_size: Physical size of the QR code in the specified unit
            physical_unit: Physical unit for size (in, cm, mm)
            dpi: DPI (dots per inch) for physical output

        Returns:
            StreamingResponse: FastAPI response containing the QR code image

        Raises:
            HTTPException: If the image format is not supported or conversion fails
        """
        # If physical dimensions are specified, use them directly
        if physical_size is not None and physical_unit is not None and dpi is not None:
            # Calculate pixel size from physical dimensions and DPI to set final output size
            if physical_unit == "in":
                pixel_size = int(physical_size * dpi)
            elif physical_unit == "cm":
                pixel_size = int(physical_size * dpi / 2.54)  # 1 inch = 2.54 cm
            elif physical_unit == "mm":
                pixel_size = int(physical_size * dpi / 25.4)  # 1 inch = 25.4 mm
            else:
                # Default to size parameter if physical unit is not recognized
                pixel_size = size * 25  # Rough estimate based on typical QR code size
        else:
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
            logo_path=True if include_logo else None,  # Pass logo_path based on include_logo
            error_level=error_level,
            svg_title=svg_title,
            svg_description=svg_description,
            physical_size=physical_size,
            physical_unit=physical_unit,
            dpi=dpi
        )

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
        deleted = self.qr_code_repo.delete(qr_id)
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
        # Get count of all QR codes
        total_qr_codes = self.qr_code_repo.count()
        
        # Get recent QR codes
        recent_qr_codes, _ = self.qr_code_repo.list_qr_codes(
            skip=0,
            limit=5,
            sort_by="created_at",
            sort_desc=True
        )
        
        return {
            "total_qr_codes": total_qr_codes,
            "recent_qr_codes": recent_qr_codes
        }

    def get_scan_analytics_data(self, qr_id: str) -> Dict[str, Any]:
        """
        Get detailed scan analytics data for a QR code.
        
        Args:
            qr_id: ID of the QR code to get analytics for
            
        Returns:
            Dictionary containing detailed analytics data
            
        Raises:
            QRCodeNotFoundError: If the QR code is not found
            DatabaseError: If a database error occurs
        """
        # Get the QR code to verify it exists and get basic info
        qr = self.get_qr_by_id(qr_id)
        
        # Get scan logs for the QR code
        scan_logs, total_logs = self.scan_log_repo.get_scan_logs_for_qr(qr_id, limit=100)
        
        # Get device statistics
        device_stats = self.scan_log_repo.get_device_statistics(qr_id)
        
        # Get browser statistics
        browser_stats = self.scan_log_repo.get_browser_statistics(qr_id)
        
        # Get OS statistics
        os_stats = self.scan_log_repo.get_os_statistics(qr_id)
        
        # Calculate percentage of genuine scans
        genuine_scan_pct = 0
        if qr.scan_count > 0:
            genuine_scan_pct = round((qr.genuine_scan_count / qr.scan_count) * 100)
        
        # Prepare timestamps for display
        created_at_formatted = qr.created_at.strftime("%B %d, %Y at %H:%M")
        last_scan_formatted = qr.last_scan_at.strftime("%B %d, %Y at %H:%M") if qr.last_scan_at else "Not yet scanned"
        first_genuine_scan_formatted = qr.first_genuine_scan_at.strftime("%B %d, %Y at %H:%M") if qr.first_genuine_scan_at else None
        last_genuine_scan_formatted = qr.last_genuine_scan_at.strftime("%B %d, %Y at %H:%M") if qr.last_genuine_scan_at else None
        
        # Prepare scan log data for table display
        scan_log_data = []
        for log in scan_logs:
            scan_log_data.append({
                "id": log.id,
                "scanned_at": log.scanned_at.strftime("%Y-%m-%d %H:%M:%S"),
                "is_genuine_scan": log.is_genuine_scan,
                "device_family": log.device_family,
                "os_family": log.os_family,
                "browser_family": log.browser_family,
                "is_mobile": log.is_mobile,
                "is_tablet": log.is_tablet,
                "is_pc": log.is_pc,
                "is_bot": log.is_bot
            })
        
        # Get time series data for chart (last 7 days)
        time_series_data = self._get_time_series_data(qr_id)
        
        return {
            "qr": qr,
            "created_at_formatted": created_at_formatted,
            "last_scan_formatted": last_scan_formatted,
            "first_genuine_scan_formatted": first_genuine_scan_formatted,
            "last_genuine_scan_formatted": last_genuine_scan_formatted,
            "genuine_scan_pct": genuine_scan_pct,
            "total_logs": total_logs,
            "scan_logs": scan_log_data,
            "device_stats": device_stats,
            "browser_stats": browser_stats,
            "os_stats": os_stats,
            "time_series_data": time_series_data
        }
        
    def _get_time_series_data(self, qr_id: str) -> Dict[str, List]:
        """
        Get time series scan data for charts (last 7 days).
        
        Args:
            qr_id: ID of the QR code to get time series data for
            
        Returns:
            Dictionary with dates and scan counts
        """
        # Get scan timeseries data
        timeseries_data = self.scan_log_repo.get_scan_timeseries(qr_id, time_range="last7days")
        return timeseries_data
