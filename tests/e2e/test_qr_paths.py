import httpx
import time
import os
import sys

API_BASE_URL = os.getenv("E2E_API_BASE_URL", "http://localhost:80")  # Traefik entry point
print(f"Using API base URL: {API_BASE_URL}")

# Get auth credentials from environment variables
AUTH_USER = os.getenv("AUTH_USER")
AUTH_PASS = os.getenv("AUTH_PASS")

# Check if credentials are set
if not AUTH_USER or not AUTH_PASS:
    print("ERROR: Authentication credentials not found in environment variables.")
    print("Please ensure AUTH_USER and AUTH_PASS are set in .env file.")
    sys.exit(1)

# For HTTPS with self-signed certificates:
client = httpx.Client(
    base_url=API_BASE_URL, 
    verify=False,  # Disable SSL verification for self-signed certs
    auth=(AUTH_USER, AUTH_PASS)  # Use environment variables for basic auth
)

def test_create_static_qr():
    """Test creation of a static QR code"""
    print("\n--- Testing Static QR Creation ---")
    payload = {
        "content": f"Test Static QR {time.time()}",
        "title": "E2E Test Static",
        "error_level": "m"
    }
    try:
        response = client.post("/api/v1/qr/static", json=payload)
        response.raise_for_status()
        qr_data = response.json()
        print(f"SUCCESS: Created static QR: ID {qr_data['id']}")
        assert qr_data["content"] == payload["content"]
        return qr_data["id"]
    except httpx.HTTPStatusError as e:
        print(f"ERROR: API call failed: {e.response.status_code} - {e.response.text}")
        assert False
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        assert False

def test_create_dynamic_qr():
    """Test creation of a dynamic QR code"""
    print("\n--- Testing Dynamic QR Creation ---")
    payload = {
        "redirect_url": f"https://example.com/test-{time.time()}",
        "title": "E2E Test Dynamic",
        "error_level": "h"
    }
    try:
        response = client.post("/api/v1/qr/dynamic", json=payload)
        response.raise_for_status()
        qr_data = response.json()
        print(f"SUCCESS: Created dynamic QR: ID {qr_data['id']}")
        assert qr_data["redirect_url"] == payload["redirect_url"]
        return qr_data["id"]
    except httpx.HTTPStatusError as e:
        print(f"ERROR: API call failed: {e.response.status_code} - {e.response.text}")
        assert False
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        assert False

def test_generate_qr_image(qr_id):
    """Test generation of QR code image"""
    print(f"\n--- Testing QR Image Generation for ID {qr_id} ---")
    image_params = {
        "image_format": "png",
        "include_logo": "true",
        "size": "15"
    }
    try:
        response = client.get(f"/api/v1/qr/{qr_id}/image", params=image_params)
        response.raise_for_status()
        assert response.headers["content-type"] == "image/png"
        print(f"SUCCESS: Generated PNG image with logo for QR ID {qr_id}. Size: {len(response.content)} bytes.")
        return True
    except httpx.HTTPStatusError as e:
        print(f"ERROR: API call failed: {e.response.status_code} - {e.response.text}")
        assert False
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        assert False

def test_redirect_dynamic_qr(short_id):
    """Test QR code redirection"""
    print(f"\n--- Testing QR Redirect for short_id {short_id} ---")
    try:
        response = client.get(f"/r/{short_id}", follow_redirects=False)
        assert 300 <= response.status_code < 400, "Expected a redirect status code"
        location = response.headers.get("location")
        print(f"SUCCESS: Redirect confirmed to URL: {location}")
        return location
    except httpx.HTTPStatusError as e:
        print(f"ERROR: API call failed: {e.response.status_code} - {e.response.text}")
        assert False
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        assert False

if __name__ == "__main__":
    print(f"Running e2e tests against {API_BASE_URL}")
    
    # Test static QR code creation
    static_qr_id = test_create_static_qr()
    if static_qr_id:
        test_generate_qr_image(static_qr_id)
    
    # Test dynamic QR code creation and redirection
    dynamic_qr_id = test_create_dynamic_qr()
    if dynamic_qr_id:
        test_generate_qr_image(dynamic_qr_id)
        # Extract short_id from API response or database
        # For now, simulate with placeholder
        # test_redirect_dynamic_qr(short_id)
    
    print("\nTests completed. Check Grafana dashboard for metrics verification.") 