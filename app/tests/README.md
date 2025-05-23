# QR Code Generator Testing Documentation

This document outlines the testing strategy, organization, and best practices for the QR code generator application.

## Testing Strategy

Our testing strategy follows a practical, value-driven approach:

1. **Integration Tests First**: We prioritize integration tests that verify multiple components working together, especially API endpoints and database interactions.
   - Integration tests provide higher business value by ensuring features work as expected from the user's perspective
   - Focus on covering core functionality and critical paths with integration tests
   - Aim for ~80-90% coverage using integration tests alone

2. **Unit Tests for Targeted Coverage**: We use unit tests to fill coverage gaps and test complex logic in isolation.
   - Unit tests supplement integration tests to achieve 100% coverage
   - Focus unit tests on edge cases, error handling, and business logic that's difficult to test through integration tests
   - Isolate components using mocks only when it provides clear testing benefits

3. **End-to-End Tests for Complete Workflows**: E2E tests verify the system works as a whole.
   - Focus on critical user journeys and workflows
   - Keep E2E test count low due to maintenance overhead

This approach balances practical test coverage with maintainability, avoiding excessive mocking while ensuring thorough test coverage.

## Test Organization

The tests are organized according to the following hierarchical structure:

```
app/tests/
├── integration/           # Integration tests that use real database connections
│   ├── api/               # API integration tests
│   │   └── v1/            # Tests for API v1 endpoints
│   └── repositories/      # Integration tests for repositories with real DB
├── unit/                  # Unit tests with mocked dependencies where appropriate
│   ├── services/          # Tests for service layer components
│   ├── repositories/      # Tests for repository layer components
│   └── utils/             # Tests for utility functions and helpers
├── e2e/                   # End-to-end tests simulating real user interactions
├── data/                  # Test data fixtures and sample data
├── conftest.py            # Pytest fixtures and configuration
├── dependencies.py        # Test-specific dependency injection functions
├── factories.py           # Test data factories using Factory Boy
├── helpers.py             # Test helper functions
├── utils.py               # Utility functions for testing
└── README.md              # This documentation file
```

### Test Categories

#### Integration Tests
- Located in `app/tests/integration/`
- Use a real test database connection
- Test multiple components working together
- Include API endpoint tests, repository tests with real database interaction
- **Primary focus** for achieving majority of test coverage

#### Unit Tests
- Located in `app/tests/unit/`
- Test components in isolation with appropriate mocks
- Focus on business logic in services, utility functions, and isolated repository behavior
- Used to **supplement integration tests** to reach 100% coverage

#### End-to-End Tests
- Located in `app/tests/e2e/`
- Simulate complete user workflows
- Test the application as a whole

**Note:** Currently there's an organizational inconsistency where some database integration tests are incorrectly placed in the `unit/repositories/` directory instead of `integration/repositories/`. This is a known issue that will be addressed in future refactoring.

## Testing Levels

Our testing strategy includes multiple levels of testing:

1. **Integration Tests**: Test multiple components working together
   - Located in `app/tests/integration/` directory
   - Test API endpoints and database interactions
   - Use the real test database
   - **Primary focus** for majority of test coverage

2. **Unit Tests**: Test individual components in isolation
   - Located in `app/tests/unit/` directory
   - Focus on testing business logic independently
   - Use mocks for external dependencies
   - Used to reach 100% coverage after integration tests

3. **End-to-End Tests**: Test the complete application flow
   - Located in `app/tests/e2e/` directory
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

1. **Centralized Dependency Configuration**:
   - All test dependencies are defined in `app/tests/dependencies.py`
   - Test-specific database sessions, repositories, and services are provided
   - These dependencies mirror the application's dependencies but use test-specific implementations

2. **Client Fixture Method**:
   - The `client` fixture in `conftest.py` handles all necessary dependency overrides
   - Overrides both `get_db` and `get_db_with_logging` to ensure all database access uses test sessions
   - Overrides `get_qr_repository` and `get_qr_service` to use test-specific implementations
   - Stores and restores original dependencies to prevent cross-test interference
   - Example usage:
     ```python
     def test_create_qr(client, static_qr_payload):
         response = client.post("/api/v1/qr/", json=static_qr_payload)
         assert response.status_code == 201
     ```

