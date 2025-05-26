"""
Service for creating and updating dynamic QR codes with updatable redirect URLs.
"""

import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Optional

import pybreaker
from pydantic import ValidationError

from ...core.config import settings, should_use_new_service
from ...core.exceptions import QRCodeNotFoundError, QRCodeValidationError, RedirectURLError
from ...core.metrics_logger import MetricsLogger
from ...models.qr import QRCode
from ...repositories import QRCodeRepository
from ...schemas.common import QRType
from ...schemas.qr.models import QRCodeCreate
from ...schemas.qr.parameters import DynamicQRCreateParameters, QRImageParameters, QRUpdateParameters
from ..new_qr_generation_service import NewQRGenerationService
from .qr_validation_service import QRValidationService

# Configure logger
logger = logging.getLogger(__name__)

class DynamicQRService:
    """Service class for dynamic QR code operations."""

    def __init__(
        self,
        qr_code_repo: QRCodeRepository,
        validation_service: QRValidationService,
        new_qr_generation_service: Optional[NewQRGenerationService] = None,
        new_qr_generation_breaker: Optional[pybreaker.CircuitBreaker] = None
    ):
        """
        Initialize the dynamic QR service with repositories and dependencies.

        Args:
            qr_code_repo: Specialized QRCodeRepository for QR code operations
            validation_service: QRValidationService for validating QR code data
            new_qr_generation_service: New QR generation service (optional, for feature flag)
            new_qr_generation_breaker: Circuit breaker for new QR generation service (optional)
        """
        self.qr_code_repo = qr_code_repo
        self.validation_service = validation_service
        self.new_qr_generation_service = new_qr_generation_service
        self.new_qr_generation_breaker = new_qr_generation_breaker

    @MetricsLogger.time_service_call("DynamicQRService", "create_dynamic_qr")
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
            # Validate redirect URL safety
            redirect_url_str = str(data.redirect_url)
            if not self.validation_service.is_safe_redirect_url(redirect_url_str):
                raise RedirectURLError(f"Redirect URL not allowed: {redirect_url_str}")

            # Generate a short unique identifier for the redirect path
            short_id = str(uuid.uuid4())[:8]
            
            # Create full URL with BASE_URL and tracking parameter
            full_url = f"{settings.BASE_URL}/r/{short_id}?scan_ref=qr"

            # Create QR code data
            qr_data = QRCodeCreate(
                id=str(uuid.uuid4()),
                content=full_url,
                qr_type=QRType.DYNAMIC,
                redirect_url=redirect_url_str,  # Use validated string
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
            self.validation_service.validate_qr_code(qr_data)

            # Create QR code using repository - ensure model_dump() converts HttpUrl to string
            model_data = qr_data.model_dump()
            # Double check that redirect_url is a string
            if "redirect_url" in model_data and not isinstance(model_data["redirect_url"], str):
                model_data["redirect_url"] = str(model_data["redirect_url"])

            qr = self.qr_code_repo.create(model_data)

            # Check if we should use the new QR generation service for pre-generating QR image
            # This doesn't affect the database record, but prepares the QR image in advance
            if (self.new_qr_generation_service is not None and 
                self.new_qr_generation_breaker is not None and
                settings.USE_NEW_QR_GENERATION_SERVICE and 
                should_use_new_service(settings)):
                
                # NEW PATH: Use NewQRGenerationService
                start_time = time.perf_counter()
                try:
                    # Create QRImageParameters for the new service
                    image_params = QRImageParameters(
                        size=data.size,
                        border=data.border,
                        fill_color=data.fill_color,
                        back_color=data.back_color,
                        error_level=data.error_level
                    )
                    
                    # Use circuit breaker to wrap the new service call
                    @self.new_qr_generation_breaker
                    def _attempt_new_service_validation():
                        return self.new_qr_generation_service.create_and_format_qr_sync(
                            content=full_url,  # Use the full URL with short_id
                            image_params=image_params,
                            output_format="png"  # Default format for validation
                        )
                    
                    # Attempt to use the new service with circuit breaker protection
                    _attempt_new_service_validation()
                    
                    # Log metrics for successful new path
                    duration = time.perf_counter() - start_time
                    MetricsLogger.log_qr_generation_path("new", "create_dynamic", duration, True)
                    
                except pybreaker.CircuitBreakerError as e:
                    # Circuit breaker is open - continue without validation
                    duration = time.perf_counter() - start_time
                    logger.warning(f"Circuit breaker for NewQRGenerationService is OPEN during dynamic QR creation. Skipping validation. Error: {e}")
                    MetricsLogger.log_circuit_breaker_fallback("NewQRGenerationService", "create_dynamic_qr")
                    MetricsLogger.log_qr_generation_path("new", "create_dynamic", duration, False)
                except Exception as e:
                    # Log the error but continue with the old implementation
                    # This doesn't affect the database record, just the validation
                    duration = time.perf_counter() - start_time
                    logger.warning(f"Error validating with new QR generation service: {e}")
                    MetricsLogger.log_qr_generation_path("new", "create_dynamic", duration, False)
            else:
                # OLD PATH: No pre-validation (traditional behavior)
                start_time = time.perf_counter()
                # This represents the "old path" which doesn't do pre-validation
                # We just log that we took the old path with minimal duration
                duration = time.perf_counter() - start_time
                MetricsLogger.log_qr_generation_path("old", "create_dynamic", duration, True)

            logger.info(f"Created dynamic QR code with ID {qr.id} and redirect path {qr.content}, short_id: {short_id}")
            
            # Log metrics for successful creation
            MetricsLogger.log_qr_created('dynamic', True)
            
            return qr
        except ValidationError as e:
            # Only catch and translate validation errors
            logger.error(f"Validation error creating dynamic QR code: {str(e)}")
            MetricsLogger.log_qr_created('dynamic', False)
            raise QRCodeValidationError(detail=e.errors())
        except ValueError as e:
            # Handle URL validation errors
            if "URL" in str(e):
                logger.error(f"Invalid redirect URL: {str(e)}")
                MetricsLogger.log_qr_created('dynamic', False)
                raise RedirectURLError(f"Invalid redirect URL: {str(e)}")
            # Other value errors are validation errors
            logger.error(f"Validation error creating dynamic QR code: {str(e)}")
            MetricsLogger.log_qr_created('dynamic', False)
            raise QRCodeValidationError(str(e))

    @MetricsLogger.time_service_call("DynamicQRService", "update_qr")
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
            qr = self.qr_code_repo.get_by_id(qr_id)
            
            if not qr:
                raise QRCodeNotFoundError(f"QR code with ID {qr_id} not found")

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
                
                # Validate redirect URL safety
                redirect_url_str = str(data.redirect_url)
                if not self.validation_service.is_safe_redirect_url(redirect_url_str):
                    raise RedirectURLError(f"Redirect URL not allowed: {redirect_url_str}")
                
                # Ensure redirect_url is a string
                update_data["redirect_url"] = redirect_url_str
            
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
    
    # Keeping this method for backwards compatibility
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