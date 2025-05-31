"""
Service for managing QR codes (CRUD operations).
"""
import logging
import time
import uuid
from datetime import timezone, datetime # Changed UTC import
from typing import Optional, Union, List, Tuple, Any, Dict

from pydantic import ValidationError as PydanticValidationError # Alias to avoid clash

from ..core.config import settings, should_use_new_service
from ..core.exceptions import (
    DatabaseError,
    InvalidQRTypeError,
    QRCodeNotFoundError,
    QRCodeValidationError, # This is our custom one
    RedirectURLError,
    ResourceConflictError, # Potentially useful for short_id clashes
    QRCodeGenerationError
)
from ..models.qr import QRCode
from ..repositories.qr_code_repository import QRCodeRepository
from ..repositories.scan_log_repository import ScanLogRepository # For scan count updates if not fully moved
from ..schemas.common import QRType, ErrorCorrectionLevel
from ..schemas.qr.models import QRCodeCreate
from ..schemas.qr.parameters import (
    DynamicQRCreateParameters,
    QRUpdateParameters,
    StaticQRCreateParameters,
    QRImageParameters # For creating image params to pass to image service
)
from .qr_validation_service import QRValidationService
from .qr_image_service import QRImageService
# from .qr_analytics_service import QRAnalyticsService # If direct calls are needed

from ..core.metrics_logger import MetricsLogger
import aiobreaker # For the circuit breaker if still managed here

logger = logging.getLogger(__name__)

