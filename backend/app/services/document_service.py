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

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".html", ".htm"}
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
    def generate_and_save_registration_document(cls, db: Session, enquiry: Enquiry) -> RegistrationDocument:
        """
        Generates the personalized Royal Knot client registration dossier HTML file,
        persists it to upload storage, and records it as a 'sent_to_client' RegistrationDocument.
        """
        upload_dir = cls._ensure_upload_dir()
        html_content = cls.generate_blank_registration_form_html(enquiry)
        content_bytes = html_content.encode("utf-8")

        doc_id = f"DOC-{uuid.uuid4().hex[:12].upper()}"
        filename = f"The_Royal_Knot_Registration_Dossier_{enquiry.id}.html"
        stored_filename = f"{doc_id}_{enquiry.id}_registration_dossier.html"
        file_path = upload_dir / stored_filename

        with open(file_path, "wb") as f:
            f.write(content_bytes)

        doc_record = RegistrationDocument(
            id=doc_id,
            enquiry_id=enquiry.id,
            client_id=enquiry.client_id,
            document_type="sent_to_client",
            original_filename=filename,
            stored_filename=stored_filename,
            file_size=len(content_bytes),
            mime_type="text/html",
            uploaded_by="The Royal Knot System"
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)
        return doc_record

    @classmethod
    def generate_blank_registration_form_html(cls, enquiry: Enquiry) -> str:
        """
        Generates a clean, professional, printable Royal Knot Client Registration Form.
        Pre-fills initial enquiry details while providing fields for couple signatures, wedding events, and choices.
        """
        agency_email = settings.AGENCY_EMAIL
        budget_str = f"₹ {enquiry.estimated_budget:,.0f}" if enquiry.estimated_budget else ""
        date_str = str(enquiry.wedding_date) if enquiry.wedding_date else ""
        guests_str = str(enquiry.expected_guest_count) if enquiry.expected_guest_count else ""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>The Royal Knot — Client Registration Dossier #{enquiry.id}</title>
  <style>
    @media print {{
      .no-print {{ display: none !important; }}
      body {{ margin: 0; padding: 20px; }}
    }}
    body {{
      font-family: 'Georgia', 'Times New Roman', serif;
      margin: 40px auto;
      max-width: 850px;
      color: #1F2421;
      background: #FAF8F5;
      line-height: 1.6;
      padding: 30px;
    }}
    .dossier-card {{
      background: #FFFFFF;
      border: 1px solid #E5E0D8;
      padding: 40px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    }}
    .action-bar {{
      background: #1F2421;
      color: #FAF8F5;
      padding: 12px 20px;
      margin-bottom: 25px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 13px;
    }}
    .btn-print {{
      background: #9E7D3B;
      color: #FFFFFF;
      border: none;
      padding: 8px 16px;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      cursor: pointer;
      font-weight: bold;
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
      letter-spacing: 3px;
      color: #1F2421;
    }}
    .subtitle {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 3px;
      color: #9E7D3B;
      margin-top: 5px;
    }}
    .section-title {{
      font-size: 13px;
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
    td, th {{
      padding: 10px 12px;
      border: 1px solid #E5E0D8;
      font-size: 13px;
    }}
    .label {{
      background: #FAF8F5;
      font-weight: bold;
      width: 32%;
      color: #4A4640;
    }}
    input[type="text"], input[type="date"], select, textarea {{
      width: 95%;
      padding: 6px 8px;
      border: 1px solid #D5CFC5;
      font-family: inherit;
      font-size: 13px;
      background: #FFF;
      color: #1F2421;
    }}
    .signature-container {{
      margin-top: 50px;
      display: flex;
      justify-content: space-between;
    }}
    .signature-box {{
      width: 45%;
      border-top: 1px solid #1F2421;
      padding-top: 10px;
      text-align: center;
      font-size: 12px;
    }}
    .instructions {{
      font-size: 12px;
      color: #736F68;
      margin-top: 40px;
      padding: 15px;
      background: #FAF8F5;
      border-left: 3px solid #9E7D3B;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="action-bar no-print">
    <span>The Royal Knot · Client Registration Dossier (Ref: {enquiry.id})</span>
    <button class="btn-print" onclick="window.print()">Print / Save as PDF</button>
  </div>

  <div class="dossier-card">
    <div class="header">
      <div class="title">The Royal Knot</div>
      <div class="subtitle">Luxury Destination Wedding Agency · Jaipur & Udaipur</div>
      <p style="font-size: 11px; margin-top: 10px; color: #706E6B; letter-spacing: 1px;">
        CONFIDENTIAL CLIENT REGISTRATION DOSSIER — REFERENCE: {enquiry.id}
      </p>
    </div>

    <form>
      <div class="section-title">1. Couple & Primary Contact Details</div>
      <table>
        <tr>
          <td class="label">Lead Client / Partner 1 Full Name:</td>
          <td><input type="text" value="{enquiry.client_name}" /></td>
        </tr>
        <tr>
          <td class="label">Partner 2 Full Name:</td>
          <td><input type="text" placeholder="Full legal name of fiancé / partner" /></td>
        </tr>
        <tr>
          <td class="label">Primary Email Address:</td>
          <td><input type="text" value="{enquiry.email}" /></td>
        </tr>
        <tr>
          <td class="label">Telephone / WhatsApp:</td>
          <td><input type="text" value="{enquiry.phone}" /></td>
        </tr>
        <tr>
          <td class="label">Residential City & Address:</td>
          <td><input type="text" placeholder="e.g. Malabar Hill, Mumbai / Vasant Vihar, New Delhi" /></td>
        </tr>
      </table>

      <div class="section-title">2. Destination Wedding Parameters</div>
      <table>
        <tr>
          <td class="label">Target Wedding Date(s):</td>
          <td><input type="text" value="{date_str}" placeholder="e.g. 26-28 November 2027 (3 Days)" /></td>
        </tr>
        <tr>
          <td class="label">Preferred Destination / Venue:</td>
          <td><input type="text" value="{enquiry.wedding_location or 'Jaipur / Udaipur Heritage Palace'}" /></td>
        </tr>
        <tr>
          <td class="label">Expected Royal Guests:</td>
          <td><input type="text" value="{guests_str}" placeholder="e.g. 450 guests" /></td>
        </tr>
        <tr>
          <td class="label">Estimated Wedding Budget:</td>
          <td><input type="text" value="{budget_str}" placeholder="e.g. ₹ 3,50,00,000 (3.5 Crores)" /></td>
        </tr>
        <tr>
          <td class="label">Design Aesthetic / Theme:</td>
          <td><input type="text" placeholder="e.g. Royal Rajputana Splendor, Twilight Palace Glamour, Ivory & Antique Gold" /></td>
        </tr>
      </table>

      <div class="section-title">3. Wedding Functions & Key Events Planned</div>
      <table>
        <thead>
          <tr style="background: #FAF8F5; text-align: left;">
            <th style="width: 25%;">Event / Function</th>
            <th style="width: 25%;">Target Date / Time</th>
            <th style="width: 50%;">Preferred Venue & Experience Vision</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Welcome Dinner & Mehndi</strong></td>
            <td><input type="text" placeholder="Day 1 Afternoon / Evening" /></td>
            <td><input type="text" placeholder="Lakeside courtyard or palace terrace with folk music" /></td>
          </tr>
          <tr>
            <td><strong>Royal Sangeet & Cocktail</strong></td>
            <td><input type="text" placeholder="Day 2 Evening" /></td>
            <td><input type="text" placeholder="Grand ballroom / palace lawn with concert staging" /></td>
          </tr>
          <tr>
            <td><strong>Haldi & Chuda Rituals</strong></td>
            <td><input type="text" placeholder="Day 3 Morning" /></td>
            <td><input type="text" placeholder="Yellow marigold canopy, poolside floral showers" /></td>
          </tr>
          <tr>
            <td><strong>Mandap, Baraat & Pheras</strong></td>
            <td><input type="text" placeholder="Day 3 Evening / Sunset" /></td>
            <td><input type="text" placeholder="Vintage car / elephant procession, floating lake mandap" /></td>
          </tr>
          <tr>
            <td><strong>Grand Palace Reception</strong></td>
            <td><input type="text" placeholder="Day 3 Night" /></td>
            <td><input type="text" placeholder="Black-tie gala dinner, royal Mewari feast & pyrotechnics" /></td>
          </tr>
        </tbody>
      </table>

      <div class="section-title">4. Service Tier & Agency Retainer Scope</div>
      <table>
        <tr>
          <td class="label">Requested Service Package:</td>
          <td>
            <label style="margin-right: 15px;"><input type="radio" name="pkg" checked /> Full-Service Royal Concierge</label>
            <label style="margin-right: 15px;"><input type="radio" name="pkg" /> Partial-Service Planning</label>
            <label><input type="radio" name="pkg" /> Executive Day-of Coordination</label>
          </td>
        </tr>
        <tr>
          <td class="label">Key Planning Services Needed:</td>
          <td>
            <label style="margin-right: 15px;"><input type="checkbox" checked /> Palace Venue Sourcing</label>
            <label style="margin-right: 15px;"><input type="checkbox" checked /> Royal Artist & Entertainment</label>
            <label style="margin-right: 15px;"><input type="checkbox" checked /> Bespoke Spatial Decor</label>
            <label><input type="checkbox" checked /> Guest Logistics & Airport Fleet</label>
          </td>
        </tr>
      </table>

      <div class="section-title">5. Culinary, Vendor & Special Requirements</div>
      <table>
        <tr>
          <td class="label">Catering & Culinary Framework:</td>
          <td>
            <input type="text" placeholder="e.g. Royal Marwari Maharaj cuisine, Jain counter, Modern European & Asian" />
          </td>
        </tr>
        <tr>
          <td class="label">Special Vendor Requirements:</td>
          <td><textarea rows="3" placeholder="Specific photographers, floral designers, sound engineers, or stylists requested">{enquiry.requirements or ''}</textarea></td>
        </tr>
      </table>

      <div class="section-title">6. Additional Notes & VIP Family Protocols</div>
      <table>
        <tr>
          <td class="label">Confidential Notes / Requests:</td>
          <td><textarea rows="3" placeholder="Security protocols, private air charter / helicopter transfers, elderly assistance, or bespoke rituals"></textarea></td>
        </tr>
      </table>

      <div class="signature-container">
        <div class="signature-box">
          <p>______________________________________</p>
          Client Signature (Partner 1)<br>Date: _______________
        </div>
        <div class="signature-box">
          <p>______________________________________</p>
          Client Signature (Partner 2)<br>Date: _______________
        </div>
      </div>
    </form>

    <div class="instructions">
      <strong>Submission Instructions:</strong> Please complete and sign this registration dossier, then reply to your enquiry email thread or send it to <strong>{agency_email}</strong>. Once received and reviewed by your agency concierge, your private Royal Knot planning portal will be activated.
    </div>
  </div>
</body>
</html>"""


document_service = DocumentService()