3. **Async Client Support**:
   - The `async_client` fixture provides similar overrides for async tests
   - Uses async database session and overrides async dependencies
   - Follows the same pattern as the synchronous client fixture
   - Example usage:
     ```python
     @pytest.mark.asyncio
     async def test_async_feature(async_client, async_test_db):
         response = await async_client.get("/api/v1/some-async-endpoint")
         assert response.status_code == 200
     ```

4. **DependencyOverrideManager** (for advanced scenarios):
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

## API Test Best Practices

Based on recent fixes to the QR code endpoint tests, here are essential best practices for API testing:

### Test Data Creation

1. **Prefer API-Based Entity Creation**
   - When testing API endpoints, create test entities through the API itself when possible
   - Use fixtures like `create_static_qr_request` and `create_dynamic_qr_request` that make actual API calls
   - This ensures entities exist in both the database and the API context

   ```python
   # Recommended - create through API
   def test_update_qr(client, create_static_qr_request):
       # First create a QR code through the API
       create_response = create_static_qr_request()
       assert create_response.status_code == 201
       qr_data = create_response.json()
       qr_id = qr_data["id"]
       
       # Now test the update operation
       response = client.put(f"/api/v1/qr/{qr_id}", json={"title": "Updated"})
       assert response.status_code == 200
   ```

2. **Factory Usage Considerations**
   - When using factories directly, be aware of transaction isolation
   - Factory-created objects may not be visible to API calls unless committed
   - If using factories, consider explicit commits, but be aware this breaks isolation

### HTTP Method Correctness

1. **Match API Implementation Methods**
   - Use the HTTP methods the API actually implements:
     - Use PUT (not PATCH) for updates if the API uses PUT
     - Consult API implementation or OpenAPI documentation to confirm
   
   ```python
   # Correct - Using PUT for updates as implemented in the API
   response = client.put(f"/api/v1/qr/{qr_id}", json=update_data)
   
   # Incorrect - Using PATCH when API implements PUT
   response = client.patch(f"/api/v1/qr/{qr_id}", json=update_data)  # Will return 405 Method Not Allowed
   ```

2. **Test Method Not Allowed**
   - Include tests that verify incorrect methods return 405 Method Not Allowed
   - This confirms API routing is properly configured

### Resilient Assertions

1. **Handle Non-Deterministic Behaviors**
   - For pagination tests, verify page sizes rather than exact page numbers
   - For sorting tests, verify the endpoint accepts sort parameters without asserting exact order
   - For search tests, verify specific items are found rather than exact result counts

   ```python
   # More resilient - verifies pages contain different items
   first_page_ids = [item["id"] for item in first_page_data["items"]]
   second_page_ids = [item["id"] for item in second_page_data["items"]]
   assert len(set(first_page_ids).intersection(set(second_page_ids))) == 0
   
   # Less resilient - assumes specific page numbering behavior
   assert data["page"] == 2  # Might not be consistent
   ```

2. **Image and File Testing**
   - For image endpoints, verify content type and non-empty response
   - Be flexible with format detection - some APIs may return different formats than requested
   
   ```python
   # Resilient image testing
   response = client.get(f"/api/v1/qr/{qr_id}/image?format=svg")
   assert response.status_code == 200
   assert "image/" in response.headers["content-type"]  # Any image type
   assert len(response.content) > 0  # Non-empty response
   ```

### Dependency Management

1. **Understanding Test Dependencies**
   - Be aware of how dependency injection is configured in `conftest.py`
   - The `client` fixture overrides dependencies to use test versions
   - Database fixtures control transaction isolation

2. **Correct Parameter Names**
   - Use the correct fixture names in test functions:
     - Use `test_db` not `test_db_session`
     - Use `size` parameter for `create_batch` not `count`
   
   ```python
   # Correct
   def test_function(client, test_db):
       # Test implementation
   
   # Factory usage
   qr_code_factory.create_batch(size=3, qr_type=QRType.STATIC.value)
   ```

These best practices should be followed when writing new API tests or refactoring existing ones to ensure consistent, reliable testing across the application. 