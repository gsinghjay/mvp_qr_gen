"""
Tests for test data factories.

This module verifies that the test data factories correctly create test data
with appropriate defaults and customization options.
"""

import pytest
from datetime import UTC, datetime, timedelta

from app.models.qr import QRCode
from app.models.scan_log import ScanLog
from app.schemas.common import QRType
from app.tests.factories import QRCodeFactory, ScanLogFactory
from app.tests.helpers import assert_qr_code_fields, assert_scan_log_fields


class TestQRCodeFactory:
    """Tests for QRCodeFactory."""

    def test_create_static_qr(self, qr_code_factory: QRCodeFactory):
        """Test creation of a static QR code."""
        # Create a static QR code
        qr_code = qr_code_factory.create_static()
        
        # Verify it has the correct type
        assert_qr_code_fields(qr_code, {"qr_type": QRType.STATIC.value})
        assert qr_code.redirect_url is None
        
        # Verify it was added to the session
        assert qr_code in qr_code_factory.db_session

    def test_create_dynamic_qr(self, qr_code_factory: QRCodeFactory):
        """Test creation of a dynamic QR code."""
        # Create a dynamic QR code with a custom redirect URL
        custom_url = "https://example.com/custom"
        qr_code = qr_code_factory.create_dynamic(redirect_url=custom_url)
        
        # Verify it has the correct type and URL
        assert_qr_code_fields(qr_code, {
            "qr_type": QRType.DYNAMIC.value,
            "redirect_url": custom_url
        })
        
        # Verify it was added to the session
        assert qr_code in qr_code_factory.db_session

    def test_create_with_params(self, qr_code_factory: QRCodeFactory):
        """Test creation of a QR code with specific parameters."""
        # Create a QR code with custom parameters
        title = "Test QR"
        description = "A test QR code"
        qr_code = qr_code_factory.create_with_params(
            qr_type=QRType.STATIC,
            content="https://example.com/test",
            fill_color="#FF0000",
            back_color="#FFFFFF",
            scan_count=5,
            created_days_ago=10,
            title=title,
            description=description
        )
        
        # Verify custom fields
        assert_qr_code_fields(qr_code, {
            "content": "https://example.com/test",
            "qr_type": QRType.STATIC.value,
            "fill_color": "#FF0000",
            "back_color": "#FFFFFF",
            "scan_count": 5,
            "title": title,
            "description": description
        })
        
        # Verify created_at date was adjusted correctly
        created_at_expected = datetime.now(UTC) - timedelta(days=10)
        assert qr_code.created_at.date() == created_at_expected.date()
        
        # Verify it was added to the session
        assert qr_code in qr_code_factory.db_session

    def test_create_batch_mixed(self, qr_code_factory: QRCodeFactory):
        """Test creation of a batch of mixed QR codes."""
        # Create a batch of 10 QR codes, 30% static and 70% dynamic
        static_ratio = 0.3
        qr_codes = qr_code_factory.create_batch_mixed(
            count=10,
            static_ratio=static_ratio,
            max_age_days=5,
            max_scan_count=10
        )
        
        # Verify count and composition
        assert len(qr_codes) == 10
        
        static_count = sum(1 for qr in qr_codes if qr.qr_type == QRType.STATIC.value)
        dynamic_count = sum(1 for qr in qr_codes if qr.qr_type == QRType.DYNAMIC.value)
        
        # Allow for slight variation due to rounding
        assert static_count in (3, 4)  # ~30%
        assert dynamic_count in (6, 7)  # ~70%
        assert static_count + dynamic_count == 10
        
        # Verify all were added to the session
        for qr_code in qr_codes:
            assert qr_code in qr_code_factory.db_session


