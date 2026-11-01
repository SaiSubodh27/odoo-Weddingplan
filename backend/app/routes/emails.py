import os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.session import get_db
from app.core.config import settings
from app.models.email_message import EmailMessage, EmailAttachment
from app.schemas.email_message import (
    EmailMessageResponse,
    EmailListResponse,
    EmailSyncResponse,
    EmailStatusResponse,
    EmailAssociateRequest,
    EmailConvertToEnquiryRequest,
)
from app.schemas.enquiry import EnquiryResponse
from app.services.email_sync_service import email_sync_service

router = APIRouter()


@router.get(
    "/status",
    response_model=EmailStatusResponse,
    summary="Get agency email configuration and sync status",
    tags=["Email Integration"]
)
def get_email_status(db: Session = Depends(get_db)):
    """
    Returns whether Gmail IMAP (incoming) and SMTP (outgoing) credentials are configured,
    along with message and classification metrics.
    """
    return email_sync_service.get_status(db=db)


@router.post(
    "/sync",
    response_model=EmailSyncResponse,
    summary="Trigger immediate check of agency Gmail inbox via IMAP",
    tags=["Email Integration"]
)
def sync_mailbox(db: Session = Depends(get_db)):
    """
    Connects to saisubodh6@gmail.com over IMAP SSL, searches for unread or recent messages,
    extracts client details, attachments, and auto-associates or flags for staff review.
    """
    return email_sync_service.sync_mailbox(db=db)


