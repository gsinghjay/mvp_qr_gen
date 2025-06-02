import logging
from typing import Annotated, Optional # Ensure Optional is imported

from fastapi import APIRouter, Depends, Request, Header # Ensure Header is imported
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime # For current_year in context

from app.core.config import settings
from app.core.exceptions import DatabaseError # Though not directly used, good for consistency if error handling evolves

templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))
logger = logging.getLogger("app.portal_pages")

router = APIRouter(
    tags=["Pages - HCCC Portal"],
    responses={404: {"description": "Not found"}},
)

# Context processor similar to pages.py
def get_base_template_context(request: Request) -> dict:
    request.scope["scheme"] = "https"
    return {
        "request": request,
        "app_version": "1.0.0", # Example, consider centralizing if needed
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

@router.get("/portal-demo", response_class=HTMLResponse)
async def portal_demo_page(
    request: Request,
    x_forwarded_email: Optional[str] = Header(None, alias="X-Forwarded-Email"),
    x_forwarded_preferred_username: Optional[str] = Header(None, alias="X-Forwarded-Preferred-Username"),
    x_forwarded_groups: Optional[str] = Header(None, alias="X-Forwarded-Groups"),
):
    """ Portal navigation demo page with user personalization. """
    try:
        # Extract user name for personalization
        user_name = extract_user_name_from_email(x_forwarded_email) if x_forwarded_email else None
        
        # Parse groups for potential role-based content
        groups_list = []
        if x_forwarded_groups:
            groups_list = [g.strip() for g in x_forwarded_groups.split(',') if g.strip()]
        
        logger.info(f"Portal demo accessed by: email={x_forwarded_email}, user_name={user_name}, groups={groups_list}")
        
        return templates.TemplateResponse(
            "pages/hccc_portal.html",
            {
                "request": request,
                "page_title": f"Portal Demo - {user_name}" if user_name else "Portal Navigation Demo",
                "page_description": "Demonstration of the new HCCC portal template with ifactory navigation",
                "user_name": user_name or "Demo User",
                "user_email": x_forwarded_email,
                "preferred_username": x_forwarded_preferred_username,
                "groups": groups_list,
                "user_role": "Faculty" if any('faculty' in g.lower() for g in groups_list) else "Staff",
            },
        )
    except Exception as e:
        logger.error(f"Error rendering portal demo page: {e}")
        return templates.TemplateResponse(
            "fragments/error.html", 
            {
                "request": request, 
                "error": "An error occurred while loading the portal demo page"
            }, 
            status_code=500,
        )

@router.get("/hccc-portal", response_class=HTMLResponse)
async def hccc_portal_page(
    request: Request,
    x_forwarded_email: Optional[str] = Header(None, alias="X-Forwarded-Email"),
    x_forwarded_preferred_username: Optional[str] = Header(None, alias="X-Forwarded-Preferred-Username"),
    x_forwarded_groups: Optional[str] = Header(None, alias="X-Forwarded-Groups"),
):
    """ Render the HCCC Faculty & Staff portal page with user personalization. """
    try:
        # Extract user name for personalization
        user_name = extract_user_name_from_email(x_forwarded_email) if x_forwarded_email else None
        
        # Parse groups for role-based content
        groups_list = []
        if x_forwarded_groups:
            groups_list = [g.strip() for g in x_forwarded_groups.split(',') if g.strip()]
        
        # Determine user role for content customization
        user_role = "Faculty & Staff"
        if any('faculty' in g.lower() for g in groups_list):
            user_role = "Faculty"
        elif any('staff' in g.lower() for g in groups_list):
            user_role = "Staff"
        
        logger.info(f"HCCC portal accessed by: email={x_forwarded_email}, user_name={user_name}, role={user_role}")
        
        return templates.TemplateResponse(
            name="pages/hccc_portal.html",
            context={
                "request": request, 
                "page_title": f"My HCCC Portal - {user_name}" if user_name else "Faculty & Staff Portal",
                "page_header": f"Welcome, {user_name}!" if user_name else "Faculty & Staff Portal",
                "user_name": user_name,
                "user_email": x_forwarded_email,
                "preferred_username": x_forwarded_preferred_username,
                "user_role": user_role,
                "groups": groups_list,
                "is_authenticated": True,
            },
        )
    except Exception as e:
        logger.error("Error in HCCC portal page", extra={"error": str(e)})
        return templates.TemplateResponse(
            name="fragments/error.html",
            context={
                "request": request, 
                "is_authenticated": True, 
                "error": "An error occurred while loading the HCCC portal"
            },
            status_code=500,
        )

@router.get("/student-home", response_class=HTMLResponse)
async def student_home_portal_page(
    request: Request,
    x_forwarded_email: Optional[str] = Header(None, alias="X-Forwarded-Email"),
    x_forwarded_preferred_username: Optional[str] = Header(None, alias="X-Forwarded-Preferred-Username"),
    x_forwarded_groups: Optional[str] = Header(None, alias="X-Forwarded-Groups"),
):
    """ Render the student home portal page with user personalization. """
    try:
        # Extract user name for personalization
        user_name = extract_user_name_from_email(x_forwarded_email) if x_forwarded_email else None
        
        # Parse groups for role-based content
        groups_list = []
        if x_forwarded_groups:
            groups_list = [g.strip() for g in x_forwarded_groups.split(',') if g.strip()]
        
        logger.info(f"Student portal accessed by: email={x_forwarded_email}, user_name={user_name}, groups={groups_list}")
        
        return templates.TemplateResponse(
            name="pages/student_homepage.html",
            context={
                "request": request, 
                "page_title": f"My HCCC Portal - {user_name}" if user_name else "My HCCC Portal - Student",
                "page_header": f"Welcome, {user_name}!" if user_name else "Welcome, Student!",
                "user_name": user_name,
                "user_email": x_forwarded_email,
                "preferred_username": x_forwarded_preferred_username,
                "groups": groups_list,
                "is_authenticated": True,
            },
        )
    except Exception as e:
        logger.error("Error in student home portal page", extra={"error": str(e)})
        return templates.TemplateResponse(
            "fragments/error.html", 
            {
                "request": request, 
                "error": "An error occurred while loading the student portal"
            }, 
            status_code=500
        )

@router.get("/hr-portal", response_class=HTMLResponse)
async def hr_portal_page(
    request: Request,
    x_forwarded_email: Optional[str] = Header(None, alias="X-Forwarded-Email"),
    x_forwarded_preferred_username: Optional[str] = Header(None, alias="X-Forwarded-Preferred-Username"),
    x_forwarded_groups: Optional[str] = Header(None, alias="X-Forwarded-Groups"),
):
    """ Render the HR portal page with user personalization. """
    try:
        # Extract user name for personalization
        user_name = extract_user_name_from_email(x_forwarded_email) if x_forwarded_email else None
        
        # Parse groups for role-based content
        groups_list = []
        if x_forwarded_groups:
            groups_list = [g.strip() for g in x_forwarded_groups.split(',') if g.strip()]
        
        # Determine if user has HR permissions
        has_hr_permissions = any('hr' in g.lower() or 'admin' in g.lower() for g in groups_list)
        
        logger.info(f"HR portal accessed by: email={x_forwarded_email}, user_name={user_name}, hr_perms={has_hr_permissions}")
        
        return templates.TemplateResponse(
            name="pages/faculty_hr.html",
            context={
                "request": request, 
                "page_title": f"Human Resources - {user_name}" if user_name else "Human Resources Portal",
                "page_header": f"Human Resources - {user_name}" if user_name else "Human Resources",
                "user_name": user_name,
                "user_email": x_forwarded_email,
                "preferred_username": x_forwarded_preferred_username,
                "groups": groups_list,
                "has_hr_permissions": has_hr_permissions,
                "is_authenticated": True,
            },
        )
    except Exception as e:
        logger.error("Error in HR portal page", extra={"error": str(e)})
        return templates.TemplateResponse(
            "fragments/error.html", 
            {
                "request": request, 
                "error": "An error occurred while loading the HR portal"
            }, 
            status_code=500
        )

@router.get("/student-academics", response_class=HTMLResponse)
async def student_academics_portal_page(
    request: Request,
    x_forwarded_email: Optional[str] = Header(None, alias="X-Forwarded-Email"),
    x_forwarded_preferred_username: Optional[str] = Header(None, alias="X-Forwarded-Preferred-Username"),
    x_forwarded_groups: Optional[str] = Header(None, alias="X-Forwarded-Groups"),
):
    """ Render the student academics portal page with user personalization. """
    try:
        # Extract user name for personalization
        user_name = extract_user_name_from_email(x_forwarded_email) if x_forwarded_email else None
        
        # Parse groups for role-based content
        groups_list = []
        if x_forwarded_groups:
            groups_list = [g.strip() for g in x_forwarded_groups.split(',') if g.strip()]
        
        # Determine academic status
        is_student = any('student' in g.lower() for g in groups_list)
        
        logger.info(f"Student academics portal accessed by: email={x_forwarded_email}, user_name={user_name}, is_student={is_student}")
        
        return templates.TemplateResponse(
            name="pages/student_academics.html",
            context={
                "request": request, 
                "page_title": f"Student Academics - {user_name}" if user_name else "Student Academics Portal",
                "page_header": f"Academic Resources - {user_name}" if user_name else "Academic Resources",
                "user_name": user_name,
                "user_email": x_forwarded_email,
                "preferred_username": x_forwarded_preferred_username,
                "groups": groups_list,
                "is_student": is_student,
                "is_authenticated": True,
            },
        )
    except Exception as e:
        logger.error("Error in student academics portal page", extra={"error": str(e)})
        return templates.TemplateResponse(
            "fragments/error.html", 
            {
                "request": request, 
                "error": "An error occurred while loading the student academics portal"
            }, 
            status_code=500
        )
