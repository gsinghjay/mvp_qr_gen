#!/usr/bin/env python
"""
Canary Rollout Monitoring Script (Task 1.5)

This script helps monitor the canary rollout of the NewQRGenerationService
by making test API calls and checking system health and metrics.

Usage:
    docker-compose exec api python /app/scripts/monitor_canary_rollout.py
"""

import json
import random
import string
import time
from datetime import datetime
import logging
import httpx
from typing import Dict, Any, Tuple, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("canary_monitor")

# Configuration
API_BASE_URL = "https://10.1.6.12"
ADMIN_USER = "admin_user"
ADMIN_PASSWORD = "strongpassword"
VERIFY_SSL = False  # Self-signed certificate


def make_authenticated_request(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Make an authenticated request to the API."""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    with httpx.Client(verify=VERIFY_SSL) as client:
        if method == "GET":
            response = client.get(url, auth=(ADMIN_USER, ADMIN_PASSWORD), headers=headers)
        elif method == "POST":
            response = client.post(url, auth=(ADMIN_USER, ADMIN_PASSWORD), headers=headers, json=data)
        elif method == "DELETE":
            response = client.delete(url, auth=(ADMIN_USER, ADMIN_PASSWORD), headers=headers)
        else:
            response = client.request(method, url, auth=(ADMIN_USER, ADMIN_PASSWORD), headers=headers, json=data)
    
    if response.status_code >= 400:
        logger.error(f"Request to {endpoint} failed with status {response.status_code}: {response.text}")
    
    return response.json() if response.status_code < 400 else {}


def get_health_status() -> Dict:
    """Get the current health status of the application."""
    return make_authenticated_request("/health")


def get_feature_flags() -> Dict:
    """Get the current feature flag settings."""
    return make_authenticated_request("/api/v1/admin/feature-flags")


def get_service_status() -> Dict:
    """Get the current service status."""
    return make_authenticated_request("/api/v1/admin/service-status")


def generate_random_content() -> str:
    """Generate random content for QR codes."""
    return "https://example.com/" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def create_static_qr() -> Tuple[Dict, float]:
    """Create a static QR code and measure execution time."""
    content = generate_random_content()
    data = {
        "title": f"Test Static QR {datetime.now().isoformat()}",
        "content": content,
        "error_correction": "M"
    }
    
    start_time = time.perf_counter()
    response = make_authenticated_request("/api/v1/qr/static", method="POST", data=data)
    execution_time = time.perf_counter() - start_time
    
    return response, execution_time


def create_dynamic_qr() -> Tuple[Dict, float]:
    """Create a dynamic QR code and measure execution time."""
    redirect_url = generate_random_content()
    data = {
        "title": f"Test Dynamic QR {datetime.now().isoformat()}",
        "target_url": redirect_url,
        "redirect_url": redirect_url,  # Using same URL for both fields
        "error_correction": "M"
    }
    
    start_time = time.perf_counter()
    response = make_authenticated_request("/api/v1/qr/dynamic", method="POST", data=data)
    execution_time = time.perf_counter() - start_time
    
    return response, execution_time


def generate_qr_image(qr_id: str, format: str = "png") -> Tuple[bool, float]:
    """Generate a QR code image and measure execution time."""
    start_time = time.perf_counter()
    
    with httpx.Client(verify=VERIFY_SSL) as client:
        response = client.get(
            f"{API_BASE_URL}/api/v1/qr/{qr_id}/image?format={format}",
            auth=(ADMIN_USER, ADMIN_PASSWORD)
        )
    
    execution_time = time.perf_counter() - start_time
    
    return response.status_code == 200, execution_time


def cleanup_qr(qr_id: str) -> bool:
    """Delete a QR code."""
    with httpx.Client(verify=VERIFY_SSL) as client:
        response = client.delete(
            f"{API_BASE_URL}/api/v1/qr/{qr_id}",
            auth=(ADMIN_USER, ADMIN_PASSWORD)
        )
    
    return response.status_code == 200


def generate_test_traffic(num_operations: int = 10) -> Dict[str, List[float]]:
    """
    Generate test traffic to measure performance of both paths.
    
    With canary testing enabled, some percentage of requests will go through
    the new path based on the CANARY_PERCENTAGE setting.
    """
    results = {
        "static_qr_times": [],
        "dynamic_qr_times": [],
        "image_generation_times": [],
        "qr_ids": []
    }
    
    for i in range(num_operations):
        # Create static QR
        static_qr, static_time = create_static_qr()
        results["static_qr_times"].append(static_time)
        if "id" in static_qr:
            results["qr_ids"].append(static_qr["id"])
            
            # Generate image for static QR
            success, image_time = generate_qr_image(static_qr["id"])
            if success:
                results["image_generation_times"].append(image_time)
        
        # Create dynamic QR
        dynamic_qr, dynamic_time = create_dynamic_qr()
        results["dynamic_qr_times"].append(dynamic_time)
        if "id" in dynamic_qr:
            results["qr_ids"].append(dynamic_qr["id"])
            
            # Generate image for dynamic QR
            success, image_time = generate_qr_image(dynamic_qr["id"])
            if success:
                results["image_generation_times"].append(image_time)
    
    return results


def cleanup_test_resources(qr_ids: List[str]) -> None:
    """Clean up test resources."""
    logger.info(f"Cleaning up {len(qr_ids)} QR codes...")
    for qr_id in qr_ids:
        cleanup_qr(qr_id)


def print_divider(char: str = "-", length: int = 80) -> None:
    """Print a divider line."""
    print(char * length)


def calculate_statistics(times: List[float]) -> Dict[str, float]:
    """Calculate statistics for a list of execution times."""
    if not times:
        return {"count": 0, "min": 0, "max": 0, "avg": 0}
    
    return {
        "count": len(times),
        "min": min(times) * 1000,  # Convert to ms
        "max": max(times) * 1000,  # Convert to ms
        "avg": (sum(times) / len(times)) * 1000  # Convert to ms
    }


def main() -> None:
    """Main function to monitor canary rollout."""
    print_divider("=")
    print(f"CANARY ROLLOUT MONITORING - Task 1.5 - {datetime.now().isoformat()}")
    print_divider("=")
    
    # Check health status
    print("\n[1] Checking system health status...")
    health = get_health_status()
    print(f"  System Status: {health.get('status', 'unknown')}")
    print(f"  Memory Usage: {health.get('system_metrics', {}).get('memory_usage', 'unknown')}%")
    print(f"  Disk Usage: {health.get('system_metrics', {}).get('disk_usage', 'unknown')}%")
    print(f"  Database Status: {health.get('checks', {}).get('database', {}).get('status', 'unknown')}")
    
    # Check feature flags
    print("\n[2] Checking feature flags and canary settings...")
    flags = get_feature_flags()
    canary_enabled = flags.get("canary_testing", {}).get("CANARY_TESTING_ENABLED", False)
    canary_percentage = flags.get("canary_testing", {}).get("CANARY_PERCENTAGE", 0)
    qr_service_enabled = flags.get("observatory_first_flags", {}).get("USE_NEW_QR_GENERATION_SERVICE", False)
    
    print(f"  Canary Testing: {'ENABLED' if canary_enabled else 'DISABLED'}")
    print(f"  Canary Percentage: {canary_percentage}%")
    print(f"  New QR Generation Service: {'ENABLED' if qr_service_enabled else 'DISABLED'}")
    
    # Generate test traffic
    print("\n[3] Generating test traffic to measure performance...")
    num_operations = 20
    print(f"  Executing {num_operations} operations for each API endpoint...")
    
    results = generate_test_traffic(num_operations)
    
    # Calculate statistics
    static_stats = calculate_statistics(results["static_qr_times"])
    dynamic_stats = calculate_statistics(results["dynamic_qr_times"])
    image_stats = calculate_statistics(results["image_generation_times"])
    
    print("\n[4] Performance Statistics:")
    print(f"  Static QR Creation: {static_stats['count']} operations")
    print(f"    Min: {static_stats['min']:.2f}ms, Max: {static_stats['max']:.2f}ms, Avg: {static_stats['avg']:.2f}ms")
    
    print(f"  Dynamic QR Creation: {dynamic_stats['count']} operations")
    print(f"    Min: {dynamic_stats['min']:.2f}ms, Max: {dynamic_stats['max']:.2f}ms, Avg: {dynamic_stats['avg']:.2f}ms")
    
    print(f"  Image Generation: {image_stats['count']} operations")
    print(f"    Min: {image_stats['min']:.2f}ms, Max: {image_stats['max']:.2f}ms, Avg: {image_stats['avg']:.2f}ms")
    
    # Clean up test resources
    print("\n[5] Cleaning up test resources...")
    cleanup_test_resources(results["qr_ids"])
    print(f"  {len(results['qr_ids'])} QR codes deleted successfully")
    
    print_divider("=")
    print(f"CANARY ROLLOUT MONITORING COMPLETE - {datetime.now().isoformat()}")
    print(f"With {canary_percentage}% canary traffic, approximately {int(num_operations * canary_percentage / 100)} requests")
    print(f"should have gone through the new QR generation service path.")
    print_divider("=")


if __name__ == "__main__":
    main() 