@router.get(
    "",
    response_model=EmailListResponse,
    include_in_schema=False
)
@router.get(
    "/inbox",
    response_model=EmailListResponse,
    summary="List incoming emails in the agency inbox / staff review queue",
    tags=["Email Integration"]
)
def list_inbox_emails(
    status_filter: Optional[str] = Query("all", description="Status filter: all, UNCLASSIFIED, ENQUIRY_CREATED, ASSOCIATED, IGNORED"),
    search: Optional[str] = Query(None, description="Search subject, sender, or body"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Returns incoming emails. Allows agency staff to review unclassified messages,
    verify client enquiries, and inspect message threads.
    """
    query = db.query(EmailMessage).filter(EmailMessage.direction == "incoming")

    if status_filter and status_filter.lower() != "all":
        query = query.filter(EmailMessage.status == status_filter.upper())

    if search:
        pat = f"%{search.strip()}%"
        query = query.filter(
            or_(
                EmailMessage.subject.ilike(pat),
                EmailMessage.sender_email.ilike(pat),
                EmailMessage.sender_name.ilike(pat),
                EmailMessage.body_text.ilike(pat)
            )
        )

    total = query.count()
    items = query.order_by(EmailMessage.created_at.desc()).offset(offset).limit(limit).all()

    # Build response with download URLs for attachments
    res_items = []
    for m in items:
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

        res_items.append(
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

    return EmailListResponse(total=total, items=res_items)


@router.get(
    "/{email_id}",
    response_model=EmailMessageResponse,
    summary="Get single email message details",
    tags=["Email Integration"]
)
def get_email_message(email_id: str, db: Session = Depends(get_db)):
    msg = db.query(EmailMessage).filter(EmailMessage.id == email_id).first()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Email message '{email_id}' not found.")

    att_res = []
    for a in msg.attachments:
        att_res.append({
            "id": a.id,
            "emailMessageId": a.email_message_id,
            "originalFilename": a.original_filename,
            "fileSize": a.file_size,
            "mimeType": a.mime_type,
            "createdAt": a.created_at,
            "downloadUrl": f"{settings.BACKEND_BASE_URL}/api/v1/emails/{msg.id}/attachments/{a.id}/download"
        })

    return EmailMessageResponse(
        id=msg.id,
        enquiryId=msg.enquiry_id,
        direction=msg.direction,
        senderName=msg.sender_name,
        senderEmail=msg.sender_email,
        recipientEmail=msg.recipient_email,
        subject=msg.subject,
        bodyText=msg.body_text,
        bodyHtml=msg.body_html,
        messageId=msg.message_id,
        threadId=msg.thread_id,
        inReplyTo=msg.in_reply_to,
        status=msg.status,
        errorMessage=msg.error_message,
        receivedAt=msg.received_at,
        sentAt=msg.sent_at,
        createdAt=msg.created_at,
        attachments=att_res
    )


@router.post(
    "/{email_id}/convert-to-enquiry",
    response_model=EnquiryResponse,
    summary="Staff action: Convert an unclassified email into an Enquiry",
    tags=["Email Integration"]
)
def convert_email_to_enquiry(
    email_id: str,
    req: Optional[EmailConvertToEnquiryRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Converts an incoming email in the review queue into a formal Enquiry.
    """
    try:
        enquiry = email_sync_service.convert_to_enquiry(
            db=db,
            email_id=email_id,
            client_name=req.client_name if req else None
        )
        return enquiry
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{email_id}/associate",
    summary="Staff action: Associate an incoming email with an existing Enquiry",
    tags=["Email Integration"]
)
def associate_email_with_enquiry(
    email_id: str,
    req: EmailAssociateRequest,
    db: Session = Depends(get_db)
):
    """
    Manually associates an incoming client email with an existing enquiry dossier.
    """
    try:
        msg = email_sync_service.associate_with_enquiry(
            db=db,
            email_id=email_id,
            enquiry_id=req.enquiry_id
        )
        return {
            "success": True,
            "message": f"Email '{msg.id}' associated with enquiry '{req.enquiry_id}'.",
            "enquiry_id": req.enquiry_id,
            "status": msg.status
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{email_id}/ignore",
    summary="Staff action: Mark an irrelevant or spam email as ignored",
    tags=["Email Integration"]
)
def ignore_email(
    email_id: str,
    db: Session = Depends(get_db)
):
    """
    Marks an email as IGNORED so it no longer clutters the staff review inbox.
    """
    try:
        msg = email_sync_service.ignore_email(db=db, email_id=email_id)
        return {
            "success": True,
            "message": f"Email '{email_id}' marked as ignored.",
            "status": msg.status
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{email_id}/attachments/{attachment_id}/download",
    summary="Download an attachment from an email securely",
    tags=["Email Integration"]
)
def download_email_attachment(
    email_id: str,
    attachment_id: str,
    db: Session = Depends(get_db)
):
    """
    Streams an email attachment safely.
    """
    att = db.query(EmailAttachment).filter(
        EmailAttachment.id == attachment_id,
        EmailAttachment.email_message_id == email_id
    ).first()

    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

    file_path = os.path.join(settings.UPLOAD_DIR, att.stored_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment file not found on disk.")

    return FileResponse(
        path=file_path,
        filename=att.original_filename,
        media_type=att.mime_type
    )


@router.post(
    "/simulate",
    summary="Simulate receiving an incoming email (for testing & development without live credentials)",
    tags=["Email Integration"]
)
async def simulate_incoming_email(
    sender_email: str = Form(...),
    sender_name: str = Form("Prospective Client"),
    subject: str = Form("Wedding Planning Inquiry - City Palace Udaipur"),
    body_text: str = Form("Hello, we are planning a 3-day royal wedding in Udaipur for 400 guests with budget ₹ 2.5 Cr. Please send registration details."),
    in_reply_to: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Simulates receiving an incoming email into saisubodh6@gmail.com.
    Validates end-to-end email intake, automatic classification, and attachment processing.
    """
    att_bytes = None
    att_filename = None
    if file:
        att_bytes = await file.read()
        att_filename = file.filename

    res = email_sync_service.simulate_incoming_email(
        db=db,
        sender_email=sender_email,
        sender_name=sender_name,
        subject=subject,
        body_text=body_text,
        in_reply_to=in_reply_to,
        attachment_bytes=att_bytes,
        attachment_filename=att_filename
    )
    return res

