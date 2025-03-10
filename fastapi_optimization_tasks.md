# FastAPI Optimization Tasks - Test Driven Development Implementation Plan

## Task 1: Implement Service-Based Dependency Injection
- [x] Write test cases for service layer functionality in `test_qr_service.py`
- [x] Define interface contracts and expected behavior through test assertions
- [x] Create stub service classes to make tests compile
- [x] Create a `services` directory in the app folder
- [x] Implement `qr_service.py` with service classes for QR code operations
- [x] Move database queries from controllers to service methods
- [x] Run tests and iterate until all tests pass
- [x] Write integration tests for updated dependency injection system
- [x] Update dependency injection in `dependencies.py` to provide services
- [x] Refactor API endpoints to use service objects instead of direct DB operations
- [x] Verify all tests still pass after refactoring
- [x] Run performance tests to verify no regression
- [x] **VERIFIED**: Implementation successfully tested with API endpoint tests
  - Service layer correctly processes QR code creation
  - Custom parameters like `fill_color` are properly handled
  - Consistent data structure with proper timestamps is returned

## Task 2: Implement Background Tasks for Scan Statistics
- [x] Write tests for background task processing in `test_background_tasks.py`
- [x] Design test cases to verify statistics are updated correctly
- [x] Mock background task execution to test isolation
- [x] Create test cases for performance improvement verification
- [x] Create a dedicated function for updating scan statistics
- [x] Write tests for timing to verify non-blocking behavior
- [x] Modify the redirect endpoint to accept FastAPI's `BackgroundTasks`
- [x] Implement background task for scan counts and timestamps
- [x] Add client IP and user agent tracking to background task
- [x] Add logging for background task failures
- [x] Run tests to verify redirects work faster and statistics are updated correctly
- [x] Benchmark response times to quantify the performance improvement
- [x] Add proper error handling for concurrent database access
- [x] Ensure proper timezone handling for timestamps
- [x] **VERIFIED**: Implementation successfully tested with API endpoint tests
  - Redirection is extremely fast (< 0.02s), confirming non-blocking behavior
  - Scan counts are properly updated in the background
  - Timestamp updates are handled correctly
  - The implementation successfully separates user-facing redirection from statistics tracking

## Task 3: Standardize Response Models for All Endpoints
- [x] Write test cases for response models validation in `test_response_models.py`
- [x] Define expected validation behaviors through test assertions
- [x] Test edge cases for parameter validation
- [x] Create parameter models for query string parameters
- [x] Write validation tests for enum types
- [x] Update endpoint function signatures to use these models
- [x] Implement and test proper response documentation
- [x] Add enum types for consistent validation (e.g., `ImageFormat`)
- [x] Run tests to verify validation behavior
- [x] Add and test detailed response examples in OpenAPI docs
- [x] Verify generated documentation is correct through automated tests
- [x] Implement integration tests to verify end-to-end behavior
- [x] **VERIFIED**: Implementation successfully tested with API endpoint tests
  - Parameter models provide consistent validation and documentation
  - Enum types ensure consistent validation of input values
  - Response models match the expected structure
  - Error responses follow a consistent format

## Task 4: Create Custom Exceptions and Handlers
- [x] Write test cases for exception handling in `test_exceptions.py`
- [x] Define expected exception behavior through test assertions
- [x] Test various error scenarios and expected responses
- [x] Create an `exceptions.py` file with custom exception classes
- [x] Write tests for exception handler responses
- [x] Implement exception handlers in `main.py`
- [x] Update service methods to use custom exceptions
- [x] Run tests to verify error handling
- [x] Add consistent error response format across the application
- [x] Ensure proper logging of exceptions
- [x] Add integration tests for error scenarios
- [x] **VERIFIED**: Implementation successfully tested with API endpoint tests
  - Custom exceptions provide consistent error handling
  - Exception handlers return properly formatted responses
  - Error responses include request ID and timestamp
  - Service layer uses appropriate exception types

## Task 5: Restructure Router Hierarchy
- [x] Write tests for router path construction in `test_router_structure.py`
- [x] Design test cases to verify path accessibility before refactoring
- [x] Create endpoint mapping to verify before/after equivalence
- [x] Reorganize router files into logical groups
- [x] Run tests after each router change to verify paths still work
- [x] Update router imports in `__init__.py`
- [x] Create parent routers with appropriate prefixes
- [x] Include child routers with proper tags
- [x] Remove duplicated prefix definitions
- [x] Execute comprehensive path accessibility tests
- [x] Verify OpenAPI documentation reflects the new structure
- [x] **VERIFIED**: Implementation successfully tested with API endpoint tests
  - Router hierarchy is properly organized with parent/child relationships
  - All endpoints remain accessible with the same paths
  - Router tags are consistent and properly organized
  - Prefix duplication has been eliminated
  - OpenAPI documentation correctly reflects the router structure

## Task 6: Simplify Middleware Configuration
- [x] Write tests for middleware behavior in `test_middleware.py`
- [x] Create test cases for each middleware function
- [x] Verify expected middleware execution order
- [x] Test conditional middleware activation
- [x] Replace custom middleware loader with direct FastAPI middleware calls
- [x] Update main.py to use built-in middleware configuration
- [x] Run middleware tests after each change
- [x] Remove complex middleware configuration dictionaries
- [x] Add conditional middleware based on environment settings
- [x] Order middleware properly for optimal request processing
- [x] Verify all middleware functions correctly with integration tests
- [x] Test middleware performance impact
- [x] **VERIFIED**: Implementation successfully tested with middleware tests
  - Middleware is correctly ordered and applied directly with FastAPI's add_middleware
  - Configuration is simplified and easier to understand
  - Conditional middleware based on environment settings works correctly
  - Middleware execution order is properly managed
  - All middleware functionality is preserved

## Task 7: Use Standard FastAPI Lifecycle Events
- [ ] Write tests for application lifecycle events in `test_lifecycle.py`
- [ ] Create test cases for startup and shutdown behaviors
- [ ] Mock database initialization for startup testing
- [ ] Test proper resource cleanup during shutdown
- [ ] Replace custom lifespan context manager with standard event handlers
- [ ] Implement `@app.on_event("startup")` for initialization code
- [ ] Implement `@app.on_event("shutdown")` for cleanup if needed
- [ ] Run tests to verify proper event handling
- [ ] Ensure database initialization happens during startup
- [ ] Add proper logging for application lifecycle events
- [ ] Test application startup and shutdown behavior
- [ ] Verify resource management through integration tests

## Task 8: Use Specific HTTP Method Decorators
- [ ] Write tests for endpoint HTTP methods in `test_http_methods.py`
- [ ] Create test cases for each HTTP verb (GET, POST, PUT, DELETE, etc.)
- [ ] Test status codes for different response scenarios
- [ ] Verify proper response formats across endpoints
- [ ] Update route declarations with specific method decorators
- [ ] Run tests to verify HTTP method handling
- [ ] Add proper status codes for each response type
- [ ] Document possible response scenarios in OpenAPI schema
- [ ] Run tests to verify documentation accuracy
- [ ] Add detailed path and query parameter descriptions
- [ ] Ensure consistent response format across similar endpoints
- [ ] Execute API contract validation tests

Each task represents approximately one story point and focuses on a specific area of FastAPI optimization. These tasks follow Test-Driven Development principles: write failing tests first, implement code to make tests pass, then refactor while ensuring tests continue to pass. Tasks should be completed in sequence for best results, as later tasks may build on earlier optimizations.