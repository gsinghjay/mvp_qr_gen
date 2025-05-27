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


def generate_image_expect_fallback_or_initial_failure(qr_id: str, call_number: int, expect_success_old_path: bool):
    print(f"--- Attempt {call_number}: Generating image for QR ID {qr_id} ---")
    image_params = {"image_format": "png", "size": "10"}
    try:
        response_image = client.get(f"/api/v1/qr/{qr_id}/image", params=image_params)
        if expect_success_old_path:
            response_image.raise_for_status()  # Should succeed via old path
            assert response_image.headers["content-type"] == "image/png"
            print(f"SUCCESS (Fallback to Old Path): Generated image for QR ID {qr_id}.")
        else:  # Initial calls that should fail on new path
            # We expect a 500 if the new path fails and the old path is then tried *within the same request context of generate_qr*.
            # The circuit breaker itself will make the *next* call go to old path directly.
            print(f"EXPECTED FAILURE (New Path): Status {response_image.status_code} for QR ID {qr_id}.")
            assert response_image.status_code >= 500  # Or specific error from forced failure
    except httpx.HTTPStatusError as e:
        if expect_success_old_path:
            print(f"ERROR (Fallback): API call failed unexpectedly: {e.response.status_code} - {e.response.text}")
            assert False
        else:
            print(f"EXPECTED FAILURE (New Path): Status {e.response.status_code} for QR ID {qr_id}.")
            assert e.response.status_code >= 500  # Or specific error
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        assert False


def test_circuit_breaker_opens_and_falls_back():
    print("\n--- Testing Circuit Breaker Opens & Falls Back ---")
    print("IMPORTANT: Manually ensure NewQRGenerationService is modified to always fail for this test.")
    
    # Print circuit breaker configuration
    fail_max = int(os.getenv("QR_GENERATION_CB_FAIL_MAX", "2"))
    reset_timeout = int(os.getenv("QR_GENERATION_CB_RESET_TIMEOUT", "60"))
    print(f"\nCircuit Breaker Configuration:")
    print(f"- FAIL_MAX: {fail_max}")
    print(f"- RESET_TIMEOUT: {reset_timeout}")
    
    # First, create a QR code to test image generation against
    static_payload = {
        "content": f"CB Test QR {time.time()}", 
        "title": "CB Test Static",
        "error_level": "m"  # Lowercase error level
    }
    response_create = client.post("/api/v1/qr/static", json=static_payload)
    if response_create.status_code >= 400:
        print(f"CRITICAL ERROR: Failed to create a base QR for CB test: {response_create.text}")
        return
    qr_id = response_create.json()['id']
    print(f"Using QR ID: {qr_id} for CB test")

    # Calls to trigger failures on the new path
    for i in range(fail_max):
        generate_image_expect_fallback_or_initial_failure(qr_id, i + 1, expect_success_old_path=True)
        time.sleep(0.5)  # Small delay

    print(f"--- After {fail_max} failures, circuit should be OPEN ---")
    
    # This call should now immediately fallback to old path due to open circuit
    generate_image_expect_fallback_or_initial_failure(qr_id, fail_max + 1, expect_success_old_path=True)
    generate_image_expect_fallback_or_initial_failure(qr_id, fail_max + 2, expect_success_old_path=True)

    # Print verification instructions
    print("VERIFY IN GRAFANA:")
    print(f"  - `app_circuit_breaker_failures_total{{service=\"NewQRGenerationService\", operation=\"qr_generation\"}}` should be >= {fail_max}.")
    print("  - `app_circuit_breaker_state_enum{service=\"NewQRGenerationService\", operation=\"qr_generation\"}` should be 1 (Open).")
    print("  - `app_circuit_breaker_fallbacks_total{service=\"NewQRGenerationService\", operation=\"generate_qr\", reason=\"exception\"}` should increment for each call.")
    print("  - `qr_generation_path_total{path=\"new\", operation=\"generate_qr_image\", status=\"failure\"}` should have counts matching the failures.")
    print("  - `qr_generation_path_total{path=\"old\", operation=\"generate_qr_image\", status=\"success\"}` should have counts for all successful fallbacks.")
    print("-------------------------------------------------")
    print("REMEMBER: Revert the forced failure in NewQRGenerationService and restart API.")


