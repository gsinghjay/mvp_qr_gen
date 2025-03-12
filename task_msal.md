# Simplified FastAPI-SSO Implementation Tasks

This document outlines a direct approach to implementing Single Sign-On (SSO) for Office 365 using fastapi-sso. This approach integrates authentication directly into the FastAPI application without requiring Traefik middleware for authentication. Each task follows Test-Driven Development principles.

## 1. SSO Integration Setup

### Task 1.1: Set Up FastAPI-SSO Dependencies
- [x] Write tests for SSO integration
- [x] Add `fastapi-sso` to requirements.txt
- [x] Add `python-jose` for JWT token handling
- [x] Create configuration for loading OAuth settings
- [x] Add environment variable support with sensible defaults
- [x] Test configuration loading works correctly
- [x] Verify tests pass

### Task 1.2: Implement SSO Login Endpoints
- [ ] Write tests for login and callback handlers
- [ ] Implement `MicrosoftSSO` integration with fastapi-sso
- [ ] Create login endpoint that redirects to Microsoft
- [ ] Implement callback endpoint that processes OAuth response
- [ ] Generate JWT tokens for successful authentication
- [ ] Store tokens in cookies for authentication state
- [ ] Test authentication flow with mock responses
- [ ] Verify tests pass

### Task 1.3: Create Authentication Utilities
- [ ] Write tests for authentication utility functions
- [ ] Create helper functions for token validation
- [ ] Implement a FastAPI dependency for requiring authentication
- [ ] Add user information extraction utilities
- [ ] Test token validation and extraction
- [ ] Verify tests pass

## 2. Route Protection Implementation

### Task 2.1: Create Authentication Dependencies
- [ ] Write tests for authentication dependencies
- [ ] Create `get_current_user` dependency for protected routes
- [ ] Implement `get_optional_user` for routes that work with and without auth
- [ ] Add support for different authentication scopes/roles if needed
- [ ] Test dependencies with various authentication scenarios
- [ ] Verify tests pass

### Task 2.2: Set Up Route-Based Authentication
- [ ] Write tests for protected and public route configurations
- [ ] Identify routes that should require authentication
- [ ] Apply authentication dependencies to protected routes
- [ ] Keep non-authenticated routes accessible
- [ ] Test both protected and open routes
- [ ] Verify tests pass

### Task 2.3: Implement Session Management
- [ ] Write tests for session management
- [ ] Implement token refresh mechanism
- [ ] Add session timeout handling
- [ ] Create session validation utilities
- [ ] Test session lifecycle (create, validate, refresh, expire)
- [ ] Verify tests pass

## 3. QR Service Minimal Integration

### Task 3.1: Add User ID to Database Model
- [ ] Write test to verify QRCode model can optionally track user information
- [ ] Create Alembic migration to add nullable `user_id` and `user_email` fields to QRCode table
- [ ] Update QRCode model in `app/models/qr.py` to include the new fields
- [ ] Ensure backward compatibility with existing QR codes
- [ ] Run migration and verify database schema changes
- [ ] Verify all tests pass

### Task 3.2: Create Authentication Context Middleware
- [ ] Write tests for authentication context middleware
- [ ] Create `app/middleware/auth_context.py` to extract user info from tokens
- [ ] Make the middleware add user info to request state when available
- [ ] Ensure middleware works even when not authenticated
- [ ] Test with and without valid authentication
- [ ] Verify tests pass

### Task 3.3: Update QR Service for User Association
- [ ] Write tests for associating QR codes with user IDs
- [ ] Update `app/services/qr_service.py` to accept optional user info parameters
- [ ] Modify QR code creation to include user ID when available
- [ ] Add method to find QR codes by user ID
- [ ] Ensure all existing functionality still works
- [ ] Verify tests pass

## 4. User Experience Integration

### Task 4.1: Create User-Aware API Endpoints
- [ ] Write tests for user-filtered listing endpoint
- [ ] Add user-filtered QR code listing endpoint
- [ ] Ensure standard listing endpoint still works
- [ ] Test with both authenticated and unauthenticated requests
- [ ] Verify tests pass

### Task 4.2: Implement Logout Integration
- [ ] Write tests for logout functionality
- [ ] Add logout endpoint to auth service
- [ ] Configure Traefik to handle logout properly
- [ ] Test complete logout flow
- [ ] Verify tests pass

