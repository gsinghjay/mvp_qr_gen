"""
Test the refactored models and schemas.
"""

from app.models.qr import QRCode
from app.schemas.common import ImageFormat, QRType
from app.schemas.qr.models import QRCodeCreate


def test_qr_code_model():
    """Test QR code model initialization."""
    qr = QRCode(
        content="https://example.com",
        qr_type="dynamic",
        redirect_url="https://example.com",
        fill_color="#000000",
        back_color="#FFFFFF",
        size=10,
        border=4,
    )

    assert qr.content == "https://example.com"
    assert qr.qr_type == "dynamic"
    assert qr.redirect_url == "https://example.com"
    assert qr.fill_color == "#000000"
    assert qr.back_color == "#FFFFFF"
    assert qr.size == 10
    assert qr.border == 4
    assert qr.scan_count == 0
    assert qr.created_at.tzinfo is not None  # Ensure timezone awareness


def test_qr_code_schema():
    """Test QR code schema validation."""
    # Test valid data
    data = {
        "content": "https://example.com",
        "qr_type": QRType.DYNAMIC,
        "redirect_url": "https://example.com",
        "fill_color": "#000000",
        "back_color": "#FFFFFF",
        "size": 10,
        "border": 4,
    }

    qr_create = QRCodeCreate(**data)
    assert qr_create.content == "https://example.com"
    assert qr_create.qr_type == QRType.DYNAMIC
    assert str(qr_create.redirect_url) == "https://example.com/"

    # Test enum values
    assert QRType.STATIC == "static"
    assert QRType.DYNAMIC == "dynamic"
    assert ImageFormat.PNG == "png"
    assert ImageFormat.SVG == "svg"
