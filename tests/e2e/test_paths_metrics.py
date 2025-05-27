import httpx
import time
import os

API_BASE_URL = os.getenv("E2E_API_BASE_URL", "http://localhost:80")
print(f"Using API base URL: {API_BASE_URL}")

# For HTTPS with self-signed certs:
client = httpx.Client(
    base_url=API_BASE_URL, 
    verify=False,  # Disable SSL verification for self-signed certs
    auth=("admin_user", "strongpassword")  # Add basic auth
)

def test_create_static_qr_new_path():
    """Test creation of a static QR code via new path"""
    print("\n--- Testing Static QR Creation (New Path) ---")
    payload = {
        "content": f"Test Static QR New Path {time.time()}",
        "title": "E2E Test New Static",
        "error_level": "m"  # Changed to lowercase
    }
    try:
        response = client.post("/api/v1/qr/static", json=payload)
        response.raise_for_status()
        qr_data = response.json()
        print(f"SUCCESS: Created static QR (New Path): ID {qr_data['id']}")
        assert qr_data["content"] == payload["content"]
        return qr_data["id"]
    except httpx.HTTPStatusError as e:
        print(f"ERROR: API call failed: {e.response.status_code} - {e.response.text}")
        assert False
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        assert False
    
    print("VERIFY IN GRAFANA: `qr_generation_path_total{path=\"new\", operation=\"create_static_qr\", status=\"success\"}` should increment.")
    print("VERIFY IN GRAFANA: `qr_generation_path_duration_seconds{path=\"new\", operation=\"create_static_qr\"}` should have new observations.")

def test_create_static_qr_old_path():
    """Test creation of a static QR code via old path"""
    print("\n--- Testing Static QR Creation (Old Path) ---")
    payload = {
        "content": f"Test Static QR Old Path {time.time()}",
        "title": "E2E Test Old Static",
        "error_level": "m"  # Changed to lowercase
    }
    try:
        response = client.post("/api/v1/qr/static", json=payload)
        response.raise_for_status()
        qr_data = response.json()
        print(f"SUCCESS: Created static QR (Old Path): ID {qr_data['id']}")
        assert qr_data["content"] == payload["content"]
        return qr_data["id"]
    except httpx.HTTPStatusError as e:
        print(f"ERROR: API call failed: {e.response.status_code} - {e.response.text}")
        assert False
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        assert False

    print("VERIFY IN GRAFANA: `qr_generation_path_total{path=\"old\", operation=\"create_static_qr\", status=\"success\"}` should increment.")
    print("VERIFY IN GRAFANA: `qr_generation_path_duration_seconds{path=\"old\", operation=\"create_static_qr\"}` should have new observations.")

def test_dynamic_qr_and_image_new_path():
    """Test dynamic QR creation and image generation via new path"""
    print("\n--- Testing Dynamic QR & Image (New Path) ---")
    qr_id = None
    # 1. Create Dynamic QR
    payload_create = {
        "redirect_url": f"https://example.com/new-path-test-{time.time()}",
        "title": "E2E Test New Dynamic",
        "error_level": "h"  # Changed to lowercase
    }
    try:
        response_create = client.post("/api/v1/qr/dynamic", json=payload_create)
        response_create.raise_for_status()
        qr_data = response_create.json()
        qr_id = qr_data.get("id")
        print(f"SUCCESS: Created dynamic QR (New Path): ID {qr_id}")
        assert qr_data["redirect_url"] == payload_create["redirect_url"]
    except httpx.HTTPStatusError as e:
        print(f"ERROR (Create): API call failed: {e.response.status_code} - {e.response.text}")
        assert False
    except Exception as e:
        print(f"ERROR (Create): An unexpected error occurred: {e}")
        assert False
    
    if not qr_id:
        return

    # 2. Generate Image (PNG with logo)
    print(f"--- Generating image for QR ID {qr_id} (New Path) ---")
    image_params = {
        "image_format": "png",
        "include_logo": "true", # Must be string for query params
        "size": "15" # Relative size
    }
    try:
        response_image = client.get(f"/api/v1/qr/{qr_id}/image", params=image_params)
        response_image.raise_for_status()
        assert response_image.headers["content-type"] == "image/png"
        print(f"SUCCESS: Generated PNG image with logo (New Path) for QR ID {qr_id}. Size: {len(response_image.content)} bytes.")
    except httpx.HTTPStatusError as e:
        print(f"ERROR (Image): API call failed: {e.response.status_code} - {e.response.text}")
        assert False
    except Exception as e:
        print(f"ERROR (Image): An unexpected error occurred: {e}")
        assert False

    print("VERIFY IN GRAFANA (Create): `qr_generation_path_total{path=\"new\", operation=\"create_dynamic_qr\", status=\"success\"}` should increment.")
    print("VERIFY IN GRAFANA (Image): `qr_generation_path_total{path=\"new\", operation=\"generate_qr_image\", status=\"success\"}` should increment.")

