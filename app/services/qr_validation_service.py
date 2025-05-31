"""
Service for validating QR code data and redirect URLs.
"""
import logging
from urllib.parse import urlparse

from ..core.config import settings
from ..core.exceptions import QRCodeValidationError, RedirectURLError
from ..schemas.common import QRType
from ..schemas.qr.models import QRCodeCreate

logger = logging.getLogger(__name__)

class QRValidationService:
    """Service class for QR code validation operations."""

    def is_safe_redirect_url(self, url: str) -> bool:
        """
        Validate if a redirect URL is safe based on scheme and domain allowlist.

        Args:
            url: The URL to validate

        Returns:
            bool: True if the URL is safe, False otherwise
        """
        try:
            parsed_url = urlparse(url)

            # Check if scheme is http or https
            if parsed_url.scheme not in ("http", "https"):
                logger.warning(f"Unsafe URL scheme: {parsed_url.scheme}")
                return False

            # Get the domain (netloc)
            domain = parsed_url.netloc.lower()
            if not domain:
                logger.warning("URL has no domain")
                return False

            # Check against allowed domains (exact match or subdomain)
            if not settings.ALLOWED_REDIRECT_DOMAINS:
                logger.warning("No allowed redirect domains configured. Denying all redirects for safety.")
                return False

            for allowed_domain_setting in settings.ALLOWED_REDIRECT_DOMAINS:
                allowed_domain = allowed_domain_setting.lower()
                # Exact match
                if domain == allowed_domain:
                    return True
                # Subdomain match (domain ends with .allowed_domain)
                if domain.endswith(f".{allowed_domain}"):
                    return True

            logger.warning(f"Domain not in allowlist: {domain}")
            return False

        except Exception as e:
            logger.error(f"Error parsing URL {url}: {str(e)}")
            return False

    def validate_qr_creation_data(self, qr_data: QRCodeCreate) -> None:
        """
        Validate QR code creation data.

        Args:
            qr_data: The QR code data to validate

        Raises:
            QRCodeValidationError: If the QR code data is invalid
            RedirectURLError: If the redirect URL is invalid (for dynamic QRs)
        """
        # Check for required content in static QR codes
        if qr_data.qr_type == QRType.STATIC and not qr_data.content:
            raise QRCodeValidationError("Static QR codes must have content")

        # Check for required redirect_url in dynamic QR codes
        if qr_data.qr_type == QRType.DYNAMIC:
            if not qr_data.redirect_url:
                raise RedirectURLError("Dynamic QR codes must have a redirect URL")
            # The actual safety check of redirect_url should be done by the caller
            # using is_safe_redirect_url before calling this method,
            # or this method could also call it if it had access to the original parameters.
            # For now, we assume the redirect_url in QRCodeCreate is the one to be used.

        # Color format validation is handled by Pydantic schemas by the time
        # QRCodeCreate is instantiated. Additional business rule validations can go here.
        # For example, ensuring size and border are within reasonable limits if not
        # strictly enforced by the schema.

        if not (0 < qr_data.size <= settings.MAX_QR_SIZE):
             raise QRCodeValidationError(f"QR code size must be between 1 and {settings.MAX_QR_SIZE}.")

        if not (0 <= qr_data.border <= settings.MAX_QR_BORDER):
            raise QRCodeValidationError(f"QR code border must be between 0 and {settings.MAX_QR_BORDER}.")

        logger.debug(f"QR creation data validated for content: {qr_data.content[:50]}...")
