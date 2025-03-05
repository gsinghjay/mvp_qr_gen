# CLAUDE.md - Agent Instructions

## Commands

### Build/Run
- Start app: `docker-compose up -d`
- Recreate containers: `docker-compose up -d --build`

### Database
- Init/migrate: `docker-compose exec api /app/scripts/manage_db.py --init`

### Tests
- Run all tests: `docker compose exec api pytest --cov -v`
- Run single test: `pytest app/tests/path_to_test.py::TestClassName::test_method_name -v`

### Linting/Formatting
- Format code: `black app/`
- Lint code: `ruff app/`
- Type checking: `mypy app/`

## Code Style Guidelines

- **Imports**: Standard library first, third-party next, then local imports - all alphabetically sorted
- **Types**: Use type hints consistently for parameters and return values
- **Naming**: snake_case for variables/functions, PascalCase for classes, UPPER_CASE for constants
- **Docstrings**: Google style with Args, Returns, Raises sections
- **Error handling**: Specific exceptions, proper HTTP status codes, transaction rollbacks
- **Code structure**: Models, schemas, routers, services pattern with dependency injection
- **Line length**: 88-100 characters maximum
- **Indentation**: 4 spaces