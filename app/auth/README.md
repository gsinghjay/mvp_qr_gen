# Microsoft Authentication Library (MSAL) Integration

This document provides an overview of the Microsoft Azure AD authentication implementation in the QR Code Generator application.

## Authentication Flow

The application implements the OAuth 2.0 authorization code flow for secure user authentication via Microsoft Azure Active Directory:

1. **User initiates login**:
   - User clicks "Login" button in the app
   - App redirects to `/auth/login` or displays login page at `/auth/login-page`

2. **Redirect to Microsoft login**:
   - App constructs authorization URL with required parameters
   - User is redirected to Microsoft login page
   - User authenticates with their Microsoft credentials

3. **Authorization code callback**:
   - Microsoft redirects back to our callback URL with an authorization code
   - App validates the code and exchanges it for access and ID tokens
   - App validates token claims and signatures

4. **Session establishment**:
   - User information extracted from tokens is stored in a secure session
   - User is redirected to the originally requested page or home

5. **Authenticated access**:
   - Protected routes check for authenticated session using dependencies
   - Routes can require specific roles for authorization

## Configuration

The MSAL integration requires the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_CLIENT_ID` | Application (client) ID from Azure portal | None (Required) |
| `AZURE_TENANT_ID` | Directory (tenant) ID from Azure portal | None (Required) |
| `AZURE_CLIENT_SECRET` | Client secret from Azure portal | None (Required) |
| `AZURE_REDIRECT_PATH` | Path for OAuth callback | `/auth/callback` |
| `AZURE_SCOPES` | Space-separated list of OAuth scopes | `User.Read` |
| `AZURE_AUTHORITY` | Azure authority URL | `https://login.microsoftonline.com/{tenant}` |
| `SESSION_SECRET_KEY` | Secret key for session encryption | None (Required) |

## Session Security

The application implements the following session security measures:

- **Secure cookies**: HTTPOnly, SameSite=Lax, and Secure flags enabled
- **Encrypted sessions**: Session data is encrypted with a secret key
- **Expiring sessions**: Sessions expire after a configurable timeout
- **Token validation**: All tokens are validated for signature, expiration, and claims
- **Role-based access**: Endpoints can require specific roles for access

## User Interface

- Login page displaying the Microsoft sign-in button
- Login/logout buttons integrated into the main application navbar
- User profile information displayed when authenticated
- Support for redirection after authentication

## Testing

The authentication implementation includes comprehensive tests:

- Unit tests for configuration, client, dependencies, and routes
- Integration tests for the full authentication flow
- Mock services for testing without an actual Azure tenant

## Diagrams

### Authentication Flow Diagram

```
+--------+                                   +---------------+                                   +----------------+
|        |---(1) Login request-------------->|               |---(2) Redirect to Microsoft----->|                |
|        |                                   |               |                                   |                |
|        |                                   |    QR App     |                                   |   Microsoft    |
| User   |                                   |               |                                   |   Identity     |
|        |<---(5) Logged in session----------|               |<--(4) Token & user info----------|                |
|        |                                   |               |                                   |                |
+--------+                                   +---------------+                                   +----------------+
    ^                                              |                                                  ^
    |                                              |                                                  |
    |                                              v                                                  |
    |                                        +---------------+                                        |
    +------(6) Access protected routes----->| Protected API |---(3) Auth code & token exchange------+
                                           +---------------+
```