### Task 4.3: Add Login UI Elements
- [ ] Write tests for UI components
- [ ] Update templates to conditionally show login/logout buttons
- [ ] Add user information display when authenticated
- [ ] Test UI rendering with and without authentication
- [ ] Verify tests pass

## 5. Implementation Details

### Task 5.1: Authentication Implementation

```python
# app/auth/sso.py
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from fastapi_sso.sso.microsoft import MicrosoftSSO
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from pydantic import BaseModel

# User model for authentication
class User(BaseModel):
    id: str
    email: str
    display_name: str
    
    @property
    def identity(self) -> str:
        return self.id

# Configure Microsoft SSO
microsoft_sso = MicrosoftSSO(
    client_id=os.getenv("MICROSOFT_CLIENT_ID"),
    client_secret=os.getenv("MICROSOFT_CLIENT_SECRET"),
    tenant=os.getenv("MICROSOFT_TENANT_ID", "common"),
    redirect_uri=os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback"),
    allow_insecure_http=os.getenv("ENVIRONMENT", "production") != "production",
)

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Create OAuth2 scheme for token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create a new JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    """Dependency to get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try to get token from cookie if not in header
    if token is None:
        token = request.cookies.get("auth_token")
        if token is None:
            raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        name = payload.get("name")
        
        if user_id is None or email is None:
            raise credentials_exception
            
        return User(id=user_id, email=email, display_name=name)
    except JWTError:
        raise credentials_exception

async def get_optional_user(request: Request, token: str = Depends(oauth2_scheme)):
    """Dependency to get the current user if authenticated, otherwise None"""
    try:
        return await get_current_user(request, token)
    except HTTPException:
        return None
```

### Task 5.2: Authentication Routes Implementation

```python
# app/routers/auth.py
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from datetime import timedelta
from ..auth.sso import microsoft_sso, create_access_token, get_current_user, User

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.get("/login")
async def login():
    """Redirect to Microsoft login page"""
    return await microsoft_sso.get_authorization_url()

@router.get("/callback")
async def callback(request: Request):
    """Process the SSO callback"""
    user = await microsoft_sso.verify_and_process(request)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "name": user.display_name
        },
        expires_delta=timedelta(minutes=60)
    )
    
    # Set token in cookie and redirect to home
    response = RedirectResponse(url="/")
    response.set_cookie(
        key="auth_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600,
    )
    
    return response

@router.get("/logout")
async def logout():
    """Log out the user by clearing the cookie"""
    response = RedirectResponse(url="/")
    response.delete_cookie("auth_token")
    return response

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get information about the current user"""
    return current_user
```

### Task 5.3: QR Code Model Update

```python
# Alembic migration to add user info fields
"""Add user fields to QRCode model

Revision ID: add_user_fields
Revises: timezone_aware_migration
Create Date: 2025-03-12 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_user_fields"
down_revision = "timezone_aware_migration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("qr_codes") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("user_email", sa.String(length=255), nullable=True))
        
        # Add an index for faster lookups by user_id
        batch_op.create_index(op.f("ix_qr_codes_user_id"), ["user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("qr_codes") as batch_op:
        batch_op.drop_index(op.f("ix_qr_codes_user_id"))
        batch_op.drop_column("user_email")
        batch_op.drop_column("user_id")
```

### Task 5.4: QR Service Update for User Integration

