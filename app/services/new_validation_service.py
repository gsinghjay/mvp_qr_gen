"""
New Validation Service Implementation.

This module provides the new validation service implementation using
interfaces in the Observatory-First refactoring architecture.
"""

import logging
from typing import Any, Dict, List

from app.core.metrics_logger import MetricsLogger
from app.services.interfaces.validation_interfaces import ValidationProvider

logger = logging.getLogger(__name__)


class NewValidationService:
    """
    New validation service using interface-based architecture.
    
    This service orchestrates validation operations using
    injected validation provider implementations.
    """

    def __init__(self, provider: ValidationProvider):
        """
        Initialize the service with validation provider dependency.
        
        Args:
            provider: Validation provider implementation
        """
        self.provider = provider
        logger.info("NewValidationService initialized")

    @MetricsLogger.time_service_call("NewValidationService", "perform_url_validation")
    async def perform_url_validation(self, url: str) -> bool:
        """
        Validate a redirect URL for safety and allowlist compliance.
        
        Args:
            url: The URL to validate
            
        Returns:
            True if URL is valid and allowed
            
        Raises:
            ValidationError: If URL is malformed or invalid
        """
        try:
            logger.debug(f"Validating URL: {url}")
            
            # Use provider to validate
            is_valid = await self.provider.validate_redirect_url(url)
            
            logger.info(f"URL validation result for {url}: {is_valid}")
            return is_valid
            
        except Exception as e:
            logger.error(f"URL validation failed for {url}: {e}")
            raise

    @MetricsLogger.time_service_call("NewValidationService", "validate_qr_params")
    async def validate_qr_params(self, params: Any) -> List[str]:
        """
        Validate QR code creation parameters.
        
        Args:
            params: QR creation parameters to validate
            
        Returns:
            List of error messages (empty if all valid)
            
        Raises:
            ValidationError: If params structure is invalid
        """
        try:
            logger.debug("Validating QR creation parameters")
            
            # Use provider to validate
            errors = await self.provider.validate_qr_creation_params(params)
            
            if errors:
                logger.warning(f"QR parameter validation found {len(errors)} errors")
            else:
                logger.info("QR parameter validation successful")
                
            return errors
            
        except Exception as e:
            logger.error(f"QR parameter validation failed: {e}")
            raise

    @MetricsLogger.time_service_call("NewValidationService", "validate_batch_urls")
    async def validate_batch_urls(self, urls: List[str]) -> Dict[str, bool]:
        """
        Validate multiple URLs in batch.
        
        Args:
            urls: List of URLs to validate
            
        Returns:
            Dictionary mapping each URL to its validation result
            
        Raises:
            ValidationError: If batch validation fails
        """
        try:
            logger.debug(f"Validating batch of {len(urls)} URLs")
            
            results = {}
            for url in urls:
                try:
                    results[url] = await self.provider.validate_redirect_url(url)
                except Exception as e:
                    logger.warning(f"Failed to validate URL {url}: {e}")
                    results[url] = False
                    
            valid_count = sum(1 for is_valid in results.values() if is_valid)
            logger.info(f"Batch validation complete: {valid_count}/{len(urls)} URLs valid")
            
            return results
            
        except Exception as e:
            logger.error(f"Batch URL validation failed: {e}")
            raise

    @MetricsLogger.time_service_call("NewValidationService", "pre_validation_check")
    async def pre_validation_check(self, data: Dict[str, Any]) -> bool:
        """
        Perform pre-validation checks on input data.
        
        Args:
            data: Data to perform pre-validation on
            
        Returns:
            True if data passes pre-validation
            
        Raises:
            ValueError: If data fails pre-validation
        """
        try:
            logger.debug("Performing pre-validation checks")
            
            # Basic structural validation
            if not isinstance(data, dict):
                raise ValueError("Data must be a dictionary")
                
            # Check for required fields (example validation)
            if "content" in data and not data["content"]:
                raise ValueError("Content cannot be empty")
                
            if "url" in data and not isinstance(data["url"], str):
                raise ValueError("URL must be a string")
                
            logger.debug("Pre-validation checks passed")
            return True
            
        except Exception as e:
            logger.error(f"Pre-validation check failed: {e}")
            raise 