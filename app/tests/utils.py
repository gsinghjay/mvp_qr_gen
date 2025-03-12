"""
Utility functions for testing the QR code generator application.

This module contains reusable testing utilities to reduce duplication across test files
and provide consistent validation patterns.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime

import json
from fastapi.testclient import TestClient
from fastapi import status

from ..models.qr import QRCode
from ..schemas.qr.models import QRType


def validate_color_code(color: str) -> bool:
    """
    Validate a color code string.
    
    Args:
        color: The color code to validate (e.g., "#FF0000")
        
    Returns:
        True if valid, raises AssertionError otherwise
    """
    assert color.startswith("#"), "Color code must start with #"
    assert len(color) in [4, 7], "Color code must be 4 or 7 characters long"
    try:
        # Remove # and try to convert to integer
        int(color[1:], 16)
        return True
    except ValueError:
        assert False, f"Invalid hex color code: {color}"


def validate_redirect_url(url: str) -> bool:
    """
    Validate a redirect URL for dynamic QR codes.
    
    Args:
        url: The URL to validate
        
    Returns:
        True if valid, raises AssertionError otherwise
    """
    assert url.startswith(("http://", "https://")), "URL must start with http:// or https://"
    # Basic URL format validation
    parts = url.split("://", 1)
    assert len(parts) == 2, "Invalid URL format"
    assert len(parts[1]) > 0, "URL must have a domain"
    return True


def validate_scan_statistics(data: Dict[str, Any]) -> bool:
    """
    Validate QR code scan statistics data.
    
    Args:
        data: The scan statistics data to validate
        
    Returns:
        True if valid, raises AssertionError otherwise
    """
    # Check required fields
    required_fields = ["scan_count", "last_scan_at"]
    for field in required_fields:
        assert field in data, f"Required field '{field}' missing from scan statistics"
    
    # Validate scan count
    assert isinstance(data["scan_count"], int), "Scan count must be an integer"
    assert data["scan_count"] >= 0, "Scan count cannot be negative"
    
    # Validate last scan timestamp if present and not null
    if data["last_scan_at"] is not None:
        try:
            datetime.fromisoformat(data["last_scan_at"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            assert False, f"Invalid last_scan_at date format: {data['last_scan_at']}"
    
    return True


def validate_qr_code_data(data: Dict[str, Any], expected: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate QR code data from API responses.
    
    Args:
        data: The QR code data to validate
        expected: Optional dictionary of expected values to check against
        
    Returns:
        True if valid, raises AssertionError otherwise
    """
    # Check required fields are present
    required_fields = ["id", "content", "qr_type", "created_at"]
    for field in required_fields:
        assert field in data, f"Required field '{field}' missing from QR code data"
    
    # Validate field types
    assert isinstance(data["id"], str), "ID should be a string"
    assert isinstance(data["content"], str), "Content should be a string"
    assert data["qr_type"] in ["static", "dynamic"], f"Invalid QR type: {data['qr_type']}"
    
    # Validate colors if present using validate_color_code
    if "fill_color" in data:
        validate_color_code(data["fill_color"])
    if "back_color" in data:
        validate_color_code(data["back_color"])
    
    # Validate scan statistics if present
    if "scan_count" in data:
        validate_scan_statistics({
            "scan_count": data["scan_count"],
            "last_scan_at": data.get("last_scan_at")
        })
    
    # Check redirect_url if QR type is dynamic using validate_redirect_url
    if data["qr_type"] == "dynamic":
        assert "redirect_url" in data, "Dynamic QR code should have redirect_url"
        validate_redirect_url(data["redirect_url"])
    
    # Validate created_at date format
    try:
        datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    except (ValueError, TypeError):
        assert False, f"Invalid created_at date format: {data['created_at']}"
    
    # Check expected values if provided
    if expected:
        for key, value in expected.items():
            assert key in data, f"Expected field '{key}' missing from QR code data"
            assert data[key] == value, f"Field '{key}' has value '{data[key]}', expected '{value}'"
    
    return True


