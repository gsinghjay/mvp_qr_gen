"""
Integration test package initialization.
Provides imports from the main tests package for easier access.
"""
import sys
import os

# Add the parent tests directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import common test components for easier access
from app.tests.conftest import *
from app.tests.factories import *
from app.tests.helpers import *
from app.tests.utils import *

# Core application imports that are commonly used in tests
from app.database import get_db, get_db_with_logging
from app.dependencies import get_qr_service
