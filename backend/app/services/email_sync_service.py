import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
import logging
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.config import settings
from app.models.email_message import EmailMessage, EmailAttachment
from app.models.enquiry import Enquiry, EnquiryNote
from app.models.document import RegistrationDocument
from app.services.enquiry_service import enquiry_service

logger = logging.getLogger("royal_knot.email_sync")

WEDDING_KEYWORDS = [
    "wedding", "marriage", "shaadi", "vivah", "mandap", "ceremony",
    "jaipur", "udaipur", "jodhpur", "rajasthan", "palace", "resort",
    "destination wedding", "planner", "planning", "decor", "catering",
    "budget", "guests", "date", "venue", "enquiry", "inquiry"
]

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".html", ".htm"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class EmailSyncService:
    @staticmethod
    def is_imap_configured() -> bool:
        """Returns True only if live IMAP credentials (host, username, password) are present."""
        return bool(settings.IMAP_HOST and settings.IMAP_USERNAME and settings.IMAP_PASSWORD)

    @classmethod
    def get_status(cls, db: Session) -> dict:
        """Returns current live email configuration status and processing statistics."""
        total_received = db.query(EmailMessage).filter(EmailMessage.direction == "incoming").count()
        total_unclassified = db.query(EmailMessage).filter(
            EmailMessage.direction == "incoming",
            EmailMessage.status == "UNCLASSIFIED"
        ).count()

        latest_incoming = db.query(EmailMessage).filter(
            EmailMessage.direction == "incoming"
        ).order_by(EmailMessage.created_at.desc()).first()

        return {
            "imap_configured": cls.is_imap_configured(),
            "smtp_configured": bool(settings.SMTP_HOST and settings.SMTP_USERNAME and settings.SMTP_PASSWORD),
            "agency_email": settings.AGENCY_EMAIL,
            "imap_host": settings.IMAP_HOST,
            "smtp_host": settings.SMTP_HOST,
            "last_sync_at": latest_incoming.created_at if latest_incoming else None,
            "total_messages_received": total_received,
            "total_unclassified": total_unclassified
        }

    @staticmethod
    def _decode_header_str(header_value: Optional[str]) -> str:
        """Decodes RFC 2047 encoded email headers into clean Python strings."""
        if not header_value:
            return ""
        decoded_parts = []
        for part, encoding in decode_header(header_value):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or "utf-8", errors="replace"))
                except Exception:
                    decoded_parts.append(part.decode("latin1", errors="replace"))
            else:
                decoded_parts.append(str(part))
        return " ".join(decoded_parts).strip()

    @classmethod
    def sync_mailbox(cls, db: Session) -> dict:
        """
        Connects to agency Gmail via secure IMAP SSL and ingests new emails.
        If credentials are not configured, returns clear status without crashing.
        """
        if not cls.is_imap_configured():
            logger.info("IMAP sync skipped: IMAP credentials not configured in .env.")
            return {
                "success": False,
                "status": "unconfigured",
                "configured": False,
                "messages_found": 0,
                "messages_processed": 0,
                "enquiries_created": 0,
                "documents_received": 0,
                "message": (
                    f"Gmail IMAP is not configured. Add IMAP_PASSWORD in backend/.env "
                    f"using a 16-character Google App Password for {settings.AGENCY_EMAIL}."
                ),
                "errors": []
            }

        mail = None
        messages_found = 0
        messages_processed = 0
        enquiries_created = 0
        documents_received = 0
        errors = []

        try:
            # 1. Connect to Gmail via SSL
            logger.info(f"Connecting to IMAP {settings.IMAP_HOST}:{settings.IMAP_PORT} as {settings.IMAP_USERNAME}...")
            mail = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT, timeout=15)
            clean_pw = settings.IMAP_PASSWORD.replace(" ", "")
            mail.login(settings.IMAP_USERNAME, clean_pw)

            status, select_data = mail.select("INBOX", readonly=True)
            if status != "OK" or not select_data:
                raise Exception("Unable to open INBOX folder.")

            total_mailbox_count = int(select_data[0].decode() if isinstance(select_data[0], bytes) else select_data[0])

            # 2. Search for unread messages first, or evaluate the latest sequence range
            mail_ids = []
            try:
                status, search_data = mail.search(None, "UNSEEN")
                if status == "OK" and search_data and search_data[0]:
                    unseen_ids = search_data[0].split()
                    mail_ids = unseen_ids[-15:] if len(unseen_ids) > 15 else unseen_ids
            except Exception as e:
                logger.warning(f"UNSEEN search warning: {e}")

            # If no unread, evaluate the latest 10 messages by sequence numbers (avoids downloading thousands of IDs)
            if not mail_ids and total_mailbox_count > 0:
                start_seq = max(1, total_mailbox_count - 9)
                mail_ids = [str(seq).encode() for seq in range(start_seq, total_mailbox_count + 1)]

            messages_found = len(mail_ids)
            logger.info(f"IMAP evaluating {messages_found} recent messages (Mailbox total: {total_mailbox_count}).")

            for msg_id_bytes in mail_ids:
                try:
                    res, msg_data = mail.fetch(msg_id_bytes, "(RFC822)")
                    if res != "OK" or not msg_data or not msg_data[0]:
                        continue

                    raw_email = msg_data[0][1]
                    email_obj = email.message_from_bytes(raw_email)

                    proc_res = cls._process_parsed_email(db, email_obj)
                    if proc_res["processed"]:
                        messages_processed += 1
                        if proc_res.get("enquiry_created"):
                            enquiries_created += 1
                        if proc_res.get("document_received"):
                            documents_received += 1

                except Exception as ex:
                    logger.error(f"Error parsing email message {msg_id_bytes}: {str(ex)}")
                    errors.append(f"Message {msg_id_bytes.decode() if isinstance(msg_id_bytes, bytes) else msg_id_bytes}: {str(ex)}")

            return {
                "success": True,
                "status": "completed",
                "configured": True,
                "messages_found": messages_found,
                "messages_processed": messages_processed,
                "enquiries_created": enquiries_created,
                "documents_received": documents_received,
                "message": f"Sync complete. {messages_processed} new message(s) ingested.",
                "errors": errors
            }

        except Exception as e:
            logger.error(f"IMAP sync failed: {str(e)}")
            return {
                "success": False,
                "status": "error",
                "configured": True,
                "messages_found": 0,
                "messages_processed": 0,
                "enquiries_created": 0,
                "documents_received": 0,
                "message": f"Gmail IMAP connection failed: {str(e)}. Please verify your App Password.",
                "errors": [str(e)]
            }
        finally:
            if mail:
                try:
                    mail.close()
                    mail.logout()
                except Exception:
                    pass

    @classmethod
    def _process_parsed_email(cls, db: Session, email_obj: email.message.Message) -> dict:
        """Extracts headers, bodies, attachments, and classifies the incoming email."""
        raw_message_id = email_obj.get("Message-ID", "")
        clean_message_id = raw_message_id.strip("<> \r\n") if raw_message_id else f"RAW-{uuid.uuid4().hex}"

        # 1. Deduplication check
        existing = db.query(EmailMessage).filter(EmailMessage.message_id == clean_message_id).first()
        if existing:
            return {"processed": False, "reason": "duplicate_message_id"}

        # 2. Extract headers
        sender_name, sender_email = parseaddr(email_obj.get("From", ""))
        sender_name = cls._decode_header_str(sender_name)
        sender_email = sender_email.strip().lower()

        _, recipient_email = parseaddr(email_obj.get("To", settings.AGENCY_EMAIL))
        subject = cls._decode_header_str(email_obj.get("Subject", "(No Subject)"))
        in_reply_to = email_obj.get("In-Reply-To", "").strip("<> \r\n") or None
        references = email_obj.get("References", "").strip() or None

        date_hdr = email_obj.get("Date")
        received_at = datetime.now(timezone.utc)
        if date_hdr:
            try:
                dt = parsedate_to_datetime(date_hdr)
                received_at = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except Exception:
                pass

        # 3. Extract text and HTML body
        body_text = ""
        body_html = ""
        attachments_info = []

        if email_obj.is_multipart():
            for part in email_obj.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition:
                    att = cls._save_email_attachment(part)
                    if att:
                        attachments_info.append(att)
                elif content_type == "text/plain" and not body_text:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                elif content_type == "text/html" and not body_html:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_html = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        else:
            payload = email_obj.get_payload(decode=True)
            if payload:
                body_text = payload.decode(email_obj.get_content_charset() or "utf-8", errors="replace")

        # 4. Association with existing enquiry
        matched_enquiry = None

        # A: Check In-Reply-To or References matching prior EmailMessage
        if in_reply_to:
            prior_msg = db.query(EmailMessage).filter(EmailMessage.message_id == in_reply_to).first()
            if prior_msg and prior_msg.enquiry_id:
                matched_enquiry = db.query(Enquiry).filter(Enquiry.id == prior_msg.enquiry_id, Enquiry.is_deleted == False).first()

        # B: Check subject reference code: e.g. ENQ-2026-001 or TRK-ENQ-2026-081
        if not matched_enquiry:
            enq_match = re.search(r"(?:TRK-)?ENQ-\d+-\d+", subject, re.IGNORECASE)
            if enq_match:
                enq_ref = enq_match.group(0).upper()
                if enq_ref.startswith("TRK-"):
                    stripped = enq_ref[4:]
                    matched_enquiry = db.query(Enquiry).filter(
                        or_(Enquiry.id == enq_ref, Enquiry.id == stripped),
                        Enquiry.is_deleted == False
                    ).first()
                else:
                    trk_variant = f"TRK-{enq_ref}"
                    matched_enquiry = db.query(Enquiry).filter(
                        or_(Enquiry.id == enq_ref, Enquiry.id == trk_variant),
                        Enquiry.is_deleted == False
                    ).first()

        # C: Check active enquiry by sender email
        if not matched_enquiry and sender_email:
            matched_enquiry = db.query(Enquiry).filter(
                Enquiry.email == sender_email,
                Enquiry.is_deleted == False,
                Enquiry.status != "Closed"
            ).order_by(Enquiry.created_at.desc()).first()

        # 5. Create EmailMessage record
        msg_db_id = f"MSG-IN-{uuid.uuid4().hex[:12].upper()}"
        enquiry_created = False
        document_received = False

        if matched_enquiry:
            msg_status = "ASSOCIATED"
            enquiry_id = matched_enquiry.id

            # Check if this email returns a completed registration document
            if attachments_info and matched_enquiry.status != "Closed":
                for att in attachments_info:
                    ext = os.path.splitext(att["original_filename"])[1].lower()
                    if ext in ALLOWED_EXTENSIONS:
                        doc_id = f"DOC-{uuid.uuid4().hex[:12].upper()}"
                        reg_doc = RegistrationDocument(
                            id=doc_id,
                            enquiry_id=matched_enquiry.id,
                            document_type="completed_by_client",
                            original_filename=att["original_filename"],
                            stored_filename=att["stored_filename"],
                            file_size=att["file_size"],
                            mime_type=att["mime_type"],
                            uploaded_by=f"Client via Email ({sender_email})"
                        )
                        db.add(reg_doc)
                        matched_enquiry.status = "Registration Received"
                        matched_enquiry.registration_received_at = received_at
                        document_received = True

                        note = EnquiryNote(
                            enquiry_id=matched_enquiry.id,
                            author="System (Email Receiver)",
                            content=f"Received completed registration document '{att['original_filename']}' from client via email."
                        )
                        db.add(note)

            # Add activity note for received email reply
            if not document_received:
                note = EnquiryNote(
                    enquiry_id=matched_enquiry.id,
                    author="Client Email",
                    content=f"Client emailed: \"{subject}\"\n\n{body_text[:300]}..."
                )
                db.add(note)

        else:
            # Check if this is a new wedding planning enquiry
            full_content = f"{subject} {body_text}".lower()
            is_wedding_lead = any(kw in full_content for kw in WEDDING_KEYWORDS)

            if is_wedding_lead:
                # Create a new Enquiry
                next_count = db.query(Enquiry).count() + 81
                new_enq_id = f"TRK-ENQ-2026-0{next_count}"
                client_display_name = sender_name or sender_email.split("@")[0].replace(".", " ").title()

                new_enquiry = Enquiry(
                    id=new_enq_id,
                    client_name=client_display_name,
                    email=sender_email,
                    phone="+91 (Awaiting Phone Verification)",
                    enquiry_source="Email",
                    requirements=body_text[:1000] if body_text else subject,
                    status="New"
                )
                db.add(new_enquiry)
                db.flush()

                enquiry_id = new_enquiry.id
                msg_status = "ENQUIRY_CREATED"
                enquiry_created = True

                note = EnquiryNote(
                    enquiry_id=new_enq_id,
                    author="System (Email Classifier)",
                    content=f"Automatically captured new email enquiry from {client_display_name} ({sender_email}). Subject: {subject}"
                )
                db.add(note)
            else:
                # Unclassified / needs staff review
                enquiry_id = None
                msg_status = "UNCLASSIFIED"

        email_message = EmailMessage(
            id=msg_db_id,
            enquiry_id=enquiry_id,
            direction="incoming",
            sender_name=sender_name or sender_email,
            sender_email=sender_email,
            recipient_email=recipient_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html or None,
            message_id=clean_message_id,
            in_reply_to=in_reply_to,
            references=references,
            status=msg_status,
            received_at=received_at
        )
        db.add(email_message)

        # Attachments
        for att in attachments_info:
            att_rec = EmailAttachment(
                id=f"ATT-{uuid.uuid4().hex[:10].upper()}",
                email_message_id=msg_db_id,
                original_filename=att["original_filename"],
                stored_filename=att["stored_filename"],
                file_size=att["file_size"],
                mime_type=att["mime_type"]
            )
            db.add(att_rec)

        db.commit()

        return {
            "processed": True,
            "message_id": msg_db_id,
            "status": msg_status,
            "enquiry_id": enquiry_id,
            "enquiry_created": enquiry_created,
            "document_received": document_received
        }

    @staticmethod
    def _save_email_attachment(part) -> Optional[dict]:
        """Saves an email attachment to disk securely, validating type and size."""
        filename = part.get_filename()
        if not filename:
            return None

        # Clean filename
        filename = decode_header(filename)[0][0]
        if isinstance(filename, bytes):
            filename = filename.decode("utf-8", errors="replace")
        filename = os.path.basename(filename)

        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.warning(f"Skipping attachment with disallowed extension: {filename}")
            return None

        payload = part.get_payload(decode=True)
        if not payload or len(payload) > MAX_FILE_SIZE:
            logger.warning(f"Skipping attachment exceeding max size: {filename}")
            return None

        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        safe_stored_name = f"ATT_{uuid.uuid4().hex[:12]}{ext}"
        stored_path = os.path.join(settings.UPLOAD_DIR, safe_stored_name)

        with open(stored_path, "wb") as f:
            f.write(payload)

        return {
            "original_filename": filename,
            "stored_filename": safe_stored_name,
            "file_size": len(payload),
            "mime_type": part.get_content_type() or "application/octet-stream"
        }

    @classmethod
    def simulate_incoming_email(
        cls,
        db: Session,
        sender_email: str,
        sender_name: str,
        subject: str,
        body_text: str,
        in_reply_to: Optional[str] = None,
        attachment_bytes: Optional[bytes] = None,
        attachment_filename: Optional[str] = None
    ) -> dict:
        """
        Simulates an incoming email from a client.
        Enables 100% automated testability and demo workflows without needing live Gmail credentials.
        """
        rfc_id = f"simulated_{uuid.uuid4().hex[:10]}@testclient.in"

        # Build dummy email message
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication

        msg = MIMEMultipart("mixed")
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = settings.AGENCY_EMAIL
        msg["Subject"] = subject
        msg["Message-ID"] = f"<{rfc_id}>"
        msg["Date"] = email.utils.formatdate(localtime=True)
        if in_reply_to:
            msg["In-Reply-To"] = f"<{in_reply_to}>"
            msg["References"] = f"<{in_reply_to}>"

        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        if attachment_bytes and attachment_filename:
            part = MIMEApplication(attachment_bytes, Name=attachment_filename)
            part["Content-Disposition"] = f'attachment; filename="{attachment_filename}"'
            msg.attach(part)

        return cls._process_parsed_email(db, msg)

    @classmethod
    def convert_to_enquiry(cls, db: Session, email_id: str, client_name: Optional[str] = None) -> Enquiry:
        """Converts an unclassified email into a formal Enquiry."""
        msg = db.query(EmailMessage).filter(EmailMessage.id == email_id).first()
        if not msg:
            raise ValueError(f"Email message '{email_id}' not found.")

        if msg.enquiry_id:
            raise ValueError(f"Email message is already associated with enquiry '{msg.enquiry_id}'.")

        next_count = db.query(Enquiry).count() + 81
        new_enq_id = f"TRK-ENQ-2026-0{next_count}"
        display_name = client_name or msg.sender_name or msg.sender_email.split("@")[0].title()

        enquiry = Enquiry(
            id=new_enq_id,
            client_name=display_name,
            email=msg.sender_email,
            phone="+91 (Awaiting Phone Verification)",
            enquiry_source="Email",
            requirements=msg.body_text[:1000] if msg.body_text else msg.subject,
            status="New"
        )
        db.add(enquiry)
        db.flush()

        msg.enquiry_id = enquiry.id
        msg.status = "ENQUIRY_CREATED"

        note = EnquiryNote(
            enquiry_id=new_enq_id,
            author="Agency Staff",
            content=f"Created enquiry from incoming email '{msg.subject}'."
        )
        db.add(note)
        db.commit()
        db.refresh(enquiry)
        return enquiry

    @classmethod
    def associate_with_enquiry(cls, db: Session, email_id: str, enquiry_id: str) -> EmailMessage:
        """Manually links an unclassified email to an existing Enquiry and extracts attached documents."""
        msg = db.query(EmailMessage).filter(EmailMessage.id == email_id).first()
        if not msg:
            raise ValueError(f"Email message '{email_id}' not found.")

        enquiry = db.query(Enquiry).filter(Enquiry.id == enquiry_id, Enquiry.is_deleted == False).first()
        if not enquiry:
            raise ValueError(f"Enquiry '{enquiry_id}' not found.")

        msg.enquiry_id = enquiry.id
        msg.status = "ASSOCIATED"

        # If this email contained document attachments, convert them into completed registration documents
        doc_created = False
        if msg.attachments:
            for att in msg.attachments:
                ext = os.path.splitext(att.original_filename)[1].lower()
                if ext in ALLOWED_EXTENSIONS:
                    doc_id = f"DOC-{uuid.uuid4().hex[:12].upper()}"
                    reg_doc = RegistrationDocument(
                        id=doc_id,
                        enquiry_id=enquiry.id,
                        document_type="completed_by_client",
                        original_filename=att.original_filename,
                        stored_filename=att.stored_filename,
                        file_size=att.file_size,
                        mime_type=att.mime_type,
                        uploaded_by=f"Staff Associated Email ({msg.sender_email})"
                    )
                    db.add(reg_doc)
                    doc_created = True

        if doc_created and enquiry.status in ["New", "Contacted", "Registration Document Sent"]:
            enquiry.status = "Registration Received"
            enquiry.registration_received_at = datetime.now(timezone.utc)

        note_content = (
            f"Associated email '{msg.subject}' from {msg.sender_email} with this enquiry dossier."
            if not doc_created
            else f"Associated email '{msg.subject}' and linked completed registration attachment(s) to enquiry dossier."
        )
        note = EnquiryNote(
            enquiry_id=enquiry.id,
            author="Agency Staff",
            content=note_content
        )
        db.add(note)
        db.commit()
        db.refresh(msg)
        return msg

    @classmethod
    def ignore_email(cls, db: Session, email_id: str) -> EmailMessage:
        """Marks an unclassified email as ignored / irrelevant."""
        msg = db.query(EmailMessage).filter(EmailMessage.id == email_id).first()
        if not msg:
            raise ValueError(f"Email message '{email_id}' not found.")

        msg.status = "IGNORED"
        db.commit()
        db.refresh(msg)
        return msg


email_sync_service = EmailSyncService()

