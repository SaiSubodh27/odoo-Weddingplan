import os
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from fastapi.responses import FileResponse, Response
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
from app.schemas.email_message import EmailMessageResponse, EmailReplyRequest
from app.models.email_message import EmailMessage
from app.models.document import RegistrationDocument
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
    return enquiry_service.add_note(
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
def get_registration_template(
    enquiry_id: str,
    download: bool = Query(False, description="Trigger file download instead of inline view"),
    db: Session = Depends(get_db)
):
    """
    Generates a personalized, printable/downloadable HTML registration form for this client.
    """
    enquiry = enquiry_service.get_enquiry(db=db, enquiry_id=enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Enquiry '{enquiry_id}' not found.")

    html_content = document_service.generate_blank_registration_form_html(enquiry)
    headers = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="The_Royal_Knot_Registration_Dossier_{enquiry.id}.html"'
    return Response(content=html_content, media_type="text/html", headers=headers)


@router.post(
    "/{enquiry_id}/documents/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload sent or received registration document",
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

    # Automatically progress status based on document type
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
    summary="Download or view an uploaded registration document securely",
    tags=["Registration Documents"]
)
def download_document(
    enquiry_id: str,
    document_id: str,
    inline: bool = Query(False, description="Whether to display inline in browser or trigger download"),
    db: Session = Depends(get_db)
):
    """
    Streams the stored file safely without exposing internal server paths.
    """
    file_path, doc = document_service.get_document_path(db=db, enquiry_id=enquiry_id, document_id=document_id)
    content_disposition = "inline" if inline else "attachment"
    return FileResponse(
        path=str(file_path),
        filename=doc.original_filename,
        media_type=doc.mime_type,
        content_disposition_type=content_disposition
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
    Dispatches the registration document via email, logs outgoing EmailMessage,
    attaches the official registration document, and updates status to 'Registration Document Sent'.
    """
    enquiry = enquiry_service.get_enquiry(db=db, enquiry_id=enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Enquiry '{enquiry_id}' not found.")

    template_url = f"{settings.BACKEND_BASE_URL}/api/v1/enquiries/{enquiry.id}/registration-template"

    # Check if a registration document already exists; if not, automatically generate and save one
    sent_doc = db.query(RegistrationDocument).filter(
        RegistrationDocument.enquiry_id == enquiry.id,
        RegistrationDocument.document_type == "sent_to_client"
    ).order_by(RegistrationDocument.created_at.desc()).first()

    if not sent_doc:
        sent_doc = document_service.generate_and_save_registration_document(db=db, enquiry=enquiry)

    doc_attachment = None
    if sent_doc:
        doc_path = Path(settings.UPLOAD_DIR) / sent_doc.stored_filename
        if doc_path.exists():
            with open(doc_path, "rb") as f:
                doc_attachment = {
                    "filename": sent_doc.original_filename,
                    "stored_filename": sent_doc.stored_filename,
                    "content": f.read(),
                    "mime_type": sent_doc.mime_type or "text/html"
                }

    email_result = EmailService.send_registration_document_email(
        to_email=enquiry.email,
        client_name=enquiry.client_name,
        enquiry_id=enquiry.id,
        document_download_url=template_url,
        document_attachment=doc_attachment,
        db=db
    )

    if not email_result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to dispatch registration document email: {email_result.get('message', 'SMTP transmission failed')}"
        )

    enquiry_service.mark_document_sent(db=db, enquiry_id=enquiry_id)

    # Note
    enquiry_service.add_note(
        db=db,
        enquiry_id=enquiry_id,
        author="Agency Staff",
        content=f"Dispatched formal Client Registration Document with attachment to {enquiry.email}."
    )

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
    enquiry_service.add_note(
        db=db,
        enquiry_id=enquiry_id,
        author="Agency Staff",
        content="Marked completed registration document as received."
    )
    return {
        "success": True,
        "message": "Completed registration document marked as received.",
        "status": updated.status,
        "received_at": updated.registration_received_at
    }


@router.post(
    "/{enquiry_id}/mark-document-reviewed",
    summary="Mark a client-returned document as reviewed by staff",
    tags=["Registration Documents"]
)
def mark_document_reviewed(
    enquiry_id: str,
    document_id: Optional[str] = Query(None, description="Specific document ID to review"),
    reviewed_by: str = Query("Agency Staff", description="Staff member who reviewed the document"),
    db: Session = Depends(get_db)
):
    """
    Marks the completed client registration document as reviewed and updates enquiry status to 'Under Review'.
    """
    enquiry = enquiry_service.get_enquiry(db=db, enquiry_id=enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Enquiry '{enquiry_id}' not found.")

    if not document_id:
        # Find latest completed document
        latest_doc = db.query(RegistrationDocument).filter(
            RegistrationDocument.enquiry_id == enquiry_id,
            RegistrationDocument.document_type == "completed_by_client"
        ).order_by(RegistrationDocument.created_at.desc()).first()

        if not latest_doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No client-returned completed document found to review."
            )
        document_id = latest_doc.id

    doc = document_service.mark_document_reviewed(
        db=db,
        enquiry_id=enquiry_id,
        document_id=document_id,
        reviewed_by=reviewed_by
    )

    return {
        "success": True,
        "message": f"Document '{doc.original_filename}' marked as reviewed by {reviewed_by}.",
        "document_id": doc.id,
        "enquiry_status": "Under Review"
    }


# --- Email Conversation Thread & Staff Replies ---

@router.get(
    "/{enquiry_id}/messages",
    response_model=List[EmailMessageResponse],
    summary="Get full email conversation thread for this enquiry",
    tags=["Email Integration"]
)
def get_enquiry_messages(
    enquiry_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns all incoming and outgoing email messages associated with this enquiry chronologically.
    """
    enquiry = enquiry_service.get_enquiry(db=db, enquiry_id=enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Enquiry '{enquiry_id}' not found.")

    messages = db.query(EmailMessage).filter(
        EmailMessage.enquiry_id == enquiry_id
    ).order_by(EmailMessage.created_at.asc()).all()

    res = []
    for m in messages:
        att_res = []
        for a in m.attachments:
            att_res.append({
                "id": a.id,
                "emailMessageId": a.email_message_id,
                "originalFilename": a.original_filename,
                "fileSize": a.file_size,
                "mimeType": a.mime_type,
                "createdAt": a.created_at,
                "downloadUrl": f"{settings.BACKEND_BASE_URL}/api/v1/emails/{m.id}/attachments/{a.id}/download"
            })

        res.append(
            EmailMessageResponse(
                id=m.id,
                enquiryId=m.enquiry_id,
                direction=m.direction,
                senderName=m.sender_name,
                senderEmail=m.sender_email,
                recipientEmail=m.recipient_email,
                subject=m.subject,
                bodyText=m.body_text,
                bodyHtml=m.body_html,
                messageId=m.message_id,
                threadId=m.thread_id,
                inReplyTo=m.in_reply_to,
                status=m.status,
                errorMessage=m.error_message,
                receivedAt=m.received_at,
                sentAt=m.sent_at,
                createdAt=m.created_at,
                attachments=att_res
            )
        )
    return res


@router.post(
    "/{enquiry_id}/reply",
    summary="Send staff reply to client via email",
    tags=["Email Integration"]
)
def reply_to_enquiry(
    enquiry_id: str,
    reply_req: EmailReplyRequest,
    db: Session = Depends(get_db)
):
    """
    Sends an email reply to the client, preserving email threading headers (In-Reply-To/References),
    logging the outbound EmailMessage, and adding an internal staff note.
    """
    enquiry = enquiry_service.get_enquiry(db=db, enquiry_id=enquiry_id)
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Enquiry '{enquiry_id}' not found.")

    # Find last message for threading headers if not supplied
    in_reply_to = reply_req.in_reply_to
    if not in_reply_to:
        last_incoming = db.query(EmailMessage).filter(
            EmailMessage.enquiry_id == enquiry_id,
            EmailMessage.direction == "incoming"
        ).order_by(EmailMessage.created_at.desc()).first()
        if last_incoming:
            in_reply_to = last_incoming.message_id

    subject = reply_req.subject or f"The Royal Knot — Concerning Your Wedding Enquiry ({enquiry.id})"

    # Optional attachments
    attachments = None
    if reply_req.attach_registration_document:
        sent_doc = db.query(RegistrationDocument).filter(
            RegistrationDocument.enquiry_id == enquiry.id,
            RegistrationDocument.document_type == "sent_to_client"
        ).order_by(RegistrationDocument.created_at.desc()).first()

        if sent_doc:
            doc_path = Path(settings.UPLOAD_DIR) / sent_doc.stored_filename
            if doc_path.exists():
                with open(doc_path, "rb") as f:
                    attachments = [{
                        "filename": sent_doc.original_filename,
                        "stored_filename": sent_doc.stored_filename,
                        "content": f.read(),
                        "mime_type": sent_doc.mime_type
                    }]

    send_result = EmailService.send_reply_email(
        to_email=enquiry.email,
        client_name=enquiry.client_name,
        subject=subject,
        body=reply_req.body,
        enquiry_id=enquiry.id,
        in_reply_to=in_reply_to,
        attachments=attachments,
        db=db
    )

    # Add staff note
    enquiry_service.add_note(
        db=db,
        enquiry_id=enquiry_id,
        author="Agency Staff (Email Reply)",
        content=f"Sent email reply to {enquiry.email}:\n\"{reply_req.body[:200]}...\""
    )

    return {
        "success": send_result.get("success", False),
        "message": send_result.get("message", "Reply processed."),
        "mode": send_result.get("mode"),
        "delivery": send_result
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
