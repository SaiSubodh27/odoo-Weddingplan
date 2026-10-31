from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.registration import ClientRegistration
from app.schemas.registration import (
    ClientRegistrationSubmitRequest,
    ClientRegistrationResponse,
    RegistrationVerifyResponse,
    GoogleFormsConfigUpdate,
    GoogleFormsConfigResponse,
    RegistrationAssociateRequest,
)
from app.services.registration_service import registration_service
from app.services.google_sheets_service import GoogleSheetsService
from app.core.config import settings

router = APIRouter()


# --- Google Forms Webhook & Import Endpoints ---

@router.post(
    "/google-forms-webhook",
    status_code=status.HTTP_200_OK,
    summary="Webhook endpoint for Google Forms submissions (Google Apps Script)",
    tags=["Google Forms Integration"]
)
async def receive_google_forms_webhook(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Receives JSON payload from a Google Apps Script trigger onFormSubmit(e),
    maps responses into PostgreSQL, deduplicates, and matches against open enquiries.
    """
    response_id = payload.get("response_id") or payload.get("id")
    result = GoogleSheetsService.ingest_single_response(
        db=db,
        raw_data=payload,
        response_id=str(response_id) if response_id else None,
        source="Google Forms Webhook"
    )
    return result


@router.post(
    "/import-csv",
    status_code=status.HTTP_200_OK,
    summary="Upload and import Google Forms / Google Sheets CSV export",
    tags=["Google Forms Integration"]
)
async def import_google_forms_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Staff action: Uploads a downloaded .csv file from Google Sheets or Google Forms.
    Parses each row, deduplicates by email/timestamp, and automatically matches to enquiries.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a .csv file."
        )

    content_bytes = await file.read()
    try:
        csv_text = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        csv_text = content_bytes.decode("latin-1", errors="replace")

    stats = GoogleSheetsService.ingest_csv_content(
        db=db,
        csv_text=csv_text,
        source=f"CSV Upload ({file.filename})"
    )
    return {
        "success": True,
        "filename": file.filename,
        "message": f"Successfully parsed {stats['total_rows']} rows: {stats['imported']} imported ({stats['matched']} matched, {stats['unmatched']} unmatched), {stats['duplicates_skipped']} duplicates skipped.",
        "stats": stats
    }


@router.post(
    "/sync-google-sheet",
    summary="Trigger live sync from linked Google Sheet CSV export",
    tags=["Google Forms Integration"]
)
def sync_google_sheet(
    sheet_id: Optional[str] = Query(None, description="Optional Google Sheet ID override"),
    db: Session = Depends(get_db)
):
    """
    Staff action: Fetches the public/published CSV export from the configured Google Sheet
    and imports all new client submissions.
    """
    result = GoogleSheetsService.sync_google_sheet(db=db, sheet_id=sheet_id)
    return result


# --- Google Forms Configuration Endpoints ---

@router.get(
    "/config",
    response_model=GoogleFormsConfigResponse,
    summary="Get Google Forms & Google Sheets configuration",
    tags=["Google Forms Integration"]
)
def get_google_forms_config():
    """
    Returns currently configured Google Forms URL, Google Sheet ID, and Webhook URL.
    """
    webhook_url = f"{settings.BACKEND_BASE_URL}/api/v1/registrations/google-forms-webhook"
    return GoogleFormsConfigResponse(
        google_forms_registration_url=settings.GOOGLE_FORMS_REGISTRATION_URL,
        google_sheet_id=settings.GOOGLE_SHEET_ID,
        google_sheet_csv_url=settings.GOOGLE_SHEET_CSV_URL,
        webhook_url=webhook_url,
        agency_email=settings.AGENCY_EMAIL
    )


@router.put(
    "/config",
    response_model=GoogleFormsConfigResponse,
    summary="Update Google Forms & Google Sheets configuration",
    tags=["Google Forms Integration"]
)
def update_google_forms_config(
    config_in: GoogleFormsConfigUpdate
):
    """
    Updates the runtime Google Forms URL and Google Sheet ID.
    """
    if config_in.google_forms_registration_url:
        settings.GOOGLE_FORMS_REGISTRATION_URL = config_in.google_forms_registration_url.strip()
    if config_in.google_sheet_id is not None:
        settings.GOOGLE_SHEET_ID = config_in.google_sheet_id.strip() if config_in.google_sheet_id else None
    if config_in.google_sheet_csv_url is not None:
        settings.GOOGLE_SHEET_CSV_URL = config_in.google_sheet_csv_url.strip() if config_in.google_sheet_csv_url else None

    webhook_url = f"{settings.BACKEND_BASE_URL}/api/v1/registrations/google-forms-webhook"
    return GoogleFormsConfigResponse(
        google_forms_registration_url=settings.GOOGLE_FORMS_REGISTRATION_URL,
        google_sheet_id=settings.GOOGLE_SHEET_ID,
        google_sheet_csv_url=settings.GOOGLE_SHEET_CSV_URL,
        webhook_url=webhook_url,
        agency_email=settings.AGENCY_EMAIL
    )


# --- Registration List & Management ---

@router.get(
    "",
    response_model=List[ClientRegistrationResponse],
    summary="List client registrations with optional status filter",
    tags=["Client Registration"]
)
def list_registrations(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status, e.g. UNMATCHED, SUBMITTED"),
    db: Session = Depends(get_db)
):
    """
    Returns submitted registrations. Can be filtered by UNMATCHED to review submissions
    that could not be linked to an enquiry automatically.
    """
    query = db.query(ClientRegistration)
    if status_filter and status_filter != "ALL":
        query = query.filter(ClientRegistration.status == status_filter)
    return query.order_by(ClientRegistration.submitted_at.desc()).all()


@router.post(
    "/{registration_id}/associate",
    summary="Manually associate an unmatched registration with an enquiry",
    tags=["Client Registration"]
)
def associate_unmatched_registration(
    registration_id: str,
    req: RegistrationAssociateRequest,
    db: Session = Depends(get_db)
):
    """
    Staff action: Associates an UNMATCHED Google Forms registration with a chosen Enquiry.
    Updates the enquiry's wedding parameters and sets registration status to 'SUBMITTED'.
    """
    result = GoogleSheetsService.associate_unmatched_registration(
        db=db,
        registration_id=registration_id,
        enquiry_id=req.enquiry_id,
        staff_name=req.staff_name
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Failed to associate registration.")
        )
    return result


# --- Legacy / Direct Form Endpoints (Maintained for Compatibility) ---

@router.get(
    "/verify",
    response_model=RegistrationVerifyResponse,
    summary="Verify registration token from client invitation email",
    tags=["Client Online Registration"]
)
def verify_registration_token(
    token: str = Query(..., description="Secure registration token"),
    db: Session = Depends(get_db)
):
    return registration_service.verify_token(db=db, token=token)


@router.post(
    "/submit",
    status_code=status.HTTP_201_CREATED,
    summary="Direct client registration form submit",
    tags=["Client Online Registration"]
)
def submit_registration_form(
    req: ClientRegistrationSubmitRequest,
    db: Session = Depends(get_db)
):
    return registration_service.submit_registration(db=db, req=req)
