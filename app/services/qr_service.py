"""
Main QR code service layer for the QR code generator application.
This service now acts as a facade, orchestrating operations via specialized services.
"""

import logging
from io import BytesIO
from typing import Optional, Union, List, Tuple, Dict, Any
from datetime import datetime, timezone # Added timezone


from fastapi import HTTPException
from fastapi.responses import StreamingResponse


from ..core.config import settings, Settings
from ..core.exceptions import (
    QRCodeNotFoundError,
    InvalidQRTypeError,
    QRCodeValidationError,
    RedirectURLError
)
from ..models.qr import QRCode
from ..schemas.common import QRType, ErrorCorrectionLevel
from ..schemas.qr.parameters import (
    DynamicQRCreateParameters,
    QRUpdateParameters,
    StaticQRCreateParameters,
    QRImageParameters
)

# Import the new specialized services
from .qr_management_service import QRManagementService
from .qr_image_service import QRImageService, IMAGE_FORMATS # IMAGE_FORMATS might be useful here
from .qr_analytics_service import QRAnalyticsService
from .qr_validation_service import QRValidationService

# For constructor type hinting, if NewQRGenerationService is passed directly to QRImageService
from .new_qr_generation_service import NewQRGenerationService
import aiobreaker

logger = logging.getLogger(__name__)

