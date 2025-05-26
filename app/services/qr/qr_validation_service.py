"""
QR code validation service for validating QR codes and redirect URLs.
"""

import logging
from typing import Optional
from urllib.parse import urlparse

from ...core.config import settings
from ...core.exceptions import QRCodeValidationError, RedirectURLError
from ...core.metrics_logger import MetricsLogger
from ...schemas.common import QRType
from ...schemas.qr.models import QRCodeCreate

# Configure logger
logger = logging.getLogger(__name__)

class QRValidationService:
    """Service class for QR code validation operations."""

    def __init__(self):
        """Initialize the QR validation service."""
        pass

    @MetricsLogger.time_service_call("QRValidationService", "is_safe_redirect_url")
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
            for allowed_domain in settings.ALLOWED_REDIRECT_DOMAINS:
                allowed_domain = allowed_domain.lower()
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

    @MetricsLogger.time_service_call("QRValidationService", "validate_qr_code")
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