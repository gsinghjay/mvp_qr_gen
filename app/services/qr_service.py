"""
QR code service layer for the QR code generator application.
"""

import logging
import time
import uuid
from datetime import UTC, datetime
from io import BytesIO
from zoneinfo import ZoneInfo
from typing import Optional, Union, List, Tuple, Dict, Any
from urllib.parse import urlparse

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
from ..core.config import settings, should_use_new_service
from ..models.qr import QRCode
from ..models.scan_log import ScanLog
from ..repositories import QRCodeRepository, ScanLogRepository
from ..schemas.common import QRType, ErrorCorrectionLevel
from ..schemas.qr.models import QRCodeCreate
from ..schemas.qr.parameters import (
    DynamicQRCreateParameters,
    QRUpdateParameters,
    StaticQRCreateParameters,
    QRImageParameters,
)
from ..utils.qr_imaging import generate_qr_image as qr_imaging_util, generate_qr_response
from ..core.metrics_logger import MetricsLogger
from ..services.new_qr_generation_service import NewQRGenerationService

# Import specialized services from the qr package
from .qr.qr_core_service import QRCoreService
from .qr.qr_validation_service import QRValidationService
from .qr.static_qr_service import StaticQRService
from .qr.dynamic_qr_service import DynamicQRService
from .qr.qr_image_service import QRImageService
from .qr.qr_analytics_service import QRAnalyticsService

# Circuit breaker imports
import pybreaker

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
    """Facade service class for QR code operations that delegates to specialized services."""

    def __init__(
        self, 
        core_service: QRCoreService,
        validation_service: QRValidationService,
        static_qr_service: StaticQRService,
        dynamic_qr_service: DynamicQRService,
        image_service: QRImageService,
        analytics_service: QRAnalyticsService,
        new_qr_generation_service: Optional[NewQRGenerationService] = None,
        new_qr_generation_breaker: Optional[pybreaker.CircuitBreaker] = None
    ):
        """
        Initialize the QR code service facade with specialized service implementations.

        Args:
            core_service: Core QR operations service
            validation_service: QR validation service
            static_qr_service: Static QR creation service
            dynamic_qr_service: Dynamic QR creation and update service
            image_service: QR image generation service
            analytics_service: QR analytics service
            new_qr_generation_service: New QR generation service (optional, for feature flag)
            new_qr_generation_breaker: Circuit breaker for new QR generation service (optional)
        """
        self.core_service = core_service
        self.validation_service = validation_service
        self.static_qr_service = static_qr_service
        self.dynamic_qr_service = dynamic_qr_service
        self.image_service = image_service
        self.analytics_service = analytics_service
        self.new_qr_generation_service = new_qr_generation_service
        self.new_qr_generation_breaker = new_qr_generation_breaker

    # Core operations delegated to QRCoreService
    
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
        return self.core_service.get_qr_by_id(qr_id)

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
        return self.core_service.get_qr_by_short_id(short_id)

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
        return self.core_service.list_qr_codes(
            skip=skip,
            limit=limit,
            qr_type=qr_type,
            search=search,
            sort_by=sort_by,
            sort_desc=sort_desc,
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
        self.core_service.delete_qr(qr_id)

    def get_dashboard_data(self) -> Dict[str, Union[int, List[QRCode]]]:
        """
        Get data for the dashboard, including total QR code count and recent QR codes.
        
        Returns:
            Dictionary containing total_qr_codes and recent_qr_codes
            
        Raises:
            DatabaseError: If a database error occurs
        """
        return self.core_service.get_dashboard_data()

    # Validation operations delegated to QRValidationService
    
    def _is_safe_redirect_url(self, url: str) -> bool:
        """
        Validate if a redirect URL is safe based on scheme and domain allowlist.
        
        Args:
            url: The URL to validate
            
        Returns:
            bool: True if the URL is safe, False otherwise
        """
        return self.validation_service.is_safe_redirect_url(url)

    def validate_qr_code(self, qr_data: Any) -> None:
        """
        Validate QR code data.

        Args:
            qr_data: The QR code data to validate

        Raises:
            QRCodeValidationError: If the QR code data is invalid
            RedirectURLError: If the redirect URL is invalid
        """
        self.validation_service.validate_qr_code(qr_data)

    # Static QR operations delegated to StaticQRService
    
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
        return self.static_qr_service.create_static_qr(data)

    # Dynamic QR operations delegated to DynamicQRService
    
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
        return self.dynamic_qr_service.create_dynamic_qr(data)

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
        return self.dynamic_qr_service.update_qr(qr_id, data)

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
        return self.dynamic_qr_service.update_dynamic_qr(qr_id, data)

    # Image generation operations delegated to QRImageService
    
    def generate_qr_image(
        self,
        content: str,
        fill_color: str = "#000000",
        back_color: str = "#FFFFFF",
        box_size: int = 10,
        border: int = 4,
        image_format: str = "PNG",
        logo_path: Optional[Union[str, bool]] = None,
    ) -> bytes:
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

        Returns:
            A BytesIO object containing the image data

        Raises:
            QRCodeValidationError: If there is an validation error with the QR parameters
            ValueError: If there are issues with the QR generation parameters
            IOError: If there are problems with file operations
        """
        return self.image_service.generate_qr_image(
            content=content,
            fill_color=fill_color,
            back_color=back_color,
            box_size=box_size,
            border=border,
            image_format=image_format,
            logo_path=logo_path
        )

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
        return self.image_service.generate_qr(
            data=data,
            size=size,
            border=border,
            fill_color=fill_color,
            back_color=back_color,
            error_level=error_level,
            image_format=image_format,
            image_quality=image_quality,
            include_logo=include_logo,
            svg_title=svg_title,
            svg_description=svg_description,
            physical_size=physical_size,
            physical_unit=physical_unit,
            dpi=dpi
        )

    # Analytics operations delegated to QRAnalyticsService
    
    def _parse_user_agent_data(self, ua_string: str | None) -> Dict[str, any]:
        """
        Parse a user agent string into structured data for scan log entries.
        
        Args:
            ua_string: Raw user agent string to parse
            
        Returns:
            Dictionary with parsed user agent data
        """
        return self.analytics_service._parse_user_agent_data(ua_string)

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
        self.analytics_service.update_scan_count(qr_id, timestamp)

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
        self.analytics_service.update_scan_statistics(
            qr_id=qr_id,
            timestamp=timestamp,
            client_ip=client_ip,
            user_agent=user_agent,
            is_genuine_scan_signal=is_genuine_scan_signal
        )

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
        return self.analytics_service.get_scan_analytics_data(qr_id)

    def _get_time_series_data(self, qr_id: str) -> Dict[str, List]:
        """
        Get time series scan data for charts (last 7 days).
        
        Args:
            qr_id: ID of the QR code to get time series data for
            
        Returns:
            Dictionary with dates and scan counts
        """
        return self.analytics_service._get_time_series_data(qr_id)
