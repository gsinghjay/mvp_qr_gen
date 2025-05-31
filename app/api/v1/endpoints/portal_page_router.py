import logging
from typing import Annotated, Optional # Ensure Optional is imported

from fastapi import APIRouter, Depends, Request, Header # Ensure Header is imported
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime # For current_year in context

from app.core.config import settings

templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))
logger = logging.getLogger("app.portal_pages")

router = APIRouter(
    tags=["Pages - HCCC Portal"],
    responses={404: {"description": "Not found"}},
from app.core.exceptions import DatabaseError # Though not directly used, good for consistency if error handling evolves

# Context processor similar to pages.py
def get_base_template_context(request: Request) -> dict:
    request.scope["scheme"] = "https" # Assuming HTTPS for all portal pages
    return {
        "request": request,
        "app_version": "1.0.0", # Example, consider centralizing
        "environment": settings.ENVIRONMENT,
        "current_year": datetime.now().year,
        "api_base_url": "/api/v1", # Or whatever is appropriate for portal context
    }

templates = Jinja2Templates(
    directory=str(settings.TEMPLATES_DIR),
    context_processors=[get_base_template_context],
)

@router.get("/portal-demo", response_class=HTMLResponse)
async def portal_demo_page(request: Request): # Renamed
    """ Portal navigation demo page. (Moved from pages.py) """
    try:
        return templates.TemplateResponse(
            "pages/portal_demo.html",
            {
                "page_title": "Portal Navigation Demo",
                "page_description": "Demonstration of the new HCCC portal template with ifactory navigation",
                "user_name": "Demo User", # Example user data
                "user_role": "Faculty",   # Example user data
            },
        )
    except Exception as e:
        logger.error(f"Error rendering portal demo page: {e}")
        return templates.TemplateResponse( # Consider a generic error page
            "error.html", {"error": "An error occurred while loading the portal demo page"}, status_code=500,
        )

@router.get("/hccc-portal", response_class=HTMLResponse)
async def hccc_main_portal_page(request: Request): # Renamed
    """ HCCC Portal homepage. (Moved from pages.py) """
    try:
        return templates.TemplateResponse(
            "pages/hccc_portal.html",
            {
                "page_title": "My HCCC Portal - Faculty & Staff",
                "page_description": "Hudson County Community College Faculty and Staff Portal",
                "page_header": "My HCCC Portal",
                "show_alert": True,
                "alert_title": "Portal Launch",
                "alert_message": "Welcome to the new HCCC Faculty & Staff Portal with enhanced navigation and resources.",
                "alert_link": "#",
            },
        )
    except Exception as e:
        logger.error(f"Error rendering HCCC portal page: {e}")
        return templates.TemplateResponse("error.html", {"error": "An error occurred while loading the HCCC portal"}, status_code=500)

@router.get("/student-portal", response_class=HTMLResponse)
async def student_home_portal_page( # Renamed
    request: Request,
    x_forwarded_email: Optional[str] = Header(None, alias="X-Forwarded-Email"),
    x_forwarded_preferred_username: Optional[str] = Header(None, alias="X-Forwarded-Preferred-Username"),
):
    """ HCCC Student Portal homepage. (Moved from pages.py) """
    try:
        user_name = None
        if x_forwarded_email:
            user_part = x_forwarded_email.split('@')[0]
            if '.' in user_part: user_name = user_part.split('.')[0].title()
        elif x_forwarded_preferred_username:
            user_part = x_forwarded_preferred_username.split('@')[0]
            if '.' in user_part: user_name = user_part.split('.')[0].title()

        return templates.TemplateResponse(
            "pages/student_homepage.html",
            {
                "page_title": "My HCCC Portal - Student",
                "page_description": "Hudson County Community College Student Portal",
                "page_header": "My HCCC Student Portal",
                "user_name": user_name,
                "email": x_forwarded_email,
                "preferred_username": x_forwarded_preferred_username,
                "show_alert": True,
                "alert_title": "Important Reminder",
                "alert_message": "Finals week is approaching! Don't forget to check your final exam schedule and visit the tutoring center for help.",
                "alert_link": "#",
            },
        )
    except Exception as e:
        logger.error(f"Error rendering student portal page: {e}")
        return templates.TemplateResponse("error.html", {"error": "An error occurred while loading the student portal"}, status_code=500)

@router.get("/faculty-hr", response_class=HTMLResponse)
async def faculty_hr_main_portal_page( # Renamed
    request: Request,
    x_forwarded_email: Optional[str] = Header(None, alias="X-Forwarded-Email"),
    x_forwarded_preferred_username: Optional[str] = Header(None, alias="X-Forwarded-Preferred-Username"),
):
    """ HCCC Faculty & Staff HR Portal. (Moved from pages.py) """
    try:
        user_name = None
        if x_forwarded_email:
            user_part = x_forwarded_email.split('@')[0]
            if '.' in user_part: user_name = user_part.split('.')[0].title()
        elif x_forwarded_preferred_username:
            user_part = x_forwarded_preferred_username.split('@')[0]
            if '.' in user_part: user_name = user_part.split('.')[0].title()

        return templates.TemplateResponse(
            "pages/faculty_hr.html",
            {
                "page_title": "Human Resources - Faculty & Staff Portal",
                "page_description": "Hudson County Community College Faculty & Staff HR Portal",
                "page_header": "Human Resources Portal",
                "user_name": user_name,
                "email": x_forwarded_email,
                "preferred_username": x_forwarded_preferred_username,
            },
        )
    except Exception as e:
        logger.error(f"Error rendering faculty HR portal page: {e}")
        return templates.TemplateResponse("error.html", {"error": "An error occurred while loading the HR portal"}, status_code=500)

@router.get("/student-academics", response_class=HTMLResponse)
async def student_academics_main_portal_page( # Renamed
    request: Request,
    x_forwarded_email: Optional[str] = Header(None, alias="X-Forwarded-Email"),
    x_forwarded_preferred_username: Optional[str] = Header(None, alias="X-Forwarded-Preferred-Username"),
):
    """ HCCC Student Academics Portal. (Moved from pages.py) """
    try:
        user_name = None
        if x_forwarded_email:
            user_part = x_forwarded_email.split('@')[0]
            if '.' in user_part: user_name = user_part.split('.')[0].title()
        elif x_forwarded_preferred_username:
            user_part = x_forwarded_preferred_username.split('@')[0]
            if '.' in user_part: user_name = user_part.split('.')[0].title()

        return templates.TemplateResponse(
            "pages/student_academics.html",
            {
                "page_title": "Student Academics - Student Portal",
                "page_description": "Hudson County Community College Student Academics Portal",
                "page_header": "Student Academics Portal",
                "user_name": user_name,
                "email": x_forwarded_email,
                "preferred_username": x_forwarded_preferred_username,
            },
        )
    except Exception as e:
        logger.error(f"Error rendering student academics portal page: {e}")
        return templates.TemplateResponse("error.html", {"error": "An error occurred while loading the student academics portal"}, status_code=500)
