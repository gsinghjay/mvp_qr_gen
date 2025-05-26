"""
Service for creating static QR codes with fixed content.
"""

import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Optional

import pybreaker
from pydantic import ValidationError

from ...core.config import settings, should_use_new_service
from ...core.exceptions import QRCodeValidationError
from ...core.metrics_logger import MetricsLogger
from ...models.qr import QRCode
from ...repositories import QRCodeRepository
from ...schemas.common import QRType
from ...schemas.qr.models import QRCodeCreate
from ...schemas.qr.parameters import QRImageParameters, StaticQRCreateParameters
from ..new_qr_generation_service import NewQRGenerationService
from .qr_validation_service import QRValidationService

# Configure logger
logger = logging.getLogger(__name__)

class StaticQRService:
    """Service class for static QR code operations."""

    def __init__(
        self,
        qr_code_repo: QRCodeRepository,
        validation_service: QRValidationService,
        new_qr_generation_service: Optional[NewQRGenerationService] = None,
        new_qr_generation_breaker: Optional[pybreaker.CircuitBreaker] = None
    ):
        """
        Initialize the static QR service with repositories and dependencies.

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

    @MetricsLogger.time_service_call("StaticQRService", "create_static_qr")
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
            self.validation_service.validate_qr_code(qr_data)

            # Create QR code using repository
            qr = self.qr_code_repo.create(qr_data.model_dump())

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
                            content=data.content,
                            image_params=image_params,
                            output_format="png"  # Default format for validation
                        )
                    
                    # Attempt to use the new service with circuit breaker protection
                    _attempt_new_service_validation()
                    
                    # Log metrics for successful new path
                    duration = time.perf_counter() - start_time
                    MetricsLogger.log_qr_generation_path("new", "create_static", duration, True)
                    
                except pybreaker.CircuitBreakerError as e:
                    # Circuit breaker is open - continue without validation
                    duration = time.perf_counter() - start_time
                    logger.warning(f"Circuit breaker for NewQRGenerationService is OPEN during static QR creation. Skipping validation. Error: {e}")
                    MetricsLogger.log_circuit_breaker_fallback("NewQRGenerationService", "create_static_qr")
                    MetricsLogger.log_qr_generation_path("new", "create_static", duration, False)
                except Exception as e:
                    # Log the error but continue with the old implementation
                    # This doesn't affect the database record, just the validation
                    duration = time.perf_counter() - start_time
                    logger.warning(f"Error validating with new QR generation service: {e}")
                    MetricsLogger.log_qr_generation_path("new", "create_static", duration, False)
            else:
                # OLD PATH: No pre-validation (traditional behavior)
                start_time = time.perf_counter()
                # This represents the "old path" which doesn't do pre-validation
                # We just log that we took the old path with minimal duration
                duration = time.perf_counter() - start_time
                MetricsLogger.log_qr_generation_path("old", "create_static", duration, True)

            logger.info(f"Created static QR code with ID {qr.id}")
            
            # Log metrics for successful creation
            MetricsLogger.log_qr_created('static', True)
            
            return qr
        except ValidationError as e:
            # Handle validation errors
            logger.error(f"Validation error creating static QR code: {str(e)}")
            MetricsLogger.log_qr_created('static', False)
            raise QRCodeValidationError(detail=e.errors())
        except ValueError as e:
            # Handle value errors like color validation
            logger.error(f"Validation error creating static QR code: {str(e)}")
            MetricsLogger.log_qr_created('static', False)
            raise QRCodeValidationError(str(e)) 