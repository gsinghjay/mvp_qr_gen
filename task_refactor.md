# Reorganized Tasks in Recommended Order

## Phase 1: Test Infrastructure and Foundation

### From: task_duplicate_tests.md

## Testing Infrastructure

### ✅ Task 8: Create Common Test Fixtures
**Description:** Extract commonly used test setup code into reusable fixtures.
**Status:** Completed
**Completion Details:**
- Created 5 QR code fixtures (static, dynamic, scanned, colored, historical)
- Added 4 payload fixtures for API requests
- Added 6 client request fixtures for common API operations
- Created comprehensive test utilities in utils.py
- Added detailed testing documentation in README.md
- All 142 tests passing with full coverage

**Affected Files:** 
- `app/tests/conftest.py`
- `app/tests/utils.py`
- `app/tests/README.md`

**Action Items:**
- [x] Identify common setup patterns across test files
- [x] Create new fixtures in `conftest.py` for creating test QR codes
- [x] Create fixtures for common client requests
- [x] Update tests to use these fixtures
- [x] Add docstrings describing fixture purpose and usage

**Acceptance Criteria:**
- [x] At least 3 new useful fixtures are created (Added 15+ fixtures)
- [x] Tests are updated to use fixtures where appropriate
- [x] Code duplication is reduced
- [x] Tests pass with the same or better coverage

### Task 9: Create Test Utility Functions
**Description:** Extract common assertion patterns into reusable utility functions.
**Status:** Completed
**Completion Details:**
- Created 3 new utility functions:
  - validate_color_code: Validates hex color codes
  - validate_redirect_url: Validates URLs for dynamic QR codes
  - validate_scan_statistics: Validates scan statistics data
- Updated validate_qr_code_data to use new utility functions
- Updated test files to use utility functions:
  - test_main.py
  - test_integration.py
  - test_response_models.py
- Removed duplicate validation code
- All tests passing with same coverage

**Affected Files:** 
- `app/tests/utils.py`
- `app/tests/test_main.py`
- `app/tests/test_integration.py`
- `app/tests/test_response_models.py`

**Action Items:**
- [x] Identify common assertion patterns across tests
- [x] Create utility functions for QR code validation
- [x] Create utility functions for response validation
- [x] Update tests to use these utilities
- [x] Add docstrings explaining utility function purpose and usage

**Acceptance Criteria:**
- [x] At least 3 new utility functions are created
- [x] Tests are updated to use them where appropriate
- [x] Code duplication is reduced
- [x] Tests pass with the same or better coverage

### Task 10: Document Testing Strategy
**Description:** Create clear documentation for test organization and maintenance.
**Status:** Completed
**Completion Details:**
- Added documentation for test file organization and purpose
- Enhanced explanation of utility functions including the new validation functions
- Added detailed section on test development workflow
- Added examples of using validation utility functions
- Extended best practices with specific code examples
- Ensured guidelines are clear and comprehensive

**Affected Files:** 
- `app/tests/README.md`

**Action Items:**
- [x] Define and document test organization principles
- [x] Create guidelines for writing new tests
- [x] Document naming conventions and standards
- [x] Explain the purpose of different test files/categories
- [x] Include examples of good test patterns

**Acceptance Criteria:**
- [x] Clear documentation exists explaining test organization
- [x] Documentation includes guidance for adding new tests
- [x] Documentation is accessible in the repository

### From: task_refactor_main.md

## FastAPI Main Module Refactoring Tasks (Docker-based)

- [ ] **Task 1: Create Application Factory Module**
   - Create a new file `app/core/factory.py`
   - Move the `create_app()` function from `main.py` to this file
   - Write a test case `test_app_factory.py` to verify:
     - The factory correctly configures FastAPI settings
     - All middleware is properly registered
     - Application metadata is correctly set
   - Test verification: `docker compose exec api pytest app/tests/test_app_factory.py -v`

- [ ] **Task 2: Refactor Middleware Configuration**
   - Create a `_configure_middleware()` helper function in `app/core/factory.py`
   - Write tests that verify each middleware is correctly applied
   - Test that middleware order is preserved (critical for proper execution)
   - Test verification: Ensure all middleware tests pass with `docker compose exec api pytest app/tests/test_middleware.py -v`

