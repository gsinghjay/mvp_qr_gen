"""
Test factories for generating test data.

This module provides a factory pattern implementation for creating test entities
in a consistent way. Factory classes provide methods to create entities with
sensible defaults, while allowing customization of specific attributes.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Generic, TypeVar

from faker import Faker
from sqlalchemy.orm import Session

from ..database import Base
from ..models.qr import QRCode
from ..models.scan_log import ScanLog
from ..schemas.common import QRType

# Initialize Faker for generating test data
fake = Faker()

# Generic type for models
T = TypeVar("T", bound=Base)


class Factory(Generic[T]):
    """
    Base factory class for creating test entities.

    Attributes:
        model_class: The SQLAlchemy model class this factory creates
        db_session: Optional SQLAlchemy session for direct database integration
    """

    model_class: type[T]

    def __init__(self, db_session: Session | None = None):
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
        Create a model instance and add it to the database session.
        
        Note: This method only adds the instance to the session but does not 
        commit or flush. The test fixtures manage transaction boundaries.

        Args:
            **kwargs: Attribute overrides for the model

        Returns:
            A model instance added to the session

        Raises:
            ValueError: If no database session was provided
        """
        if self.db_session is None:
            raise ValueError("Database session is required for create()")

        instance = self.build(**kwargs)
        self.db_session.add(instance)
        
        # No flush here - let the test manage transaction boundaries
        
        return instance

    def create_batch(self, size: int, **kwargs: Any) -> list[T]:
        """
        Create multiple model instances in a batch.
        
        Note: This method only adds the instances to the session but does not 
        commit or flush. The test fixtures manage transaction boundaries.

        Args:
            size: Number of instances to create
            **kwargs: Attribute overrides for the models

        Returns:
            List of model instances added to the session

        Raises:
            ValueError: If no database session was provided
        """
        if self.db_session is None:
            raise ValueError("Database session is required for create_batch()")

        instances = [self.build(**kwargs) for _ in range(size)]
        self.db_session.add_all(instances)
        
        # No flush here - let the test manage transaction boundaries
        
        return instances

    def _get_default_attributes(self) -> dict[str, Any]:
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

    def _get_default_attributes(self) -> dict[str, Any]:
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
        attrs = {"qr_type": QRType.STATIC.value, "content": fake.url(), "redirect_url": None}
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
            "redirect_url": redirect_url,
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
        static_attrs = {"qr_type": QRType.STATIC.value, "content": fake.url(), "redirect_url": None}
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
            "redirect_url": redirect_url,
        }
        dynamic_attrs.update(kwargs)

        return self.create(**dynamic_attrs)

    def create_with_scans(
        self, scan_count: int = 10, last_scan_days_ago: int = 1, **kwargs: Any
    ) -> QRCode:
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

        attrs = {"scan_count": scan_count, "last_scan_at": last_scan_at}
        attrs.update(kwargs)

        return self.create(**attrs)

    def create_batch_mixed(
        self,
        count: int = 10,
        static_ratio: float = 0.5,
        max_age_days: int = 30,
        max_scan_count: int = 100,
    ) -> list[QRCode]:
        """
        Create a batch of mixed static and dynamic QR codes.

        Args:
            count: Total number of QR codes to create
            static_ratio: Ratio of static to dynamic QR codes (0.0 to 1.0)
            max_age_days: Maximum age of QR codes in days
            max_scan_count: Maximum scan count for QR codes

        Returns:
            List of saved QR code instances
        """
        qr_codes = []
        static_count = int(count * static_ratio)
        dynamic_count = count - static_count
        
        # Ensure at least one of each type if both are supposed to be present
        if static_ratio > 0 and static_ratio < 1:
            if static_count == 0:
                static_count = 1
                dynamic_count = count - 1
            elif dynamic_count == 0:
                dynamic_count = 1
                static_count = count - 1

        # Create static QR codes
        for _ in range(static_count):
            age_days = fake.random.randint(0, max_age_days)
            scan_count = fake.random.randint(0, max_scan_count)
            
            # Sometimes set a last scan date
            last_scan_days_ago = None
            if scan_count > 0:
                last_scan_days_ago = fake.random.randint(0, age_days)
                
            qr_code = self.create_with_params(
                qr_type=QRType.STATIC,
                scan_count=scan_count,
                created_days_ago=age_days,
                last_scan_days_ago=last_scan_days_ago,
            )
            qr_codes.append(qr_code)

        # Create dynamic QR codes
        for _ in range(dynamic_count):
            age_days = fake.random.randint(0, max_age_days)
            scan_count = fake.random.randint(0, max_scan_count)
            
            # Sometimes set a last scan date
            last_scan_days_ago = None
            if scan_count > 0:
                last_scan_days_ago = fake.random.randint(0, age_days)
                
            qr_code = self.create_with_params(
                qr_type=QRType.DYNAMIC,
                scan_count=scan_count,
                created_days_ago=age_days,
                last_scan_days_ago=last_scan_days_ago,
            )
            qr_codes.append(qr_code)

        return qr_codes

    def create_with_params(
        self,
        qr_type: QRType = QRType.STATIC,
        content: str | None = None,
        redirect_url: str | None = None,
        fill_color: str = "#000000",
        back_color: str = "#FFFFFF",
        scan_count: int = 0,
        created_days_ago: int = 0,
        last_scan_days_ago: int | None = None,
        **kwargs: Any
    ) -> QRCode:
        """
        Create a QR code with fully specified parameters.
        
        This method is a direct replacement for create_test_qr_code in conftest.py,
        offering the same parameters but using the factory pattern.
        
        Args:
            qr_type: Type of QR code (static or dynamic)
            content: QR code content (generated if None)
            redirect_url: Redirect URL for dynamic QR codes
            fill_color: QR code fill color
            back_color: QR code background color
            scan_count: Initial scan count
            created_days_ago: Days to subtract from creation date
            last_scan_days_ago: Days to subtract from last scan date (None = no last scan)
            **kwargs: Additional attribute overrides
            
        Returns:
            A saved QR code instance
        """
        if self.db_session is None:
            raise ValueError("Database session is required for create_with_params()")
            
        # Generate test data if needed
        if content is None:
            if qr_type == QRType.STATIC:
                content = fake.url()
            else:
                content = f"/r/{uuid.uuid4().hex[:8]}"

        # For dynamic QR codes, ensure redirect_url is set
        if qr_type == QRType.DYNAMIC and redirect_url is None:
            redirect_url = fake.url()

        # Calculate dates
        created_at = datetime.now(UTC)
        if created_days_ago > 0:
            created_at = created_at - timedelta(days=created_days_ago)

        # Handle last scan date
        last_scan_at = None
        if last_scan_days_ago is not None:
            last_scan_at = datetime.now(UTC) - timedelta(days=last_scan_days_ago)
        
        # Create QR code with specified attributes
        attrs = {
            "content": content,
            "qr_type": qr_type.value,
            "redirect_url": redirect_url,
            "fill_color": fill_color,
            "back_color": back_color,
            "scan_count": scan_count,
            "created_at": created_at,
            "last_scan_at": last_scan_at,
        }
        attrs.update(kwargs)
        
        # Create the QR code
        qr_code = self.create(**attrs)
        
        # Flush to ensure the QR code is saved to the database
        self.db_session.flush()
        
        return qr_code

    async def async_create_with_params(
        self,
        qr_type: QRType = QRType.STATIC,
        content: str | None = None,
        redirect_url: str | None = None,
        fill_color: str = "#000000",
        back_color: str = "#FFFFFF",
        scan_count: int = 0,
        created_days_ago: int = 0,
        last_scan_days_ago: int | None = None,
        **kwargs: Any
    ) -> QRCode:
        """
        Async version of create_with_params.
        
        Create a QR code with fully specified parameters using an async session.
        
        Args:
            qr_type: Type of QR code (static or dynamic)
            content: QR code content (generated if None)
            redirect_url: Redirect URL for dynamic QR codes
            fill_color: QR code fill color
            back_color: QR code background color
            scan_count: Initial scan count
            created_days_ago: Days to subtract from creation date
            last_scan_days_ago: Days to subtract from last scan date (None = no last scan)
            **kwargs: Additional attribute overrides
            
        Returns:
            A saved QR code instance
        """
        if self.db_session is None:
            raise ValueError("Database session is required for async_create_with_params()")
            
        # Generate test data if needed
        if content is None:
            if qr_type == QRType.STATIC:
                content = fake.url()
            else:
                content = f"/r/{uuid.uuid4().hex[:8]}"

        # For dynamic QR codes, ensure redirect_url is set
        if qr_type == QRType.DYNAMIC and redirect_url is None:
            redirect_url = fake.url()

        # Calculate dates - use naive datetimes for SQLAlchemy's asyncpg dialect
        created_at = datetime.now(UTC).replace(tzinfo=None)
        if created_days_ago > 0:
            created_at = created_at - timedelta(days=created_days_ago)

        # Handle last scan date
        last_scan_at = None
        if last_scan_days_ago is not None:
            last_scan_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=last_scan_days_ago)
        
        # Prepare attributes
        attrs = {
            "id": str(uuid.uuid4()),
            "content": content,
            "qr_type": qr_type.value,
            "redirect_url": redirect_url,
            "fill_color": fill_color,
            "back_color": back_color,
            "scan_count": scan_count,
            "created_at": created_at,
            "last_scan_at": last_scan_at,
            "size": 10,
            "border": 4,
        }
        attrs.update(kwargs)
        
        # Create and save the QR code
        qr_code = QRCode(**attrs)
        self.db_session.add(qr_code)
        await self.db_session.flush()
        
        return qr_code

    async def async_create_batch_mixed(
        self,
        count: int = 10,
        static_ratio: float = 0.5,
        max_age_days: int = 30,
        max_scan_count: int = 100,
    ) -> list[QRCode]:
        """
        Async version of create_batch_mixed.
        
        Create a batch of mixed QR codes using an async session.
        
        Args:
            count: Number of QR codes to create
            static_ratio: Ratio of static to dynamic QR codes (0.0 to 1.0)
            max_age_days: Maximum age of QR codes in days
            max_scan_count: Maximum scan count for QR codes
            
        Returns:
            List of created QR code instances
        """
        if self.db_session is None:
            raise ValueError("Database session is required for async_create_batch_mixed()")
            
        qr_codes = []
        
        for i in range(count):
            # Determine if this QR code should be static based on the ratio
            is_static = fake.random.random() < static_ratio
            
            # Generate random age and scan count
            age_days = fake.random.randint(0, max_age_days)
            scan_count = fake.random.randint(0, max_scan_count)
            
            # Sometimes set a last scan date
            last_scan_days_ago = None
            if scan_count > 0:
                last_scan_days_ago = fake.random.randint(0, age_days)
                
            # Create parameters for the QR code
            params = {
                "qr_type": QRType.STATIC if is_static else QRType.DYNAMIC,
                "scan_count": scan_count,
                "created_days_ago": age_days,
                "last_scan_days_ago": last_scan_days_ago,
            }
            
            # Create QR code
            qr_code = await self.async_create_with_params(**params)
            qr_codes.append(qr_code)
            
        # Flush to ensure all changes are saved
        await self.db_session.flush()
        
        return qr_codes


