# QR Code Generator Testing Documentation

This document outlines the testing strategy, organization, and best practices for the QR code generator application.

## Test Organization

The tests are organized according to the following structure:

```
app/tests/
├── conftest.py             # Test fixtures and configuration
├── factories.py            # Test data factories
├── helpers.py              # Test helper classes and functions
├── utils.py                # Test assertion utilities
├── README.md               # This documentation file
├── test_main.py            # API endpoint integration tests
├── test_integration.py     # End-to-end integration tests
├── test_middleware.py      # Middleware specific tests
├── test_background_tasks.py # Background task tests
├── test_qr_service.py      # Service layer unit tests
├── test_response_models.py # Response model validation tests
├── test_validation_parameterized.py # Parameterized validation tests
```

### Purpose of Test Files

* **test_main.py**: Tests all FastAPI endpoints directly, focusing on HTTP aspects and API behavior
* **test_integration.py**: End-to-end tests that verify complete application workflows
* **test_middleware.py**: Tests middleware components in isolation and how they transform requests/responses
* **test_background_tasks.py**: Tests asynchronous background task processing 
* **test_qr_service.py**: Unit tests for the service layer business logic without API concerns
* **test_response_models.py**: Tests that focus specifically on response model validation
* **test_validation_parameterized.py**: Tests input validation using parameterized test cases for efficiency

## Testing Levels

Our testing strategy includes multiple levels of testing:

1. **Unit Tests**: Test individual components in isolation
   - Located in files like `test_qr_service.py`
   - Focus on testing business logic independently

2. **Integration Tests**: Test multiple components working together
   - Located in files like `test_main.py`
   - Test API endpoints and database interactions

3. **End-to-End Tests**: Test the complete application flow
   - Located in `test_integration.py`
   - Test entire user workflows from request to response

## Testing Principles

### DRY (Don't Repeat Yourself)

- Use fixtures from `conftest.py` instead of duplicating setup code
- Use utility functions in `utils.py` for common assertions
- Use parameterized tests for repetitive test cases

### Isolation

- Tests should be independent of each other
- Use database transaction isolation to prevent test interference
- Reset state between tests

### Comprehensive Coverage

- Test both happy paths and error scenarios
- Test edge cases and boundary conditions
- Test validation logic thoroughly

## Test Fixtures

The `conftest.py` file provides common fixtures that should be used across tests:

### Database Fixtures

- `test_db`: Provides an isolated database session
- `async_test_db`: Provides an isolated async database session
- `seeded_db`: Provides a database pre-populated with test data

### QR Code Fixtures

- `static_qr`: Creates a standard static QR code
- `dynamic_qr`: Creates a standard dynamic QR code
- `scanned_qr`: Creates a QR code with scan history
- `colored_qr`: Creates a QR code with custom colors
- `historical_qr`: Creates an older QR code for date filtering tests

### API Fixtures

- `client`: Provides a FastAPI TestClient
- `create_static_qr_request`: Function for creating static QR codes
- `create_dynamic_qr_request`: Function for creating dynamic QR codes
- `get_qr_request`: Function for retrieving QR codes
- `update_qr_request`: Function for updating QR codes
- `list_qr_request`: Function for listing QR codes
- `redirect_qr_request`: Function for testing redirects

### Payload Fixtures

- `static_qr_payload`: Standard payload for static QR code creation
- `dynamic_qr_payload`: Standard payload for dynamic QR code creation
- `invalid_color_payload`: Payload with invalid color for testing validation
- `invalid_url_payload`: Payload with invalid URL for testing validation

## Utility Functions

The `utils.py` file provides common utility functions for assertions and validations:

- `validate_qr_code_data`: Validate QR code data from API responses
- `validate_qr_code_list_response`: Validate list response structure
- `validate_error_response`: Validate error response structure
- `assert_successful_response`: Assert successful API response
- `assert_qr_code_in_db`: Assert QR code exists in database
- `assert_qr_redirects`: Assert QR code redirects correctly
- `assert_validation_error`: Assert validation error response
- `parameterize_test_cases`: Generate parameterized test cases
- `validate_color_code`: Validate hex color codes used in QR codes
- `validate_redirect_url`: Validate URLs for dynamic QR codes
- `validate_scan_statistics`: Validate QR code scan statistics data

## Best Practices

### Writing New Tests

1. **Use fixtures**: Always use fixtures for common setup:
   ```python
   def test_get_qr_code(client, static_qr):
       response = client.get(f"/api/v1/qr-codes/{static_qr.id}")
       assert response.status_code == 200
   ```