def test_circuit_breaker_resets_and_closes():
    print("\n--- Testing Circuit Breaker Resets & Closes ---")
    print("IMPORTANT: Follow manual steps for this test carefully.")
    
    static_payload = {
        "content": f"CB Reset Test QR {time.time()}", 
        "title": "CB Reset Static",
        "error_level": "m"  # Lowercase error level
    }
    response_create = client.post("/api/v1/qr/static", json=static_payload)
    if response_create.status_code >= 400:
        print(f"CRITICAL ERROR: Failed to create a base QR for CB reset test: {response_create.text}")
        return
    qr_id = response_create.json()['id']
    print(f"Using QR ID: {qr_id} for CB reset test")

    fail_max = int(os.getenv("QR_GENERATION_CB_FAIL_MAX", "2"))
    reset_timeout = int(os.getenv("QR_GENERATION_CB_RESET_TIMEOUT", "10"))

    print(f"1. Manually ensure NewQRGenerationService will FAIL. Restart API.")
    input("Press Enter after configuring service to fail and restarting API...")

    # Trip the breaker
    for i in range(fail_max):
        generate_image_expect_fallback_or_initial_failure(qr_id, i + 1, expect_success_old_path=True)
        time.sleep(0.5)
    print("Circuit should now be OPEN.")
    
    print(f"2. Waiting for {reset_timeout + 5} seconds for CB to enter HALF-OPEN...")
    time.sleep(reset_timeout + 5)

    print(f"3. Manually ensure NewQRGenerationService will SUCCEED NOW. Revert changes and restart API.")
    input("Press Enter after configuring service to succeed and restarting API...")
    
    # This call should go to the new path (HALF-OPEN state), succeed, and close the circuit.
    print(f"--- Attempting call in expected HALF-OPEN state for QR ID {qr_id} ---")
    image_params = {"image_format": "png", "size": "10"}
    try:
        response_image = client.get(f"/api/v1/qr/{qr_id}/image", params=image_params)
        response_image.raise_for_status()  # Should succeed via new path
        assert response_image.headers["content-type"] == "image/png"
        print(f"SUCCESS (New Path in Half-Open/Closed): Generated image for QR ID {qr_id}.")
    except Exception as e:
        print(f"ERROR (Half-Open/Closed): API call failed unexpectedly: {e}")
        assert False  # This call should succeed

    print("--- Attempting another call, circuit should be CLOSED ---")
    try:
        response_image = client.get(f"/api/v1/qr/{qr_id}/image", params=image_params)
        response_image.raise_for_status()  # Should succeed via new path
        assert response_image.headers["content-type"] == "image/png"
        print(f"SUCCESS (New Path, Circuit Closed): Generated image for QR ID {qr_id}.")
    except Exception as e:
        print(f"ERROR (Closed): API call failed unexpectedly: {e}")
        assert False

    print("VERIFY IN GRAFANA:")
    print(f"  - `app_circuit_breaker_state_enum` should have transitioned OPEN -> HALF_OPEN -> CLOSED.")
    print(f"  - `qr_generation_path_total{{path=\"new\", operation=\"generate_qr_image\", status=\"success\"}}` should show new successful calls.")
    print("-------------------------------------------------")


if __name__ == "__main__":
    print(f"Running circuit breaker tests against {API_BASE_URL}")
    print("\nIMPORTANT: Testing the circuit breaker requires manual modification of the code.")
    print("You need to modify the NewQRGenerationService to force failures for testing.")
    print("Follow these steps:")
    print("1. Edit app/services/new_qr_generation_service.py to add a forced failure")
    print("2. Add a line like: raise RuntimeError('Forced E2E Test Failure')")
    print("3. IMPORTANT: Since we refactored to use async methods, add the failure to")
    print("   one of the async methods that is called by the API endpoints, such as:")
    print("   - generate_qr_async")
    print("   - format_qr_image_async")
    print("   (The create_and_format_qr_sync method has been removed)")
    print("4. Restart the API container: docker-compose restart api")
    print("5. Run the test_circuit_breaker_opens_and_falls_back function")
    print("6. After testing, remember to revert your changes and restart the API")
    print("\nTo run a test, uncomment one of the test functions below:")
    # test_circuit_breaker_opens_and_falls_back()
    # test_circuit_breaker_resets_and_closes() 