- [ ] **Task 3: Extract Application Lifecycle Management**
   - Create a new file `app/core/lifecycle.py`
   - Move the `lifespan()` function from `main.py`
   - Write tests for both startup and shutdown events
   - Test both successful and error scenarios
   - Test verification: `docker compose exec api pytest app/tests/test_lifecycle.py -v`

## Phase 2: Database Optimization and Security

### From: task_sqlite_prod.md

## Database Structure and Performance Tasks

- [ ] **Configure SQLite WAL Mode**
  - [ ] Add environment variables in docker-compose.yml for SQLite journal mode
  - [ ] Update database.py to read and apply these settings
  - [ ] Add code to verify journal mode is active on startup
  - [ ] Test concurrent writes with WAL mode enabled

- [ ] **Add SQLite Connection Pooling Optimizations**
  - [ ] Modify database.py to implement connection pooling optimizations
  - [ ] Configure optimal pool size based on expected load
  - [ ] Add connection validation and timeout settings
  - [ ] Measure and document performance improvements

- [ ] **Implement SQLite Performance Tuning**
  - [ ] Add pragmas for cache size, page size, and memory mapping
  - [ ] Create a configuration mechanism to adjust these settings per environment
  - [ ] Test read/write performance before and after changes
  - [ ] Document optimal settings for production

## Network Isolation and Security Tasks

- [ ] **Enhance Docker Network Isolation**
  - [ ] Review and strengthen network isolation in docker-compose.yml
  - [ ] Configure internal networks for service-to-service communication
  - [ ] Ensure Traefik is the only entry point to the backend API
  - [ ] Document network architecture and security boundaries

- [ ] **Configure Traefik as Security Gateway**
  - [ ] Update Traefik configuration to act as the primary security layer
  - [ ] Add IP-based access restrictions for sensitive endpoints
  - [ ] Implement request filtering rules
  - [ ] Test security configuration with penetration testing tools

- [ ] **Implement Production CORS Configuration**
  - [ ] Update CORS settings to restrict allowed origins
  - [ ] Modify `app/core/config.py` to set specific CORS_ORIGINS in production
  - [ ] Configure Traefik to handle CORS headers consistently
  - [ ] Test cross-origin requests to verify proper restrictions

- [ ] **Implement Additional Security Headers**
  - [ ] Add Content-Security-Policy headers as noted in `security.py`
  - [ ] Configure other security headers to protect against common attacks
  - [ ] Test headers with security scanning tools
  - [ ] Document security posture improvements

## Phase 3: Complete Main Refactoring and Test Improvements

### From: task_refactor_main.md

- [ ] **Task 4: Create Exception Handlers Module**
   - Create a new file `app/core/exceptions/handlers.py`
   - Move all exception handlers from `main.py`
   - Write tests to verify each exception handler works correctly
   - Test that exception responses follow the defined format
   - Test verification: `docker compose exec api pytest app/tests/test_exception_handlers.py -v`

- [ ] **Task 5: Create Request/Response Middleware Module**
   - Create a new file `app/core/middleware.py`
   - Move the `add_request_id` middleware from `main.py`
   - Write tests to verify request ID is correctly added to responses
   - Test that the middleware correctly handles various request scenarios
   - Test verification: `docker compose exec api pytest app/tests/test_request_middleware.py -v`

- [ ] **Task 6: Create Static Files Configuration Module**
   - Create a new file `app/core/static.py`
   - Move static file mounting logic from `main.py`
   - Write tests to verify static files are correctly served
   - Test that the HTTPS enforcement middleware works correctly
   - Test verification: `docker compose exec api pytest app/tests/test_static_files.py -v`

- [ ] **Task 7: Simplify Main Entry Point**
   - Refactor `main.py` to be a minimal entry point
   - Write an integration test that ensures the application still works
   - Verify all endpoints remain accessible after refactoring
   - Test verification: `docker compose exec api pytest app/tests/test_main_integration.py -v`

### From: task_duplicate_tests.md

## QR Code Creation Tests

