#!/usr/bin/env python3
"""
API Endpoint Testing Script for QR Code Generator
Tests all major endpoints and validates responses with proper timezone handling.
"""

import requests
import json
from datetime import datetime, timezone
import sys
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from colorama import init, Fore, Style
import urllib3
import logging
from pathlib import Path
import re
from urllib.parse import urlparse

# Initialize colorama for cross-platform colored output
init()

# Disable SSL verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging with timezone-aware timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03dZ - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S',
    handlers=[
        logging.FileHandler('api_test_results.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Add timezone info to log timestamps
logging.Formatter.converter = lambda *args: datetime.now(timezone.utc).timetuple()

@dataclass
class TestResult:
    """Store test results with metadata"""
    endpoint: str
    method: str
    status_code: int
    response_time: float
    success: bool
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    validation_errors: List[str] = None

    def __post_init__(self):
        """Initialize validation_errors if not provided"""
        if self.validation_errors is None:
            self.validation_errors = []

class APITester:
    """Test suite for QR Code Generator API endpoints"""
    
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.session = requests.Session()
        self.created_qr_ids = []
        self.logger = logging.getLogger(__name__)
        
    def validate_datetime(self, dt_str: str) -> List[str]:
        """Validate datetime string format and timezone awareness."""
        errors = []
        if not dt_str:
            return errors
            
        try:
            # Handle 'Z' suffix by replacing with '+00:00'
            if dt_str.endswith('Z'):
                dt_str = dt_str[:-1] + '+00:00'
            
            dt = datetime.fromisoformat(dt_str)
            
            if dt.tzinfo is None:
                errors.append(f"Datetime '{dt_str}' is not timezone-aware")
            elif dt.tzinfo != timezone.utc:
                errors.append(f"Datetime '{dt_str}' is not in UTC")
                
        except ValueError as e:
            errors.append(f"Invalid datetime format '{dt_str}': {str(e)}")
            
        return errors
    
    def validate_color(self, color: str) -> List[str]:
        """Validate hex color format."""
        errors = []
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            errors.append(f"Invalid hex color format: {color}")
        return errors
    
    def validate_url(self, url: str) -> List[str]:
        """Validate URL format."""
        errors = []
        if not url:
            return errors
            
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                errors.append(f"Invalid URL format: {url}")
        except Exception as e:
            errors.append(f"URL validation error: {str(e)}")
            
        return errors
    
    def validate_response(self, result: TestResult) -> None:
        """Validate response data based on endpoint type."""
        if not result.response_data:
            return
            
        data = result.response_data
        
        # Validate common fields
        if "created_at" in data:
            result.validation_errors.extend(
                self.validate_datetime(data["created_at"])
            )
        
        if "last_scan_at" in data and data["last_scan_at"]:
            result.validation_errors.extend(
                self.validate_datetime(data["last_scan_at"])
            )
        
        if "fill_color" in data:
            result.validation_errors.extend(
                self.validate_color(data["fill_color"])
            )
            
        if "back_color" in data:
            result.validation_errors.extend(
                self.validate_color(data["back_color"])
            )
            
        if "redirect_url" in data and data["redirect_url"]:
            result.validation_errors.extend(
                self.validate_url(data["redirect_url"])
            )
            
        # Validate QR code specific fields
        if "qr_type" in data:
            if data["qr_type"] == "dynamic":
                if not data.get("redirect_url"):
                    result.validation_errors.append("Dynamic QR code missing redirect_url")
            elif data["qr_type"] == "static":
                if data.get("redirect_url"):
                    result.validation_errors.append("Static QR code should not have redirect_url")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> TestResult:
        """Make HTTP request and return TestResult with validation"""
        url = f"{self.base_url}{endpoint}"
        start_time = datetime.now(timezone.utc)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data if data else None,
                verify=False,  # Allow self-signed certificates
                timeout=10
            )
            
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            try:
                response_data = response.json() if response.text else None
            except json.JSONDecodeError:
                response_data = {"text": response.text[:200] + "..." if len(response.text) > 200 else response.text}
            
            success = 200 <= response.status_code < 300
            
            result = TestResult(
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                response_time=elapsed,
                success=success,
                response_data=response_data
            )
            
            # Validate response data
            self.validate_response(result)
            
            return result
            
        except requests.RequestException as e:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            return TestResult(
                endpoint=endpoint,
                method=method,
                status_code=0,
                response_time=elapsed,
                success=False,
                error_message=str(e)
            )
    
    def print_result(self, result: TestResult) -> None:
        """Print test result with color coding and validation errors"""
        status_color = Fore.GREEN if result.success and not result.validation_errors else Fore.RED
        status_text = "SUCCESS" if result.success and not result.validation_errors else "FAILED"
        
        print(f"\n{Style.BRIGHT}Testing {result.method} {result.endpoint}{Style.RESET_ALL}")
        print(f"Status: {status_color}{status_text}{Style.RESET_ALL}")
        print(f"Status Code: {status_color}{result.status_code}{Style.RESET_ALL}")
        print(f"Response Time: {result.response_time:.2f}s")
        
        if result.error_message:
            print(f"Error: {Fore.RED}{result.error_message}{Style.RESET_ALL}")
        
        if result.validation_errors:
            print(f"{Fore.RED}Validation Errors:{Style.RESET_ALL}")
            for error in result.validation_errors:
                print(f"- {error}")
        
        if result.response_data:
            print("Response Data:")
            print(json.dumps(result.response_data, indent=2))
        
        print("-" * 80)
        
        # Log results
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoint": result.endpoint,
            "method": result.method,
            "status_code": result.status_code,
            "response_time": result.response_time,
            "success": result.success,
            "validation_errors": result.validation_errors
        }
        self.logger.info(json.dumps(log_data))
    
    def run_tests(self) -> None:
        """Run all API endpoint tests"""
        tests = [
            # Basic endpoints
            ("GET", "/"),
            ("GET", "/docs"),
            ("GET", "/redoc"),
            ("GET", "/openapi.json"),
            ("GET", "/api/v1/qr"),
            
            # Create static QR code
            ("POST", "/api/v1/qr/static", {
                "content": "https://example.com",
                "qr_type": "static",
                "fill_color": "#000000",
                "back_color": "#FFFFFF",
                "size": 10,
                "border": 4
            }),
            
            # Create dynamic QR code
            ("POST", "/api/v1/qr/dynamic", {
                "content": "My Dynamic QR",
                "qr_type": "dynamic",
                "redirect_url": "https://example.com",
                "fill_color": "#000000",
                "back_color": "#FFFFFF",
                "size": 10,
                "border": 4
            }),
            
            # Test invalid cases
            ("POST", "/api/v1/qr/static", {
                "content": "https://example.com",
                "qr_type": "static",
                "redirect_url": "https://example.com",  # Should fail
                "fill_color": "#000000",
                "back_color": "#FFFFFF",
                "size": 10,
                "border": 4
            }),
            
            ("POST", "/api/v1/qr/dynamic", {
                "content": "My Dynamic QR",
                "qr_type": "dynamic",
                "fill_color": "#000000",  # Missing redirect_url
                "back_color": "#FFFFFF",
                "size": 10,
                "border": 4
            })
        ]
        
        results = []
        for test in tests:
            method, endpoint, *data = test
            result = self._make_request(method, endpoint, data[0] if data else None)
            results.append(result)
            self.print_result(result)
            
            # Store QR code ID if created successfully
            if result.success and result.response_data and "id" in result.response_data:
                self.created_qr_ids.append(result.response_data["id"])
        
        # Test endpoints that depend on created QR codes
        for qr_id in self.created_qr_ids:
            # Get QR code by ID
            result = self._make_request("GET", f"/api/v1/qr/{qr_id}")
            results.append(result)
            self.print_result(result)
            
            # Get QR code image in different formats
            for fmt in ["png", "jpeg", "svg", "webp"]:
                result = self._make_request("GET", f"/api/v1/qr/{qr_id}/image?image_format={fmt}")
                results.append(result)
                self.print_result(result)
            
            # Update QR code (for dynamic QR codes)
            if result.response_data and result.response_data.get("qr_type") == "dynamic":
                result = self._make_request(
                    "PUT",
                    f"/api/v1/qr/{qr_id}",
                    {"redirect_url": "https://updated-example.com"}
                )
                results.append(result)
                self.print_result(result)
        
        # Print summary
        self._print_summary(results)
    
    def _print_summary(self, results: list[TestResult]) -> None:
        """Print test summary statistics"""
        total = len(results)
        successful = sum(1 for r in results if r.success and not r.validation_errors)
        failed = total - successful
        avg_response_time = sum(r.response_time for r in results) / total
        
        print(f"\n{Style.BRIGHT}Test Summary:{Style.RESET_ALL}")
        print(f"Total Tests: {total}")
        print(f"Successful: {Fore.GREEN}{successful}{Style.RESET_ALL}")
        print(f"Failed: {Fore.RED if failed else Fore.GREEN}{failed}{Style.RESET_ALL}")
        print(f"Average Response Time: {avg_response_time:.2f}s")
        
        if failed > 0:
            print(f"\n{Fore.RED}Failed Tests:{Style.RESET_ALL}")
            for result in results:
                if not result.success or result.validation_errors:
                    print(f"\n- {result.method} {result.endpoint}")
                    print(f"  Status: {result.status_code}")
                    if result.error_message:
                        print(f"  Error: {result.error_message}")
                    if result.validation_errors:
                        print("  Validation Errors:")
                        for error in result.validation_errors:
                            print(f"    - {error}")

def main():
    """Main entry point"""
    print(f"{Style.BRIGHT}QR Code Generator API Endpoint Tests{Style.RESET_ALL}")
    print("Testing endpoints...")
    
    try:
        tester = APITester()
        tester.run_tests()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Tests interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Error running tests: {str(e)}{Style.RESET_ALL}")
        logging.exception("Unexpected error during test execution")
        sys.exit(1)

if __name__ == "__main__":
    main() 