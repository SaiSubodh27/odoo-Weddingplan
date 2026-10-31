import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.document import RegistrationDocument
from app.models.enquiry import Enquiry, EnquiryNote

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB


class DocumentService:
    @staticmethod
    def _ensure_upload_dir() -> Path:
        upload_path = Path(settings.UPLOAD_DIR)
        upload_path.mkdir(parents=True, exist_ok=True)
        return upload_path

    @classmethod
    async def save_uploaded_document(
        cls,
        db: Session,
        enquiry: Enquiry,
        file: UploadFile,
        document_type: str,
        uploaded_by: str = "Agency Staff"
    ) -> RegistrationDocument:
        """
        Validates, saves to disk using a sanitized UUID filename, and records metadata in database.
        """
        original_filename = file.filename or "registration_document.pdf"
        file_ext = Path(original_filename).suffix.lower()

        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension '{file_ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        content = await file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)} MB."
            )

        upload_dir = cls._ensure_upload_dir()
        doc_id = f"DOC-{uuid.uuid4().hex[:12].upper()}"
        stored_filename = f"{doc_id}_{uuid.uuid4().hex[:8]}{file_ext}"
        destination = upload_dir / stored_filename

        with open(destination, "wb") as f:
            f.write(content)

        doc_record = RegistrationDocument(
            id=doc_id,
            enquiry_id=enquiry.id,
            client_id=enquiry.client_id,
            document_type=document_type,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            uploaded_by=uploaded_by
        )

        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)
        return doc_record

    @classmethod
    def get_document_path(cls, db: Session, enquiry_id: str, document_id: str) -> tuple[Path, RegistrationDocument]:
        """Validates enquiry association and returns disk path safely."""
        doc = db.query(RegistrationDocument).filter(
            RegistrationDocument.id == document_id,
            RegistrationDocument.enquiry_id == enquiry_id
        ).first()

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_id}' not found for enquiry '{enquiry_id}'."
            )

        file_path = Path(settings.UPLOAD_DIR) / doc.stored_filename
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File content not found on server storage."
            )

        return file_path, doc

    @classmethod
    def list_documents(cls, db: Session, enquiry_id: str) -> List[RegistrationDocument]:
        return db.query(RegistrationDocument).filter(
            RegistrationDocument.enquiry_id == enquiry_id
        ).order_by(RegistrationDocument.created_at.desc()).all()

    @classmethod
    def mark_document_reviewed(
        cls,
        db: Session,
        enquiry_id: str,
        document_id: str,
        reviewed_by: str = "Agency Staff"
    ) -> RegistrationDocument:
        """Marks a client-returned document as reviewed by staff."""
        doc = db.query(RegistrationDocument).filter(
            RegistrationDocument.id == document_id,
            RegistrationDocument.enquiry_id == enquiry_id
        ).first()

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_id}' not found for enquiry '{enquiry_id}'."
            )

        now = datetime.now(timezone.utc)
        doc.is_reviewed = True
        doc.reviewed_by = reviewed_by
        doc.reviewed_at = now

        enquiry = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()
        if enquiry:
            enquiry.registration_reviewed_at = now
            enquiry.status = "Under Review"

            note = EnquiryNote(
                enquiry_id=enquiry.id,
                author=reviewed_by,
                content=f"Reviewed registration document '{doc.original_filename}'. Enquiry dossier updated to Under Review."
            )
            db.add(note)

        db.commit()
        db.refresh(doc)
        return doc

    @classmethod
    def generate_blank_registration_form_html(cls, enquiry: Enquiry) -> str:
        """
        Generates a clean, professional, printable Royal Knot Client Registration Form.
        Pre-fills initial enquiry details while providing fields for couple signatures and wedding choices.
        """
        agency_email = settings.AGENCY_EMAIL
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>The Royal Knot — Client Registration Dossier #{enquiry.id}</title>
  <style>
    body {{
      font-family: 'Times New Roman', serif;
      margin: 40px;
      color: #1F2421;
      line-height: 1.6;
    }}
    .header {{
      text-align: center;
      border-bottom: 2px solid #9E7D3B;
      padding-bottom: 20px;
      margin-bottom: 30px;
    }}
    .title {{
      font-size: 26px;
      font-weight: bold;
      text-transform: uppercase;
      letter-spacing: 2px;
      color: #1F2421;
    }}
    .subtitle {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 3px;
      color: #9E7D3B;
      margin-top: 5px;
    }}
    .section-title {{
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      font-weight: bold;
      background: #F5F2EB;
      padding: 8px 12px;
      margin-top: 25px;
      margin-bottom: 15px;
      border-left: 4px solid #9E7D3B;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 15px;
    }}
    td {{
      padding: 8px 12px;
      border: 1px solid #E5E0D8;
      font-size: 13px;
    }}
    .label {{
      background: #FAF8F5;
      font-weight: bold;
      width: 30%;
    }}
    .signature-box {{
      margin-top: 40px;
      border-top: 1px solid #1F2421;
      padding-top: 10px;
      width: 45%;
      display: inline-block;
      text-align: center;
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div class="title">The Royal Knot</div>
    <div class="subtitle">Luxury Wedding Planning Agency · Jaipur & Udaipur</div>
    <p style="font-size: 12px; margin-top: 10px; color: #706E6B;">
      CONFIDENTIAL CLIENT REGISTRATION DOSSIER — REF: {enquiry.id}
    </p>
  </div>

  <div class="section-title">1. Couple & Primary Contact Details</div>
  <table>
    <tr>
      <td class="label">Lead Client / Partner 1 Name:</td>
      <td>{enquiry.client_name}</td>
    </tr>
    <tr>
      <td class="label">Partner 2 Full Name:</td>
      <td>________________________________________________</td>
    </tr>
    <tr>
      <td class="label">Primary Email:</td>
      <td>{enquiry.email}</td>
    </tr>
    <tr>
      <td class="label">Telephone / WhatsApp:</td>
      <td>{enquiry.phone}</td>
    </tr>
    <tr>
      <td class="label">Residential Address:</td>
      <td>________________________________________________</td>
    </tr>
  </table>

  <div class="section-title">2. Destination Wedding Parameters</div>
  <table>
    <tr>
      <td class="label">Target Wedding Date:</td>
      <td>{enquiry.wedding_date or '____________________'}</td>
    </tr>
    <tr>
      <td class="label">Preferred Destination / Venue:</td>
      <td>{enquiry.wedding_location or 'Jaipur / Udaipur Heritage Palace'}</td>
    </tr>
    <tr>
      <td class="label">Expected Royal Guests:</td>
      <td>{enquiry.expected_guest_count or '______'} Guests</td>
    </tr>
    <tr>
      <td class="label">Estimated Wedding Budget:</td>
      <td>₹ {enquiry.estimated_budget or '__________________'}</td>
    </tr>
    <tr>
      <td class="label">Preferred Design Aesthetic / Theme:</td>
      <td>________________________________________________</td>
    </tr>
  </table>

  <div class="section-title">3. Service Tier Selection</div>
  <table>
    <tr>
      <td class="label">Requested Service Package:</td>
      <td>[ &nbsp; ] Full-Service &nbsp;&nbsp;&nbsp;&nbsp; [ &nbsp; ] Partial Planning &nbsp;&nbsp;&nbsp;&nbsp; [ &nbsp; ] Day-of Coordination</td>
    </tr>
    <tr>
      <td class="label">Special Culinary & Vendor Requests:</td>
      <td>{enquiry.requirements or '________________________________________________'}</td>
    </tr>
  </table>

  <div style="margin-top: 60px;">
    <div class="signature-box" style="float: left;">
      Client Signature (Partner 1)<br>Date: _______________
    </div>
    <div class="signature-box" style="float: right;">
      Client Signature (Partner 2)<br>Date: _______________
    </div>
    <div style="clear: both;"></div>
  </div>

  <p style="font-size: 11px; color: #8C877D; margin-top: 60px; text-align: center;">
    Please return this completed dossier to <strong>{agency_email}</strong>. Once received, your private client planning portal will be activated.
  </p>
</body>
</html>"""


document_service = DocumentService()
