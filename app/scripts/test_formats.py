#!/usr/bin/env python
"""
Test script to verify format handling in NewQRGenerationService.

This script directly tests the format handling in NewQRGenerationService
by generating QR codes in different formats and verifying the output.
"""

import asyncio
import logging
import sys
from io import BytesIO
from pathlib import Path

import segno
from PIL import Image

from app.adapters.segno_qr_adapter import SegnoQRCodeGenerator, PillowQRImageFormatter
from app.schemas.common import ErrorCorrectionLevel
from app.schemas.qr.parameters import QRImageParameters
from app.services.new_qr_generation_service import NewQRGenerationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("test_formats")

# Test parameters
TEST_CONTENT = "https://example.com/test"
OUTPUT_DIR = Path("/tmp/qr_test_formats")
OUTPUT_DIR.mkdir(exist_ok=True)

async def test_format(service, format_name, error_level=ErrorCorrectionLevel.M):
    """Test a specific format."""
    logger.info(f"Testing format: {format_name}")
    
    # Create image parameters
    params = QRImageParameters(
        size=10,
        border=4,
        fill_color="#000000",
        back_color="#FFFFFF",
        error_level=error_level,
        image_format=format_name
    )
    
    try:
        # Generate QR code
        image_bytes = await service.create_and_format_qr(
            content=TEST_CONTENT,
            image_params=params,
            output_format=format_name
        )
        
        # Save the output for manual inspection
        output_path = OUTPUT_DIR / f"test_qr_{format_name}.{format_name}"
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        
        # Check file signature to determine actual format
        format_detected = detect_format(image_bytes)
        logger.info(f"Format requested: {format_name}, detected: {format_detected}")
        
        if format_name == format_detected:
            logger.info(f"✅ {format_name.upper()} test PASSED")
            return True
        else:
            logger.error(f"❌ {format_name.upper()} test FAILED - got {format_detected} instead")
            return False
            
    except Exception as e:
        logger.error(f"Error testing {format_name}: {e}")
        return False

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
        with Image.open(BytesIO(image_bytes)) as img:
            return img.format.lower()
    except:
        pass
    
    return "unknown"

async def run_tests():
    """Run all format tests."""
    # Create service components
    generator = SegnoQRCodeGenerator()
    formatter = PillowQRImageFormatter()
    service = NewQRGenerationService(generator=generator, formatter=formatter)
    
    logger.info("Starting QR code format tests")
    
    # Test each format
    formats = ["png", "svg", "jpeg", "webp"]
    results = {}
    
    for fmt in formats:
        results[fmt] = await test_format(service, fmt)
    
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
    asyncio.run(run_tests()) 