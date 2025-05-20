# Test Directory Structure

This document outlines the organization of the test suite for the QR Code Generator application following the implementation of Task 1.1 from the Test Refactoring Plan.

## Directory Structure

```
app/tests/
├── integration/           # Integration tests that use real database connections
│   └── api/               # API integration tests
│       └── v1/            # Tests for API v1 endpoints
├── unit/                  # Unit tests with mocked dependencies where appropriate
│   ├── services/          # Tests for service layer components
│   ├── repositories/      # Tests for repository layer components
│   └── utils/             # Tests for utility functions and helpers
├── data/                  # Test data fixtures and sample data
├── e2e/                   # End-to-end tests simulating real user interactions
├── conftest.py            # Pytest fixtures and configuration
├── dependencies.py        # Test-specific dependency injection functions
├── factories.py           # Test data factories using Factory Boy
├── helpers.py             # Test helper functions
└── utils.py               # Utility functions for testing
```

## Test Categories

### Integration Tests
- Located in `app/tests/integration/`
- Use a real test database connection
- Test multiple components working together
- Focus on API endpoints, database operations, and middleware

### Unit Tests
- Located in `app/tests/unit/`
- Test components in isolation with appropriate mocks
- Organized by component type (services, repositories, utilities)

### End-to-End Tests
- Located in `app/tests/e2e/`
- Simulate complete user workflows
- Test the application as a whole

## Naming Conventions

- All test files follow the pattern `test_*.py`
- Test functions follow the pattern `test_*`
- Test file names reflect the component or functionality they test
- Tests are grouped into directories by type and function

## How to Run Tests

To run all tests:
```bash
docker exec qr_generator_api pytest
```

To run tests from a specific category:
```bash
docker exec qr_generator_api pytest app/tests/integration/
docker exec qr_generator_api pytest app/tests/unit/services/
docker exec qr_generator_api pytest app/tests/e2e/
```

To run a specific test file:
```bash
docker exec qr_generator_api pytest app/tests/unit/services/test_qr_service.py
```

## Notes

- The tests use a dedicated PostgreSQL test database configured in docker-compose.yml
- Test isolation is achieved through transaction-based roll-back after each test
- Test dependencies and fixtures are defined in conftest.py
- Dependency injection for tests is managed through dependencies.py, which provides test-specific implementations
- Test data is created using factory_boy factories in factories.py 