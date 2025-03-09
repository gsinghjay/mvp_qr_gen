"""
Test factories for generating test data.

This module provides a factory pattern implementation for creating test entities
in a consistent way. Factory classes provide methods to create entities with
sensible defaults, while allowing customization of specific attributes.
"""

import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional, TypeVar, Type, Generic, cast

from faker import Faker
from sqlalchemy.orm import Session

from ..database import Base
from ..models.qr import QRCode
from ..schemas.common import QRType

# Initialize Faker for generating test data
fake = Faker()

# Generic type for models
T = TypeVar('T', bound=Base)


class Factory(Generic[T]):
    """
    Base factory class for creating test entities.
    
    Attributes:
        model_class: The SQLAlchemy model class this factory creates
        db_session: Optional SQLAlchemy session for direct database integration
    """
    
    model_class: Type[T]
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize the factory with an optional database session.
        
        Args:
            db_session: SQLAlchemy session for database integration
        """
        self.db_session = db_session
    
    def build(self, **kwargs: Any) -> T:
        """
        Build a model instance without saving it to the database.
        
        Args:
            **kwargs: Attribute overrides for the model
            
        Returns:
            An unsaved model instance
        """
        attrs = self._get_default_attributes()
        attrs.update(kwargs)
        
        return self.model_class(**attrs)
    
    def create(self, **kwargs: Any) -> T:
        """
        Create a model instance and save it to the database.
        
        Args:
            **kwargs: Attribute overrides for the model
            
        Returns:
            A saved model instance
            
        Raises:
            ValueError: If no database session was provided
        """
        if self.db_session is None:
            raise ValueError("Database session is required for create()")
        
        instance = self.build(**kwargs)
        self.db_session.add(instance)
        self.db_session.flush()  # Flush to get generated IDs, but don't commit
        
        return instance
    
    def create_batch(self, size: int, **kwargs: Any) -> List[T]:
        """
        Create multiple model instances in a batch.
        
        Args:
            size: Number of instances to create
            **kwargs: Attribute overrides for the models
            
        Returns:
            List of saved model instances
            
        Raises:
            ValueError: If no database session was provided
        """
        if self.db_session is None:
            raise ValueError("Database session is required for create_batch()")
        
        instances = [self.build(**kwargs) for _ in range(size)]
        self.db_session.add_all(instances)
        self.db_session.flush()  # Flush to get generated IDs, but don't commit
        
        return instances
    
    def _get_default_attributes(self) -> Dict[str, Any]:
        """
        Get the default attributes for the model.
        
        Returns:
            Dictionary of default attributes
        """
        # This should be implemented by subclasses
        return {}


class QRCodeFactory(Factory[QRCode]):
    """
    Factory for creating QRCode instances for testing.
    
    Provides methods to create both static and dynamic QR codes with sensible defaults.
    All datetime fields are created in UTC timezone.
    """
    
    model_class = QRCode
    
    def _get_default_attributes(self) -> Dict[str, Any]:
        """
        Get default attributes for a QR code.
        
        Returns:
            Dictionary of default attributes
        """
        return {
            "id": str(uuid.uuid4()),
            "content": fake.url(),
            "qr_type": QRType.STATIC.value,
            "fill_color": "#000000",
            "back_color": "#FFFFFF",
            "size": 10,
            "border": 4,
            "scan_count": 0,
            "created_at": datetime.now(UTC),
        }
    
    def build_static(self, **kwargs: Any) -> QRCode:
        """
        Build a static QR code instance.
        
        Args:
            **kwargs: Attribute overrides
            
        Returns:
            An unsaved static QR code instance
        """
        # Set static-specific defaults
        attrs = {
            "qr_type": QRType.STATIC.value,
            "content": fake.url(),
            "redirect_url": None
        }
        attrs.update(kwargs)
        
        return self.build(**attrs)
    
    def build_dynamic(self, **kwargs: Any) -> QRCode:
        """
        Build a dynamic QR code instance.
        
        Args:
            **kwargs: Attribute overrides
            
        Returns:
            An unsaved dynamic QR code instance
        """
        # Generate a short unique identifier for the path
        short_id = str(uuid.uuid4())[:8]
        redirect_url = fake.url()
        
        # Set dynamic-specific defaults
        attrs = {
            "qr_type": QRType.DYNAMIC.value,
            "content": f"https://qr.example.com/{short_id}",
            "redirect_url": redirect_url
        }
        attrs.update(kwargs)
        
        return self.build(**attrs)
    
    def create_static(self, **kwargs: Any) -> QRCode:
        """
        Create a static QR code and save it to the database.
        
        Args:
            **kwargs: Attribute overrides
            
        Returns:
            A saved static QR code instance
        """
        # Get static attributes and pass them to create method
        static_attrs = {
            "qr_type": QRType.STATIC.value,
            "content": fake.url(),
            "redirect_url": None
        }
        static_attrs.update(kwargs)
        
        return self.create(**static_attrs)
    
    def create_dynamic(self, **kwargs: Any) -> QRCode:
        """
        Create a dynamic QR code and save it to the database.
        
        Args:
            **kwargs: Attribute overrides
            
        Returns:
            A saved dynamic QR code instance
        """
        # Generate a short unique identifier for the path
        short_id = str(uuid.uuid4())[:8]
        redirect_url = kwargs.pop("redirect_url", fake.url())
        
        # Get dynamic attributes and pass them to create method
        dynamic_attrs = {
            "qr_type": QRType.DYNAMIC.value,
            "content": f"https://qr.example.com/{short_id}",
            "redirect_url": redirect_url
        }
        dynamic_attrs.update(kwargs)
        
        return self.create(**dynamic_attrs)
    
    def create_with_scans(self, scan_count: int = 10, last_scan_days_ago: int = 1, **kwargs: Any) -> QRCode:
        """
        Create a QR code with scan history.
        
        Args:
            scan_count: Number of scans to record
            last_scan_days_ago: Days ago for the last scan
            **kwargs: Additional attribute overrides
            
        Returns:
            A saved QR code instance with scan history
        """
        last_scan_at = datetime.now(UTC) - timedelta(days=last_scan_days_ago)
        
        attrs = {
            "scan_count": scan_count,
            "last_scan_at": last_scan_at
        }
        attrs.update(kwargs)
        
        return self.create(**attrs) 