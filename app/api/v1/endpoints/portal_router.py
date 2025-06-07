import logging
from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.dependencies import get_content_service
from app.services.content_service import ContentService, ContentNotFoundError, ContentParsingError

logger = logging.getLogger("app.portal_router")

# Initialize templates
def get_base_template_context(request: Request) -> dict:
    request.scope["scheme"] = "https"
    return {
        "request": request,
        "app_version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "current_year": datetime.now().year,
        "api_base_url": "/api/v1",
    }

templates = Jinja2Templates(
    directory=str(settings.TEMPLATES_DIR),
    context_processors=[get_base_template_context],
)

def extract_user_name_from_email(email: str) -> str:
    """Extract a display name from an email address."""
    if not email:
        return None
    
    # Extract user part before @ symbol
    user_part = email.split('@')[0]
    
    # If it contains a dot, assume first.last format
    if '.' in user_part:
        first_name = user_part.split('.')[0]
        return first_name.title()
    
    # Otherwise, use the whole user part
    return user_part.title()

router = APIRouter(
    prefix="/portal",
    tags=["Portal - Dynamic Content"],
    responses={404: {"description": "Page not found"}},
)

@router.get("/json/{page_path:path}")
async def get_portal_page_json(
    page_path: str,
    content_service: Annotated[ContentService, Depends(get_content_service)],
):
    """
    JSON API endpoint for portal content - returns raw data for API consumers.
    
    Args:
        page_path: The path to the page (e.g., "faculty/announcements" maps to "faculty/announcements.md")
        content_service: Injected ContentService for parsing content
        
    Returns:
        JSONResponse containing parsed metadata and HTML content
        
    Raises:
        HTTPException 404: If the requested page is not found
        HTTPException 500: If there's an error parsing the content
    """
    try:
        logger.info(f"Portal JSON API requested: {page_path}")
        
        # Use ContentService to fetch and parse the page
        page_data = content_service.get_page_data(page_path)
        
        # Handle date serialization for JSON response
        metadata = page_data["meta"].copy()
        for key, value in metadata.items():
            if hasattr(value, 'isoformat'):  # Check if it's a date/datetime object
                metadata[key] = value.isoformat()
        
        # Return the parsed data as JSON
        return JSONResponse(
            content={
                "success": True,
                "page_path": page_path,
                "metadata": metadata,
                "content": page_data["content"],
                "cache_info": content_service.get_cache_info()
            }
        )
        
    except ContentNotFoundError as e:
        logger.warning(f"Portal page not found: {page_path} - {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Portal page not found: {page_path}"
        )
        
    except ContentParsingError as e:
        logger.error(f"Error parsing portal page {page_path}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing portal page: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error loading portal page {page_path}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while loading portal page"
        )

@router.get("/{page_path:path}", response_class=HTMLResponse)
async def get_portal_page(
    request: Request,
    page_path: str,
    content_service: Annotated[ContentService, Depends(get_content_service)],
    x_forwarded_email: Optional[str] = Header(None, alias="X-Forwarded-Email"),
    x_forwarded_preferred_username: Optional[str] = Header(None, alias="X-Forwarded-Preferred-Username"),
    x_forwarded_groups: Optional[str] = Header(None, alias="X-Forwarded-Groups"),
):
    """
    Dynamic catch-all portal router that serves any page from app/content/portal/ based on URL path.
    
    This endpoint uses the ContentService to load Markdown files with YAML frontmatter
    and renders them using the universal portal template with HCCC institutional styling.
    
    Args:
        request: FastAPI request object
        page_path: The path to the page (e.g., "faculty/announcements" maps to "faculty/announcements.md")
        content_service: Injected ContentService for parsing content
        x_forwarded_email: User email from OAuth2-Proxy headers
        x_forwarded_preferred_username: Preferred username from OAuth2-Proxy headers
        x_forwarded_groups: User groups from OAuth2-Proxy headers
        
    Returns:
        HTMLResponse with rendered portal page using institutional template
        
    Raises:
        HTTPException 404: If the requested page is not found
        HTTPException 500: If there's an error parsing the content
    """
    try:
        logger.info(f"Portal content requested: {page_path}")
        
        # Extract user information for personalization
        user_name = extract_user_name_from_email(x_forwarded_email) if x_forwarded_email else None
        
        # Parse groups for role-based content
        groups_list = []
        if x_forwarded_groups:
            groups_list = [g.strip() for g in x_forwarded_groups.split(',') if g.strip()]
        
        logger.info(f"Portal page accessed by: email={x_forwarded_email}, user_name={user_name}, groups={groups_list}")
        
        # Use ContentService to fetch and parse the page
        page_data = content_service.get_page_data(page_path)
        
        # Render the page using the universal portal template
        return templates.TemplateResponse(
            name="pages/portal_layout.html",
            context={
                "request": request,
                "page_path": page_path,
                "page": page_data,
                "user_name": user_name,
                "user_email": x_forwarded_email,
                "preferred_username": x_forwarded_preferred_username,
                "groups": groups_list,
                "is_authenticated": True,
                "cache_info": content_service.get_cache_info(),
            },
        )
        
    except ContentNotFoundError as e:
        logger.warning(f"Portal page not found: {page_path} - {str(e)}")
        return templates.TemplateResponse(
            name="fragments/error.html",
            context={
                "request": request,
                "error": f"Portal page not found: {page_path}",
                "is_authenticated": True,
            },
            status_code=404,
        )
        
    except ContentParsingError as e:
        logger.error(f"Error parsing portal page {page_path}: {str(e)}")
        return templates.TemplateResponse(
            name="fragments/error.html",
            context={
                "request": request,
                "error": f"Error parsing portal page: {str(e)}",
                "is_authenticated": True,
            },
            status_code=500,
        )
        
    except Exception as e:
        logger.error(f"Unexpected error loading portal page {page_path}: {str(e)}")
        return templates.TemplateResponse(
            name="fragments/error.html",
            context={
                "request": request,
                "error": "Internal server error while loading portal page",
                "is_authenticated": True,
            },
            status_code=500,
        )

@router.get("/")
async def list_available_pages(
    content_service: Annotated[ContentService, Depends(get_content_service)],
):
    """
    List all available portal pages.
    
    Args:
        content_service: Injected ContentService for content operations
        
    Returns:
        JSONResponse containing list of available pages and cache information
    """
    try:
        available_pages = content_service.list_available_pages()
        
        return JSONResponse(
            content={
                "success": True,
                "available_pages": available_pages,
                "total_pages": len(available_pages),
                "cache_info": content_service.get_cache_info()
            }
        )
        
    except Exception as e:
        logger.error(f"Error listing available pages: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving available pages"
        ) 