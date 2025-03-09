# QR Generator Test Refactoring Tasks (1 Story Point Each)

## Test Factory Implementation

1. [x] **Create Basic Test Factory Module**
   - Create `app/tests/factories.py` with basic factory structure
   - Implement base `Factory` class with common functionality
   - Add direct DB session integration
   - Acceptance: Factory can be imported and initialized in tests

2. [x] **Implement QRCode Factory**
   - Add `QRCodeFactory` class to create test QR codes
   - Include both static and dynamic QR code creation methods
   - Support customizing all QRCode fields
   - Acceptance: Factory can create QRCodes with sensible defaults

3. [x] **Add Bulk Generation Support**
   - Implement `create_batch` method to generate multiple entities
   - Add sequence support for creating related entities
   - Support customization of batch properties
   - Acceptance: Can create 100+ test entities efficiently

## Test DRY Improvements

4. [x] **Extract Common Test Helpers**
   - Create `app/tests/helpers.py` with shared test functions
   - Move duplicate assertion logic to helper functions
   - Implement reusable QR code validation helpers
   - Acceptance: At least 3 common helpers extracted from existing tests

5. [x] **Parameterize QR Code Validation Tests**
   - Convert color validation tests to use pytest.mark.parametrize
   - Add comprehensive test parameters for validation edge cases
   - Remove duplicated test code
   - Acceptance: Validation test count reduced by 50% with same coverage

6. [x] **Parameterize QR Service Tests**
   - Convert service methods tests to use pytest.mark.parametrize
   - Add test parameters for success/failure conditions
   - Consolidate mock and real DB test variants
   - Acceptance: Service test count reduced by 30% with same coverage

## Fix Skipped SQLite Tests

7. [x] **Fix Concurrent Writes Test**
   - Debug and fix the concurrent writes test in `test_sqlite_specific.py`
   - Implement proper thread synchronization
   - Use SQLAlchemy's concurrency patterns correctly
   - Acceptance: Test passes consistently without being skipped

8. [x] **Fix Busy Timeout Test**
   - Debug and fix the busy timeout handling test
   - Implement reliable method to test timeout behavior
   - Create proper isolation between test connection and main connection
   - Acceptance: Test passes consistently without being skipped

9. [x] **Fix Database Checkpoint Test**
   - Debug and fix WAL file size measurement
   - Implement reliable checkpoint verification
   - Add proper test cleanup to prevent side effects
   - Acceptance: Test passes consistently without being skipped

10. [x] **Fix UTC DateTime Function Test**
    - Debug and fix UTC function testing approach
    - Implement reliable datetime testing methods
    - Create isolated test environment for SQLite function testing
    - Acceptance: Test passes consistently without being skipped

## FastAPI-Specific Testing

11. [x] **Standardize Dependency Injection Tests**
    - Refactor tests to use FastAPI's `app.dependency_overrides` consistently
    - Implement proper cleanup of dependency overrides between tests
    - Create helper for managing dependency overrides
    - Acceptance: All tests use consistent dependency injection pattern
    - Implementation: Created `DependencyOverrideManager` class in `helpers.py` with context manager pattern and convenience methods. Added comprehensive examples in `test_dependency_overrides.py`. All tests pass successfully in Docker.

12. [ ] **Improve Path Operation Testing**
    - Standardize endpoint testing using FastAPI's TestClient
    - Create consistent patterns for testing each HTTP method
    - Add helper functions for common endpoint test scenarios
    - Acceptance: All endpoints have consistent test coverage

13. [ ] **Enhance Request Validation Testing**
    - Create comprehensive tests for input validation
    - Test endpoint behavior with invalid inputs
    - Verify error messages match expectations
    - Acceptance: All validation rules are properly tested

14. [x] **Implement Response Model Validation**
    - Add tests to verify responses match Pydantic response models
    - Create validation helper for checking response against schema
    - Test all response types (success, error, partial) against models
    - Acceptance: All endpoint responses validated against Pydantic models

15. [ ] **Add Middleware Testing**
    - Create tests specifically for each middleware in the application
    - Test middleware execution order and effects
    - Implement middleware mocking capabilities
    - Acceptance: All middleware components have dedicated tests

16. [ ] **Test FastAPI Lifecycle Events**
    - Implement tests for application startup/shutdown events
    - Add tests for lifespan context management
    - Create fixtures for testing lifecycle events
    - Acceptance: All lifecycle events are properly tested

## Async Testing Improvements

17. [ ] **Create Async Testing Utilities**
    - Implement `AsyncTestHelper` class in tests package
    - Add methods for testing concurrent operations
    - Create utilities for waiting on async operations
    - Acceptance: Helper simplifies testing of async code

18. [ ] **Improve Background Task Testing**
    - Create reliable test pattern for background tasks
    - Implement wait utilities for background task completion
    - Add task mocking capabilities
    - Acceptance: Background task tests are deterministic

19. [ ] **Implement Event Loop Isolation**
    - Fix potential event loop leakage between tests
    - Add event loop fixtures with proper cleanup
    - Ensure each async test gets a clean event loop
    - Acceptance: Async tests don't interfere with each other

## Test Documentation and Organization

20. [ ] **Add Comprehensive Test Docstrings**
    - Add detailed docstrings to all test modules
    - Document test strategies and patterns used
    - Update existing test documentation
    - Acceptance: All test modules have comprehensive docstrings

21. [ ] **Standardize Test Structure**
    - Create consistent naming and organization pattern
    - Reorganize tests into logical groupings
    - Implement standard test class/function structure
    - Acceptance: All tests follow consistent organization

22. [ ] **Create Testing Guide Document**
    - Document test philosophy and approach
    - Add examples of best practices
    - Create troubleshooting guide for common issues
    - Acceptance: New developers can understand testing approach

## Performance Optimization

23. [ ] **Add Test Duration Metrics**
    - Create pytest plugin or hook to measure test duration
    - Add reporting for slow tests
    - Implement tracking of test performance over time
    - Acceptance: Can identify the slowest 10% of tests

24. [ ] **Optimize Test Database Setup**
    - Implement faster DB initialization for tests
    - Add in-memory SQLite option for appropriate tests
    - Optimize transaction management in tests
    - Acceptance: Test suite runs at least 20% faster

25. [ ] **Optimize Fixture Scope**
    - Review and update fixture scopes for optimal performance
    - Convert function-scoped fixtures to session when possible
    - Implement caching for expensive fixture operations
    - Acceptance: Reduced test setup/teardown time

## Advanced Testing Improvements

26. [ ] **Implement OpenAPI Schema Validation**
    - Create test to validate actual responses against OpenAPI schema
    - Add test for all major API endpoints
    - Implement schema compliance checker
    - Acceptance: Tests verify API matches documented schema

27. [ ] **Add API Performance Tests**
    - Implement performance baseline tests for key API endpoints
    - Add response time assertions
    - Create test fixtures for performance measurement
    - Acceptance: Performance regression can be detected by tests

28. [ ] **Implement Property-Based Tests**
    - Add hypothesis for property-based testing
    - Implement property tests for QR code generation
    - Create strategies for testing with random valid inputs
    - Acceptance: Key components tested with property-based approach

29. [ ] **Add Database Concurrency Stress Tests**
    - Implement stress tests for concurrent database operations
    - Verify data integrity under concurrent load
    - Add test for WAL mode benefits
    - Acceptance: System handles concurrent operations reliably

30. [ ] **Implement Test Environment Isolation**
    - Create dedicated test configuration
    - Implement environment detection and configuration
    - Ensure all tests clean up resources
    - Acceptance: Tests run in isolation without side effects