class ScanLogFactory(Factory[ScanLog]):
    """
    Factory for creating ScanLog instances for testing.
    
    Provides methods to create scan logs with sensible defaults.
    All datetime fields are created in UTC timezone.
    """
    
    model_class = ScanLog
    
    def _get_default_attributes(self) -> dict[str, Any]:
        """
        Get default attributes for a scan log.
        
        Returns:
            Dictionary of default attributes
        """
        return {
            "id": str(uuid.uuid4()),
            "qr_code_id": str(uuid.uuid4()),  # This should be overridden with a real QR ID
            "scanned_at": datetime.now(UTC),
            "ip_address": fake.ipv4(),
            "raw_user_agent": fake.user_agent(),
            "is_genuine_scan": True,
            "device_family": fake.random.choice(["iPhone", "Samsung Galaxy", "Google Pixel", "Other"]),
            "os_family": fake.random.choice(["iOS", "Android", "Windows", "macOS", "Linux"]),
            "os_version": fake.random.choice(["15.0", "12.0", "11", "10.15", "5.10"]), 
            "browser_family": fake.random.choice(["Chrome", "Safari", "Firefox", "Edge"]),
            "browser_version": fake.random.choice(["96.0", "15.0", "95.0", "98.0"]),
            "is_mobile": False,
            "is_tablet": False,
            "is_pc": True,
            "is_bot": False,
        }
    
    def create_for_qr(
        self, 
        qr_code: QRCode | str,
        is_genuine_scan: bool = True,
        days_ago: int = 0,
        hours_ago: int = 0,
        **kwargs: Any
    ) -> ScanLog:
        """
        Create a scan log for a specific QR code.
        
        Args:
            qr_code: QR code instance or ID
            is_genuine_scan: Whether this is a genuine QR scan
            days_ago: Days to subtract from scanned_at date
            hours_ago: Hours to subtract from scanned_at date (in addition to days)
            **kwargs: Additional attribute overrides
            
        Returns:
            A saved scan log instance
        """
        # Extract QR code ID
        qr_code_id = qr_code if isinstance(qr_code, str) else qr_code.id
        
        # Calculate scanned_at
        scanned_at = datetime.now(UTC)
        if days_ago > 0 or hours_ago > 0:
            scanned_at = scanned_at - timedelta(days=days_ago, hours=hours_ago)
        
        # Determine device type based on user agent or explicit overrides
        is_mobile = kwargs.get("is_mobile", False)
        is_tablet = kwargs.get("is_tablet", False)
        is_pc = kwargs.get("is_pc", not (is_mobile or is_tablet))
        is_bot = kwargs.get("is_bot", False)
        
        # For mobile devices, update the device family and OS if not explicitly provided
        if is_mobile and "device_family" not in kwargs:
            device_family = fake.random.choice(["iPhone", "Samsung Galaxy", "Google Pixel"])
            kwargs["device_family"] = device_family
            
            if "os_family" not in kwargs:
                if device_family == "iPhone":
                    kwargs["os_family"] = "iOS"
                    kwargs["os_version"] = fake.random.choice(["15.0", "14.0", "13.0"])
                else:
                    kwargs["os_family"] = "Android"
                    kwargs["os_version"] = fake.random.choice(["12.0", "11.0", "10.0"])
        
        # For tablets, update the device family and OS if not explicitly provided
        if is_tablet and "device_family" not in kwargs:
            device_family = fake.random.choice(["iPad", "Samsung Tab", "Amazon Fire"])
            kwargs["device_family"] = device_family
            
            if "os_family" not in kwargs:
                if device_family == "iPad":
                    kwargs["os_family"] = "iOS"
                    kwargs["os_version"] = fake.random.choice(["15.0", "14.0", "13.0"])
                else:
                    kwargs["os_family"] = "Android"
                    kwargs["os_version"] = fake.random.choice(["12.0", "11.0", "10.0"])
        
        # Prepare scan log attributes
        scan_attrs = {
            "qr_code_id": qr_code_id,
            "is_genuine_scan": is_genuine_scan,
            "scanned_at": scanned_at,
            "is_mobile": is_mobile,
            "is_tablet": is_tablet,
            "is_pc": is_pc,
            "is_bot": is_bot,
        }
        scan_attrs.update(kwargs)
        
        return self.create(**scan_attrs)
    
    def create_batch_for_qr(
        self,
        qr_code: QRCode | str,
        count: int = 10,
        genuine_ratio: float = 0.8,
        max_days_ago: int = 30,
        **kwargs: Any
    ) -> list[ScanLog]:
        """
        Create multiple scan logs for a specific QR code.
        
        Args:
            qr_code: QR code instance or ID
            count: Number of scan logs to create
            genuine_ratio: Ratio of genuine to non-genuine scans (0.0 to 1.0)
            max_days_ago: Maximum age of scan logs in days
            **kwargs: Additional attribute overrides for all scan logs
            
        Returns:
            List of saved scan log instances
        """
        if self.db_session is None:
            raise ValueError("Database session is required for create_batch_for_qr()")
        
        # Extract QR code ID
        qr_code_id = qr_code if isinstance(qr_code, str) else qr_code.id
        
        scan_logs = []
        genuine_count = int(count * genuine_ratio)
        non_genuine_count = count - genuine_count
        
        # Create genuine scans
        for _ in range(genuine_count):
            days_ago = fake.random.randint(0, max_days_ago)
            hours_ago = fake.random.randint(0, 23)
            
            # Random device type distribution (mostly mobile for genuine scans)
            is_mobile = fake.random.random() < 0.7  # 70% mobile
            is_tablet = not is_mobile and fake.random.random() < 0.4  # 12% tablet (40% of non-mobile)
            is_pc = not (is_mobile or is_tablet)  # 18% PC
            
            scan_log = self.create_for_qr(
                qr_code_id,
                is_genuine_scan=True,
                days_ago=days_ago,
                hours_ago=hours_ago,
                is_mobile=is_mobile,
                is_tablet=is_tablet,
                is_pc=is_pc,
                **kwargs
            )
            scan_logs.append(scan_log)
        
        # Create non-genuine scans (direct URL access)
        for _ in range(non_genuine_count):
            days_ago = fake.random.randint(0, max_days_ago)
            hours_ago = fake.random.randint(0, 23)
            
            # Random device type distribution (mostly desktop for non-genuine)
            is_mobile = fake.random.random() < 0.2  # 20% mobile
            is_tablet = not is_mobile and fake.random.random() < 0.1  # 8% tablet
            is_pc = not (is_mobile or is_tablet)  # 72% PC
            
            scan_log = self.create_for_qr(
                qr_code_id,
                is_genuine_scan=False,
                days_ago=days_ago,
                hours_ago=hours_ago,
                is_mobile=is_mobile,
                is_tablet=is_tablet,
                is_pc=is_pc,
                **kwargs
            )
            scan_logs.append(scan_log)
        
        return scan_logs
    
    async def async_create_for_qr(
        self, 
        qr_code: QRCode | str,
        is_genuine_scan: bool = True,
        days_ago: int = 0,
        hours_ago: int = 0,
        **kwargs: Any
    ) -> ScanLog:
        """
        Asynchronously create a scan log for a specific QR code.
        
        Args:
            qr_code: QR code instance or ID
            is_genuine_scan: Whether this is a genuine QR scan
            days_ago: Days to subtract from scanned_at date
            hours_ago: Hours to subtract from scanned_at date (in addition to days)
            **kwargs: Additional attribute overrides
            
        Returns:
            A saved scan log instance
        """
        if self.db_session is None:
            raise ValueError("Async database session is required for async_create_for_qr()")
        
        # Extract QR code ID
        qr_code_id = qr_code if isinstance(qr_code, str) else qr_code.id
        
        # Calculate scanned_at
        scanned_at = datetime.now(UTC)
        if days_ago > 0 or hours_ago > 0:
            scanned_at = scanned_at - timedelta(days=days_ago, hours=hours_ago)
        
        # Determine device type based on user agent or explicit overrides
        is_mobile = kwargs.get("is_mobile", False)
        is_tablet = kwargs.get("is_tablet", False)
        is_pc = kwargs.get("is_pc", not (is_mobile or is_tablet))
        is_bot = kwargs.get("is_bot", False)
        
        # Prepare scan log attributes
        scan_attrs = {
            "qr_code_id": qr_code_id,
            "is_genuine_scan": is_genuine_scan,
            "scanned_at": scanned_at,
            "is_mobile": is_mobile,
            "is_tablet": is_tablet,
            "is_pc": is_pc,
            "is_bot": is_bot,
        }
        scan_attrs.update(kwargs)
        
        # Build the instance
        attrs = self._get_default_attributes()
        attrs.update(scan_attrs)
        instance = self.model_class(**attrs)
        
        # Add to async session
        self.db_session.add(instance)
        
        return instance
