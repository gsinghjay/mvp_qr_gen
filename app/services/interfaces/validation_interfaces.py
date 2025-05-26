"""
Validation Interface Definitions.

This module defines abstract base classes for validation services
to establish clear contracts for future implementations in the Observatory-First architecture.
"""

from abc import ABC, abstractmethod
from typing import Any, List


class ValidationProvider(ABC):
    """
    Abstract base class for validation services.
    
    This interface defines the contract for validating various inputs
    such as redirect URLs and QR creation parameters.
    """

    @abstractmethod
    async def validate_redirect_url(self, url: str) -> bool:
        """
        Validate if a redirect URL is allowed and safe.
        
        Args:
            url: The URL to validate
            
        Returns:
            True if URL is valid and allowed, False otherwise
            
        Raises:
            ValidationError: If URL format is malformed beyond simple validation
        """
        pass

    @abstractmethod
    async def validate_qr_creation_params(self, params: Any) -> List[str]:
        """
        Validate QR code creation parameters.
        
        Args:
            params: QR creation parameters to validate (e.g., Pydantic model)
            
        Returns:
            List of error messages. Empty list if all parameters are valid.
            
        Raises:
            ValidationError: If params structure is fundamentally invalid
        """
        pass 