class QRManagementService:
    """Service class for QR code management operations."""

    def __init__(
        self,
        qr_code_repo: QRCodeRepository,
        qr_validation_service: QRValidationService,
        qr_image_service: QRImageService,
        # scan_log_repo: ScanLogRepository, # Keep if update_scan_count remains partially here
        # For now, assuming NewQRGenerationService and its breaker are managed by QRImageService
    ):
        self.qr_code_repo = qr_code_repo
        self.qr_validation_service = qr_validation_service
        self.qr_image_service = qr_image_service
        # self.scan_log_repo = scan_log_repo

    @MetricsLogger.time_service_call("QRManagementService", "get_qr_by_id")
    def get_qr_by_id(self, qr_id: str) -> QRCode:
        qr = self.qr_code_repo.get_by_id(qr_id)
        if not qr:
            raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found")
        return qr

    @MetricsLogger.time_service_call("QRManagementService", "get_qr_by_short_id")
    def get_qr_by_short_id(self, short_id: str) -> QRCode:
        qr = self.qr_code_repo.get_by_short_id(short_id)
        if not qr:
            logger.warning(f"QR code with short ID {short_id} not found")
            raise QRCodeNotFoundError(f"QR code with short ID {short_id} not found")
        if qr.qr_type != QRType.DYNAMIC.value: # Use enum value for comparison
            logger.warning(f"QR code with short ID {short_id} is not dynamic (type: {qr.qr_type})")
            raise InvalidQRTypeError(f"QR code with short ID {short_id} is not dynamic")
        return qr

    @MetricsLogger.time_service_call("QRManagementService", "list_qr_codes")
    def list_qr_codes(
        self,
        skip: int = 0,
        limit: int = 100,
        qr_type: Optional[Union[QRType, str]] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
    ) -> Tuple[List[QRCode], int]:
        qr_type_str = qr_type.value if isinstance(qr_type, QRType) else qr_type
        return self.qr_code_repo.list_qr_codes(
            skip=skip, limit=limit, qr_type=qr_type_str, search=search, sort_by=sort_by, sort_desc=sort_desc
        )

    @MetricsLogger.time_service_call("QRManagementService", "create_static_qr")
    async def create_static_qr(self, params: StaticQRCreateParameters) -> QRCode:
        try:
            qr_data_payload = QRCodeCreate(
                content=params.content,
                qr_type=QRType.STATIC,
                title=params.title,
                description=params.description,
                fill_color=params.fill_color,
                back_color=params.back_color,
                size=params.size, # This is scale factor
                border=params.border,
                error_level=params.error_level.value,
            )
            self.qr_validation_service.validate_qr_creation_data(qr_data_payload)

            # Image generation (new vs. legacy is handled by QRImageService)
            # We just need to ensure the QR code can be generated before saving to DB.
            # The actual image isn't stored with the QR record, but parameters are.
            # The QRImageService's create_and_format_qr_from_service can be used if we need bytes.
            # For creation, we might not need the actual image bytes, just confirm params are valid for generation.
            # However, the original service did try to generate an image.

            image_params_for_gen = QRImageParameters(
                fill_color=params.fill_color,
                back_color=params.back_color,
                size=params.size, # Scale factor
                border=params.border,
                include_logo=False # Static QRs typically don't include logos here by default
            )

            # This call will attempt generation, handling new/legacy and circuit breaker internally
            # It returns bytes, which we don't store here, but it validates generation capability.
            try:
                await self.qr_image_service.create_and_format_qr_from_service(
                    content=params.content,
                    image_params=image_params_for_gen,
                    output_format="png", # Default format for validation
                    error_correction=params.error_level
                )
                MetricsLogger.log_qr_created('static', True)
            except Exception as img_gen_exc:
                MetricsLogger.log_qr_created('static', False)
                logger.error(f"Pre-generation check failed for static QR: {img_gen_exc}")
                # Convert to QRCodeGenerationError or re-raise specific error if needed
                raise QRCodeGenerationError(f"Static QR image pre-generation failed: {img_gen_exc}")


            qr = self.qr_code_repo.create(qr_data_payload.model_dump())
            logger.info(f"Created static QR code with ID {qr.id}")
            # MetricsLogger.log_qr_created('static', True) # This metric is now in pre-gen check
            return qr
        except PydanticValidationError as e:
            logger.error(f"Validation error creating static QR code: {e.errors()}")
            MetricsLogger.log_qr_created('static', False)
            raise QRCodeValidationError(detail=e.errors()) # Pass Pydantic errors
        except QRCodeValidationError as e: # Catch our custom validation errors
            logger.error(f"QR Code validation error: {str(e)}")
            MetricsLogger.log_qr_created('static', False)
            raise
        except QRCodeGenerationError as e: # Catch image generation specific errors
             logger.error(f"QR Code generation error: {str(e)}")
             MetricsLogger.log_qr_created('static', False)
             raise
        except Exception as e:
            logger.exception(f"Unexpected error creating static QR: {e}")
            MetricsLogger.log_qr_created('static', False)
            raise DatabaseError(f"Could not create static QR due to an unexpected error: {e}")


    @MetricsLogger.time_service_call("QRManagementService", "create_dynamic_qr")
    async def create_dynamic_qr(self, params: DynamicQRCreateParameters) -> QRCode:
        try:
            redirect_url_str = str(params.redirect_url)
            if not self.qr_validation_service.is_safe_redirect_url(redirect_url_str):
                raise RedirectURLError(f"Redirect URL not allowed: {redirect_url_str}")

            short_id = str(uuid.uuid4())[:8]
            # Ensure short_id is unique (optional, DB constraint should handle this mostly)
            # while self.qr_code_repo.get_by_short_id(short_id) is not None:
            #    short_id = str(uuid.uuid4())[:8]
            #    logger.info(f"Generated new short_id {short_id} due to collision.")

            full_url = f"{settings.BASE_URL}/r/{short_id}?scan_ref=qr"

            qr_data_payload = QRCodeCreate(
                content=full_url,
                qr_type=QRType.DYNAMIC,
                redirect_url=redirect_url_str,
                title=params.title,
                description=params.description,
                fill_color=params.fill_color,
                back_color=params.back_color,
                size=params.size, # Scale factor
                border=params.border,
                error_level=params.error_level.value,
                short_id=short_id,
            )
            self.qr_validation_service.validate_qr_creation_data(qr_data_payload)

            image_params_for_gen = QRImageParameters(
                fill_color=params.fill_color,
                back_color=params.back_color,
                size=params.size, # Scale factor
                border=params.border,
                include_logo=False # Dynamic QRs typically don't include logos here
            )
            try:
                await self.qr_image_service.create_and_format_qr_from_service(
                    content=full_url, # Dynamic QRs encode the redirect path
                    image_params=image_params_for_gen,
                    output_format="png",
                    error_correction=params.error_level
                )
                MetricsLogger.log_qr_created('dynamic', True)
            except Exception as img_gen_exc:
                MetricsLogger.log_qr_created('dynamic', False)
                logger.error(f"Pre-generation check failed for dynamic QR: {img_gen_exc}")
                raise QRCodeGenerationError(f"Dynamic QR image pre-generation failed: {img_gen_exc}")

            model_data = qr_data_payload.model_dump()
            qr = self.qr_code_repo.create(model_data)
            logger.info(f"Created dynamic QR code with ID {qr.id}, short_id: {short_id}")
            # MetricsLogger.log_qr_created('dynamic', True)
            return qr
        except PydanticValidationError as e:
            logger.error(f"Validation error creating dynamic QR code: {e.errors()}")
            MetricsLogger.log_qr_created('dynamic', False)
            raise QRCodeValidationError(detail=e.errors())
        except RedirectURLError as e: # Catch specific redirect error
            logger.error(f"Redirect URL error: {str(e)}")
            MetricsLogger.log_qr_created('dynamic', False)
            raise
        except QRCodeValidationError as e:
            logger.error(f"QR Code validation error: {str(e)}")
            MetricsLogger.log_qr_created('dynamic', False)
            raise
        except QRCodeGenerationError as e:
             logger.error(f"QR Code generation error: {str(e)}")
             MetricsLogger.log_qr_created('dynamic', False)
             raise
        except Exception as e: # Catch-all for other issues like DB errors during creation
            # Check for unique constraint violation for short_id (example, depends on DB driver)
            if "unique constraint" in str(e).lower() and "short_id" in str(e).lower():
                 logger.error(f"Short ID collision for {short_id}: {e}")
                 MetricsLogger.log_qr_created('dynamic', False)
                 raise ResourceConflictError(f"Generated short_id {short_id} already exists. Please try again.")
            logger.exception(f"Unexpected error creating dynamic QR: {e}")
            MetricsLogger.log_qr_created('dynamic', False)
            raise DatabaseError(f"Could not create dynamic QR due to an unexpected error: {e}")


    @MetricsLogger.time_service_call("QRManagementService", "update_qr")
    async def update_qr(self, qr_id: str, params: QRUpdateParameters) -> QRCode:
        try:
            current_qr = self.get_qr_by_id(qr_id) # Ensures QR exists

            update_data: Dict[str, Any] = {}
            if params.title is not None:
                update_data["title"] = params.title
            if params.description is not None:
                update_data["description"] = params.description

            if params.redirect_url is not None:
                if current_qr.qr_type != QRType.DYNAMIC.value:
                    raise QRCodeValidationError("Cannot update redirect URL for non-dynamic QR code.")

                redirect_url_str = str(params.redirect_url)
                if not self.qr_validation_service.is_safe_redirect_url(redirect_url_str):
                    raise RedirectURLError(f"Updated redirect URL not allowed: {redirect_url_str}")
                update_data["redirect_url"] = redirect_url_str

            if not update_data: # No actual changes
                return current_qr

            update_data["updated_at"] = datetime.now(timezone.utc) # Changed UTC

            updated_qr = self.qr_code_repo.update_qr(qr_id, update_data)
            if not updated_qr: # Should not happen if get_qr_by_id succeeded
                raise QRCodeNotFoundError(f"QR code with ID {qr_id} disappeared during update.")

            logger.info(f"Updated QR code with ID {updated_qr.id}")
            return updated_qr
        except PydanticValidationError as e: # If QRUpdateParameters had complex validation
            logger.error(f"Validation error updating QR {qr_id}: {e.errors()}")
            raise QRCodeValidationError(detail=e.errors())
        # Specific exceptions like QRCodeNotFoundError, RedirectURLError, QRCodeValidationError are re-raised
        except (QRCodeNotFoundError, RedirectURLError, QRCodeValidationError) as e:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error updating QR {qr_id}: {e}")
            raise DatabaseError(f"Could not update QR {qr_id} due to an unexpected error: {e}")

    # Keep for backward compatibility if it was exposed in API before
    async def update_dynamic_qr(self, qr_id: str, data: QRUpdateParameters) -> QRCode:
        logger.info("update_dynamic_qr called, redirecting to update_qr.")
        return await self.update_qr(qr_id, data)

    @MetricsLogger.time_service_call("QRManagementService", "delete_qr")
    def delete_qr(self, qr_id: str) -> None:
        deleted = self.qr_code_repo.delete(qr_id)
        if not deleted:
            raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found for deletion.")
        logger.info(f"Deleted QR code with ID {qr_id}")
