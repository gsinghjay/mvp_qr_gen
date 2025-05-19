"""
Tests for the test factory implementation.

These tests ensure that our test factories work correctly and can be used
in other tests to generate test data consistently.
"""

import pytest
from sqlalchemy.orm import Session

from ..models.qr import QRCode
from ..schemas.common import QRType
from .factories import Factory, QRCodeFactory


class TestBaseFactory:
    """Tests for the base Factory class."""

    def test_factory_requires_model_class(self):
        """Test that a factory must have a model_class attribute."""

        # Create a subclass without setting model_class
        class BadFactory(Factory):
            pass

        # Should raise AttributeError when used
        with pytest.raises(AttributeError):
            BadFactory().build()

    def test_build_method_creates_instance(self):
        """Test that build() creates an instance but doesn't save it."""

        # Create a factory with a model class
        class TestFactory(Factory[QRCode]):
            model_class = QRCode

            def _get_default_attributes(self):
                return {
                    "content": "test",
                    "qr_type": QRType.STATIC.value,
                    "fill_color": "#000000",
                    "back_color": "#FFFFFF",
                }

        # Build an instance
        instance = TestFactory().build()

        # Should be a QRCode
        assert isinstance(instance, QRCode)
        assert instance.content == "test"
        assert instance.qr_type == QRType.STATIC.value


class TestQRCodeFactory:
    """Tests for the QRCodeFactory class."""

    def test_build_creates_unsaved_instance(self):
        """Test that build() creates a QRCode but doesn't save it."""
        qr = QRCodeFactory().build()

        assert isinstance(qr, QRCode)
        assert qr.content is not None
        assert qr.qr_type == QRType.STATIC.value

    def test_build_static_creates_static_qr(self):
        """Test that build_static() creates a static QRCode."""
        qr = QRCodeFactory().build_static()

        assert isinstance(qr, QRCode)
        assert qr.qr_type == QRType.STATIC.value
        assert qr.redirect_url is None

    def test_build_dynamic_creates_dynamic_qr(self):
        """Test that build_dynamic() creates a dynamic QRCode."""
        qr = QRCodeFactory().build_dynamic()

        assert isinstance(qr, QRCode)
        assert qr.qr_type == QRType.DYNAMIC.value
        assert qr.redirect_url is not None
        assert qr.content.startswith("https://qr.example.com/")

    def test_create_requires_db_session(self):
        """Test that create() requires a database session."""
        with pytest.raises(ValueError):
            QRCodeFactory().create()

    def test_create_batch_requires_db_session(self):
        """Test that create_batch() requires a database session."""
        with pytest.raises(ValueError):
            QRCodeFactory().create_batch(size=3)

    def test_create_saves_to_database(self, test_db: Session):
        """Test that create() saves an instance to the database."""
        factory = QRCodeFactory(test_db)
        qr = factory.create()

        # Should be able to query it
        db_qr = test_db.query(QRCode).filter_by(id=qr.id).first()
        assert db_qr is not None
        assert db_qr.id == qr.id

    def test_create_static_saves_static_qr(self, test_db: Session):
        """Test that create_static() saves a static QRCode."""
        factory = QRCodeFactory(test_db)
        qr = factory.create_static()

        assert qr.qr_type == QRType.STATIC.value
        assert qr.redirect_url is None

        # Should be able to query it
        db_qr = test_db.query(QRCode).filter_by(id=qr.id).first()
        assert db_qr is not None
        assert db_qr.qr_type == QRType.STATIC.value

    def test_create_dynamic_saves_dynamic_qr(self, test_db: Session):
        """Test that create_dynamic() saves a dynamic QRCode."""
        factory = QRCodeFactory(test_db)
        qr = factory.create_dynamic()

        assert qr.qr_type == QRType.DYNAMIC.value
        assert qr.redirect_url is not None

        # Should be able to query it
        db_qr = test_db.query(QRCode).filter_by(id=qr.id).first()
        assert db_qr is not None
        assert db_qr.qr_type == QRType.DYNAMIC.value
        assert db_qr.redirect_url == qr.redirect_url

    def test_create_with_scans_adds_scan_history(self, test_db: Session):
        """Test that create_with_scans() adds scan history."""
        factory = QRCodeFactory(test_db)
        qr = factory.create_with_scans(scan_count=5)

        assert qr.scan_count == 5
        assert qr.last_scan_at is not None

        # Should be able to query it
        db_qr = test_db.query(QRCode).filter_by(id=qr.id).first()
        assert db_qr is not None
        assert db_qr.scan_count == 5
        assert db_qr.last_scan_at is not None

    def test_create_batch_creates_multiple_instances(self, test_db: Session):
        """Test that create_batch() creates multiple QRCode instances."""
        factory = QRCodeFactory(test_db)
        qrs = factory.create_batch(size=3)

        assert len(qrs) == 3
        for qr in qrs:
            assert isinstance(qr, QRCode)

        # Should have unique IDs
        ids = [qr.id for qr in qrs]
        assert len(set(ids)) == 3