2. **Use utility functions**: Use utility functions for common assertions:
   ```python
   def test_create_qr_code(client, test_db, static_qr_payload):
       response = client.post("/api/v1/qr-codes/", json=static_qr_payload)
       data = assert_successful_response(response, status.HTTP_201_CREATED)
       validate_qr_code_data(data)
       assert_qr_code_in_db(test_db, data["id"])
   ```

3. **Test both success and failure cases**:
   ```python
   def test_update_nonexistent_qr(client):
       response = client.patch("/api/v1/qr-codes/nonexistent", json={"redirect_url": "https://example.com"})
       assert_successful_response(response, status.HTTP_404_NOT_FOUND)
   ```

4. **Use parameterized tests for multiple similar cases**:
   ```python
   @pytest.mark.parametrize("invalid_color", ["not-a-color", "rgb(255,0,0)", "#XYZ123"])
   def test_invalid_color(client, invalid_color):
       payload = static_qr_payload.copy()
       payload["fill_color"] = invalid_color
       response = client.post("/api/v1/qr-codes/", json=payload)
       assert_validation_error(response, field="fill_color")
   ```

5. **Add descriptive docstrings**:
   ```python
   def test_dynamic_qr_redirect():
       """Test that dynamic QR codes redirect to the correct URL and increment scan count."""
       # Test implementation...
   ```

6. **Separate API and service tests**:
   ```python
   # In test_main.py - Test API behavior
   def test_create_qr_api(client):
       """Test API endpoint for creating QR codes."""
       # Test HTTP aspects, status codes, and headers

   # In test_qr_service.py - Test service logic 
   def test_create_qr_service(test_db):
       """Test business logic for creating QR codes."""
       # Test internal logic and database operations
   ```

7. **Use validation utilities for consistent checking**:
   ```python
   # Instead of manually checking color format
   assert data["fill_color"].startswith("#")
   
   # Use the validation utility
   validate_color_code(data["fill_color"])
   
   # Instead of manually checking URL format
   assert data["redirect_url"].startswith(("http://", "https://"))
   
   # Use the validation utility
   validate_redirect_url(data["redirect_url"])
   
   # Instead of manual scan statistics validation
   assert isinstance(data["scan_count"], int)
   assert data["scan_count"] >= 0
   
   # Use the validation utility
   validate_scan_statistics({
       "scan_count": data["scan_count"],
       "last_scan_at": data.get("last_scan_at")
   })
   ```

### Test Naming Conventions

- Use descriptive test names that indicate what's being tested
- Follow the pattern: `test_<what>_<condition>`
- Examples:
  - `test_create_static_qr_success`
  - `test_update_qr_invalid_url`
  - `test_list_qr_pagination`

### Running Tests

Run tests using Docker with the following command:

```bash
docker compose exec api pytest --cov -v
```

For specific test files:

```bash
docker compose exec api pytest app/tests/test_main.py -v
```

For specific test cases:

```bash
docker compose exec api pytest app/tests/test_main.py::test_create_static_qr -v
```

## Test Development Workflow

When adding new features or fixing bugs, follow this workflow:

1. **Write failing tests first**: Create tests that validate the expected behavior
2. **Implement the feature or fix the bug**: Make the failing tests pass
3. **Refactor if needed**: Clean up the code without breaking tests
4. **Add edge cases and error condition tests**: Ensure robust behavior

For new tests, follow these guidelines:

1. **Choose the right test file**: Place your test in the appropriate file based on what you're testing
2. **Use existing fixtures**: Utilize fixtures from conftest.py rather than creating your own setup code
3. **Use utility functions**: Leverage utils.py for common validation patterns
4. **Follow naming conventions**: Name tests clearly as `test_<what>_<condition>`
5. **Add descriptive docstrings**: Explain what aspect of functionality is being tested
6. **Test both success and failure paths**: Don't just test the happy path
7. **Keep tests focused**: Test one thing per test function
8. **Maintain isolation**: Ensure tests don't affect each other

## Troubleshooting

### Common Issues

1. **Database locked errors**: This usually happens when tests don't clean up database connections properly.
   - Solution: Use the `test_db` fixture which handles transaction isolation.

2. **Failing assertions**: If tests are failing with assertion errors, use the verbose flag to see detailed output:
   ```bash
   docker compose exec api pytest app/tests/test_failing.py -v
   ```

3. **Test interference**: If tests interfere with each other, they may not be properly isolated.
   - Solution: Make sure tests don't share state outside of fixtures.

4. **Slow tests**: If tests are running slowly, identify and optimize the bottlenecks.
   - Use session-scoped fixtures for expensive setup operations
   - Use in-memory SQLite for tests that don't need file-based storage

## Maintenance

- Keep this documentation up to date when adding new fixtures or utilities
- Regularly review tests for duplication and refactor as needed
- Monitor test coverage and add tests for uncovered code
- Update tests when requirements or code changes 