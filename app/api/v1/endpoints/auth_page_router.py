import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request, HTTPException, Header, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings # For templates directory and potentially auth related settings
# Assuming some auth utilities might be needed, e.g., from a security module
# from app.core import security # Example if custom auth utils are used

# Configure templates
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))
logger = logging.getLogger("app.auth_pages")

router = APIRouter(
    tags=["Pages - Authentication"], # Updated tag
    responses={404: {"description": "Not found"}},
)

# Note: The original pages.py had a context_processor for 'request'.
# If these templates rely on it, Jinja2Templates instance here should also have it.
# For now, assuming 'request' will be passed explicitly if needed by template context itself.

# Context processor similar to pages.py
def get_base_template_context(request: Request) -> dict:
    request.scope["scheme"] = "https"
    return {
        "request": request,
        "app_version": "1.0.0", # Example, consider centralizing if needed
        "environment": settings.ENVIRONMENT,
        "current_year": 2024, # Or use datetime.now().year
        "api_base_url": "/api/v1",
    }

templates = Jinja2Templates(
    directory=str(settings.TEMPLATES_DIR),
    context_processors=[get_base_template_context],
)

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """ Render the login page. """
    try:
        return templates.TemplateResponse(
            name="auth/login.html",
            context={"request": request, "page_title": "Login"},
        )
    except Exception as e:
        logger.error("Error in login page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="auth/login.html",
            context={"request": request, "page_title": "Login", "error": "An error occurred while loading the login page"},
            status_code=500,
        )

@router.get("/logout", response_class=HTMLResponse)
async def logout_page(request: Request):
    """ Render the logout page or handle logout. """
    try:
        # This might redirect to an external logout URL or render a logout confirmation
        return templates.TemplateResponse(
            name="auth/logout.html",
            context={"request": request, "page_title": "Logout"},
        )
    except Exception as e:
        logger.error("Error in logout page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="auth/logout.html",
            context={"request": request, "page_title": "Logout", "error": "An error occurred during logout"},
            status_code=500,
        )

@router.get("/unauthorized", response_class=HTMLResponse)
async def unauthorized_page(request: Request):
    """ Render the unauthorized access page. """
    try:
        return templates.TemplateResponse(
            name="auth/unauthorized.html",
            context={"request": request, "page_title": "Unauthorized", "error_message": "You are not authorized to access this resource."},
        )
    except Exception as e:
        logger.error("Error in unauthorized page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="auth/unauthorized.html",
            context={"request": request, "page_title": "Unauthorized", "error": "An error occurred while loading the unauthorized page"},
            status_code=500,
        )

@router.get("/hello-secure", response_class=HTMLResponse)
async def hello_secure_page( # Renamed from hello_secure to avoid conflict if pages.py is still imported
    request: Request,
    x_forwarded_email: Optional[str] = Header(None, alias="X-Forwarded-Email"),
    x_forwarded_preferred_username: Optional[str] = Header(None, alias="X-Forwarded-Preferred-Username"),
    x_forwarded_groups: Optional[str] = Header(None, alias="X-Forwarded-Groups"),
    x_forwarded_roles: Optional[str] = Header(None, alias="X-Forwarded-Roles"),
    x_forwarded_access_token: Optional[str] = Header(None, alias="X-Forwarded-Access-Token")
):
    """
    Protected page that displays authenticated user information.
    (Moved from pages.py)
    """
    try:
        all_headers = dict(request.headers)
        auth_headers = {k: v for k, v in all_headers.items() if k.lower().startswith('x-forwarded') or k.lower().startswith('x-auth')}
        logger.info(f"AUTH HEADERS: {auth_headers}")

        groups_list = []
        if x_forwarded_groups:
            groups_list.extend(x_forwarded_groups.split(','))
        if x_forwarded_roles:
            groups_list.extend(x_forwarded_roles.split(','))

        groups_list = list(filter(None, list(set(groups_list))))

        debug_info = {
            "groups_header_raw": x_forwarded_groups,
            "roles_header_raw": x_forwarded_roles,
            "groups_parsed": groups_list,
            "groups_count": len(groups_list),
            "has_access_token": bool(x_forwarded_access_token),
            "token_preview": x_forwarded_access_token[:50] + "..." if x_forwarded_access_token else None,
            "azure_ad_status": "Checking for Azure AD groups and mapped roles"
        }

        logger.info(f"AZURE AD sAMAccountName GROUP DEBUG: {debug_info}")
        logger.info(f"Secure page accessed with auth headers: email={x_forwarded_email}, username={x_forwarded_preferred_username}, groups={groups_list}")

        token_groups = []
        if x_forwarded_access_token:
            try:
                import base64
                import json
                parts = x_forwarded_access_token.split('.')
                if len(parts) == 3:
                    payload = parts[1]
                    payload += '=' * (4 - len(payload) % 4)
                    decoded = base64.urlsafe_b64decode(payload)
                    token_data = json.loads(decoded)

                    client_roles = token_data.get('resource_access', {}).get('oauth2-proxy-client', {}).get('roles', [])
                    realm_roles = token_data.get('realm_access', {}).get('roles', [])
                    direct_groups = token_data.get('groups', [])
                    direct_roles = token_data.get('roles', [])

                    token_groups = client_roles + realm_roles + direct_groups + direct_roles

                    logger.info(f"TOKEN GROUPS (Client Roles): {client_roles}")
                    logger.info(f"TOKEN GROUPS (Realm Roles): {realm_roles}")
                    logger.info(f"TOKEN GROUPS (Direct Groups): {direct_groups}")
                    logger.info(f"TOKEN GROUPS (All Combined): {token_groups}")
                    logger.info(f"Full token payload for debugging: {json.dumps(token_data, indent=2)}")
            except Exception as e:
                logger.warning(f"Could not decode access token for group debugging: {e}")

        return templates.TemplateResponse(
            name="pages/hello_secure.html",
            context={
                "request": request,
                "email": x_forwarded_email,
                "preferred_username": x_forwarded_preferred_username,
                "groups": groups_list,
                "token_groups": token_groups,
                "debug_info": debug_info,
                "page_title": "Secure Hello Page",
                "all_headers": auth_headers,
            },
        )
    except Exception as e:
        logger.error(f"Error in secure hello page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="pages/hello_secure.html", # Or an error template
            context={
                "request": request,
                "error": "An error occurred while loading the secure page",
            },
            status_code=500,
        )