class TestScanLogFactory:
    """Tests for ScanLogFactory."""

    def test_create_scan_log(self, qr_code_factory: QRCodeFactory, scan_log_factory: ScanLogFactory):
        """Test creation of a scan log."""
        # First create a QR code
        qr_code = qr_code_factory.create_dynamic()
        
        # Create a scan log for this QR code
        scan_log = scan_log_factory.create_for_qr(
            qr_code=qr_code,
            is_genuine_scan=True,
            ip_address="192.168.1.1"
        )
        
        # Verify scan log properties
        assert_scan_log_fields(scan_log, {
            "qr_code_id": qr_code.id,
            "is_genuine_scan": True,
            "ip_address": "192.168.1.1"
        })
        
        # Verify it was added to the session
        assert scan_log in scan_log_factory.db_session

    def test_create_scan_log_with_device_types(self, qr_code_factory: QRCodeFactory, scan_log_factory: ScanLogFactory):
        """Test creation of scan logs with different device types."""
        # Create a QR code
        qr_code = qr_code_factory.create_dynamic()
        
        # Create mobile scan
        mobile_scan = scan_log_factory.create_for_qr(
            qr_code=qr_code,
            is_genuine_scan=True,
            is_mobile=True
        )
        
        # Verify mobile properties
        assert_scan_log_fields(mobile_scan, {
            "is_mobile": True,
            "is_tablet": False,
            "is_pc": False,
            "is_bot": False
        })
        
        # Verify a mobile device family is set
        assert mobile_scan.device_family in ["iPhone", "Samsung Galaxy", "Google Pixel"]
        
        # Create tablet scan
        tablet_scan = scan_log_factory.create_for_qr(
            qr_code=qr_code,
            is_genuine_scan=True,
            is_tablet=True
        )
        
        # Verify tablet properties
        assert_scan_log_fields(tablet_scan, {
            "is_mobile": False,
            "is_tablet": True,
            "is_pc": False,
            "is_bot": False
        })
        
        # Verify a tablet device family is set
        assert tablet_scan.device_family in ["iPad", "Samsung Tab", "Amazon Fire"]
        
        # Create PC scan
        pc_scan = scan_log_factory.create_for_qr(
            qr_code=qr_code,
            is_genuine_scan=True,
            is_pc=True
        )
        
        # Verify PC properties
        assert_scan_log_fields(pc_scan, {
            "is_mobile": False,
            "is_tablet": False,
            "is_pc": True,
            "is_bot": False
        })

    def test_create_batch_for_qr(self, qr_code_factory: QRCodeFactory, scan_log_factory: ScanLogFactory):
        """Test creation of a batch of scan logs for a QR code."""
        # Create a QR code
        qr_code = qr_code_factory.create_dynamic()
        
        # Create a batch of scan logs
        scan_logs = scan_log_factory.create_batch_for_qr(
            qr_code=qr_code,
            count=20,
            genuine_ratio=0.7,  # 70% genuine scans
            max_days_ago=10
        )
        
        # Verify count and composition
        assert len(scan_logs) == 20
        
        genuine_count = sum(1 for log in scan_logs if log.is_genuine_scan)
        non_genuine_count = sum(1 for log in scan_logs if not log.is_genuine_scan)
        
        # Allow for slight variations due to rounding
        assert genuine_count in (13, 14, 15)  # ~70%
        assert non_genuine_count in (5, 6, 7)  # ~30%
        assert genuine_count + non_genuine_count == 20
        
        # Verify device type distributions follow expected patterns
        genuine_logs = [log for log in scan_logs if log.is_genuine_scan]
        non_genuine_logs = [log for log in scan_logs if not log.is_genuine_scan]
        
        # In genuine logs, mobile should be more common
        mobile_genuine = sum(1 for log in genuine_logs if log.is_mobile)
        assert mobile_genuine > len(genuine_logs) * 0.5  # More than 50% should be mobile
        
        # In non-genuine logs, PC should be more common
        pc_non_genuine = sum(1 for log in non_genuine_logs if log.is_pc)
        assert pc_non_genuine > len(non_genuine_logs) * 0.5  # More than 50% should be PC


class TestCombinedFixtures:
    """Tests for fixtures that combine multiple factories."""

    def test_qr_with_scans_fixture(self, qr_with_scans):
        """Test the qr_with_scans fixture."""
        # Unpack the fixture
        qr_code, scan_logs = qr_with_scans
        
        # Verify structure
        assert isinstance(qr_code, QRCode)
        assert isinstance(scan_logs, list)
        assert all(isinstance(log, ScanLog) for log in scan_logs)
        
        # Verify counts
        assert len(scan_logs) == 20
        assert qr_code.scan_count == 20
        
        # Verify relationship
        assert all(log.qr_code_id == qr_code.id for log in scan_logs)
        
        # Verify scan statistics are correct
        genuine_logs = [log for log in scan_logs if log.is_genuine_scan]
        assert qr_code.genuine_scan_count == len(genuine_logs)
        
        # Verify timestamps
        if scan_logs:
            # Last scan at should match most recent scan
            all_timestamps = [log.scanned_at for log in scan_logs]
            assert qr_code.last_scan_at == max(all_timestamps)
            
            # Last genuine scan at should match most recent genuine scan
            if genuine_logs:
                genuine_timestamps = [log.scanned_at for log in genuine_logs]
                assert qr_code.last_genuine_scan_at == max(genuine_timestamps)
                
                # First genuine scan at should match earliest genuine scan
                assert qr_code.first_genuine_scan_at == min(genuine_timestamps) 