def validate_qr_code_list_response(response_data: Dict[str, Any], expected_count: Optional[int] = None) -> bool:
    """
    Validate a QR code list response from the API.
    
    Args:
        response_data: The response data to validate
        expected_count: Optional expected number of items
        
    Returns:
        True if valid, raises AssertionError otherwise
    """
    # Check required fields
    required_fields = ["items", "total", "page", "size"]
    for field in required_fields:
        assert field in response_data, f"Required field '{field}' missing from list response"
    
    # Validate field types
    assert isinstance(response_data["items"], list), "Items should be a list"
    assert isinstance(response_data["total"], int), "Total should be an integer"
    assert isinstance(response_data["page"], int), "Page should be an integer"
    assert isinstance(response_data["size"], int), "Size should be an integer"
    
    # Validate items if present
    if response_data["items"]:
        for item in response_data["items"]:
            validate_qr_code_data(item)
    
    # Check expected count if provided
    if expected_count is not None:
        assert len(response_data["items"]) == expected_count, \
            f"Expected {expected_count} items, got {len(response_data['items'])}"
    
    # Validate pagination logic
    assert response_data["total"] >= len(response_data["items"]), \
        "Total count should be >= number of items returned"
    assert response_data["page"] >= 0, "Page should be >= 0"
    assert response_data["size"] > 0, "Size should be > 0"
    
    return True


def validate_error_response(response_data: Dict[str, Any], expected_detail: Optional[str] = None) -> bool:
    """
    Validate an error response from the API.
    
    Args:
        response_data: The error response data to validate
        expected_detail: Optional expected detail message
        
    Returns:
        True if valid, raises AssertionError otherwise
    """
    # Check required fields
    assert "detail" in response_data, "Error response should contain 'detail' field"
    
    # Check detail matches expected if provided
    if expected_detail:
        assert response_data["detail"] == expected_detail, \
            f"Expected detail '{expected_detail}', got '{response_data['detail']}'"
    
    return True


def assert_successful_response(
    response, 
    expected_status: int = status.HTTP_200_OK,
    expected_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Assert that a response was successful and optionally matches expected data.
    
    Args:
        response: The TestClient response to validate
        expected_status: Expected HTTP status code
        expected_data: Optional dictionary of expected data fields
        
    Returns:
        Response data as a dictionary
    """
    assert response.status_code == expected_status, \
        f"Expected status {expected_status}, got {response.status_code}: {response.text}"
    
    try:
        data = response.json()
    except json.JSONDecodeError:
        assert False, f"Response is not valid JSON: {response.text}"
    
    if expected_data:
        for key, value in expected_data.items():
            assert key in data, f"Expected field '{key}' missing from response"
            assert data[key] == value, f"Field '{key}' has value '{data[key]}', expected '{value}'"
    
    return data


def assert_qr_code_in_db(db_session, qr_id: str) -> QRCode:
    """
    Assert that a QR code exists in the database.
    
    Args:
        db_session: SQLAlchemy database session
        qr_id: The ID of the QR code to check
        
    Returns:
        The QR code instance if found
    """
    qr_code = db_session.query(QRCode).filter(QRCode.id == qr_id).first()
    assert qr_code is not None, f"QR code with ID {qr_id} not found in database"
    return qr_code


def assert_qr_redirects(client: TestClient, qr_path: str, expected_url: str) -> None:
    """
    Assert that a QR code correctly redirects to the expected URL.
    
    Args:
        client: TestClient instance
        qr_path: The QR code path to test (without the /r/ prefix)
        expected_url: The expected redirect URL
    """
    response = client.get(f"/r/{qr_path}", allow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT, \
        f"Expected status 307, got {response.status_code}"
    assert response.headers["location"] == expected_url, \
        f"Expected redirect to '{expected_url}', got '{response.headers.get('location')}'"


def assert_validation_error(
    response, 
    expected_status: int = status.HTTP_422_UNPROCESSABLE_ENTITY,
    field: Optional[str] = None
) -> Dict[str, Any]:
    """
    Assert that a response contains a validation error.
    
    Args:
        response: The TestClient response to validate
        expected_status: Expected HTTP status code
        field: Optional specific field that should have a validation error
        
    Returns:
        Error details as a dictionary
    """
    assert response.status_code == expected_status, \
        f"Expected status {expected_status}, got {response.status_code}"
    
    try:
        data = response.json()
    except json.JSONDecodeError:
        assert False, f"Response is not valid JSON: {response.text}"
    
    assert "detail" in data, "Error response missing 'detail' field"
    
    if field:
        errors = data.get("detail", [])
        if isinstance(errors, list):
            field_errors = [e for e in errors if e.get("loc") and field in e.get("loc")]
            assert field_errors, f"No validation errors found for field '{field}'"
        elif isinstance(errors, dict) and "loc" in errors:
            assert field in errors["loc"], f"Validation error not for field '{field}'"
    
    return data


def parameterize_test_cases(base_data: Dict[str, Any], test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate parameterized test cases by combining base data with test case variations.
    
    Args:
        base_data: Base data for all test cases
        test_cases: List of test case variations to apply
        
    Returns:
        List of complete test case data dictionaries
    """
    result = []
    for case in test_cases:
        case_data = base_data.copy()
        case_data.update(case)
        result.append(case_data)
    return result 