### Task 1: Consolidate Static QR Code Creation Tests
**Description:** Merge duplicate static QR code creation tests into a single comprehensive test suite.
**Affected Files:** `test_main.py`, `test_integration.py`, `test_validation_parameterized.py`, `test_qr_service.py`

**Action Items:**
- [ ] Move all static QR code creation tests to `test_validation_parameterized.py`
- [ ] Expand the parameterized test to include all validation scenarios 
- [ ] Remove duplicate static QR creation tests from `test_main.py` and `test_integration.py`
- [ ] Add clear docstring explaining the test purpose and coverage
- [ ] Keep only service-level unit tests in `test_qr_service.py` with explicit documentation

**Acceptance Criteria:**
- [ ] All static QR creation test scenarios are maintained but not duplicated
- [ ] Tests still pass with same or better coverage
- [ ] Clear separation between API-level and service-level tests

### Task 2: Consolidate Dynamic QR Code Creation Tests
**Description:** Merge duplicate dynamic QR code creation tests into a single comprehensive test suite.
**Affected Files:** `test_main.py`, `test_integration.py`, `test_validation_parameterized.py`, `test_response_models.py`

**Action Items:**
- [ ] Move all dynamic QR code creation tests to `test_validation_parameterized.py`
- [ ] Expand the parameterized test to include all validation scenarios
- [ ] Remove duplicate dynamic QR creation tests from other files
- [ ] Keep only response model validation tests in `test_response_models.py` 
- [ ] Update tests to use shared fixtures where possible

**Acceptance Criteria:**
- [ ] All dynamic QR creation test scenarios are maintained but not duplicated
- [ ] Tests still pass with same or better coverage
- [ ] Clear separation between functional tests and response model validation

## QR Code Retrieval Tests

### Task 3: Differentiate API and Service Retrieval Tests
**Description:** Clearly separate API-level and service-level retrieval tests to eliminate perception of duplication.
**Affected Files:** `test_main.py`, `test_qr_service.py`

**Action Items:**
- [ ] Rename API-level test in `test_main.py` to `test_get_qr_code_api()`
- [ ] Enhance service-level test in `test_qr_service.py` to test more edge cases
- [ ] Add clear docstrings explaining the different focus of each test
- [ ] Ensure API test focuses on HTTP aspects while service test focuses on business logic
- [ ] Remove any truly duplicated assertions

**Acceptance Criteria:**
- [ ] Tests have clear, distinct purposes documented in code
- [ ] Service test includes additional edge cases not covered by API test
- [ ] Both tests pass and maintain coverage

## Phase 4: Monitoring and Operations

### From: task_sqlite_prod.md

## Monitoring and Operations Tasks

- [ ] **Enhance API Healthcheck for Database Validation**
  - [ ] Update health endpoint to include database connection validation
  - [ ] Add database performance metrics to health response
  - [ ] Configure more precise healthcheck command in docker-compose.yml
  - [ ] Test failure scenarios and container restart behavior

- [ ] **Implement SQLite Statistics Monitoring**
  - [ ] Create script to capture and log key database metrics
  - [ ] Configure monitoring for database size, free pages, and busy time
  - [ ] Set up periodic logging of statistics to structured format
  - [ ] Document key metrics and warning thresholds

- [ ] **Improve Traefik Access Logging**
  - [ ] Configure detailed access logs in Traefik for security monitoring
  - [ ] Set up structured logging for easy analysis
  - [ ] Add relevant headers to track request sources
  - [ ] Document log formats and retention policy

## Backup and Recovery Tasks

- [ ] **Create Automatic Backup Service**
  - [ ] Add db-backup service to docker-compose.yml
  - [ ] Implement daily backup script with SQLite's .backup command
  - [ ] Configure backup file rotation with configurable retention
  - [ ] Test backup process with large database files

- [ ] **Add Database Integrity Check Service**
  - [ ] Create db-health service in docker-compose.yml
  - [ ] Implement script to run PRAGMA integrity_check regularly
  - [ ] Configure JSON logging of check results
  - [ ] Set up alert mechanism for failed integrity checks

