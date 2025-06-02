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

@router.get("/portal-demo", response_class=HTMLResponse)
async def portal_demo_page(request: Request): # Renamed
    """ Portal navigation demo page. (Moved from pages.py) """
    try:
        # Use the existing hccc_portal template as a demo for now
        return templates.TemplateResponse(
            "pages/hccc_portal.html",
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
            "fragments/error.html", {"error": "An error occurred while loading the portal demo page"}, status_code=500,
        )

@router.get("/hccc-portal", response_class=HTMLResponse)
async def hccc_portal_page(request: Request): # Renamed from hccc_portal
    """ Render the HCCC portal page. (Moved from pages.py) """
    try:
        return templates.TemplateResponse(
            name="pages/hccc_portal.html",
            context={"request": request, "is_authenticated": True}, # Assuming auth, request already in context_processor
        )
    except Exception as e:
        logger.error("Error in HCCC portal page", extra={"error": str(e)})
        return templates.TemplateResponse( # Consider a generic error page
            name="fragments/error.html",
            context={"request": request, "is_authenticated": True, "error": "An error occurred while loading the HCCC portal"},
            status_code=500,
        )

@router.get("/student-home", response_class=HTMLResponse)
async def student_home_portal_page(request: Request): # Renamed from student_home_portal
    """ Render the student home portal page. (Moved from pages.py) """
    try:
        return templates.TemplateResponse(
            name="pages/student_homepage.html",  # Fixed: use correct template name
            context={"request": request, "is_authenticated": True}, # Assuming auth, request already in context_processor
        )
    except Exception as e:
        logger.error("Error in student home portal page", extra={"error": str(e)})
        return templates.TemplateResponse("fragments/error.html", {"request": request, "error": "An error occurred while loading the student portal"}, status_code=500)

@router.get("/hr-portal", response_class=HTMLResponse)
async def hr_portal_page(request: Request): # Renamed from hr_portal
    """ Render the HR portal page. (Moved from pages.py) """
    try:
        # Assuming HR portal has specific data or permissions
        # For now, using a generic template
        return templates.TemplateResponse(
            name="pages/faculty_hr.html",  # Fixed: use correct template name
            context={"request": request, "is_authenticated": True}, # Assuming auth, request already in context_processor
        )
    except Exception as e:
        logger.error("Error in HR portal page", extra={"error": str(e)})
        return templates.TemplateResponse("fragments/error.html", {"request": request, "error": "An error occurred while loading the HR portal"}, status_code=500)

@router.get("/student-academics", response_class=HTMLResponse)
async def student_academics_portal_page(request: Request): # Renamed from student_academics_portal
    """ Render the student academics portal page. (Moved from pages.py) """
    try:
        # Assuming student academics portal has specific data
        # For now, using a generic template
        return templates.TemplateResponse(
            name="pages/student_academics.html",
            context={"request": request, "is_authenticated": True}, # Assuming auth, request already in context_processor
        )
    except Exception as e:
        logger.error("Error in student academics portal page", extra={"error": str(e)})
        return templates.TemplateResponse("fragments/error.html", {"request": request, "error": "An error occurred while loading the student academics portal"}, status_code=500)
