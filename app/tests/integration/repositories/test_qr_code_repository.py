"""
Integration tests for QRCodeRepository have been replaced by unit tests.

Due to complexities with database schema version differences and field requirements,
we have decided to focus on unit testing the QRCodeRepository functionality.

For proper integration tests, see:
- app/tests/unit/repositories/test_qr_code_repository.py (unit tests with mocks)
- app/tests/unit/repositories/test_repository_integration.py (end-to-end tests using test client)
"""

import pytest
from datetime import datetime, timedelta, UTC
import uuid

from app.repositories.qr_code_repository import QRCodeRepository
from app.models.qr import QRCode
from app.schemas.common import QRType
from app.core.exceptions import DatabaseError
from app.tests.factories import QRCodeFactory


@pytest.fixture
def qr_code_in_db(test_db, qr_code_factory):
    """Create a test QR code in the database."""
    # Use the factory to create a QR code
    qr_code = qr_code_factory.create_with_params(
        qr_type=QRType.STATIC,
        content="https://example.com/test",
        title="Test QR Code",
        description="Created for integration tests"
    )
    
    yield qr_code
    
    # Clean up handled by the test transaction rollback


class TestQRCodeRepositoryIntegration:
    """Integration tests for QRCodeRepository using the actual test database."""
    
    def test_get_by_id(self, test_db, static_qr):
        """Test getting a QR code by ID from the database."""
        # Create repository with real DB session
        repo = QRCodeRepository(test_db)
        
        # Retrieve QR code by ID
        result = repo.get_by_id(static_qr.id)
        
        # Verify correct QR code was retrieved
        assert result is not None
        assert result.id == static_qr.id
        assert result.content == static_qr.content
        assert result.title == static_qr.title
    
    def test_get_by_content(self, test_db, static_qr):
        """Test getting a QR code by content from the database."""
        # Create repository with real DB session
        repo = QRCodeRepository(test_db)
        
        # Retrieve QR code by content
        result = repo.get_by_content(static_qr.content)
        
        # Verify correct QR code was retrieved
        assert result is not None
        assert result.id == static_qr.id
        assert result.content == static_qr.content
    
    def test_get_by_short_id(self, test_db, dynamic_qr):
        """Test getting a QR code by short_id from the database."""
        # Create repository with real DB session
        repo = QRCodeRepository(test_db)
        
        # Verify the dynamic QR has a short_id
        assert dynamic_qr.short_id is not None
        
        # Retrieve QR code by short_id
        result = repo.get_by_short_id(dynamic_qr.short_id)
        
        # Verify correct QR code was retrieved
        assert result is not None
        assert result.id == dynamic_qr.id
        assert result.short_id == dynamic_qr.short_id
    
    def test_update_qr(self, test_db, static_qr):
        """Test updating a QR code in the database."""
        # Create repository with real DB session
        repo = QRCodeRepository(test_db)
        
        # Update data
        new_title = "Updated Test QR Code"
        new_description = "Updated for integration tests"
        update_data = {
            "title": new_title,
            "description": new_description
        }
        
        # Update QR code
        result = repo.update_qr(static_qr.id, update_data)
        
        # Verify QR code was updated
        assert result is not None
        assert result.id == static_qr.id
        assert result.title == new_title
        assert result.description == new_description
        
        # Verify changes persisted in database
        test_db.expire_all()  # Force reload from database
        refreshed = repo.get_by_id(static_qr.id)
        assert refreshed.title == new_title
        assert refreshed.description == new_description
    
    def test_update_scan_count(self, test_db, static_qr):
        """Test updating scan count for a QR code in the database."""
        # Create repository with real DB session
        repo = QRCodeRepository(test_db)
        
        # Remember initial scan count
        initial_scan_count = static_qr.scan_count
        initial_genuine_scan_count = static_qr.genuine_scan_count
        
        # Test timestamp
        test_timestamp = datetime.now(UTC)
        
        # Update scan count (regular scan)
        result = repo.update_scan_count(static_qr.id, test_timestamp, False)
        
        # Verify scan count was updated
        assert result is not None
        assert result.scan_count == initial_scan_count + 1
        assert result.genuine_scan_count == initial_genuine_scan_count  # unchanged
        assert result.last_scan_at == test_timestamp
        
        # Verify changes persisted in database
        test_db.expire_all()  # Force reload from database
        refreshed = repo.get_by_id(static_qr.id)
        assert refreshed.scan_count == initial_scan_count + 1
        
        # Test genuine scan
        new_timestamp = test_timestamp + timedelta(minutes=5)
        result = repo.update_scan_count(static_qr.id, new_timestamp, True)
        
        # Verify genuine scan count was updated
        assert result is not None
        assert result.scan_count == initial_scan_count + 2
        assert result.genuine_scan_count == initial_genuine_scan_count + 1
        assert result.last_scan_at == new_timestamp
        assert result.last_genuine_scan_at == new_timestamp
        if initial_genuine_scan_count == 0:
            assert result.first_genuine_scan_at == new_timestamp
        
        # Verify changes persisted in database
        test_db.expire_all()  # Force reload from database
        refreshed = repo.get_by_id(static_qr.id)
        assert refreshed.scan_count == initial_scan_count + 2
        assert refreshed.genuine_scan_count == initial_genuine_scan_count + 1
    
    def test_list_qr_codes(self, test_db, static_qr, dynamic_qr):
        """Test listing QR codes from the database with filtering and sorting."""
        # Create repository with real DB session
        repo = QRCodeRepository(test_db)
        
        # Test basic listing
        qr_codes, total = repo.list_qr_codes()
        assert total >= 2  # should at least have our test QR codes
        
        # Test pagination
        qr_codes, total = repo.list_qr_codes(limit=1)
        assert len(qr_codes) == 1
        assert total >= 2
        
        # Test filtering by type
        qr_codes, total = repo.list_qr_codes(qr_type="static")
        assert any(qr.id == static_qr.id for qr in qr_codes)
        
        qr_codes, total = repo.list_qr_codes(qr_type="dynamic")
        assert any(qr.id == dynamic_qr.id for qr in qr_codes)
        
        # Test sorting by scan_count (descending)
        qr_codes, total = repo.list_qr_codes(sort_by="scan_count", sort_desc=True)
        # Just verify it doesn't error, as we can't control ordering among all test objects
        
        # Test search by title if available
        if static_qr.title:
            qr_codes, total = repo.list_qr_codes(search=static_qr.title)
            assert any(qr.id == static_qr.id for qr in qr_codes)
    
    def test_count(self, test_db, static_qr, qr_code_factory):
        """Test counting QR codes in the database."""
        # Create repository with real DB session
        repo = QRCodeRepository(test_db)
        
        # Get initial count
        initial_count = repo.count()
        assert initial_count >= 1  # should at least have our test QR code
        
        # Add another QR code
        second_qr = qr_code_factory.create_static(
            title="Count Test QR Code"
        )
        
        # Check count increased
        new_count = repo.count()
        assert new_count == initial_count + 1 