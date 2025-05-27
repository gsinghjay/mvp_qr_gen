#!/usr/bin/env python3

import asyncio
import base64
import logging
import os
import sys
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Tuple
from xml.etree import ElementTree as ET

# Add project root to sys.path to import app modules
# This assumes the script is run from the project root or a similar context
# where 'app' is discoverable. If run from within 'app/scripts', adjust accordingly.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent # Assumes app/scripts/test_...py
sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image

# Import necessary components from your application
# These imports assume the script is run in an environment where 'app' is in PYTHONPATH
try:
    from app.core.config import settings
    from app.adapters.segno_qr_adapter import SegnoQRCodeGenerator, PillowQRImageFormatter
    from app.services.new_qr_generation_service import NewQRGenerationService
    from app.schemas.qr.parameters import QRImageParameters
    from app.schemas.common import ErrorCorrectionLevel, ImageFormat
except ImportError as e:
    print(f"Error importing application modules: {e}")
    print("Please ensure this script is run from the project root or "
          "that 'app' is in your PYTHONPATH.")
    sys.exit(1)


# --- Configuration ---
OUTPUT_DIR = Path("test_advanced_qr_images")
OUTPUT_DIR.mkdir(exist_ok=True)

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Test Helper Functions ---

def print_section(title: str):
    logger.info(f"\n{'='*10} {title.upper()} {'='*10}")

def assert_condition(condition: bool, success_msg: str, failure_msg: str):
    if condition:
        logger.info(f"✅ PASS: {success_msg}")
    else:
        logger.error(f"❌ FAIL: {failure_msg}")
        raise AssertionError(failure_msg)

async def generate_and_save_qr(
    service: NewQRGenerationService,
    content: str,
    image_params_dict: Dict[str, Any],
    output_format_str: str,
    filename_suffix: str,
    error_correction: ErrorCorrectionLevel = ErrorCorrectionLevel.M
) -> Tuple[Path, QRImageParameters]:
    """Generates QR, saves it, and returns the path and params used."""
    print_section(f"Testing: {filename_suffix} ({output_format_str})")
    
    # Create Pydantic model from dict for validation and type safety
    try:
        image_params = QRImageParameters(**image_params_dict)
        logger.info(f"  Using parameters: {image_params.model_dump_json(indent=2)}")
    except Exception as e:
        logger.error(f"  Parameter validation failed for {filename_suffix}: {e}")
        raise

    output_filename = f"qr_{filename_suffix}.{output_format_str}"
    output_path = OUTPUT_DIR / output_filename

    try:
        image_bytes = await service.create_and_format_qr(
            content=content,
            image_params=image_params, # Pass the Pydantic model instance
            output_format=output_format_str,
            error_correction=error_correction
        )
        assert_condition(len(image_bytes) > 0, f"{output_filename} generated with non-zero size.",
                         f"{output_filename} generated empty.")

        with open(output_path, "wb") as f:
            f.write(image_bytes)
        logger.info(f"  Saved to: {output_path}")
        return output_path, image_params
    except Exception as e:
        logger.error(f"  Error generating {output_filename}: {e}")
        raise
    finally:
        print("-" * 30) # Separator after each test case block

def validate_image_properties(image_path: Path, expected_format: str, expected_size_px: Tuple[int, int] | None = None):
    try:
        img = Image.open(image_path)
        assert_condition(img.format.lower() == expected_format.lower(),
                         f"{image_path.name} format is {img.format} (expected {expected_format}).",
                         f"{image_path.name} format is {img.format}, expected {expected_format}.")
        
        if expected_size_px:
            # Allow for variations due to discrete QR module calculations and scale rounding
            tolerance = max(10, int(expected_size_px[0] * 0.1))  # 10% tolerance, minimum 10 pixels
            width_match = abs(img.width - expected_size_px[0]) <= tolerance
            height_match = abs(img.height - expected_size_px[1]) <= tolerance
            assert_condition(width_match and height_match,
                             f"{image_path.name} size is {img.size} (expected close to {expected_size_px}).",
                             f"{image_path.name} size is {img.size}, expected close to {expected_size_px}.")
        logger.info(f"  Image properties: Mode={img.mode}, Size={img.size}")

    except Exception as e:
        logger.error(f"  Error validating image {image_path.name}: {e}")
        raise

