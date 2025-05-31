import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, Response # Response for 204 No Content
from fastapi.templating import Jinja2Templates
from datetime import datetime # For current_year

from app.core.config import settings
from app.schemas.common import QRType # For path parameter
from app.schemas.qr import QRCodeResponse, StaticQRCreateParameters, DynamicQRCreateParameters, QRUpdateParameters # For request/response models
from app.services.qr_creation_service import QRCreationService
from app.services.qr_update_service import QRUpdateService
from app.services.qr_retrieval_service import QRRetrievalService
from app.dependencies import get_qr_creation_service, get_qr_update_service, get_qr_retrieval_service
from app.core.exceptions import QRCodeNotFoundError, QRCodeValidationError, RedirectURLError, DatabaseError


# Dependency types
QRCreationServiceDep = Annotated[QRCreationService, Depends(get_qr_creation_service)]
QRUpdateServiceDep = Annotated[QRUpdateService, Depends(get_qr_update_service)]
QRRetrievalServiceDep = Annotated[QRRetrievalService, Depends(get_qr_retrieval_service)]

# Templates setup
def get_base_template_context(request: Request) -> dict:
    # request.scope["scheme"] = "https"
    return {
        "request": request,
        "app_version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "current_year": datetime.now().year, # Corrected to use datetime
        "api_base_url": "/api/v1",
    }

templates = Jinja2Templates(
    directory=str(settings.TEMPLATES_DIR / "fragments"), # Assuming fragments are in a subfolder
    context_processors=[get_base_template_context],
)

logger = logging.getLogger("app.qr_form_fragments")
router = APIRouter(
    prefix="/fragments", # Common prefix for these fragments
    tags=["Fragments - QR Forms"],
    responses={404: {"description": "Not found"}},
)

# Corrected template directory path to not assume "fragments" subdirectory in path names
templates = Jinja2Templates(
    directory=str(settings.TEMPLATES_DIR / "fragments"),
    context_processors=[get_base_template_context],
)

@router.get("/qr-form/{qr_type}", response_class=HTMLResponse)
async def get_qr_form_fragment(request: Request, qr_type: str):
    """ Get the QR code creation form fragment. (Moved from fragments.py) """
    if qr_type not in ["static", "dynamic"]:
        raise HTTPException(status_code=400, detail="Invalid QR type")
    return templates.TemplateResponse(
        "qr_form.html", # Template path relative to 'fragments'
        {"qr_type": qr_type, "error_levels": ["L", "M", "Q", "H"]}
    )

@router.post("/qr-create", response_class=HTMLResponse)
async def create_qr_code_fragment( # Renamed from create_qr_code
    request: Request,
    qr_creation_service: QRCreationServiceDep, # Changed dependency
    qr_type: str = Form(...),
    content: Optional[str] = Form(None), # Made Optional
    title: str = Form(...),
    description: Optional[str] = Form(None), # Made Optional
    redirect_url: Optional[str] = Form(None), # Made Optional
    error_level: str = Form("M"),
    # Removed unused image generation params like svg_title, include_logo for create operation
):
    """ Create a QR code from form submission. (Moved from fragments.py) """
    try:
        logger.info(f"Creating {qr_type} QR code fragment with title: {title}")
        error_level_enum = ErrorCorrectionLevel(error_level.lower())

        qr_data: QRCode # To hold the created QR object
        if qr_type == "static":
            params = StaticQRCreateParameters(
                content=content, title=title, description=description, error_level=error_level_enum
            )
            qr_data = await qr_creation_service.create_static_qr(params)
        elif qr_type == "dynamic":
            params = DynamicQRCreateParameters(
                redirect_url=redirect_url, title=title, description=description, error_level=error_level_enum
            )
            qr_data = await qr_creation_service.create_dynamic_qr(params)
        else:
            raise HTTPException(status_code=400, detail="Invalid QR type for creation")

        # Return 204 No Content with HX-Trigger header to redirect on client-side
        response = Response(status_code=status.HTTP_204_NO_CONTENT)
        import json
        response.headers["HX-Trigger"] = json.dumps({"qrCreated": {"id": qr_data.id}})
        return response

    except (QRCodeValidationError, RedirectURLError) as e:
        # Re-render form with errors
        return templates.TemplateResponse(
            "qr_form.html",
            {
                "qr_type": qr_type, "content": content, "title": title, "description": description,
                "redirect_url": redirect_url, "error_level": error_level.upper(),
                "error_messages": e.errors() if isinstance(e, ValidationError) else [{"msg": str(e), "loc": ["form"]}],
                "error_levels": ["L", "M", "Q", "H"]
            },
            status_code=422 # Unprocessable Entity for validation errors
        )
    except Exception as e:
        logger.error(f"Error creating QR code fragment: {str(e)}")
        return templates.TemplateResponse("error.html", {"error": str(e)}, status_code=500)


