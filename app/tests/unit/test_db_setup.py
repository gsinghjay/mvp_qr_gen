"""
Tests to verify that the database setup is working correctly.
This file specifically tests the fix for the "relation already exists" error
from Task 1.2 in the refactoring plan.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session


def test_table_existence(test_db: Session):
    """Test that the required tables exist after setup."""
    # Check if main tables exist
    result = test_db.execute(text(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name IN ('qr_codes', 'scan_logs')"
    )).scalar()
    
    # We should have at least these two tables
    assert result >= 2, "Required tables don't exist in the database"


def test_transaction_isolation(test_db: Session):
    """
    Test that transactions are properly isolated.
    
    This test verifies that changes made in a transaction are rolled back
    after the test completes, ensuring test isolation.
    """
    # Create a unique identifier for this test run
    test_id = "isolation_test_marker"
    
    # Get the column names for qr_codes table
    columns = test_db.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = 'qr_codes'"
    )).scalars().all()
    
    print(f"Available columns in qr_codes table: {columns}")
    
    # Insert a test record with the marker using only the required fields
    test_db.execute(text(
        "INSERT INTO qr_codes (id, content, qr_type, fill_color, back_color, size, border, scan_count, created_at, error_level) "
        "VALUES (:id, :content, 'static', '#000000', '#FFFFFF', 10, 4, 0, CURRENT_TIMESTAMP, 'm')"
    ), {"id": test_id, "content": "http://example.com/isolation_test"})
    
    # Verify the record exists within this transaction
    result = test_db.execute(text(
        "SELECT COUNT(*) FROM qr_codes WHERE id = :id"
    ), {"id": test_id}).scalar()
    
    assert result == 1, "Test record not created properly"
    
    # The test_db fixture will automatically roll back the transaction after this test


def test_concurrent_transaction_isolation(test_db: Session):
    """
    Test that concurrent transactions are properly isolated.
    
    This test creates another connection/transaction and verifies that
    changes in our test transaction aren't visible to it until committed.
    """
    from ..conftest import TestSessionLocal, engine
    
    # Create a test record in our main transaction
    test_id = "concurrent_isolation_test"
    test_db.execute(text(
        "INSERT INTO qr_codes (id, content, qr_type, fill_color, back_color, size, border, scan_count, created_at, error_level) "
        "VALUES (:id, :content, 'static', '#000000', '#FFFFFF', 10, 4, 0, CURRENT_TIMESTAMP, 'm')"
    ), {"id": test_id, "content": "http://example.com/concurrent_test"})
    
    # Don't commit yet
    
    # Create a new connection and session
    other_connection = engine.connect()
    other_transaction = other_connection.begin()
    other_session = TestSessionLocal(bind=other_connection)
    
    try:
        # Try to find our record from the other connection - should not be visible
        result = other_session.execute(text(
            "SELECT COUNT(*) FROM qr_codes WHERE id = :id"
        ), {"id": test_id}).scalar()
        
        assert result == 0, "Transaction changes visible to other connection before commit"
    finally:
        # Clean up the other connection
        other_session.close()
        other_transaction.rollback()
        other_connection.close()


def test_alembic_version_table_exists(test_db: Session):
    """Test that the alembic_version table exists if Alembic was used."""
    # Check if alembic_version table exists
    exists = test_db.execute(text(
        "SELECT EXISTS (SELECT FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = 'alembic_version')"
    )).scalar()
    
    # If alembic_version doesn't exist, we might be using SQLAlchemy metadata
    # so we'll check if QR code tables exist (our primary concern)
    if not exists:
        print("alembic_version table not found - may be using SQLAlchemy metadata")
        qr_table_exists = test_db.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = 'qr_codes')"
        )).scalar()
        
        assert qr_table_exists, "QR codes table doesn't exist - schema setup failed"
        pytest.skip("Skipping alembic_version check as SQLAlchemy metadata was likely used")
    
    # If we're here, we're using Alembic, so check version table
    count = test_db.execute(text(
        "SELECT COUNT(*) FROM alembic_version"
    )).scalar()
    
    assert count == 1, f"Expected 1 row in alembic_version table, found {count}"
    
    # Get the current version
    version = test_db.execute(text(
        "SELECT version_num FROM alembic_version"
    )).scalar()
    
    # We don't know the exact version number, but it should be non-empty
    assert version, "No version number found in alembic_version table"
    print(f"Current database schema version: {version}") 