def validate_svg_content(svg_path: Path, checks: Dict[str, str | bool]):
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        if "title_text" in checks:
            title_el = root.find(".//{http://www.w3.org/2000/svg}title") # SVG namespace
            title_el_no_ns = root.find(".//title") # Some generators might omit namespace
            
            actual_title = title_el.text if title_el is not None else (title_el_no_ns.text if title_el_no_ns is not None else None)
            assert_condition(actual_title == checks["title_text"],
                             f"SVG title is '{actual_title}' (expected '{checks['title_text']}').",
                             f"SVG title is '{actual_title}', expected '{checks['title_text']}'.")

        if "desc_text" in checks:
            desc_el = root.find(".//{http://www.w3.org/2000/svg}desc")
            desc_el_no_ns = root.find(".//desc")
            actual_desc = desc_el.text if desc_el is not None else (desc_el_no_ns.text if desc_el_no_ns is not None else None)

            assert_condition(actual_desc == checks["desc_text"],
                             f"SVG description is '{actual_desc}' (expected '{checks['desc_text']}').",
                             f"SVG description is '{actual_desc}', expected '{checks['desc_text']}'.")

        if "width_attr" in checks:
            assert_condition(root.get("width") == checks["width_attr"],
                             f"SVG width attribute is '{root.get('width')}' (expected '{checks['width_attr']}').",
                             f"SVG width attribute is '{root.get('width')}', expected '{checks['width_attr']}'.")
        
        if "height_attr" in checks:
            assert_condition(root.get("height") == checks["height_attr"],
                             f"SVG height attribute is '{root.get('height')}' (expected '{checks['height_attr']}').",
                             f"SVG height attribute is '{root.get('height')}', expected '{checks['height_attr']}'.")
        
        if "dark_fill" in checks:
            # This is a simplified check; real SVGs from Segno have a single path.
            # We'd need to parse the 'd' attribute or check stroke/fill of that path.
            # For now, let's check if the color appears in the SVG string.
            with open(svg_path, "r") as f:
                svg_string = f.read()
            expected_fill = checks["dark_fill"].lower()  # Make case-insensitive
            # Segno might use "stroke" for path, or "fill" if it's complex.
            # Check if the color appears anywhere in the SVG (case-insensitive)
            found = expected_fill in svg_string.lower()
            assert_condition(found,
                             f"SVG dark fill color '{expected_fill}' seems to be present.",
                             f"SVG dark fill color '{expected_fill}' not found directly. Manual verification of path style needed.")

        if "has_no_xmldecl" in checks and checks["has_no_xmldecl"]:
            with open(svg_path, "r") as f:
                svg_string = f.read()
            assert_condition(not svg_string.strip().startswith("<?xml"),
                             "SVG does not have XML declaration as expected.",
                             "SVG has XML declaration, but was not expected.")

    except ET.ParseError as e:
        logger.error(f"  Error parsing SVG {svg_path.name}: {e}")
        raise
    except Exception as e:
        logger.error(f"  Error validating SVG {svg_path.name}: {e}")
        raise


# --- Test Cases ---

