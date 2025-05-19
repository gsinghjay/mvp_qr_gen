"""
Tests to verify that the test database connection works correctly.
"""

import pytest
from sqlalchemy import text

from app.database import get_database_url, is_testing_mode


def test_testing_mode():
    """Test that the application is in testing mode."""
    assert is_testing_mode() is True


def test_database_url():
    """Test that the test database URL is correctly configured."""
    db_url = get_database_url()
    assert db_url is not None
    assert "test" in db_url.lower()
    assert "postgres" in db_url.lower()


def test_database_connection(test_db):
    """Test that the connection to the test database works."""
    # Execute a simple query
    result = test_db.execute(text("SELECT 1")).scalar()
    assert result == 1


def test_create_table(test_db, test_engine):
    """Test creating and querying a table in the test database."""
    # Create a temporary test table
    test_db.execute(text("""
        CREATE TABLE IF NOT EXISTS test_table (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL
        )
    """))
    test_db.commit()
    
    # Insert a record
    test_db.execute(text("""
        INSERT INTO test_table (name) VALUES ('test_record')
    """))
    test_db.commit()
    
    # Query the record
    result = test_db.execute(text("SELECT name FROM test_table")).scalar()
    assert result == 'test_record'
    
    # Clean up - drop the table
    test_db.execute(text("DROP TABLE test_table"))
    test_db.commit()


@pytest.mark.xfail(reason="Testing if pytest runner is working properly")
def test_intentional_failure():
    """A test that's marked to fail to check if the test runner is working."""
    assert False 