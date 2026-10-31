from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.enquiry import (
    EnquiryCreate,
    EnquiryUpdate,
    EnquiryResponse,
    EnquiryListResponse,
    EnquiryNoteCreate,
    EnquiryNoteResponse,
    EnquiryRegisterRequest,
)
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.services.enquiry_service import enquiry_service
from app.services.document_service import document_service
from app.services.email_service import EmailService
from app.core.config import settings

router = APIRouter()


@router.post(
    "",
    response_model=EnquiryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new wedding enquiry (Email or Phone)",
    tags=["Enquiry Management"]
)
def create_enquiry(
    enquiry_in: EnquiryCreate,
    db: Session = Depends(get_db)
):
    """
    Staff-facing endpoint to record an incoming wedding enquiry.
    Supports Email, Phone, and future Website channels.
    """
    return enquiry_service.create_enquiry(db=db, enquiry_in=enquiry_in)


@router.get(
    "",
    response_model=EnquiryListResponse,
    summary="List all enquiries with searching & filtering",
    tags=["Enquiry Management"]
)
def list_enquiries(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by client name, email, phone, or location"),
    status: Optional[str] = Query(None, description="Filter by status (New, Contacted, Registration Document Sent, etc.)"),
    source: Optional[str] = Query(None, description="Filter by source (Email, Phone, Website)"),
    db: Session = Depends(get_db)
):
    """
    Lists enquiries with full pagination, search, and status/source filters.
    """
    items, total = enquiry_service.list_enquiries(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        status_filter=status,
        source_filter=source
    )
    return EnquiryListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.get(
    "/{enquiry_id}",
    response_model=EnquiryResponse,
    summary="Retrieve full enquiry details",
    tags=["Enquiry Management"]
)
def get_enquiry_details(
    enquiry_id: str,
    db: Session = Depends(get_db)
):
    """
    Fetches full enquiry dossier including document history and staff notes.
    """
    enquiry = enquiry_service.get_enquiry(db=db, enquiry_id=enquiry_id)
    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enquiry '{enquiry_id}' not found."
        )
    return enquiry


@router.put(
    "/{enquiry_id}",
    response_model=EnquiryResponse,
    summary="Update enquiry details or workflow status",
    tags=["Enquiry Management"]
)
def update_enquiry(
    enquiry_id: str,
    enquiry_in: EnquiryUpdate,
    db: Session = Depends(get_db)
):
    """
    Updates enquiry information, assigned staff, or status.
    """
    updated = enquiry_service.update_enquiry(db=db, enquiry_id=enquiry_id, enquiry_in=enquiry_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enquiry '{enquiry_id}' not found."
        )
    return updated


@router.post(
    "/{enquiry_id}/notes",
    response_model=EnquiryNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an internal staff note to an enquiry",
    tags=["Enquiry Management"]
)
def add_enquiry_note(
    enquiry_id: str,
    note_in: EnquiryNoteCreate,
    db: Session = Depends(get_db)
):
    """
    Records an internal confidential staff note in the enquiry history.
    """
    return enquiry_service.add_internal_note(
        db=db,
        enquiry_id=enquiry_id,
        content=note_in.content,
        author=note_in.author or "Agency Staff"
    )


# --- Registration Documents & Email Workflows ---

