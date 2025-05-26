#!/usr/bin/env python
"""
Script to create 4 new QR codes in different formats (PNG, SVG, JPEG, WebP) and verify them.
"""

import logging
import sys
import httpx
import json
import time
from pathlib import Path
from io import BytesIO
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("create_verify_formats")

# Test parameters
OUTPUT_DIR = Path("/tmp/qr_test_new_formats")
OUTPUT_DIR.mkdir(exist_ok=True)

# API configuration
API_URL = "https://10.1.6.12"
AUTH = ("admin_user", "strongpassword")

def detect_format(image_bytes):
    """Detect the actual format of the image bytes."""
    # Check first few bytes for signatures
    if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        return "png"
    elif image_bytes[:2] == b'\xff\xd8':
        return "jpeg"
    elif b'<svg' in image_bytes[:100]:
        return "svg"
    elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
        return "webp"
    
    # Try using PIL
    try:
        from PIL import Image
        with Image.open(BytesIO(image_bytes)) as img:
            return img.format.lower()
    except:
        pass
    
    return "unknown"

def create_static_qr(format_name: str) -> Dict[str, Any]:
    """Create a static QR code with a unique content for each format."""
    timestamp = int(time.time())
    data = {
        "title": f"Test QR in {format_name.upper()} format",
        "description": f"Created by create_verify_formats.py at {timestamp}",
        "content": f"https://example.com/test/{format_name}/{timestamp}",
        "fill_color": "#000000",
        "back_color": "#FFFFFF",
        "size": 10,
        "border": 4,
        "error_level": "m"
    }
    
    logger.info(f"Creating static QR code for {format_name} format...")
    
    try:
        with httpx.Client(auth=AUTH, verify=False) as client:
            response = client.post(
                f"{API_URL}/api/v1/qr/static",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
        if response.status_code == 201:
            qr_data = response.json()
            logger.info(f"✅ QR code created successfully with ID: {qr_data['id']}")
            return qr_data
        else:
            logger.error(f"Failed to create QR code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error creating QR code: {e}")
        return None

def get_qr_image(qr_id: str, format_name: str) -> bytes:
    """Get a QR code image in the specified format."""
    logger.info(f"Getting QR image in {format_name} format...")
    
    try:
        with httpx.Client(auth=AUTH, verify=False) as client:
            response = client.get(
                f"{API_URL}/api/v1/qr/{qr_id}/image?format={format_name}",
                headers={"Accept": f"image/{format_name}"}
            )
            
        if response.status_code == 200:
            logger.info(f"✅ QR image retrieved successfully")
            return response.content
        else:
            logger.error(f"Failed to get QR image: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting QR image: {e}")
        return None

def verify_format(image_bytes: bytes, expected_format: str) -> bool:
    """Verify that the image is in the expected format."""
    if image_bytes is None:
        return False
        
    actual_format = detect_format(image_bytes)
    
    if actual_format == expected_format:
        logger.info(f"✅ Format verification PASSED: Expected {expected_format}, got {actual_format}")
        return True
    else:
        logger.error(f"❌ Format verification FAILED: Expected {expected_format}, got {actual_format}")
        return False

def delete_qr(qr_id: str) -> bool:
    """Delete a QR code."""
    logger.info(f"Deleting QR code {qr_id}...")
    
    try:
        with httpx.Client(auth=AUTH, verify=False) as client:
            response = client.delete(
                f"{API_URL}/api/v1/qr/{qr_id}"
            )
            
        if response.status_code == 204:
            logger.info(f"✅ QR code deleted successfully")
            return True
        else:
            logger.error(f"Failed to delete QR code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error deleting QR code: {e}")
        return False

def test_format(format_name: str) -> bool:
    """Create a QR code, get it in the specified format, verify, and clean up."""
    logger.info(f"\n=== Testing {format_name.upper()} Format ===")
    
    # Create a QR code
    qr_data = create_static_qr(format_name)
    if not qr_data:
        return False
    
    qr_id = qr_data["id"]
    
    # Get the QR image in the specified format
    image_bytes = get_qr_image(qr_id, format_name)
    if not image_bytes:
        delete_qr(qr_id)
        return False
    
    # Save the image for inspection
    output_path = OUTPUT_DIR / f"new_qr_{format_name}.{format_name}"
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    
    # Verify the format
    result = verify_format(image_bytes, format_name)
    
    # Clean up
    delete_qr(qr_id)
    
    return result

def main():
    """Create and verify QR codes in different formats."""
    logger.info("Starting QR code format creation and verification")
    
    # Test each format
    formats = ["png", "svg", "jpeg", "webp"]
    results = {}
    
    for fmt in formats:
        results[fmt] = test_format(fmt)
    
    # Print summary
    logger.info("\n----- TEST SUMMARY -----")
    for fmt, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{fmt.upper()}: {status}")
    
    # Overall result
    if all(results.values()):
        logger.info("ALL TESTS PASSED")
    else:
        logger.error("SOME TESTS FAILED")
    
    logger.info(f"Output files saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main() 