```python
# Update to QRCodeService class in app/services/qr_service.py

# Add user info parameters to create_static_qr method
def create_static_qr(self, data: StaticQRCreateParameters, user_id: str = None, user_email: str = None) -> QRCode:
    """
    Create a new static QR code.

    Args:
        data: Parameters for creating a static QR code
        user_id: Optional user ID to associate with the QR code
        user_email: Optional user email to associate with the QR code

    Returns:
        The created QR code object
    """
    try:
        # Create QR code data
        qr_data = QRCodeCreate(
            id=str(uuid.uuid4()),
            content=data.content,
            qr_type=QRType.STATIC,
            fill_color=data.fill_color,
            back_color=data.back_color,
            created_at=datetime.now(UTC),
        )

        # Validate QR code data
        self.validate_qr_code(qr_data)

        # Create QR code in database
        qr = QRCode(**qr_data.model_dump())
        
        # Add user info if provided
        if user_id:
            qr.user_id = user_id
        if user_email:
            qr.user_email = user_email
            
        self.db.add(qr)
        self.db.commit()
        self.db.refresh(qr)

        logger.info(f"Created static QR code with ID {qr.id}")
        return qr
    except ValidationError as e:
        logger.error(f"Validation error creating static QR code: {str(e)}")
        raise QRCodeValidationError(detail=e.errors())
    except SQLAlchemyError as e:
        self.db.rollback()
        logger.error(f"Database error creating static QR code: {str(e)}")
        raise DatabaseError(f"Database error while creating QR code: {str(e)}")
    except Exception as e:
        self.db.rollback()
        logger.error(f"Unexpected error creating static QR code: {str(e)}")
        raise DatabaseError(f"Unexpected error while creating QR code: {str(e)}")


# Add method to find QR codes by user ID
def get_qr_codes_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> tuple[list[QRCode], int]:
    """
    Get QR codes for a specific user.

    Args:
        user_id: The user ID to filter by
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return

    Returns:
        Tuple of (list of QR codes, total count)
    """
    try:
        # Build the query with user filter
        query = self.db.query(QRCode).filter(QRCode.user_id == user_id)

        # Get total count
        total = query.count()

        # Apply pagination
        qr_codes = query.order_by(QRCode.created_at.desc()).offset(skip).limit(limit).all()

        return qr_codes, total
    except SQLAlchemyError as e:
        logger.error(f"Database error listing user QR codes: {str(e)}")
        raise DatabaseError(f"Database error while listing QR codes: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error listing user QR codes: {str(e)}")
        raise DatabaseError(f"Unexpected error while listing QR codes: {str(e)}")
```

## 6. Testing and Documentation

### Task 6.1: Write Integration Tests
- [ ] Create integration tests for the complete authentication flow
- [ ] Test protected and public routes with different authentication states
- [ ] Verify login, callback, and logout functionality
- [ ] Test both authenticated and anonymous user scenarios
- [ ] Verify all integration tests pass

### Task 6.2: Write Unit Tests for Auth Components
- [ ] Create unit tests for token generation and validation
- [ ] Test auth dependencies with mock requests
- [ ] Verify error handling for expired/invalid tokens
- [ ] Test session management functionality
- [ ] Verify all unit tests pass

### Task 6.3: Document Architecture and Configuration
- [ ] Create documentation explaining the authentication architecture
- [ ] Document all required environment variables
- [ ] Provide setup instructions for Azure/Microsoft application
- [ ] Create diagrams showing the authentication flow
- [ ] Include troubleshooting information
- [ ] Document any security considerations

## 7. Integration Example

```python
# app/main.py - Main application file with integrated auth
from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

from .auth.sso import get_current_user, get_optional_user, User
from .routers import qr_router, auth_router

app = FastAPI(
    title="QR Code Generator",
    description="QR Code Generator with Microsoft SSO",
)

# Include routers
app.include_router(auth_router)
app.include_router(qr_router)

# Set up templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user: User = Depends(get_optional_user)):
    """Home page, works with or without authentication"""
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "user": user,
            "is_authenticated": user is not None
        }
    )

@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, user: User = Depends(get_current_user)):
    """Profile page, requires authentication"""
    return templates.TemplateResponse(
        "profile.html", 
        {
            "request": request, 
            "user": user
        }
    )
```

## 8. Security Considerations

1. **JWT Secret Key**: Ensure the JWT secret key is strong and stored securely as an environment variable.

2. **Token Storage**: Store authentication tokens in HTTP-only cookies to prevent JavaScript access.

3. **CSRF Protection**: Implement CSRF protection for authenticated routes.

4. **HTTPS Required**: Enforce HTTPS for all authenticated routes in production.

5. **Session Management**: Implement proper session timeouts and rotation.

6. **Rate Limiting**: Add rate limiting to authentication endpoints to prevent brute force attacks.

7. **Audit Logging**: Implement audit logging for authentication events.

8. **Azure App Registration**: Follow Microsoft's security recommendations for app registration.

9. **Least Privilege**: Configure minimal permissions in the Azure application registration.

10. **Regular Testing**: Conduct regular security testing of the authentication flow.

## 9. Environment Variables

```
# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=your-tenant-id
REDIRECT_URI=http://localhost:8000/auth/callback

# JWT Configuration
SECRET_KEY=your-secret-key-change-in-production
```