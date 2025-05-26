#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.adapters.segno_qr_adapter import SegnoQRCodeGenerator, PillowQRImageFormatter
from app.schemas.qr.parameters import QRImageParameters
from app.schemas.common import ErrorCorrectionLevel

async def debug_svg():
    generator = SegnoQRCodeGenerator()
    formatter = PillowQRImageFormatter()
    params = QRImageParameters(
        size=8, border=2, fill_color='#000080', back_color='#F0F0F0',
        data_dark_color='#FF4500', svg_title='Test QR Code',
        svg_description='QR code for testing data URI methods'
    )
    qr_data = await generator.generate_qr_data('Test QR Content', ErrorCorrectionLevel.M)
    inline_svg = await formatter.get_svg_inline(qr_data, params)
    print('SVG output:')
    print(inline_svg[:500])

asyncio.run(debug_svg()) 