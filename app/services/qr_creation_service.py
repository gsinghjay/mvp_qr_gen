import logging
import time
import uuid
from typing import Optional
from urllib.parse import urlparse

import aiobreaker
from pydantic import ValidationError

from app.core.config import Settings, should_use_new_service # For settings and feature flag
from app.core.exceptions import (
    QRCodeValidationError,
    RedirectURLError,
)
from app.models.qr import QRCode
from app.repositories.qr_code_repository import QRCodeRepository
from app.schemas.common import QRType
from app.schemas.qr.models import QRCodeCreate
from app.schemas.qr.parameters import (
    DynamicQRCreateParameters,
    StaticQRCreateParameters,
    QRImageParameters # Needed for new service path
)
from app.services.new_qr_generation_service import NewQRGenerationService
from app.core.metrics_logger import MetricsLogger # Assuming this is used by the creation methods

logger = logging.getLogger(__name__)

class QRCreationService:
    def __init__(
        self,
        qr_code_repo: QRCodeRepository,
        settings: Settings, # Injected for BASE_URL, USE_NEW_QR_GENERATION_SERVICE
        new_qr_generation_service: Optional[NewQRGenerationService],
        new_qr_generation_breaker: Optional[aiobreaker.CircuitBreaker],
    ):
        self.qr_code_repo = qr_code_repo
        self.settings = settings
        self.new_qr_generation_service = new_qr_generation_service
        self.new_qr_generation_breaker = new_qr_generation_breaker

    # Moved from QRCodeService
    def _is_safe_redirect_url(self, url: str) -> bool:
        """
        Validate if a redirect URL is safe based on scheme validation only.
        
        Allows any HTTP/HTTPS URL to any domain while blocking malicious schemes.

        Args:
            url: The URL to validate

        Returns:
            bool: True if the URL is safe, False otherwise
        """
        try:
            parsed_url = urlparse(url)

            # Check if scheme is http or https - this is the primary security boundary
            if parsed_url.scheme not in ("http", "https"):
                logger.warning(f"Unsafe URL scheme: {parsed_url.scheme}")
                return False

            # Ensure domain exists
            domain = parsed_url.netloc.lower()
            if not domain:
                logger.warning("URL has no domain")
                return False

            # All HTTP/HTTPS URLs with valid domains are now allowed
            logger.info(f"Validated redirect URL: {url}")
            return True

        except Exception as e:
            logger.error(f"Error parsing URL {url}: {str(e)}")
            return False

    # Moved from QRCodeService (was validate_qr_code)
    def _validate_qr_code(self, qr_data: QRCodeCreate) -> None:
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

    # Moved from QRCodeService
    @MetricsLogger.time_service_call("QRCreationService", "create_static_qr") # Updated Metric Tag
    async def create_static_qr(self, data: StaticQRCreateParameters) -> QRCode:
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
                content=data.content,
                qr_type=QRType.STATIC,
                title=data.title,
                description=data.description,
                fill_color=data.fill_color,
                back_color=data.back_color,
                size=data.size,
                border=data.border,
                error_level=data.error_level.value,
            )

            # Validate QR code data
            self._validate_qr_code(qr_data) # Changed to self._validate_qr_code

            # Check if we should use the new QR generation service with circuit breaker protection
            if (self.new_qr_generation_service is not None and
                self.new_qr_generation_breaker is not None and
                self.settings.USE_NEW_QR_GENERATION_SERVICE and # Changed to self.settings
                should_use_new_service(self.settings, user_identifier=qr_data.content)): # Changed to self.settings

                new_path_start_time = time.perf_counter()
                try:
                    image_params = QRImageParameters(
                        fill_color=data.fill_color,
                        back_color=data.back_color,
                        size=data.size,
                        border=data.border,
                        include_logo=False
                    )

                    @self.new_qr_generation_breaker
                    async def protected_create_static_qr():
                        return await self.new_qr_generation_service.create_and_format_qr(
                            content=data.content,
                            image_params=image_params,
                            output_format="png", # Assuming default or placeholder, this might need to be configurable
                            error_correction=data.error_level
                        )

                    _ = await protected_create_static_qr() # Image bytes not directly used here for DB record

                    qr = self.qr_code_repo.create(qr_data.model_dump())

                    new_path_duration = time.perf_counter() - new_path_start_time
                    MetricsLogger.log_qr_generation_path("new", "create_static_qr", True, new_path_duration)

                    logger.info(f"Created static QR code with ID {qr.id} using new service")
                    MetricsLogger.log_qr_created('static', True)
                    return qr

                except aiobreaker.CircuitBreakerError as e:
                    new_path_duration = time.perf_counter() - new_path_start_time
                    MetricsLogger.log_qr_generation_path("new", "create_static_qr", False, new_path_duration)
                    logger.warning(f"Circuit breaker open for NewQRGenerationService: {e}")
                    MetricsLogger.log_circuit_breaker_fallback("NewQRGenerationService", "create_static_qr", "circuit_open")

                except Exception as e:
                    new_path_duration = time.perf_counter() - new_path_start_time
                    MetricsLogger.log_qr_generation_path("new", "create_static_qr", False, new_path_duration)
                    logger.error(f"Error with NewQRGenerationService: {e}")
                    MetricsLogger.log_circuit_breaker_fallback("NewQRGenerationService", "create_static_qr", "exception")

            old_path_start_time = time.perf_counter()
            try:
                qr = self.qr_code_repo.create(qr_data.model_dump())
                old_path_duration = time.perf_counter() - old_path_start_time
                MetricsLogger.log_qr_generation_path("old", "create_static_qr", True, old_path_duration)
                logger.info(f"Created static QR code with ID {qr.id} using legacy service")
            except Exception as e:
                old_path_duration = time.perf_counter() - old_path_start_time
                MetricsLogger.log_qr_generation_path("old", "create_static_qr", False, old_path_duration)
                raise

            MetricsLogger.log_qr_created('static', True)
            return qr
        except ValidationError as e:
            logger.error(f"Validation error creating static QR code: {str(e)}")
            MetricsLogger.log_qr_created('static', False)
            raise QRCodeValidationError(detail=e.errors())
        except ValueError as e:
            logger.error(f"Validation error creating static QR code: {str(e)}")
            MetricsLogger.log_qr_created('static', False)
            raise QRCodeValidationError(str(e))

    # Moved from QRCodeService
    @MetricsLogger.time_service_call("QRCreationService", "create_dynamic_qr") # Updated Metric Tag
    async def create_dynamic_qr(self, data: DynamicQRCreateParameters) -> QRCode:
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
            redirect_url_str = str(data.redirect_url)
            if not self._is_safe_redirect_url(redirect_url_str): # Changed to self._is_safe_redirect_url
                raise RedirectURLError(f"Invalid redirect URL: {redirect_url_str}. Only HTTP and HTTPS URLs are allowed.")

            short_id = str(uuid.uuid4())[:8]
            full_url = f"{self.settings.BASE_URL}/r/{short_id}?scan_ref=qr" # Changed to self.settings

            qr_data = QRCodeCreate(
                content=full_url,
                qr_type=QRType.DYNAMIC,
                redirect_url=redirect_url_str,
                title=data.title,
                description=data.description,
                fill_color=data.fill_color,
                back_color=data.back_color,
                size=data.size,
                border=data.border,
                error_level=data.error_level.value,
                short_id=short_id,
            )

            self._validate_qr_code(qr_data) # Changed to self._validate_qr_code

            if (self.new_qr_generation_service is not None and
                self.new_qr_generation_breaker is not None and
                self.settings.USE_NEW_QR_GENERATION_SERVICE and # Changed to self.settings
                should_use_new_service(self.settings, user_identifier=qr_data.content)): # Changed to self.settings

                new_path_start_time = time.perf_counter()
                try:
                    image_params = QRImageParameters(
                        fill_color=data.fill_color,
                        back_color=data.back_color,
                        size=data.size,
                        border=data.border,
                        include_logo=False
                    )

                    @self.new_qr_generation_breaker
                    async def protected_create_dynamic_qr():
                        return await self.new_qr_generation_service.create_and_format_qr(
                            content=full_url,
                            image_params=image_params,
                            output_format="png", # Assuming default or placeholder
                            error_correction=data.error_level
                        )

                    _ = await protected_create_dynamic_qr() # Image bytes not directly used

                    model_data = qr_data.model_dump()
                    if "redirect_url" in model_data and not isinstance(model_data["redirect_url"], str):
                        model_data["redirect_url"] = str(model_data["redirect_url"])

                    qr = self.qr_code_repo.create(model_data)

                    new_path_duration = time.perf_counter() - new_path_start_time
                    MetricsLogger.log_qr_generation_path("new", "create_dynamic_qr", True, new_path_duration)

                    logger.info(f"Created dynamic QR code with ID {qr.id} using new service, short_id: {short_id}")
                    MetricsLogger.log_qr_created('dynamic', True)
                    return qr

                except aiobreaker.CircuitBreakerError as e:
                    new_path_duration = time.perf_counter() - new_path_start_time
                    MetricsLogger.log_qr_generation_path("new", "create_dynamic_qr", False, new_path_duration)
                    logger.warning(f"Circuit breaker open for NewQRGenerationService: {e}")
                    MetricsLogger.log_circuit_breaker_fallback("NewQRGenerationService", "create_dynamic_qr", "circuit_open")

                except Exception as e:
                    new_path_duration = time.perf_counter() - new_path_start_time
                    MetricsLogger.log_qr_generation_path("new", "create_dynamic_qr", False, new_path_duration)
                    logger.error(f"Error with NewQRGenerationService: {e}")
                    MetricsLogger.log_circuit_breaker_fallback("NewQRGenerationService", "create_dynamic_qr", "exception")

            old_path_start_time = time.perf_counter()
            try:
                model_data = qr_data.model_dump()
                if "redirect_url" in model_data and not isinstance(model_data["redirect_url"], str):
                    model_data["redirect_url"] = str(model_data["redirect_url"])
                qr = self.qr_code_repo.create(model_data)
                old_path_duration = time.perf_counter() - old_path_start_time
                MetricsLogger.log_qr_generation_path("old", "create_dynamic_qr", True, old_path_duration)
                logger.info(f"Created dynamic QR code with ID {qr.id} using legacy service, redirect path {qr.content}, short_id: {short_id}")
            except Exception as e:
                old_path_duration = time.perf_counter() - old_path_start_time
                MetricsLogger.log_qr_generation_path("old", "create_dynamic_qr", False, old_path_duration)
                raise

            MetricsLogger.log_qr_created('dynamic', True)
            return qr
        except ValidationError as e:
            logger.error(f"Validation error creating dynamic QR code: {str(e)}")
            MetricsLogger.log_qr_created('dynamic', False)
            raise QRCodeValidationError(detail=e.errors())
        except ValueError as e:
            if "URL" in str(e): # Check if error is related to URL validation
                logger.error(f"Invalid redirect URL: {str(e)}")
                MetricsLogger.log_qr_created('dynamic', False)
                raise RedirectURLError(f"Invalid redirect URL: {str(e)}")
            logger.error(f"Validation error creating dynamic QR code: {str(e)}")
            MetricsLogger.log_qr_created('dynamic', False)
            raise QRCodeValidationError(str(e))
