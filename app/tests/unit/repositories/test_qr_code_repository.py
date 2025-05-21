"""
Unit tests for the QRCodeRepository class in qr_code_repository module.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, UTC

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.qr_code_repository import QRCodeRepository
from app.models.qr import QRCode
from app.core.exceptions import DatabaseError, QRCodeNotFoundError


class TestQRCodeRepository:
    """Tests for the QRCodeRepository class."""

    def test_get_by_id(self):
        """Test getting a QR code by ID."""
        # Create a mock db session
        mock_db = Mock(spec=Session)
        
        # Create a mock QR code object
        mock_qr = Mock(spec=QRCode)
        mock_qr.id = "test-id"
        
        # Configure the mock session query 
        mock_query = Mock()
        mock_filter = Mock()
        mock_first = Mock(return_value=mock_qr)
        
        mock_filter.first = mock_first
        mock_query.filter = Mock(return_value=mock_filter)
        mock_db.query = Mock(return_value=mock_query)
        
        # Create repository with mock session
        repo = QRCodeRepository(mock_db)
        
        # Call the method
        result = repo.get_by_id("test-id")
        
        # Verify the result
        assert result == mock_qr
        mock_db.query.assert_called_once_with(QRCode)
        mock_query.filter.assert_called_once()

    def test_get_by_id_not_found(self):
        """Test getting a QR code by ID when not found."""
        # Create a mock db session
        mock_db = Mock(spec=Session)
        
        # Configure the mock session query to return None
        mock_query = Mock()
        mock_filter = Mock()
        mock_first = Mock(return_value=None)
        
        mock_filter.first = mock_first
        mock_query.filter = Mock(return_value=mock_filter)
        mock_db.query = Mock(return_value=mock_query)
        
        # Create repository with mock session
        repo = QRCodeRepository(mock_db)
        
        # Call the method
        result = repo.get_by_id("test-id")
        
        # Verify the result
        assert result is None
        mock_db.query.assert_called_once_with(QRCode)
        mock_query.filter.assert_called_once()

    def test_get_by_id_database_error(self):
        """Test database error handling when getting a QR code by ID."""
        # Create a mock db session
        mock_db = Mock(spec=Session)
        
        # Configure the mock session query to raise an exception
        mock_db.query = Mock(side_effect=SQLAlchemyError("Test error"))
        
        # Create repository with mock session
        repo = QRCodeRepository(mock_db)
        
        # Call the method and verify it raises the expected exception
        with pytest.raises(DatabaseError):
            repo.get_by_id("test-id")

    def test_get_by_content(self):
        """Test getting a QR code by content."""
        # Create a mock db session
        mock_db = Mock(spec=Session)
        
        # Create a mock QR code object
        mock_qr = Mock(spec=QRCode)
        mock_qr.content = "test-content"
        
        # Configure the mock session query
        mock_query = Mock()
        mock_filter = Mock()
        mock_first = Mock(return_value=mock_qr)
        
        mock_filter.first = mock_first
        mock_query.filter = Mock(return_value=mock_filter)
        mock_db.query = Mock(return_value=mock_query)
        
        # Create repository with mock session
        repo = QRCodeRepository(mock_db)
        
        # Call the method
        result = repo.get_by_content("test-content")
        
        # Verify the result
        assert result == mock_qr
        mock_db.query.assert_called_once_with(QRCode)
        mock_query.filter.assert_called_once()

    def test_update_scan_count(self):
        """Test updating scan count for a QR code."""
        # Create a mock db session
        mock_db = Mock(spec=Session)
        
        # Create a properly configured QRCode mock
        mock_qr = Mock()
        mock_qr.id = "test-id"
        mock_qr.scan_count = 5
        mock_qr.genuine_scan_count = 2
        mock_qr.first_genuine_scan_at = None
        
        # Set up patch for the get_by_id method
        with patch.object(QRCodeRepository, 'get_by_id', return_value=mock_qr) as mock_get_by_id:
            # Create repository instance
            repo = QRCodeRepository(mock_db)
            
            # Set timestamp for testing
            timestamp = datetime.now(UTC)
            
            # Test regular scan update
            result = repo.update_scan_count("test-id", timestamp, False)
            
            # Verify get_by_id was called
            mock_get_by_id.assert_called_once_with("test-id")
            
            # Verify updates were made
            assert mock_qr.scan_count == 6  # Incremented
            assert mock_qr.last_scan_at == timestamp
            assert mock_qr.genuine_scan_count == 2  # Unchanged
            
            # Verify db operations
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_qr)
            
            # Verify result
            assert result == mock_qr

    def test_update_scan_count_genuine(self):
        """Test updating scan count for a genuine scan."""
        # Create a mock db session
        mock_db = Mock(spec=Session)
        
        # Create a properly configured QRCode mock
        mock_qr = Mock()
        mock_qr.id = "test-id"
        mock_qr.scan_count = 5
        mock_qr.genuine_scan_count = 2
        mock_qr.first_genuine_scan_at = None
        
        # Set up patch for the get_by_id method
        with patch.object(QRCodeRepository, 'get_by_id', return_value=mock_qr) as mock_get_by_id:
            # Create repository instance
            repo = QRCodeRepository(mock_db)
            
            # Set timestamp for testing
            timestamp = datetime.now(UTC)
            
            # Test genuine scan update
            result = repo.update_scan_count("test-id", timestamp, True)
            
            # Verify get_by_id was called
            mock_get_by_id.assert_called_once_with("test-id")
            
            # Verify updates were made
            assert mock_qr.scan_count == 6  # Incremented
            assert mock_qr.genuine_scan_count == 3  # Incremented
            assert mock_qr.last_scan_at == timestamp
            assert mock_qr.last_genuine_scan_at == timestamp
            assert mock_qr.first_genuine_scan_at == timestamp  # First genuine scan
            
            # Verify db operations
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_qr)
            
            # Verify result
            assert result == mock_qr

    def test_update_scan_count_qr_not_found(self):
        """Test updating scan count for a non-existent QR code."""
        # Create a mock db session
        mock_db = Mock(spec=Session)
        
        # Set up patch for the get_by_id method to return None
        with patch.object(QRCodeRepository, 'get_by_id', return_value=None) as mock_get_by_id:
            # Create repository instance
            repo = QRCodeRepository(mock_db)
            
            # Test update with non-existent QR code
            result = repo.update_scan_count("test-id", datetime.now(UTC), False)
            
            # Verify get_by_id was called
            mock_get_by_id.assert_called_once_with("test-id")
            
            # Verify result
            assert result is None
            
            # Verify no db operations
            mock_db.commit.assert_not_called()
            mock_db.refresh.assert_not_called()

    def test_update_scan_count_database_error(self):
        """Test database error handling when updating scan count."""
        # Create a mock db session
        mock_db = Mock(spec=Session)
        
        # Configure db to raise error on commit
        mock_db.commit = Mock(side_effect=SQLAlchemyError("Test error"))
        
        # Create a properly configured QRCode mock
        mock_qr = Mock()
        mock_qr.id = "test-id"
        mock_qr.scan_count = 5
        
        # Set up patch for the get_by_id method
        with patch.object(QRCodeRepository, 'get_by_id', return_value=mock_qr) as mock_get_by_id:
            # Create repository instance
            repo = QRCodeRepository(mock_db)
            
            # Test exception handling
            with pytest.raises(DatabaseError):
                repo.update_scan_count("test-id", datetime.now(UTC), False)
                
            # Verify rollback was called
            mock_db.rollback.assert_called_once() 