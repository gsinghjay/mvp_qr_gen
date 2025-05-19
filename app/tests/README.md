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

## Test Infrastructure

### Test Database Configuration

The test suite uses a dedicated PostgreSQL database separate from the production database:

1. **Schema Management with Alembic**: 
   - Test database schema is created using Alembic migrations to ensure it exactly matches production schema
   - The `setup_test_database` fixture in `conftest.py` runs `alembic upgrade head` to create the schema

2. **Transaction Isolation**: 
   - Each test runs in its own transaction that gets rolled back at the end
   - The `test_db` fixture manages this transaction isolation
   - Prevents tests from interfering with each other's data

3. **Docker Integration**:
   - Dedicated `postgres_test` service in Docker Compose provides isolated test database
   - Environment variables (`TEST_DATABASE_URL`, etc.) configure the test database connection

### Test Data Management

1. **Factory Pattern**:
   - Test data is created using the factory pattern via classes in `factories.py`
   - `QRCodeFactory` provides methods to create both static and dynamic QR codes
   - Factory methods allow customizing attributes while using sensible defaults

2. **Fixtures Using Factories**:
   - Fixtures in `conftest.py` use the factory pattern to create test entities
   - Common entity types (static QR, dynamic QR, etc.) have dedicated fixtures
   - Factories only add entities to the session without committing or flushing, letting the test fixture manage transactions

3. **Transaction Management**:
   - All test data is created within a transaction that is rolled back after the test
   - Factories don't flush or commit changes, letting the test fixtures control transaction boundaries
   - This ensures test data doesn't persist beyond the test and tests remain isolated

### Asynchronous Testing Support

1. **Async Session Fixtures**:
   - `async_test_db` fixture provides an async SQLAlchemy session
   - Uses nested transactions for test isolation similar to the sync version
   - Automatically rolls back changes after each test

2. **Async Client Fixture**:
   - `async_client` fixture configures a test client with async database overrides
   - Overrides async dependencies to use the test database session
   - Works with pytest-asyncio for true async tests

3. **Async Factory Methods**:
   - `QRCodeFactory` provides async methods for async test contexts
   - `async_create_with_params` and `async_create_batch_mixed` support async tests
   - See `test_async_example.py` for examples of async testing patterns

## Test Fixtures

The `conftest.py` file provides common fixtures that should be used across tests:

### Database Fixtures

- `test_db`: Provides an isolated database session within a transaction
- `async_test_db`: Provides an isolated async database session for async tests
- `seeded_db`: Provides a database pre-populated with test data

### Factory Fixtures

- `qr_code_factory`: Provides a configured `QRCodeFactory` instance for creating custom QR codes
- `async_qr_code_factory`: Provides a configured `QRCodeFactory` for async tests

### QR Code Fixtures

- `static_qr`: Creates a standard static QR code
- `dynamic_qr`: Creates a standard dynamic QR code
- `scanned_qr`: Creates a QR code with scan history
- `colored_qr`: Creates a QR code with custom colors
- `historical_qr`: Creates an older QR code for date filtering tests

### API Fixtures

- `client`: Provides a FastAPI TestClient with dependency overrides configured
  - Overrides `get_db` and `get_db_with_logging` to use the test database session
  - Automatically restores original dependencies after tests
- `async_client`: Provides a TestClient configured for async tests
  - Overrides async dependencies to use the async test database session
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

## Dependency Overrides

Tests use a standardized approach to dependency overrides:

1. **Client Fixture Method**:
   - The `client` fixture in `conftest.py` handles all necessary dependency overrides
   - Overrides both `get_db` and `get_db_with_logging` to ensure all database access uses test sessions
   - Stores and restores original dependencies to prevent cross-test interference
   - Example usage:
     ```python
     def test_create_qr(client, static_qr_payload):
         response = client.post("/api/v1/qr/", json=static_qr_payload)
         assert response.status_code == 201
     ```

2. **DependencyOverrideManager** (for advanced scenarios):
   - For tests requiring more complex dependency overrides, use the `DependencyOverrideManager` in `helpers.py`
   - Can be used as a context manager to apply overrides within a specific test scope
   - Example usage:
     ```python
     from app.tests.helpers import DependencyOverrideManager
     
     def test_special_case(test_db):
         with DependencyOverrideManager.create_db_override(app, test_db) as override:
             # Add additional overrides if needed
             override.override(get_settings, lambda: test_settings)
             
             # Test code here
             client = TestClient(app)
             response = client.get("/api/v1/special")
             # The overrides are automatically restored after the context manager exits
     ```

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

7. **Use factories for test data**:
   ```python
   # Let fixtures provide standard entities
   def test_standard_qr(client, static_qr):
       response = client.get(f"/api/v1/qr/{static_qr.id}")
       assert response.status_code == 200
   
   # Use factory directly for custom scenarios
   def test_custom_qr(client, qr_code_factory):
       special_qr = qr_code_factory.create_static(
           content="https://special.example.com",
           title="Special Test QR",
           size=15
       )
       response = client.get(f"/api/v1/qr/{special_qr.id}")
       assert response.status_code == 200
   ```