- [ ] **Create Database Vacuum Maintenance Script**
  - [ ] Write vacuum_db.sh script for safe VACUUM operations
  - [ ] Implement VACUUM INTO with verification steps
  - [ ] Add backup safeguards before replacing the main database
  - [ ] Test recovery from failed vacuum operations

## Phase 5: Finalize Refactoring and Test Suite

### From: task_refactor_main.md

- [ ] **Task 8: Create Application Configuration Function**
   - Create a new file `app/core/setup.py`
   - Implement a `configure_app(app)` function
   - Write tests to verify each configuration step is applied
   - Test verification: `docker compose exec api pytest app/tests/test_app_setup.py -v`

- [ ] **Task 9: Implement Router Registration Module**
   - Create a new file `app/core/routers.py`
   - Create a function to register all routers with the application
   - Write tests to verify all routers are correctly registered
   - Test that endpoint paths remain consistent
   - Test verification: `docker compose exec api pytest app/tests/test_router_registration.py -v`

- [ ] **Task 10: Add Integration Tests for Refactored Modules**
   - Create comprehensive integration tests
   - Test the full application lifecycle with the refactored modules
   - Verify all endpoints function as expected
   - Test verification: `docker compose exec api pytest app/tests/test_refactored_integration.py -v`

- [ ] **Task 11: Update Documentation and Type Hints**
   - Add detailed documentation to all new modules
   - Verify documentation with mypy and pydoc
   - Add inline examples where appropriate
   - Test verification: Documentation review and manual code inspection

- [ ] **Task 12: Optimize Import Statements**
   - Review and clean up import statements
   - Use tools like isort and autoflake to organize imports
   - Test that imports don't introduce circular dependencies
   - Test verification: `ruff check app/core/`

### From: task_duplicate_tests.md

## QR Code Update Tests

### Task 4: Consolidate QR Code Update Tests
**Description:** Merge duplicate QR code update tests into a single parameterized test suite.
**Affected Files:** `test_main.py`, `test_response_models.py`, `test_validation_parameterized.py`

**Action Items:**
- [ ] Enhance update tests in `test_validation_parameterized.py` to be more comprehensive
- [ ] Move unique test cases from other files to the parameterized test
- [ ] Remove duplicate update tests from `test_main.py`
- [ ] Keep only response model validation tests in `test_response_models.py`
- [ ] Ensure all original test cases are covered

**Acceptance Criteria:**
- [ ] All update test scenarios are maintained but not duplicated
- [ ] Tests still pass with same or better coverage
- [ ] Clear separation between functional tests and response model validation

## QR Code Redirect Tests

### Task 5: Consolidate Redirect Tests
**Description:** Separate basic redirect tests from background task-specific tests to avoid duplication.
**Affected Files:** `test_main.py`, `test_background_tasks.py`

**Action Items:**
- [ ] Keep the basic redirect functionality test in `test_main.py`
- [ ] Update docstrings to explain test focuses clearly
- [ ] Remove duplicate assertions between files
- [ ] Ensure `test_background_tasks.py` focuses specifically on the async background processing
- [ ] Add cross-references in comments between related tests

**Acceptance Criteria:**
- [ ] Tests have distinct focuses with no redundant assertions
- [ ] Both basic functionality and background task behavior are still well-tested
- [ ] Tests pass with the same or better coverage

## Validation Tests

### Task 6: Consolidate Color Validation Tests
**Description:** Remove duplicate color validation tests and create a single comprehensive test.
**Affected Files:** `test_main.py`, `test_validation_parameterized.py`

**Action Items:**
- [ ] Keep only the more comprehensive validation test in `test_validation_parameterized.py`
- [ ] Remove the duplicate test from `test_main.py`
- [ ] Ensure the remaining test covers all original test cases
- [ ] Add a reference comment in `test_main.py` pointing to the consolidated test
- [ ] Enhance test docstring to describe validation coverage

**Acceptance Criteria:**
- [ ] All color validation scenarios are still tested
- [ ] No duplicate tests exist
- [ ] Tests pass with the same or better coverage

## QR Code Listing Tests

