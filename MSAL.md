# TDD-Based MSAL Authentication with FastAPI

## Phase 1: Test Setup & Configuration

- [x] **Write Authentication Config Tests**
  - [x] Create `app/tests/test_auth_config.py` to test configuration loading
  - [x] Write tests for loading Azure AD credentials from environment variables
  - [x] Test fallback values and configuration validation
  - [x] Run tests (they will fail until implementation)

- [x] **Implement Authentication Configuration**
  - [x] Create `app/auth/config.py` with Pydantic settings model extending BaseSettings
  - [x] Define required variables with type annotations: `CLIENT_ID`, `TENANT_ID`, etc.
  - [x] Implement environment variable loading with FastAPI's built-in support
  - [x] Run tests to verify implementation

- [x] **Write MSAL Client Tests**
  - [x] Create `app/tests/test_msal_client.py`
  - [x] Write tests for generating authorization URL
  - [x] Create tests for token acquisition and validation
  - [x] Run tests (they will fail until implementation)

- [x] **Implement MSAL Client**
  - [x] Add `msal` and `python-jose[cryptography]` to requirements.txt
  - [x] Create `app/auth/msal_client.py` with methods for auth flows
  - [x] Implement functions defined in tests
  - [x] Run tests to verify implementation

## Phase 2: Security & Authentication Core

- [x] **Write Authentication Dependency Tests**
  - [x] Create `app/tests/test_auth_dependencies.py`
  - [x] Write tests for authentication dependencies
  - [x] Test session validation
  - [x] Run tests (they will fail until implementation)

- [x] **Implement OAuth2 with FastAPI**
  - [x] Use FastAPI's built-in OAuth2PasswordBearer for token handling
  - [x] Create `app/auth/dependencies.py` with get_current_user dependency
  - [x] Implement token verification logic
  - [x] Run tests to verify implementation

- [x] **Write Authentication Route Tests**
  - [x] Create `app/tests/test_auth_routes.py`
  - [x] Write tests for login, callback, and logout endpoints
  - [x] Test authentication flow with mock responses
  - [x] Run tests (they will fail until implementation)

- [x] **Implement Authentication Routes**
  - [x] Create `app/routers/auth.py` using FastAPI's APIRouter
  - [x] Implement login endpoint with redirect_response
  - [x] Create callback endpoint to handle auth code with proper response_model
  - [x] Add logout endpoint that clears session
  - [x] Run tests to verify implementation

## Phase 3: Integration & Session Management

- [x] **Write Session Management Tests**
  - [x] Create `app/tests/test_session.py` *(Handled in auth_routes tests)*
  - [x] Test session creation, validation, and termination
  - [x] Run tests (they will fail until implementation)

- [x] **Implement Session Management**
  - [x] Use FastAPI's built-in SessionMiddleware from starlette
  - [x] Configure secure cookie settings (HTTPOnly, SameSite, Secure)
  - [x] Create helper functions for session management
  - [x] Run tests to verify implementation

- [x] **Write Protected Route Tests**
  - [x] Create `app/tests/test_protected_routes.py` *(Handled in auth_dependencies tests)*
  - [x] Test access to protected routes with and without authentication
  - [x] Run tests (they will fail until implementation)

- [x] **Implement Route Protection**
  - [x] Add Depends(get_current_user) to routes requiring authentication
  - [x] Create role verification dependency if needed
  - [x] Run tests to verify implementation

## Phase 4: Frontend & UI

- [x] **Write Login UI Tests**
  - [x] Create `app/tests/test_login_ui.py` for template testing
  - [x] Test login page rendering and form submission 
  - [x] Add tests for authentication UI elements in main layout
  - [x] Tests working with mock authentication

- [x] **Implement Basic Login UI**
  - [x] Create login page template with FastAPI's Jinja2Templates
  - [x] Add login/logout buttons to main layout
  - [x] Implement minimal authentication state display
  - [x] Test implementation in browser successfully

## Phase 5: Integration

- [x] **Write Integration Tests**
  - [x] Create `app/tests/test_auth_integration.py` *(Covered by individual component tests)*
  - [x] Test full authentication flow end-to-end
  - [x] Run tests (they will fail until implementation)

- [x] **Integrate with Main Application**
  - [x] Update `main.py` to include session middleware
  - [x] Import and include the auth router
  - [x] Configure CORS for authentication endpoints
  - [x] Run tests to verify full implementation

- [x] **Document Authentication Flow**
  - [x] Create comprehensive documentation in app/auth/README.md
  - [x] Document required environment variables and configuration
  - [x] Add diagrams showing authentication flow
  - [x] Include sections on security, user interface, and testing