@router.get("/qr-edit-form/{qr_id}", response_class=HTMLResponse)
async def get_qr_edit_form_fragment( # This was get_qr_edit_form_fragment in fragments.py
    request: Request,
    qr_id: str,
    qr_retrieval_service: QRRetrievalServiceDep, # Changed dependency
):
    """ Get the QR code edit form fragment for the analytics page. (Moved from fragments.py) """
    try:
        qr = await qr_retrieval_service.get_qr_by_id(qr_id)
        return templates.TemplateResponse("qr_edit_form.html", {"qr": qr})
    except QRCodeNotFoundError:
        return templates.TemplateResponse("error.html", {"error": f"QR code with ID {qr_id} not found."}, status_code=404)
    except Exception as e:
        logger.error(f"Error retrieving QR code for editing: {str(e)}")
        return templates.TemplateResponse("error.html", {"error": f"An error occurred: {str(e)}"}, status_code=500)

@router.get("/qr-edit/{qr_id}", response_class=HTMLResponse) # As per subtask, this is distinct
async def get_qr_edit_modal_fragment( # Renamed to differentiate
    request: Request,
    qr_id: str,
    qr_retrieval_service: QRRetrievalServiceDep, # Changed dependency
):
    """ Get the QR code edit modal fragment. (Moved from fragments.py, was get_qr_edit_fragment) """
    try:
        # The original logic returned an HX-Redirect. If this is for a modal, it should return the modal content.
        # Assuming it's for a modal edit form, similar to qr_edit_form.html but perhaps simpler or for a different context.
        qr = await qr_retrieval_service.get_qr_by_id(qr_id)
        # The original fragments.py /qr-edit/{qr_id} returned HX-Redirect.
        # If this is still desired, then:
        # response = HTMLResponse(content="Redirecting...", status_code=200)
        # response.headers["HX-Redirect"] = f"/qr/{qr_id}/analytics" # Or another appropriate page
        # return response
        # For now, let's assume it's meant to return a form fragment, similar to qr_edit_form.html, maybe for a modal.
        return templates.TemplateResponse("qr_edit.html", {"qr": qr}) # Assuming qr_edit.html exists
    except QRCodeNotFoundError:
        return templates.TemplateResponse("error.html", {"error": f"QR code with ID {qr_id} not found."}, status_code=404)
    except Exception as e:
        logger.error(f"Error retrieving QR code for edit modal: {str(e)}")
        return templates.TemplateResponse("error.html", {"error": f"An error occurred: {str(e)}"}, status_code=500)


@router.post("/qr-update/{qr_id}", response_class=HTMLResponse)
async def update_qr_code_fragment( # Renamed from update_qr_code
    request: Request,
    qr_id: str,
    qr_update_service: QRUpdateServiceDep, # Changed dependency
    qr_retrieval_service: QRRetrievalServiceDep, # For fetching QR data for form re-render on error
    redirect_url: Optional[str] = Form(None), # Made Optional
    title: Optional[str] = Form(None), # Made Optional
    description: Optional[str] = Form(None), # Made Optional
):
    """ Update a QR code. (Moved from fragments.py) """
    logger.info(f"Updating QR code fragment {qr_id} - Title: '{title}', Description: '{description}', Redirect URL: '{redirect_url}'")
    try:
        params = QRUpdateParameters(
            redirect_url=redirect_url, title=title, description=description
        )
        await qr_update_service.update_qr(qr_id, params) # Use update service

        # Respond with HX-Redirect to analytics page or another appropriate target
        response = HTMLResponse(content="QR Code updated successfully. Redirecting...")
        response.headers["HX-Redirect"] = f"/qr/{qr_id}/analytics" # Or use url_for if available
        return response
    except (QRCodeNotFoundError, QRCodeValidationError, RedirectURLError) as e:
        # Re-render edit form with errors
        try:
            qr = await qr_retrieval_service.get_qr_by_id(qr_id) # Fetch current data
            # Determine which form to render based on HX-Target or other headers if needed
            # For simplicity, assume qr_edit_form.html or qr_edit.html
            # Original logic had different templates based on HX-Target
            template_name = "qr_edit_form.html" # Default, adjust if needed
            if request.headers.get("HX-Target") and "qr-edit-form-container" not in request.headers.get("HX-Target"):
                 template_name = "qr_edit.html" # If not the analytics page inline form

            return templates.TemplateResponse(
                template_name,
                {
                    "qr": qr, "redirect_url": redirect_url, "title": title, "description": description,
                    "error_messages": e.errors() if isinstance(e, ValidationError) else [{"msg": str(e), "loc": ["form"]}]
                },
                status_code=422
            )
        except QRCodeNotFoundError: # If QR not found even for re-rendering form
             return templates.TemplateResponse("error.html", {"error": f"QR code with ID {qr_id} not found."}, status_code=404)
        except Exception as fetch_err: # Catch error during fetch for re-render
            logger.error(f"Error fetching QR for form re-render: {fetch_err}")
            return templates.TemplateResponse("error.html", {"error": "Error processing update."}, status_code=500)

    except Exception as e:
        logger.error(f"Error updating QR code fragment: {str(e)}")
        return templates.TemplateResponse("error.html", {"error": f"An error occurred: {str(e)}"}, status_code=500)

@router.get("/qr-edit-form-cancel/{qr_id}", response_class=HTMLResponse)
async def cancel_qr_edit_form_fragment( # Renamed from cancel_qr_edit_form
    request: Request, # Added request
    qr_id: str, # qr_id is part of path, not a query param
):
    """ Cancel the QR code edit form and return an empty response. (Moved from fragments.py) """
    return HTMLResponse(content="")
