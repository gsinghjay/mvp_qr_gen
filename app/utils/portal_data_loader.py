"""
Portal Data Loader Utility
Handles loading and caching portal data from JSON files.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache

from app.core.config import settings

logger = logging.getLogger("app.portal_data_loader")

class PortalDataLoader:
    """Loads and caches portal data from JSON files."""
    
    _instance: Optional['PortalDataLoader'] = None
    _data_cache: Dict[str, Dict[str, Any]] = {}
    
    def __new__(cls) -> 'PortalDataLoader':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.data_dir = Path(settings.STATIC_DIR) / "portal_data"
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Ensure the portal data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    @lru_cache(maxsize=10)
    def load_json_file(self, filename: str) -> Dict[str, Any]:
        """
        Load JSON data from a file with caching.
        
        Args:
            filename: Name of the JSON file (without .json extension)
            
        Returns:
            Dictionary containing the loaded data
            
        Raises:
            FileNotFoundError: If the JSON file doesn't exist
            json.JSONDecodeError: If the JSON is malformed
        """
        file_path = self.data_dir / f"{filename}.json"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Loaded portal data from {file_path}")
                return data
        except FileNotFoundError:
            logger.warning(f"Portal data file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in portal data file {file_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading portal data from {file_path}: {e}")
            return {}
    
    def get_faculty_staff_data(self) -> Dict[str, Any]:
        """Get faculty/staff portal data."""
        return self.load_json_file("faculty_staff_data")
    
    def get_student_data(self) -> Dict[str, Any]:
        """Get student portal data."""
        return self.load_json_file("student_data")
    
    def get_hr_data(self) -> Dict[str, Any]:
        """Get HR portal data."""
        return self.load_json_file("hr_data")
    
    def get_academics_data(self) -> Dict[str, Any]:
        """Get academic portal data (could be different from general student data)."""
        # For now, use the same student data, but this could be a separate file
        return self.get_student_data()
    
    def reload_cache(self):
        """Clear the cache to force reloading data from files."""
        self.load_json_file.cache_clear()
        logger.info("Portal data cache cleared")


# Singleton instance
portal_data_loader = PortalDataLoader()

# Convenience functions for easy importing
def get_faculty_staff_data() -> Dict[str, Any]:
    """Get structured data for faculty/staff portal."""
    return portal_data_loader.get_faculty_staff_data()

def get_student_data() -> Dict[str, Any]:
    """Get structured data for student portals."""
    return portal_data_loader.get_student_data()

def get_hr_data() -> Dict[str, Any]:
    """Get structured data for HR portal."""
    return portal_data_loader.get_hr_data()

def get_academics_data() -> Dict[str, Any]:
    """Get structured data for academic portal."""
    return portal_data_loader.get_academics_data()

def reload_portal_data_cache():
    """Reload portal data cache (useful for development/testing)."""
    portal_data_loader.reload_cache() 