def test_dynamic_qr_and_image_old_path():
    """Test dynamic QR creation and image generation via old path"""
    print("\n--- Testing Dynamic QR & Image (Old Path) ---")
    qr_id = None
    # 1. Create Dynamic QR
    payload_create = {
        "redirect_url": f"https://example.com/old-path-test-{time.time()}",
        "title": "E2E Test Old Dynamic",
        "error_level": "h"  # Changed to lowercase
    }
    try:
        response_create = client.post("/api/v1/qr/dynamic", json=payload_create)
        response_create.raise_for_status()
        qr_data = response_create.json()
        qr_id = qr_data.get("id")
        print(f"SUCCESS: Created dynamic QR (Old Path): ID {qr_id}")
        assert qr_data["redirect_url"] == payload_create["redirect_url"]
    except httpx.HTTPStatusError as e:
        print(f"ERROR (Create): API call failed: {e.response.status_code} - {e.response.text}")
        assert False
    except Exception as e:
        print(f"ERROR (Create): An unexpected error occurred: {e}")
        assert False
    
    if not qr_id:
        return

    # 2. Generate Image (PNG with logo)
    print(f"--- Generating image for QR ID {qr_id} (Old Path) ---")
    image_params = {
        "image_format": "png",
        "include_logo": "true", # Must be string for query params
        "size": "15" # Relative size
    }
    try:
        response_image = client.get(f"/api/v1/qr/{qr_id}/image", params=image_params)
        response_image.raise_for_status()
        assert response_image.headers["content-type"] == "image/png"
        print(f"SUCCESS: Generated PNG image with logo (Old Path) for QR ID {qr_id}. Size: {len(response_image.content)} bytes.")
    except httpx.HTTPStatusError as e:
        print(f"ERROR (Image): API call failed: {e.response.status_code} - {e.response.text}")
        assert False
    except Exception as e:
        print(f"ERROR (Image): An unexpected error occurred: {e}")
        assert False

    print("VERIFY IN GRAFANA (Create): `qr_generation_path_total{path=\"old\", operation=\"create_dynamic_qr\", status=\"success\"}` should increment.")
    print("VERIFY IN GRAFANA (Image): `qr_generation_path_total{path=\"old\", operation=\"generate_qr_image\", status=\"success\"}` should increment.")

if __name__ == "__main__":
    print(f"Running path-specific metrics tests against {API_BASE_URL}")
    print("\nNOTE: Ensure .env has the correct feature flag settings before running each test:")
    print("For new path: USE_NEW_QR_GENERATION_SERVICE=True and CANARY_PERCENTAGE=100 if enabled")
    print("For old path: USE_NEW_QR_GENERATION_SERVICE=False")
    
    # With current settings (USE_NEW_QR_GENERATION_SERVICE=True, CANARY_TESTING_ENABLED=True, CANARY_PERCENTAGE=5)
    # we should see a mix of old and new path usage
    
    # Test both paths:
    print("\n--- TESTING NEW PATH (should hit new implementation occasionally based on canary %) ---")
    test_create_static_qr_new_path()
    test_dynamic_qr_and_image_new_path()
    
    print("\n--- TESTING OLD PATH (should hit old implementation most of the time based on canary %) ---")
    test_create_static_qr_old_path()
    test_dynamic_qr_and_image_old_path()
    
    print("\nTests completed. Verify metrics in Grafana dashboard qr-refactoring-detailed.json to see the path distribution.") 