@router.get("/logout/oidc", response_class=RedirectResponse)
async def oidc_logout_page( # Renamed from oidc_logout
    request: Request,
    x_forwarded_access_token: Optional[str] = Header(None, alias="X-Forwarded-Access-Token"),
    x_forwarded_user: Optional[str] = Header(None, alias="X-Forwarded-User"),
    x_forwarded_email: Optional[str] = Header(None, alias="X-Forwarded-Email"),
    authorization: Optional[str] = Header(None)
):
    """
    OIDC logout endpoint that properly handles logout with id_token_hint.
    (Moved from pages.py)
    """
    try:
        import base64
        import json
        from urllib.parse import quote, urlencode

        all_headers = dict(request.headers)
        auth_headers = {k: v for k, v in all_headers.items() if k.lower().startswith('x-forwarded') or k.lower().startswith('x-auth')}
        logger.info(f"OIDC logout - Auth headers: {auth_headers}")
        logger.info(f"OIDC logout - Token info: access_token={bool(x_forwarded_access_token)}, user={x_forwarded_user}, email={x_forwarded_email}")

        id_token = None

        if authorization and "," in authorization:
            auth_parts = authorization.split(", Bearer ")
            if len(auth_parts) > 1:
                potential_id_token = auth_parts[1]
                logger.info(f"Found potential ID token from Authorization header: {potential_id_token[:50]}...")
                try:
                    if potential_id_token.count('.') == 2:
                        _, payload, _ = potential_id_token.split('.')
                        payload += '=' * (4 - len(payload) % 4)
                        decoded_payload = base64.urlsafe_b64decode(payload)
                        token_data = json.loads(decoded_payload)
                        if token_data.get('typ') == 'ID':
                            id_token = potential_id_token
                            logger.info("Found valid ID token in Authorization header")
                        else:
                            logger.info(f"Token in Authorization header is type: {token_data.get('typ')}, not ID token")
                except Exception as e:
                    logger.warning(f"Could not decode Authorization token: {e}")

        if x_forwarded_access_token and not id_token: # Only log if ID token not already found
             logger.info("Found X-Forwarded-Access-Token but skipping as it's an access token, not ID token (unless it was already parsed as ID)")

        if not id_token:
            logger.info("No ID token found - proceeding with logout without id_token_hint")

        base_logout_url = "https://auth.hccc.edu/realms/hccc-apps-realm/protocol/openid-connect/logout"
        post_logout_redirect_uri = "https://web.hccc.edu/logout" # Make sure this matches exactly what's in Keycloak

        keycloak_logout_url = f"{base_logout_url}?client_id=oauth2-proxy-client&post_logout_redirect_uri={post_logout_redirect_uri}"

        if id_token:
            keycloak_logout_url += f"&id_token_hint={id_token}"
            logger.info("OIDC logout with id_token_hint")
        else:
            logger.warning("OIDC logout without id_token_hint - may show confirmation page")
            if x_forwarded_email: # login_hint can help Keycloak identify the session
                keycloak_logout_url += f"&login_hint={quote(x_forwarded_email)}"

        oauth2_proxy_logout_url = f"/oauth2/sign_out?rd={quote(keycloak_logout_url)}"

        logger.info(f"Keycloak logout URL: {keycloak_logout_url}")
        logger.info(f"OAuth2-Proxy logout URL: {oauth2_proxy_logout_url}")

        return RedirectResponse(url=oauth2_proxy_logout_url, status_code=status.HTTP_302_FOUND)

    except Exception as e:
        logger.error(f"Error in OIDC logout endpoint", extra={"error": str(e)})
        fallback_logout_url = f"/oauth2/sign_out?rd={quote('https://web.hccc.edu/logout')}"
        return RedirectResponse(url=fallback_logout_url, status_code=status.HTTP_302_FOUND)