async def test_all_features(service: NewQRGenerationService):
    test_content = "Hello, New QR Service! Testing 123..."
    base_params = {"size": 8, "border": 2, "fill_color": "#1A2B3C", "back_color": "#F0E0D0"}

    # 1. Advanced Color Control
    params_adv_color_png = {**base_params, "data_dark_color": "#FF4500", "data_light_color": "#E0FFFF"}
    png_adv_color, _ = await generate_and_save_qr(service, test_content, params_adv_color_png, "png", "adv_color_png")
    validate_image_properties(png_adv_color, "PNG") # Visual inspection needed for exact colors

    params_adv_color_svg = {**base_params, "data_dark_color": "#483D8B", "data_light_color": "#EEE8AA"}
    svg_adv_color, _ = await generate_and_save_qr(service, test_content, params_adv_color_svg, "svg", "adv_color_svg")
    validate_svg_content(svg_adv_color, {"dark_fill": "#483D8B"}) # Checks if data_dark_color is used as primary stroke/fill

    # 2. Logo Embedding
    params_logo = {**base_params, "include_logo": True}
    # When include_logo is true, error_level is forced to 'h' by the service/adapter logic
    png_logo, _ = await generate_and_save_qr(service, test_content, params_logo, "png", "logo_png", error_correction=ErrorCorrectionLevel.H)
    validate_image_properties(png_logo, "PNG") # Visual inspection for logo

    jpeg_logo, _ = await generate_and_save_qr(service, test_content, params_logo, "jpeg", "logo_jpeg", error_correction=ErrorCorrectionLevel.H)
    validate_image_properties(jpeg_logo, "JPEG")

    # 3. SVG Accessibility
    params_svg_acc = {**base_params, "svg_title": "Test SVG QR", "svg_description": "Accessible QR code."}
    svg_acc, _ = await generate_and_save_qr(service, test_content, params_svg_acc, "svg", "accessible_svg")
    validate_svg_content(svg_acc, {"title_text": "Test SVG QR", "desc_text": "Accessible QR code."})

    # 4. Physical Dimensions
    # SVG with physical units
    params_phys_svg = {**base_params, "physical_size": 2.5, "physical_unit": "in", "dpi": 300}
    svg_phys, _ = await generate_and_save_qr(service, test_content, params_phys_svg, "svg", "physical_svg")
    validate_svg_content(svg_phys, {"width_attr": "2.5in", "height_attr": "2.5in"})

    # PNG with physical units (influences scale, target pixels are calculated)
    # 2in * 150dpi = 300px. The `size` parameter in image_params will be overridden by this.
    params_phys_png = {"border": 2, "fill_color": "#000000", "back_color": "#FFFFFF", 
                       "physical_size": 2, "physical_unit": "in", "dpi": 150}
    png_phys, used_params_phys_png = await generate_and_save_qr(service, test_content, params_phys_png, "png", "physical_png")
    # The adapter's _calculate_precise_scale will determine module count and derive a scale for Segno.
    # Then Pillow resizes to target_pixels. For 2in @ 150dpi, target is 300x300px.
    # The size parameter in QRImageParameters for this call is based on the _calculate_precise_scale.
    # The final output from Pillow should be close to 300x300.
    validate_image_properties(png_phys, "PNG", expected_size_px=(300, 300))

    # PNG with relative pixel size (size=12 -> 12*25 = 300px target for Pillow stage)
    params_pixel_png = {"size": 12, "border": 1, "fill_color": "#111111", "back_color": "#EEEEEE"}
    png_pixel, _ = await generate_and_save_qr(service, test_content, params_pixel_png, "png", "pixel_png")
    # Adapter logic: size * 25 is target for Pillow. 12 * 25 = 300px.
    validate_image_properties(png_pixel, "PNG", expected_size_px=(300, 300))

    # 5. Error Correction for Logo
    # Adapter logic should force 'h' if logo is true, regardless of 'error_level' in params
    params_logo_err_m = {"size": 8, "border": 4, "include_logo": True, "error_level": ErrorCorrectionLevel.M}
    png_logo_err_m, _ = await generate_and_save_qr(service, test_content, params_logo_err_m, "png", "logo_error_m_becomes_h")
    validate_image_properties(png_logo_err_m, "PNG") # Expect 'h' to be used by Segno
    logger.info("  (Manually verify this QR is scannable, implying 'h' was used for logo)")

    # 7. Test Segno SVG optimizations (omitsize, no xmldecl, no ns)
    # PillowQRImageFormatter by default applies these: xmldecl=False, svgns=False, omitsize=True (if no physical units)
    params_svg_optimized = {"size": 10, "border": 1} # no physical units, so omitsize=True should apply
    svg_opt, _ = await generate_and_save_qr(service, test_content, params_svg_optimized, "svg", "optimized_svg")
    validate_svg_content(svg_opt, {"has_no_xmldecl": True})
    svg_opt_content = svg_opt.read_text()
    assert_condition("xmlns=" not in svg_opt_content, "SVG does not have xmlns namespace.", "SVG has xmlns namespace.")
    # Note: We now keep width/height attributes for better browser compatibility
    # instead of using omitsize=True which can cause display issues
    assert_condition('width=' in svg_opt_content and 'height=' in svg_opt_content,
                     "SVG has width/height attributes for better browser compatibility.",
                     "SVG missing width/height attributes - may cause display issues.")


    # 8. Data URI generation
    print_section("Data URI Generation")
    png_data_uri = await service.formatter.get_png_data_uri(
        await service.generator.generate_qr_data(test_content, ErrorCorrectionLevel.M),
        QRImageParameters(**base_params)
    )
    assert_condition(png_data_uri.startswith("data:image/png;base64,"), "PNG Data URI generated.", "PNG Data URI generation failed.")
    logger.info(f"  PNG Data URI (first 100 chars): {png_data_uri[:100]}...")

    svg_data_uri = await service.formatter.get_svg_data_uri(
        await service.generator.generate_qr_data(test_content, ErrorCorrectionLevel.M),
        QRImageParameters(**params_svg_acc) # Use params with title/desc
    )
    # Segno uses UTF-8 encoding for SVG data URIs, not base64
    assert_condition(svg_data_uri.startswith("data:image/svg+xml;charset=utf-8,"), "SVG Data URI generated.", "SVG Data URI generation failed.")
    logger.info(f"  SVG Data URI (first 100 chars): {svg_data_uri[:100]}...")
    # Verify title in SVG Data URI
    import urllib.parse
    decoded_svg_uri_content = urllib.parse.unquote(svg_data_uri.split(",", 1)[1])
    assert_condition("<title>Test SVG QR</title>" in decoded_svg_uri_content,
                     "SVG Data URI contains the correct title.",
                     "SVG Data URI does not contain the correct title.")


    # 9. Inline SVG generation
    print_section("Inline SVG Generation")
    inline_svg_str = await service.formatter.get_svg_inline(
        await service.generator.generate_qr_data(test_content, ErrorCorrectionLevel.M),
        QRImageParameters(**params_svg_acc) # Use params with title/desc
    )
    assert_condition(inline_svg_str.startswith("<svg") and inline_svg_str.endswith("</svg>"),
                     "Inline SVG string generated.", "Inline SVG string generation failed.")
    assert_condition("<title>Test SVG QR</title>" in inline_svg_str,
                     "Inline SVG contains the correct title.",
                     "Inline SVG does not contain the correct title.")
    logger.info(f"  Inline SVG (first 100 chars): {inline_svg_str[:100]}...")

    logger.info("All advanced feature tests completed.")


async def main():
    # Instantiate services directly
    # This assumes the script can resolve these dependencies.
    # In a full test suite, you might use FastAPI's TestClient or dependency overrides.
    segno_generator = SegnoQRCodeGenerator()
    pillow_formatter = PillowQRImageFormatter()
    new_qr_service = NewQRGenerationService(generator=segno_generator, formatter=pillow_formatter)

    logger.info(f"Using settings: DEFAULT_LOGO_PATH={settings.DEFAULT_LOGO_PATH}")
    assert_condition(settings.DEFAULT_LOGO_PATH.exists(),
                     "Default logo path exists.",
                     f"Default logo path {settings.DEFAULT_LOGO_PATH} does not exist!")

    await test_all_features(new_qr_service)

    logger.info(f"\n🎉 All Python-based tests for NewQRGenerationService PASSED! 🎉")
    logger.info(f"Generated images are in: {OUTPUT_DIR.resolve()}")

if __name__ == "__main__":
    asyncio.run(main())