8. **Use async features for async code**:
   ```python
   # For async endpoints or services, use async fixtures
   @pytest.mark.asyncio
   async def test_async_feature(async_client, async_qr_code_factory):
       # Create test data asynchronously
       qr = await async_qr_code_factory.async_create_with_params(
           qr_type=QRType.DYNAMIC,
           redirect_url="https://example.com/async"
       )
       
       # Test the endpoint
       response = async_client.get(f"/api/v1/qr/{qr.id}")
       assert response.status_code == 200
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

## CI/CD Integration

The CI/CD pipeline is configured to run tests against the dedicated test database:

1. **Environment Setup**:
   - The `postgres_test` service is started in Docker Compose
   - `TEST_DATABASE_URL` and `TESTING_MODE=true` environment variables are set

2. **Test Execution**:
   - Alembic runs migrations to set up the test database schema
   - Pytest runs the test suite against the isolated test database
   - Test transactions are rolled back to keep the database clean

3. **Test Reports**:
   - Test coverage reports are generated
   - Test failures are reported in the CI/CD logs

## Troubleshooting

### Common Issues

1. **Test database connection issues**:
   - Ensure the `postgres_test` service is running in Docker Compose
   - Check that `TEST_DATABASE_URL` is correctly configured
   - Verify that the `TESTING_MODE=true` environment variable is set

2. **Failing assertions**: If tests are failing with assertion errors, use the verbose flag to see detailed output:
   ```bash
   docker compose exec api pytest app/tests/test_failing.py -v
   ```

3. **Test interference**: If tests interfere with each other, they may not be properly isolated.
   - Make sure tests don't commit transactions directly (let the fixtures handle it)
   - Use factory methods that don't flush to the database
   - Ensure all tests use the `test_db` fixture for database operations

4. **Slow tests**: If tests are running slowly, identify and optimize the bottlenecks.
   - Use session-scoped fixtures for expensive setup operations
   - Consider if some tests can be unit tests without database interaction

## Maintenance

- Keep this documentation up to date when adding new fixtures or utilities
- Regularly review tests for duplication and refactor as needed
- Monitor test coverage and add tests for uncovered code
- Update tests when requirements or code changes 

## Usage Examples

### Basic Test with Database

```python
def test_qr_code_creation(test_db, qr_code_factory):
    """Test creating a QR code with the factory."""
    # Create a QR code using the factory
    qr = qr_code_factory.create_with_params(
        qr_type=QRType.STATIC,
        content="https://example.com",
        fill_color="#FF0000",
        back_color="#0000FF"
    )
    
    # Verify the QR code was created properly
    assert qr.id is not None
    assert qr.content == "https://example.com"
    assert qr.qr_type == "static"
    assert qr.fill_color == "#FF0000"
    assert qr.back_color == "#0000FF"
    
    # Verify it was added to the database
    result = test_db.execute(select(QRCode).where(QRCode.id == qr.id))
    db_qr = result.scalar_one_or_none()
    assert db_qr is not None
    assert db_qr.id == qr.id
```

### Advanced Test with API Client

```python
def test_api_integration(client, qr_code_factory):
    """Test API integration with pre-created data."""
    # Create a QR code for testing
    qr = qr_code_factory.create_with_params(
        qr_type=QRType.STATIC,
        content="https://example.com/test",
        title="Test QR",
        description="A test QR code"
    )
    
    # Use the client to retrieve the QR code
    response = client.get(f"/api/v1/qr/{qr.id}")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == qr.id
    assert data["content"] == "https://example.com/test"
    assert data["title"] == "Test QR"
```

## Known Issues and Limitations

### Asynchronous Testing

The test infrastructure includes support for asynchronous testing with pytest-asyncio, but there are some known limitations:

1. **Timezone Issues with asyncpg**: There are issues with PostgreSQL's asyncpg driver when handling timezone-aware vs naive datetimes. The current implementation includes a workaround that converts aware datetimes to naive ones, but this is an area that needs further improvement.

2. **Async API Tests**: The async API client tests are currently skipped in `test_async_example.py` due to dependency resolution issues. These need to be addressed in a future update.

3. **Example File**: An example file `test_async_example.py` shows how to structure async tests but contains skipped tests that serve as templates for future implementation.

### Async Test Strategy:

Until the above issues are resolved, the recommended approach for testing async code is:

1. Use the regular synchronous test fixtures for most tests
2. Only use async fixtures when testing code that requires async/await patterns
3. Convert timezone-aware datetime objects to naive ones before storing in the database
4. Be aware that transaction management might behave differently between sync and async tests 