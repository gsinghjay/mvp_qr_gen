"""
Test helper functions for the QR code generator API.

This module provides reusable helper functions for common test operations,
particularly focusing on response validation against Pydantic models.
"""

import json
import logging
from typing import Any, Dict, List, Type, TypeVar, Union, Optional, Callable

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.qr import QRCode

# Type variable for Pydantic models
ModelType = TypeVar("ModelType", bound=BaseModel)

# Configure logger
logger = logging.getLogger(__name__)


def validate_response_model(
    response_data: Union[Dict[str, Any], List[Dict[str, Any]]],
    model_class: Type[ModelType],
    is_list: bool = False,
) -> bool:
    """
    Validate that a response matches a Pydantic model structure.

    Args:
        response_data: The response data to validate, either a dict or list of dicts
        model_class: The Pydantic model class to validate against
        is_list: If True, validates response_data as a list of model instances

    Returns:
        bool: True if validation succeeds, raises ValueError otherwise

    Raises:
        ValueError: If the response data doesn't match the model structure
    """
    try:
        if is_list:
            # For list responses, validate each item
            if not isinstance(response_data, list):
                raise ValueError(f"Expected a list of items but got {type(response_data)}")
            
            for item in response_data:
                # This will raise ValidationError if invalid
                model_instance = model_class.model_validate(item)
        else:
            # For single item responses
            model_instance = model_class.model_validate(response_data)
            
        return True
    except Exception as e:
        logger.error(f"Response validation failed: {str(e)}")
        logger.debug(f"Failed data: {json.dumps(response_data, default=str)}")
        logger.debug(f"Expected model: {model_class.__name__}")
        raise ValueError(f"Response does not match {model_class.__name__} schema: {str(e)}")


def validate_list_response(
    response_data: Dict[str, Any],
    item_model_class: Type[ModelType],
    list_model_class: Type[ModelType],
    item_key: str = "items",
) -> bool:
    """
    Validate a paginated list response against both the list model and item model.

    Args:
        response_data: The response data to validate (must be a dict with items key)
        item_model_class: The Pydantic model class for list items
        list_model_class: The Pydantic model class for the list container
        item_key: The key in the response that contains the list of items

    Returns:
        bool: True if validation succeeds, raises ValueError otherwise

    Raises:
        ValueError: If the list response doesn't match the expected structure
    """
    # First validate the overall structure
    validate_response_model(response_data, list_model_class)
    
    # Then validate each item in the list
    if item_key not in response_data:
        raise ValueError(f"List response missing '{item_key}' key")
    
    items = response_data[item_key]
    if not isinstance(items, list):
        raise ValueError(f"Expected list for '{item_key}' but got {type(items)}")
    
    for item in items:
        validate_response_model(item, item_model_class)
    
    return True


def assert_error_response(response_data: Dict[str, Any], expected_detail: str = None) -> bool:
    """
    Validate that a response is a properly formatted error response.

    Args:
        response_data: The error response data to validate
        expected_detail: If provided, also checks that the detail message matches

    Returns:
        bool: True if validation succeeds, raises AssertionError otherwise
    """
    assert "detail" in response_data, "Error response missing 'detail' field"
    
    if expected_detail:
        assert response_data["detail"] == expected_detail, (
            f"Error detail mismatch. Expected: '{expected_detail}', Got: '{response_data['detail']}'"
        )
    
    return True


def assert_qr_code_fields(qr_code: Union[QRCode, Dict[str, Any]], expected_values: Dict[str, Any]) -> bool:
    """
    Validate that a QR code (model or dict) has the expected field values.
    
    Args:
        qr_code: QR code instance or dictionary with QR code data
        expected_values: Dictionary mapping field names to expected values
        
    Returns:
        bool: True if validation succeeds, raises AssertionError otherwise
        
    Raises:
        AssertionError: If any field value doesn't match the expected value
    """
    # Convert QRCode instance to dict if needed
    qr_data = qr_code
    if isinstance(qr_code, QRCode):
        # Convert to dict for consistent access
        qr_data = {
            "id": str(qr_code.id),
            "content": qr_code.content,
            "qr_type": qr_code.qr_type,
            "redirect_url": qr_code.redirect_url,
            "fill_color": qr_code.fill_color,
            "back_color": qr_code.back_color,
            "scan_count": qr_code.scan_count,
            "created_at": qr_code.created_at,
            "last_scan_at": qr_code.last_scan_at,
        }
    
    # Check each expected field
    for field, expected_value in expected_values.items():
        assert field in qr_data, f"QR code missing field: {field}"
        assert qr_data[field] == expected_value, (
            f"QR code field '{field}' mismatch. Expected: '{expected_value}', Got: '{qr_data[field]}'"
        )
    
    return True


