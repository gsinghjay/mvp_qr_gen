# Test Refactoring To-Do List: Reducing Mocks for Production-Like Tests

## 1. Update Test Configuration

- [x] Replace in-memory SQLite with file-based SQLite for integration tests
  - [x] Create a dedicated test database directory with proper cleanup
  - [x] Update `conftest.py` to use file-based SQLite instead of `:memory:`
  - [x] Implement test database lifecycle management (setup/teardown)

- [x] Configure SQLite with production-relevant PRAGMAs
  - [x] Apply WAL mode for integration tests
  - [x] Set up proper journal modes and cache sizes
  - [x] Configure appropriate timeout and busy handling settings

- [x] Create test data fixtures that mirror production scenarios
  - [x] Implement database seeding functions
  - [x] Create realistic test data generators

## 2. Refactor Existing Tests

- [ ] Identify and categorize current mock usage
  - [ ] Audit all test files for mock usage
  - [ ] Classify mocks as "necessary" vs "replaceable"
  - [ ] Document external dependencies that still require mocking

- [ ] Replace `MagicMock` instances with real components
  - [ ] Refactor `test_qr_service.py` to use real database sessions
  - [ ] Replace mocked database sessions in `test_main.py`
  - [ ] Update HTTP client tests to use the actual service layer

- [ ] Restructure test assertions
  - [ ] Update assertions to check database state directly
  - [ ] Replace mock verification with actual state verification
  - [ ] Add database integrity checks post-test

## 3. Create SQLite-Specific Test Suite

- [ ] Test WAL mode functionality
  - [ ] Verify WAL files are created and managed properly
  - [ ] Test checkpoint behaviors

- [ ] Implement concurrency tests
  - [ ] Test `with_retry` decorator with actual concurrent operations
  - [ ] Verify database locking behavior under load
  - [ ] Test concurrent read/write operations

- [ ] Add database integrity validation tests
  - [ ] Test SQLite PRAGMA integrity_check
  - [ ] Verify transaction rollback functionality
  - [ ] Test proper constraint enforcement

- [ ] Implement backup and recovery tests
  - [ ] Test database backup functionality
  - [ ] Verify database restoration process
  - [ ] Test corruption recovery scenarios

## 4. Enhance Integration Test Coverage

- [ ] Create end-to-end flow tests
  - [ ] Test complete QR code creation to scan flows
  - [ ] Test dynamic QR code updates and redirections
  - [ ] Add long-running tests with database persistence

- [ ] Add load and performance tests
  - [ ] Test database performance under multiple concurrent users
  - [ ] Verify connection pooling behavior
  - [ ] Measure and assert response times for key operations

- [ ] Test service layer directly with real database
  - [ ] Replace `QRCodeService` mock tests with real service tests
  - [ ] Test service transaction integrity
  - [ ] Verify service error handling with real database errors

## 5. Update CI Pipeline

- [ ] Update GitHub Actions workflow
  - [ ] Configure proper test database setup in CI
  - [ ] Add database artifact preservation for failed tests
  - [ ] Implement parallel test execution with database isolation

- [ ] Add Database Verification Steps
  - [ ] Add post-test database validation steps
  - [ ] Implement test database analysis for optimal test patterns
  - [ ] Create reporting for SQLite-specific metrics during tests

## 6. Refine Test Isolation Strategy

- [ ] Implement transaction-based test isolation
  - [ ] Use SQLAlchemy's nested transactions for test isolation
  - [ ] Ensure all tests properly cleanup database state
  - [ ] Add cleanup verification steps to prevent test contamination

- [ ] Create database fixture management
  - [ ] Implement database resets between test suites
  - [ ] Add database state verification between tests
  - [ ] Create isolation verification tooling

## 7. Document New Testing Approach

- [ ] Update testing documentation
  - [ ] Document the new testing approach and philosophy
  - [ ] Create guidelines for when to use mocks vs real components
  - [ ] Add examples of effective database testing patterns

- [ ] Create testing tutorials for new team members
  - [ ] Write step-by-step guide for running integration tests
  - [ ] Document common testing patterns and anti-patterns
  - [ ] Create troubleshooting guide for database test issues