"""
Unit tests for QRAnalyticsService.
"""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from app.services.qr_analytics_service import QRAnalyticsService
from app.repositories.qr_code_repository import QRCodeRepository
from app.repositories.scan_log_repository import ScanLogRepository
from app.models.qr import QRCode # For type hinting and creating test objects
from app.models.scan_log import ScanLog # For type hinting and creating test objects
from app.schemas.common import QRType


class TestQRAnalyticsService(unittest.TestCase):

    def setUp(self):
        self.mock_qr_code_repo = MagicMock(spec=QRCodeRepository)
        self.mock_scan_log_repo = MagicMock(spec=ScanLogRepository)
        self.service = QRAnalyticsService(
            qr_code_repo=self.mock_qr_code_repo,
            scan_log_repo=self.mock_scan_log_repo
        )

    def test_parse_user_agent_data_known_agents(self):
        # Desktop Chrome
        ua_desktop_chrome = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        parsed_desktop = self.service._parse_user_agent_data(ua_desktop_chrome)
        self.assertEqual(parsed_desktop["device_family"], "Other") # user_agents lib often gives 'Other' for generic PC
        self.assertEqual(parsed_desktop["os_family"], "Windows")
        self.assertEqual(parsed_desktop["os_version"], "10")
        self.assertEqual(parsed_desktop["browser_family"], "Chrome")
        self.assertEqual(parsed_desktop["browser_version"], "91.0.4472")
        self.assertFalse(parsed_desktop["is_mobile"])
        self.assertFalse(parsed_desktop["is_tablet"])
        self.assertTrue(parsed_desktop["is_pc"])
        self.assertFalse(parsed_desktop["is_bot"])

        # iPhone Safari
        ua_iphone_safari = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        parsed_iphone = self.service._parse_user_agent_data(ua_iphone_safari)
        self.assertEqual(parsed_iphone["device_family"], "iPhone")
        self.assertEqual(parsed_iphone["os_family"], "iOS")
        self.assertEqual(parsed_iphone["browser_family"], "Mobile Safari")
        self.assertTrue(parsed_iphone["is_mobile"])
        self.assertFalse(parsed_iphone["is_tablet"])
        self.assertFalse(parsed_iphone["is_pc"])

        # Android Chrome
        ua_android_chrome = "Mozilla/5.0 (Linux; Android 11; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
        parsed_android = self.service._parse_user_agent_data(ua_android_chrome)
        self.assertEqual(parsed_android["device_family"], "Samsung SM-G975F")
        self.assertEqual(parsed_android["os_family"], "Android")
        self.assertEqual(parsed_android["browser_family"], "Chrome Mobile")
        self.assertTrue(parsed_android["is_mobile"])

        # Google Bot
        ua_google_bot = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        parsed_bot = self.service._parse_user_agent_data(ua_google_bot)
        self.assertEqual(parsed_bot["device_family"], "Spider")
        self.assertEqual(parsed_bot["browser_family"], "Googlebot")
        self.assertTrue(parsed_bot["is_bot"])


    def test_parse_user_agent_data_empty_or_none(self):
        parsed_none = self.service._parse_user_agent_data(None)
        self.assertEqual(parsed_none["device_family"], "Unknown")
        self.assertTrue(parsed_none["is_pc"]) # Default

        parsed_empty = self.service._parse_user_agent_data("")
        self.assertEqual(parsed_empty["device_family"], "Unknown")
        self.assertTrue(parsed_empty["is_pc"])

    def test_record_scan_event(self):
        qr_id = "test_qr_id"
        timestamp = datetime.utcnow()
        client_ip = "123.123.123.123"
        user_agent = "TestAgent/1.0"
        is_genuine = True

        # Mock the return value of _parse_user_agent_data
        parsed_ua_mock = {"device_family": "TestDevice"}
        with patch.object(self.service, '_parse_user_agent_data', return_value=parsed_ua_mock) as mock_parse_ua:
            # Mock the return of qr_code_repo.update_scan_count
            mock_updated_qr = MagicMock(spec=QRCode)
            self.mock_qr_code_repo.update_scan_count.return_value = mock_updated_qr

            self.service.record_scan_event(qr_id, timestamp, client_ip, user_agent, is_genuine)

            mock_parse_ua.assert_called_once_with(user_agent)
            self.mock_qr_code_repo.update_scan_count.assert_called_once_with(qr_id, timestamp, is_genuine)
            self.mock_scan_log_repo.create_scan_log.assert_called_once_with(
                qr_id=qr_id,
                timestamp=timestamp,
                ip_address=client_ip,
                raw_user_agent=user_agent,
                parsed_ua_data=parsed_ua_mock,
                is_genuine_scan_signal=is_genuine
            )

    def test_record_scan_event_repo_failure(self):
        # Test that an exception in repo call is logged but doesn't crash the method (as per original logic)
        self.mock_qr_code_repo.update_scan_count.side_effect = Exception("DB boom")
        with patch.object(self.service, '_parse_user_agent_data', return_value={}) as mock_parse_ua:
            with self.assertLogs(logger='app.services.qr_analytics_service', level='ERROR') as cm:
                self.service.record_scan_event("id", datetime.utcnow(), "ip", "ua", False)
                self.assertTrue(any("Error recording scan event" in log_msg for log_msg in cm.output))
            # Scan log should not be called if update_scan_count fails and raises
            # However, the current implementation logs and swallows the exception.
            # If we want to ensure create_scan_log is not called, we'd need to check for that.
            # Based on current code, create_scan_log would still be called if update_scan_count doesn't raise.
            # If it *does* raise, then create_scan_log won't be hit.
            # The test above assumes update_scan_count fails by raising an exception.
            self.mock_scan_log_repo.create_scan_log.assert_not_called()


    def test_update_qr_scan_count_stats(self):
        qr_id = "another_qr_id"
        now = datetime.utcnow()
        self.service.update_qr_scan_count_stats(qr_id, now, is_genuine_scan_signal=True)
        self.mock_qr_code_repo.update_scan_count.assert_called_once_with(qr_id, now, True)

    def test_get_dashboard_summary(self):
        self.mock_qr_code_repo.count.return_value = 120
        mock_recent_qrs = [MagicMock(spec=QRCode) for _ in range(3)]
        self.mock_qr_code_repo.list_qr_codes.return_value = (mock_recent_qrs, 120)

        summary = self.service.get_dashboard_summary()

        self.assertEqual(summary["total_qr_codes"], 120)
        self.assertEqual(summary["recent_qr_codes"], mock_recent_qrs)
        self.mock_qr_code_repo.count.assert_called_once()
        self.mock_qr_code_repo.list_qr_codes.assert_called_once_with(
            skip=0, limit=5, sort_by="created_at", sort_desc=True
        )

    def test_get_detailed_scan_analytics(self):
        qr_id = "detail_id"
        now = datetime.utcnow()
        mock_qr = QRCode(
            id=qr_id, content="test", qr_type=QRType.STATIC.value,
            created_at=now - timedelta(days=10),
            scan_count=10, genuine_scan_count=5,
            last_scan_at=now - timedelta(days=1),
            last_genuine_scan_at=now - timedelta(hours=5)
        )
        self.mock_qr_code_repo.get_by_id.return_value = mock_qr

        mock_scan_logs = [MagicMock(spec=ScanLog) for _ in range(5)]
        self.mock_scan_log_repo.get_scan_logs_for_qr.return_value = (mock_scan_logs, 5)
        self.mock_scan_log_repo.get_device_statistics.return_value = {"PC": 5}
        self.mock_scan_log_repo.get_browser_statistics.return_value = {"Chrome": 5}
        self.mock_scan_log_repo.get_os_statistics.return_value = {"Windows": 5}

        # Mock _get_scan_timeseries_data
        mock_timeseries = {"dates": ["2023-01-01"], "counts": [5]}
        with patch.object(self.service, '_get_scan_timeseries_data', return_value=mock_timeseries) as mock_get_ts:
            analytics = self.service.get_detailed_scan_analytics(qr_id)

            self.assertEqual(analytics["qr"], mock_qr.to_dict())
            self.assertEqual(analytics["genuine_scan_pct"], 50) # 5/10 * 100
            self.assertEqual(analytics["total_logs"], 5)
            self.assertEqual(len(analytics["scan_logs"]), 5)
            self.assertEqual(analytics["device_stats"], {"PC": 5})
            self.assertEqual(analytics["time_series_data"], mock_timeseries)
            mock_get_ts.assert_called_once_with(qr_id)

    def test_get_detailed_scan_analytics_qr_not_found(self):
        self.mock_qr_code_repo.get_by_id.return_value = None
        from app.core.exceptions import QRCodeNotFoundError # Import here to avoid circularity if service raises it
        with self.assertRaises(QRCodeNotFoundError):
            self.service.get_detailed_scan_analytics("non_existent_id")


    def test_get_scan_timeseries_data(self):
        qr_id = "ts_id"
        expected_data = {"dates": ["2023-01-01", "2023-01-02"], "counts": [10, 12]}
        self.mock_scan_log_repo.get_scan_timeseries.return_value = expected_data

        timeseries = self.service._get_scan_timeseries_data(qr_id) # Test private method directly

        self.assertEqual(timeseries, expected_data)
        self.mock_scan_log_repo.get_scan_timeseries.assert_called_once_with(qr_id, time_range="last7days")

if __name__ == '__main__':
    unittest.main()