def assert_http_exception(
    exc_info: Any, expected_status_code: int = None, expected_detail_substring: str = None
) -> bool:
    """
    Validate that an HTTPException has the expected status code and detail.
    
    Args:
        exc_info: Exception info object from pytest.raises
        expected_status_code: If provided, checks that the status code matches
        expected_detail_substring: If provided, checks that the detail contains this substring
        
    Returns:
        bool: True if validation succeeds, raises AssertionError otherwise
    """
    assert isinstance(exc_info.value, HTTPException), (
        f"Expected HTTPException but got {type(exc_info.value)}"
    )
    
    if expected_status_code is not None:
        assert exc_info.value.status_code == expected_status_code, (
            f"HTTP status code mismatch. Expected: {expected_status_code}, Got: {exc_info.value.status_code}"
        )
    
    if expected_detail_substring is not None:
        assert expected_detail_substring in exc_info.value.detail, (
            f"HTTP detail mismatch. Expected substring: '{expected_detail_substring}', Got: '{exc_info.value.detail}'"
        )
    
    return True


def assert_qr_in_database(db: Session, qr_id: str, expected_values: Dict[str, Any] = None) -> bool:
    """
    Validate that a QR code exists in the database and optionally has expected values.
    
    Args:
        db: SQLAlchemy session
        qr_id: ID of the QR code to check
        expected_values: Optional dictionary mapping field names to expected values
        
    Returns:
        bool: True if validation succeeds, raises AssertionError otherwise
        
    Raises:
        AssertionError: If the QR code doesn't exist or has unexpected field values
    """
    # Query for the QR code
    qr_code = db.scalar(select(QRCode).where(QRCode.id == qr_id))
    
    assert qr_code is not None, f"QR code with id '{qr_id}' not found in database"
    
    # Check expected values if provided
    if expected_values:
        return assert_qr_code_fields(qr_code, expected_values)
    
    return True


class DependencyOverrideManager:
    """
    Helper class for managing FastAPI dependency overrides consistently.
    
    This class provides a context manager for temporarily overriding
    dependencies in FastAPI applications during tests.
    """
    
    def __init__(self, app: FastAPI):
        """
        Initialize with a FastAPI application instance.
        
        Args:
            app: The FastAPI application instance
        """
        self.app = app
        self.original_overrides = {}
        self.overrides = {}
    
    def override(self, dependency: Callable, override_with: Callable) -> None:
        """
        Override a dependency with a test implementation.
        
        Args:
            dependency: The original dependency function to override
            override_with: The function to use instead during tests
                           This can be a regular function or a generator function
        """
        # Check if the override is a generator function (for FastAPI dependencies)
        # FastAPI dependencies are typically generator functions that yield a value
        self.overrides[dependency] = override_with
    
    def __enter__(self):
        """Apply all registered overrides when entering the context."""
        # Store original overrides before applying new ones
        for dependency, override_with in self.overrides.items():
            self.original_overrides[dependency] = self.app.dependency_overrides.get(dependency)
            self.app.dependency_overrides[dependency] = override_with
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore original dependencies when exiting the context."""
        self.restore()
        return False  # Don't suppress exceptions
    
    def restore(self) -> None:
        """Restore original dependencies."""
        for dependency, original in self.original_overrides.items():
            if original is None:
                # If there was no original override, remove our override
                self.app.dependency_overrides.pop(dependency, None)
            else:
                # Restore the original override
                self.app.dependency_overrides[dependency] = original
                
        # Clear the stored overrides
        self.original_overrides = {}

    @classmethod
    def create_db_override(cls, app: FastAPI, db_session: Session) -> 'DependencyOverrideManager':
        """
        Create a dependency manager with database overrides.
        
        This convenience method creates a manager with overrides for both
        the database session and QRCodeService dependencies, using the
        provided database session.
        
        Args:
            app: The FastAPI application instance
            db_session: SQLAlchemy session to use for tests
            
        Returns:
            A configured DependencyOverrideManager instance
        """
        from ..database import get_db, get_db_with_logging
        from ..dependencies import get_qr_service
        from ..services.qr_service import QRCodeService
        
        manager = cls(app)
        
        # Define the DB session provider
        def override_db():
            """Override the database session with the test session."""
            try:
                yield db_session
            finally:
                # Don't close the session here as it's managed by the test fixtures
                pass
        
        # Define the QR service provider using the test session
        def override_qr_service():
            """Override the QR service with one using the test session."""
            yield QRCodeService(db_session)
        
        # Register both overrides
        manager.override(get_db, override_db)
        manager.override(get_db_with_logging, override_db)
        manager.override(get_qr_service, override_qr_service)
        
        return manager 