@router.get(
    "/{enquiry_id}/registration-template",
    summary="Download pre-filled client registration document template (HTML printable)",
    tags=["Registration Documents"]
)
def download_blank_template(
    enquiry_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns an elegant, printable Royal Knot Client Registration Dossier template
    pre-filled with the couple's enquiry details.
    """
    enquiry = enquiry_service.get_enquiry(db=db, enquiry_id=enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Enquiry '{enquiry_id}' not found.")

    html_content = document_service.generate_blank_registration_form_html(enquiry)
    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f'inline; filename="TheRoyalKnot_RegistrationForm_{enquiry.id}.html"'
        }
    )


@router.post(
    "/{enquiry_id}/documents/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a registration document (sent to client or returned by client)",
    tags=["Registration Documents"]
)
async def upload_document(
    enquiry_id: str,
    document_type: str = Form(..., description="'sent_to_client' or 'completed_by_client'"),
    file: UploadFile = File(...),
    uploaded_by: str = Form("Agency Staff"),
    db: Session = Depends(get_db)
):
    """
    Attaches a registration document to the enquiry (e.g. customized PDF sent or filled PDF received).
    Validates file format, size, and uses safe local storage paths.
    """
    enquiry = enquiry_service.get_enquiry(db=db, enquiry_id=enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Enquiry '{enquiry_id}' not found.")

    doc = await document_service.save_uploaded_document(
        db=db,
        enquiry=enquiry,
        file=file,
        document_type=document_type,
        uploaded_by=uploaded_by
    )

    # Automatically progress status based on document type if appropriate
    if document_type == "completed_by_client" and enquiry.status in {"New", "Contacted", "Registration Document Sent"}:
        enquiry_service.mark_document_received(db=db, enquiry_id=enquiry_id)

    return doc


@router.get(
    "/{enquiry_id}/documents",
    response_model=DocumentListResponse,
    summary="List all uploaded registration documents for an enquiry",
    tags=["Registration Documents"]
)
def list_enquiry_documents(
    enquiry_id: str,
    db: Session = Depends(get_db)
):
    enquiry = enquiry_service.get_enquiry(db=db, enquiry_id=enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Enquiry '{enquiry_id}' not found.")

    docs = document_service.list_documents(db=db, enquiry_id=enquiry_id)
    return DocumentListResponse(total=len(docs), items=docs)


@router.get(
    "/{enquiry_id}/documents/{document_id}/download",
    summary="Download an uploaded registration document securely",
    tags=["Registration Documents"]
)
def download_document(
    enquiry_id: str,
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Streams the stored file safely without exposing internal server paths.
    """
    file_path, doc = document_service.get_document_path(db=db, enquiry_id=enquiry_id, document_id=document_id)
    return FileResponse(
        path=str(file_path),
        filename=doc.original_filename,
        media_type=doc.mime_type
    )


@router.post(
    "/{enquiry_id}/send-document",
    summary="Send the registration document by email and mark status as sent",
    tags=["Registration Documents"]
)
def send_registration_document(
    enquiry_id: str,
    db: Session = Depends(get_db)
):
    """
    Dispatches the registration document via email and sets enquiry status to 'Registration Document Sent'.
    """
    enquiry = enquiry_service.get_enquiry(db=db, enquiry_id=enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Enquiry '{enquiry_id}' not found.")

    template_url = f"{settings.BACKEND_BASE_URL}/api/v1/enquiries/{enquiry.id}/registration-template"
    email_result = EmailService.send_registration_document_email(
        to_email=enquiry.email,
        client_name=enquiry.client_name,
        enquiry_id=enquiry.id,
        document_download_url=template_url
    )

    enquiry_service.mark_document_sent(db=db, enquiry_id=enquiry_id)

    return {
        "success": True,
        "message": f"Registration document sent to {enquiry.email}.",
        "email_delivery": email_result,
        "enquiry_status": "Registration Document Sent"
    }


@router.post(
    "/{enquiry_id}/mark-document-received",
    summary="Manually record that the completed registration document was received",
    tags=["Registration Documents"]
)
def mark_document_received(
    enquiry_id: str,
    db: Session = Depends(get_db)
):
    """
    Records receipt of the completed client registration document.
    """
    updated = enquiry_service.mark_document_received(db=db, enquiry_id=enquiry_id)
    return {
        "success": True,
        "message": "Completed registration document marked as received.",
        "status": updated.status,
        "received_at": updated.registration_received_at
    }


# --- Client Registration from Enquiry ---

@router.post(
    "/{enquiry_id}/register",
    summary="Register client, create pending account, and send activation link",
    tags=["Client Registration"]
)
def register_client(
    enquiry_id: str,
    register_data: EnquiryRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Explicit staff action: Converts an enquiry into a registered client dossier,
    creates a pending client account, generates a secure activation token,
    and sends the activation email.
    """
    result = enquiry_service.register_client_from_enquiry(
        db=db,
        enquiry_id=enquiry_id,
        register_data=register_data
    )
    return result
