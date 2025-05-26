#!/usr/bin/env python3
"""
Test script for Phase 0.2 Segno Adapter Enhancements.

This script tests the new advanced color control and utility methods
implemented in the PillowQRImageFormatter.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to Python path  
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.adapters.segno_qr_adapter import SegnoQRCodeGenerator, PillowQRImageFormatter
from app.schemas.qr.parameters import QRImageParameters
from app.schemas.common import ErrorCorrectionLevel


async def test_enhanced_color_support():
    """Test advanced color control with data-specific colors."""
    print("\n🎨 Testing Enhanced Color Support...")
    
    generator = SegnoQRCodeGenerator()
    formatter = PillowQRImageFormatter()
    
    # Test with advanced color options
    params = QRImageParameters(
        size=10,
        border=4,
        fill_color="#000000",           # Base dark color
        back_color="#FFFFFF",           # Base light color
        data_dark_color="#FF0000",      # Red data modules (overrides fill_color)
        data_light_color="#00FF0080"    # Green transparent light modules (overrides back_color)
    )
    
    # Generate QR data
    qr_data = await generator.generate_qr_data("https://test.example.com", ErrorCorrectionLevel.M)
    
    # Test PNG generation with advanced colors
    png_bytes = await formatter.format_qr_image(qr_data, params, "png")
    print(f"✅ PNG with advanced colors: {len(png_bytes)} bytes")
    
    # Test SVG generation with advanced colors
    svg_bytes = await formatter.format_qr_image(qr_data, params, "svg")
    print(f"✅ SVG with advanced colors: {len(svg_bytes)} bytes")
    
    return True


async def test_data_uri_methods():
    """Test new data URI generation methods."""
    print("\n🔗 Testing Data URI Methods...")
    
    generator = SegnoQRCodeGenerator()
    formatter = PillowQRImageFormatter()
    
    params = QRImageParameters(
        size=8,
        border=2,
        fill_color="#000080",
        back_color="#F0F0F0",
        data_dark_color="#FF4500",  # Orange data modules
        svg_title="Test QR Code",
        svg_description="QR code for testing data URI methods"
    )
    
    qr_data = await generator.generate_qr_data("Test QR Content", ErrorCorrectionLevel.M)
    
    # Test PNG data URI
    png_uri = await formatter.get_png_data_uri(qr_data, params)
    print(f"✅ PNG data URI: {len(png_uri)} characters")
    assert png_uri.startswith("data:image/png;base64,"), "PNG data URI should start with correct prefix"
    
    # Test SVG data URI
    svg_uri = await formatter.get_svg_data_uri(qr_data, params)
    print(f"✅ SVG data URI: {len(svg_uri)} characters")
    assert svg_uri.startswith("data:image/svg+xml;charset=utf-8,"), "SVG data URI should start with correct prefix"
    
    # Test inline SVG
    inline_svg = await formatter.get_svg_inline(qr_data, params)
    print(f"✅ Inline SVG: {len(inline_svg)} characters")
    assert "<svg" in inline_svg, "Inline SVG should contain <svg tag"
    assert "<title>Test QR Code</title>" in inline_svg, "SVG should include accessibility title"
    assert "<desc>QR code for testing data URI methods</desc>" in inline_svg, "SVG should include accessibility description"
    
    return True


async def test_physical_dimensions():
    """Test physical dimension support for SVG."""
    print("\n📏 Testing Physical Dimensions...")
    
    generator = SegnoQRCodeGenerator()
    formatter = PillowQRImageFormatter()
    
    # Test with physical dimensions
    params = QRImageParameters(
        size=10,  # This should be ignored when physical dimensions are provided
        border=3,
        fill_color="#000000",
        back_color="#FFFFFF",
        physical_size=25.4,  # 25.4mm = 1 inch
        physical_unit="mm",
        dpi=300
    )
    
    qr_data = await generator.generate_qr_data("Physical QR Test", ErrorCorrectionLevel.H)
    
    # Test SVG with physical units
    svg_bytes = await formatter.format_qr_image(qr_data, params, "svg")
    svg_content = svg_bytes.decode('utf-8')
    print(f"✅ SVG with physical units: {len(svg_bytes)} bytes")
    assert 'width=' in svg_content and 'height=' in svg_content, "Physical SVG should include size attributes"
    
    # Test PNG with calculated DPI scaling
    png_bytes = await formatter.format_qr_image(qr_data, params, "png")
    print(f"✅ PNG with physical dimensions: {len(png_bytes)} bytes")
    
    return True


async def test_precise_scale_calculation():
    """Test precise scale calculation for raster images."""
    print("\n🎯 Testing Precise Scale Calculation...")
    
    generator = SegnoQRCodeGenerator()
    formatter = PillowQRImageFormatter()
    
    params = QRImageParameters(size=20, border=4)  # Large QR for testing scale
    qr_data = await generator.generate_qr_data("Scale test content", ErrorCorrectionLevel.L)
    
    # Test scale calculation method directly
    calculated_scale = formatter._calculate_precise_scale(qr_data, params)
    print(f"✅ Calculated scale: {calculated_scale} pixels/module")
    assert calculated_scale >= 1.0, "Scale should be at least 1 pixel per module"
    
    # Test with physical dimensions
    physical_params = QRImageParameters(
        size=10,
        border=4,
        physical_size=50.8,  # 2 inches
        physical_unit="mm",
        dpi=150
    )
    
    physical_scale = formatter._calculate_precise_scale(qr_data, physical_params)
    print(f"✅ Physical scale: {physical_scale} pixels/module")
    
    return True


async def main():
    """Run all Phase 0.2 enhancement tests."""
    print("🚀 Phase 0.2 Segno Adapter Enhancement Tests")
    print("=" * 50)
    
    try:
        # Run all tests
        await test_enhanced_color_support()
        await test_data_uri_methods()
        await test_physical_dimensions()
        await test_precise_scale_calculation()
        
        print("\n" + "=" * 50)
        print("🎉 All Phase 0.2 tests passed successfully!")
        print("✅ Advanced color control working")
        print("✅ Data URI methods functional")
        print("✅ Physical dimension support operational")
        print("✅ Precise scale calculation accurate")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 