class QRCodeService:
    """
    Facade service for QR code operations.
    Delegates calls to specialized services for management, image generation, analytics, and validation.
    """

    def __init__(
        self,
        qr_management_service: QRManagementService,
        qr_image_service: QRImageService,
        qr_analytics_service: QRAnalyticsService,
        qr_validation_service: QRValidationService,
        app_settings: Settings = settings # Allow settings injection for testability
    ):
        self.qr_management_service = qr_management_service
        self.qr_image_service = qr_image_service
        self.qr_analytics_service = qr_analytics_service
        self.qr_validation_service = qr_validation_service
        self.settings = app_settings # If any direct settings access is still needed

    # --- Validation Methods (Delegated) ---
    def _is_safe_redirect_url(self, url: str) -> bool:
        # This method was originally in QRCodeService, now delegated.
        # It's kept here if other methods in this facade still use it directly,
        # otherwise calls should go to qr_validation_service directly from consumer.
        return self.qr_validation_service.is_safe_redirect_url(url)

    def validate_qr_code(self, qr_data: Any) -> None: # qr_data is QRCodeCreate
        # Similarly, kept for facade pattern if needed, else direct call.
        self.qr_validation_service.validate_qr_creation_data(qr_data)

    # --- QR Management Methods (Delegated) ---
    def get_qr_by_id(self, qr_id: str) -> QRCode:
        return self.qr_management_service.get_qr_by_id(qr_id)

    def get_qr_by_short_id(self, short_id: str) -> QRCode:
        return self.qr_management_service.get_qr_by_short_id(short_id)

    def list_qr_codes(
        self,
        skip: int = 0,
        limit: int = 100,
        qr_type: Optional[Union[QRType, str]] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
    ) -> Tuple[List[QRCode], int]:
        return self.qr_management_service.list_qr_codes(
            skip=skip, limit=limit, qr_type=qr_type, search=search, sort_by=sort_by, sort_desc=sort_desc
        )

    async def create_static_qr(self, data: StaticQRCreateParameters) -> QRCode:
        return await self.qr_management_service.create_static_qr(data)

    async def create_dynamic_qr(self, data: DynamicQRCreateParameters) -> QRCode:
        return await self.qr_management_service.create_dynamic_qr(data)

    async def update_qr(self, qr_id: str, data: QRUpdateParameters) -> QRCode:
        return await self.qr_management_service.update_qr(qr_id, data)

    async def update_dynamic_qr(self, qr_id: str, data: QRUpdateParameters) -> QRCode:
        # Maintained for backward compatibility if API directly called this variant
        return await self.qr_management_service.update_dynamic_qr(qr_id, data)

    def delete_qr(self, qr_id: str) -> None:
        self.qr_management_service.delete_qr(qr_id)

    # --- QR Image Generation Methods (Delegated) ---
    async def generate_qr(
        self,
        data: str, # Content to encode
        size: int = 10, # This is 'scale factor' for image_params
        border: int = 4,
        fill_color: str = "black",
        back_color: str = "white",
        error_level: Optional[str] = "M", # String error level
        image_format: str = "png",
        image_quality: Optional[int] = 90, # Legacy support for quality
        include_logo: bool = False,
        svg_title: Optional[str] = None,
        svg_description: Optional[str] = None,
        physical_size: Optional[float] = None,
        physical_unit: Optional[str] = None,
        dpi: Optional[int] = None,
    ) -> StreamingResponse:
        
        image_params = QRImageParameters(
            size=size, # Scale factor
            border=border,
            fill_color=fill_color,
            back_color=back_color,
            include_logo=include_logo,
            svg_title=svg_title,
            svg_description=svg_description,
            physical_size=physical_size,
            physical_unit=physical_unit,
            dpi=dpi
        )
        return await self.qr_image_service.generate_qr_for_streaming(
            data=data,
            image_params=image_params,
            error_level_str=error_level,
            image_format=image_format,
            image_quality=image_quality
        )

    def generate_qr_image_service( # Old name, maps to generate_qr_image_bytes
        self,
        content: str,
        fill_color: str = "#000000",
        back_color: str = "#FFFFFF",
        box_size: int = 10, # This is 'scale factor' for image_params
        border: int = 4,
        image_format: str = "PNG",
        logo_path: Optional[Union[str, bool]] = None, # Maps to include_logo
    ) -> BytesIO:

        image_params = QRImageParameters(
            size=box_size, # Scale factor
            border=border,
            fill_color=fill_color,
            back_color=back_color,
            include_logo=bool(logo_path), # Convert logo_path to boolean include_logo
            # Other params like svg_title, physical_size are not available in this old signature
        )
        # Error level is also missing from old signature, QRImageService will use default
        return self.qr_image_service.generate_qr_image_bytes(
            content=content,
            image_params=image_params,
            image_format=image_format
            # error_level_str will use default in generate_qr_image_bytes
        )

    # --- Analytics Methods (Delegated) ---
    def update_scan_count(self, qr_id: str, timestamp: Optional[datetime] = None) -> None:
        # This specific method only updated scan count via qr_code_repo.update_scan_count
        # The new QRAnalyticsService.update_qr_scan_count_stats is the direct equivalent.
        self.qr_analytics_service.update_qr_scan_count_stats(qr_id, timestamp, is_genuine_scan_signal=False)


    def update_scan_statistics(
        self,
        qr_id: str,
        timestamp: Optional[datetime] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        is_genuine_scan_signal: bool = False,
    ) -> None:
        # This method is now record_scan_event in QRAnalyticsService
        self.qr_analytics_service.record_scan_event(
            qr_id=qr_id,
            timestamp=timestamp,
            client_ip=client_ip,
            user_agent=user_agent,
            is_genuine_scan_signal=is_genuine_scan_signal
        )

    def get_dashboard_data(self) -> Dict[str, Any]:
        return self.qr_analytics_service.get_dashboard_summary()

    def get_scan_analytics_data(self, qr_id: str) -> Dict[str, Any]:
        return self.qr_analytics_service.get_detailed_scan_analytics(qr_id)

    # _parse_user_agent_data and _get_time_series_data were helper methods
    # and are now internal to QRAnalyticsService. They are not exposed on this facade.

    # Note: The original QRCodeService __init__ took qr_code_repo, scan_log_repo,
    # new_qr_generation_service, and new_qr_generation_breaker.
    # These are now encapsulated within the specialized services.
    # The dependency injection mechanism (e.g., in app/dependencies.py) will need to be
    # updated to construct these specialized services and then pass them to this facade.
    # For this step, we assume this facade's __init__ signature is what we'll adapt to.

    # Any methods that were purely helpers for moved logic (like _parse_user_agent_data)
    # are no longer present here as they live within their respective new services.

    # The circuit breaker logic and new/legacy path decision for QR generation
    # are now fully encapsulated within QRImageService.create_and_format_qr_from_service
    # and QRImageService.generate_qr_for_streaming.
    # QRManagementService calls create_and_format_qr_from_service for pre-generation checks.
    # API endpoints will call QRCodeService.generate_qr which in turn calls
    # QRImageService.generate_qr_for_streaming.

    # The original `create_static_qr` and `create_dynamic_qr` in QRCodeService
    # had the new/legacy path logic directly within them. This logic has now been
    # centralized into how QRImageService.create_and_format_qr_from_service is called
    # by QRManagementService.

    logger.info("QRCodeService (Facade) initialized, delegating to specialized services.")