### Task 7: Consolidate QR Code Listing Tests
**Description:** Clarify the distinction between listing endpoint tests and model validation.
**Affected Files:** `test_main.py`, `test_response_models.py`

**Action Items:**
- [ ] Update the API endpoint test in `test_main.py` to focus on business functionality
- [ ] Update test in `test_response_models.py` to focus specifically on response structure
- [ ] Add clear docstrings describing the different test purposes
- [ ] Remove any duplicated assertions
- [ ] Create cross-references in comments between related tests

**Acceptance Criteria:**
- [ ] Tests have clear distinct purposes with no redundant assertions
- [ ] Both API behavior and response structure are well-tested
- [ ] Tests pass with the same or better coverage

### Task 11: Test Coverage Verification
**Description:** Ensure test consolidation doesn't reduce code coverage.
**Affected Files:** Various test files

**Action Items:**
- [ ] Run coverage report before making changes
- [ ] Maintain a checklist of tested scenarios
- [ ] After consolidation, run coverage report again
- [ ] Identify and address any coverage gaps
- [ ] Document coverage metrics before and after

**Acceptance Criteria:**
- [ ] Test coverage is maintained or improved after consolidation
- [ ] No regression in test quality or coverage
- [ ] Coverage report shows all key components are still well-tested

### Task 12: Final Test Suite Cleanup
**Description:** Final pass to remove any remaining duplication and ensure consistency.
**Affected Files:** All test files

**Action Items:**
- [ ] Review all test files for any remaining duplication
- [ ] Ensure consistent naming conventions across tests
- [ ] Verify all tests have proper docstrings
- [ ] Check for unused imports or test functions
- [ ] Run full test suite to verify everything works

**Acceptance Criteria:**
- [ ] No unnecessary code duplication exists
- [ ] All tests follow consistent naming and documentation patterns
- [ ] Full test suite passes
- [ ] Codebase is cleaner and more maintainable

## Phase 6: Production Readiness

### From: task_sqlite_prod.md

## Database Structure and Performance Tasks

- [ ] **Implement Named Volumes for SQLite**
  - [ ] Replace bind mounts with named volumes in docker-compose.yml
  - [ ] Configure the volume with `driver: local`
  - [ ] Test persistence across container restarts
  - [ ] Document volume backup procedures for operations team

## Network Isolation and Security Tasks

- [ ] **Add Traefik Rate Limiting**
  - [ ] Configure rate limiting in Traefik to prevent abuse
  - [ ] Set appropriate limits based on expected usage patterns
  - [ ] Implement different limits for different endpoints
  - [ ] Test with load testing tools to verify effectiveness

## Backup and Recovery Tasks

- [ ] **Implement Multi-Tier Backup Strategy**
  - [ ] Create directory structure for daily, weekly, and monthly backups
  - [ ] Write script to manage backups at different frequencies
  - [ ] Implement cleanup logic to manage disk space
  - [ ] Document restore procedures for each backup type

## Monitoring and Operations Tasks

- [ ] **Set Up Database Maintenance Cron Service**
  - [ ] Add db-maintenance service to docker-compose.yml
  - [ ] Configure weekly VACUUM and daily quick maintenance tasks
  - [ ] Set up appropriate logging of maintenance activities
  - [ ] Test maintenance operations with production-sized datasets

## Additional Security Tasks Aligned with Zero-Auth Approach

- [ ] **Configure TLS with Proper Certificates**
  - [ ] Replace self-signed certificates with proper TLS certificates
  - [ ] Configure Let's Encrypt integration as noted in infrastructure docs
  - [ ] Set up automatic certificate renewal
  - [ ] Test TLS configuration with security scanning tools

- [ ] **Enhance Request Validation**
  - [ ] Review and strengthen Pydantic model validation
  - [ ] Add additional validation for URL parameters
  - [ ] Implement input sanitization for all user inputs
  - [ ] Test with malicious input patterns

- [ ] **Update SQLite File Permissions**
  - [ ] Configure appropriate file permissions for database files
  - [ ] Set proper ownership for SQLite and WAL files
  - [ ] Implement least privilege principle for container access
  - [ ] Test application functionality with restricted permissions