import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import make_msgid, formatdate
from datetime import datetime, timezone
from typing import Optional, List, Dict
import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.email_message import EmailMessage, EmailAttachment

logger = logging.getLogger("royal_knot.email")

# In-memory development outbox to preview generated emails when SMTP is not configured
DEV_OUTBOX: List[Dict] = []


class EmailService:
    @staticmethod
    def is_smtp_configured() -> bool:
        """Returns True only if live SMTP credentials (host, username, password) are present."""
        return bool(settings.SMTP_HOST and settings.SMTP_USERNAME and settings.SMTP_PASSWORD)

    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[dict]] = None,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None,
        enquiry_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> dict:
        """
        Sends an email via live SMTP (if credentials configured) or records it in DEV_OUTBOX.
        If a db session is provided, persists an EmailMessage record for conversation tracking.
        """
        rfc_message_id = make_msgid(domain="theroyalknot.in")
        now = datetime.now(timezone.utc)
        sender_email = settings.SMTP_FROM_EMAIL or settings.AGENCY_EMAIL
        sender_name = settings.SMTP_FROM_NAME

        email_record = {
            "to": to_email,
            "subject": subject,
            "html": html_content,
            "text": text_content,
            "message_id": rfc_message_id,
            "in_reply_to": in_reply_to,
            "sent_via": "live_smtp" if cls.is_smtp_configured() else "dev_outbox",
            "has_attachments": bool(attachments),
            "timestamp": now.isoformat()
        }

        # 1. In Development/Unconfigured mode: Save to outbox without failing
        if not cls.is_smtp_configured():
            DEV_OUTBOX.append(email_record)
            logger.info(f"[DEV EMAIL OUTBOX] Email to {to_email} recorded. Subject: {subject}")

            # Persist outgoing message in DB if session available
            msg_id = f"MSG-OUT-{uuid.uuid4().hex[:12].upper()}"
            if db:
                db_msg = EmailMessage(
                    id=msg_id,
                    enquiry_id=enquiry_id,
                    direction="outgoing",
                    sender_name=sender_name,
                    sender_email=sender_email,
                    recipient_email=to_email,
                    subject=subject,
                    body_text=text_content or "",
                    body_html=html_content,
                    message_id=rfc_message_id,
                    in_reply_to=in_reply_to,
                    references=references or in_reply_to,
                    status="SENT",  # Logged as sent in development environment
                    sent_at=now
                )
                db.add(db_msg)

                # Persist attachment records if any
                if attachments:
                    for att in attachments:
                        att_id = f"ATT-OUT-{uuid.uuid4().hex[:10].upper()}"
                        db_att = EmailAttachment(
                            id=att_id,
                            email_message_id=msg_id,
                            original_filename=att.get("filename", "document.pdf"),
                            stored_filename=att.get("stored_filename", att.get("filename", "document.pdf")),
                            file_size=len(att.get("content", b"")),
                            mime_type=att.get("mime_type", "application/pdf")
                        )
                        db.add(db_att)

                db.commit()

            return {
                "success": True,
                "mode": "development",
                "message_id": rfc_message_id,
                "message": (
                    "Email recorded in development outbox (SMTP password not configured in .env). "
                    "Configure SMTP_PASSWORD to deliver real emails to Gmail."
                ),
                "preview": {
                    "to": to_email,
                    "subject": subject,
                    "message_id": rfc_message_id
                }
            }

        # 2. Live SMTP network transmission
        msg_id = f"MSG-OUT-{uuid.uuid4().hex[:12].upper()}"
        try:
            if attachments:
                msg = MIMEMultipart("mixed")
                body_part = MIMEMultipart("alternative")
                if text_content:
                    body_part.attach(MIMEText(text_content, "plain", "utf-8"))
                body_part.attach(MIMEText(html_content, "html", "utf-8"))
                msg.attach(body_part)

                for att in attachments:
                    part = MIMEApplication(att["content"], Name=att.get("filename", "document.pdf"))
                    part["Content-Disposition"] = f'attachment; filename="{att.get("filename", "document.pdf")}"'
                    msg.attach(part)
            else:
                msg = MIMEMultipart("alternative")
                if text_content:
                    msg.attach(MIMEText(text_content, "plain", "utf-8"))
                msg.attach(MIMEText(html_content, "html", "utf-8"))

            msg["Subject"] = subject
            msg["From"] = f"{sender_name} <{sender_email}>"
            msg["To"] = to_email
            msg["Date"] = formatdate(localtime=True)
            msg["Message-ID"] = rfc_message_id

            if in_reply_to:
                msg["In-Reply-To"] = in_reply_to
            if references:
                msg["References"] = references

            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                clean_pw = settings.SMTP_PASSWORD.replace(" ", "")
                server.login(settings.SMTP_USERNAME, clean_pw)

            server.sendmail(sender_email, [to_email], msg.as_string())
            server.quit()

            DEV_OUTBOX.append(email_record)

            if db:
                db_msg = EmailMessage(
                    id=msg_id,
                    enquiry_id=enquiry_id,
                    direction="outgoing",
                    sender_name=sender_name,
                    sender_email=sender_email,
                    recipient_email=to_email,
                    subject=subject,
                    body_text=text_content or "",
                    body_html=html_content,
                    message_id=rfc_message_id,
                    in_reply_to=in_reply_to,
                    references=references or in_reply_to,
                    status="SENT",
                    sent_at=now
                )
                db.add(db_msg)

                # Persist attachment records if any
                if attachments:
                    for att in attachments:
                        att_id = f"ATT-OUT-{uuid.uuid4().hex[:10].upper()}"
                        db_att = EmailAttachment(
                            id=att_id,
                            email_message_id=msg_id,
                            original_filename=att.get("filename", "document.html"),
                            stored_filename=att.get("stored_filename", att.get("filename", "document.html")),
                            file_size=len(att.get("content", b"")),
                            mime_type=att.get("mime_type", "text/html")
                        )
                        db.add(db_att)

                db.commit()

            return {
                "success": True,
                "mode": "live_smtp",
                "message_id": rfc_message_id,
                "message": f"Email delivered successfully to {to_email} via Gmail SMTP."
            }

        except Exception as e:
            error_str = str(e)
            logger.error(f"Live SMTP delivery failed to {to_email}: {error_str}")

            if db:
                db_msg = EmailMessage(
                    id=msg_id,
                    enquiry_id=enquiry_id,
                    direction="outgoing",
                    sender_name=sender_name,
                    sender_email=sender_email,
                    recipient_email=to_email,
                    subject=subject,
                    body_text=text_content or "",
                    body_html=html_content,
                    message_id=rfc_message_id,
                    in_reply_to=in_reply_to,
                    references=references or in_reply_to,
                    status="FAILED",
                    error_message=error_str,
                    sent_at=now
                )
                db.add(db_msg)

                # Persist attachment records if any
                if attachments:
                    for att in attachments:
                        att_id = f"ATT-OUT-{uuid.uuid4().hex[:10].upper()}"
                        db_att = EmailAttachment(
                            id=att_id,
                            email_message_id=msg_id,
                            original_filename=att.get("filename", "document.html"),
                            stored_filename=att.get("stored_filename", att.get("filename", "document.html")),
                            file_size=len(att.get("content", b"")),
                            mime_type=att.get("mime_type", "text/html")
                        )
                        db.add(db_att)

                db.commit()

            return {
                "success": False,
                "mode": "error",
                "message_id": rfc_message_id,
                "message": f"SMTP transmission failed: {error_str}. Please verify Gmail credentials in .env."
            }

    @classmethod
    def send_enquiry_thank_you_email(
        cls,
        to_email: str,
        client_name: str,
        enquiry_id: str,
        registration_url: Optional[str] = None,
        wedding_location: Optional[str] = None,
        db: Optional[Session] = None
    ) -> dict:
        """
        Sends an automated luxury thank-you email immediately upon enquiry receipt,
        welcoming the couple and providing both the Google Forms link and the private portal registration link.
        Contains no document attachments and no plain-text credentials.
        """
        google_form_url = settings.GOOGLE_FORMS_REGISTRATION_URL
        if enquiry_id and "?" in google_form_url:
            form_link = f"{google_form_url}&enquiry_ref={enquiry_id}"
        elif enquiry_id:
            form_link = f"{google_form_url}?enquiry_ref={enquiry_id}"
        else:
            form_link = google_form_url

        portal_link = registration_url or f"{settings.FRONTEND_BASE_URL}/register"

        subject = f"Thank You for Contacting The Royal Knot — Wedding Celebration Enquiry ({enquiry_id})"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body {{ font-family: 'Georgia', serif; color: #1F2421; background-color: #FAF8F5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #FFFFFF; border: 1px solid #E5E0D8; padding: 40px; }}
            .header {{ text-align: center; border-bottom: 1px solid #E5E0D8; padding-bottom: 24px; }}
            .brand {{ font-size: 26px; font-weight: normal; text-transform: uppercase; letter-spacing: 3px; color: #1F2421; }}
            .tagline {{ font-size: 11px; text-transform: uppercase; letter-spacing: 3px; color: #9E7D3B; margin-top: 6px; }}
            .content {{ padding: 32px 0; font-size: 14px; line-height: 1.85; color: #4A4640; }}
            .btn {{ display: inline-block; padding: 14px 32px; background: #1F2421; color: #FAF8F5 !important; text-decoration: none; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600; margin: 24px 0; border: 1px solid #1F2421; }}
            .highlight-box {{ background: #FAF8F5; border-left: 2px solid #9E7D3B; padding: 18px 22px; margin: 22px 0; font-size: 13px; color: #2C2724; line-height: 1.8; }}
            .footer {{ border-top: 1px solid #E5E0D8; padding-top: 24px; font-size: 11px; color: #8C877D; text-align: center; line-height: 1.6; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <div class="brand">The Royal Knot</div>
              <div class="tagline">Bespoke Destination Weddings · Jaipur & Udaipur</div>
            </div>
            <div class="content">
              <p>Dear {client_name},</p>
              <p>Thank you for contacting <strong>The Royal Knot</strong>. We are delighted that you are considering us for your special celebration.</p>
              
              <div class="highlight-box">
                <p style="margin: 0 0 10px 0;">To help us understand your requirements and proceed with your registration, kindly complete the registration form using the link below.</p>
                <strong>Enquiry Reference:</strong> <span style="font-family: monospace; font-size: 14px; color: #1F2421;">{enquiry_id}</span>
              </div>

              <p style="text-align: center;">
                <a href="{form_link}" class="btn">Open Registration Form</a>
              </p>

              <p>Alternatively, you may complete your registration via our private portal: <a href="{portal_link}" style="color: #9E7D3B;">{portal_link}</a></p>

              <p>Once you submit your details through the form, our senior wedding concierges will review your celebration parameters and issue your confidential client portal activation link so you can begin private planning consultations.</p>

              <p>With our warmest regards,<br>
              <strong>The Royal Knot Concierge Team</strong><br>
              <em>Jaipur: Rambagh Enclave · Udaipur: Lake Pichola Promenade</em></p>
            </div>
            <div class="footer">
              Enquiry Reference: <strong>{enquiry_id}</strong><br>
              Official Concierge Desk: {settings.AGENCY_EMAIL}<br>
              Direct Form Link: <a href="{form_link}" style="color: #9E7D3B;">{form_link}</a><br>
              Direct Portal Link: <a href="{portal_link}" style="color: #9E7D3B;">{portal_link}</a>
            </div>
          </div>
        </body>
        </html>
        """

        text_content = (
            f"Dear {client_name},\n\n"
            f"Thank you for contacting The Royal Knot. We are delighted that you are considering us for your special celebration. "
            f"To help us understand your requirements and proceed with your registration, kindly complete the registration form using the link below:\n\n"
            f"{form_link}\n\n"
            f"Direct Portal Link: {portal_link}\n\n"
            f"Enquiry Reference: {enquiry_id}\n\n"
            f"Warm regards,\n"
            f"The Royal Knot Concierge Team\n"
            f"{settings.AGENCY_EMAIL}"
        )

        return cls.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            enquiry_id=enquiry_id,
            db=db
        )

    @classmethod
    def send_corrections_requested_email(
        cls,
        to_email: str,
        client_name: str,
        enquiry_id: str,
        registration_url: str,
        correction_notes: str,
        db: Optional[Session] = None
    ) -> dict:
        """Sends feedback and request for registration corrections to the client."""
        subject = f"The Royal Knot — Action Requested on Your Wedding Registration ({enquiry_id})"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body {{ font-family: 'Georgia', serif; color: #1F2421; background-color: #FAF8F5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #FFFFFF; border: 1px solid #E5E0D8; padding: 40px; }}
            .header {{ text-align: center; border-bottom: 1px solid #E5E0D8; padding-bottom: 24px; }}
            .brand {{ font-size: 24px; font-weight: normal; text-transform: uppercase; letter-spacing: 3px; color: #1F2421; }}
            .tagline {{ font-size: 11px; text-transform: uppercase; letter-spacing: 3px; color: #9E7D3B; margin-top: 6px; }}
            .content {{ padding: 30px 0; font-size: 14px; line-height: 1.85; color: #4A4640; }}
            .note-box {{ background: #FAF8F5; border-left: 2px solid #9E7D3B; padding: 16px 20px; margin: 20px 0; font-size: 13px; color: #2C2724; white-space: pre-wrap; }}
            .btn {{ display: inline-block; padding: 14px 30px; background: #1F2421; color: #FAF8F5 !important; text-decoration: none; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600; margin: 24px 0; border: 1px solid #1F2421; }}
            .footer {{ border-top: 1px solid #E5E0D8; padding-top: 24px; font-size: 11px; color: #8C877D; text-align: center; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <div class="brand">The Royal Knot</div>
              <div class="tagline">Bespoke Destination Weddings · Jaipur & Udaipur</div>
            </div>
            <div class="content">
              <p>Dear {client_name},</p>
              <p>Our senior wedding directors have reviewed your submitted client registration for enquiry <strong>#{enquiry_id}</strong>.</p>
              <p>To finalize your dossier and activate your client portal, please review the following notes and update your registration details:</p>
              
              <div class="note-box">
                <strong>Director Notes:</strong><br>
                {correction_notes}
              </div>

              <p style="text-align: center;">
                <a href="{registration_url}" class="btn">Update Registration Dossier</a>
              </p>

              <p>Warmest regards,<br>
              <strong>The Royal Knot Concierge Team</strong></p>
            </div>
            <div class="footer">
              Enquiry Reference: {enquiry_id}<br>
              Agency Email: {settings.AGENCY_EMAIL}
            </div>
          </div>
        </body>
        </html>
        """

        text_content = (
            f"Dear {client_name},\n\n"
            f"Please update your registration details for #{enquiry_id}:\n\n"
            f"Notes:\n{correction_notes}\n\n"
            f"Update link: {registration_url}\n\n"
            f"The Royal Knot Concierge Team"
        )

        return cls.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            enquiry_id=enquiry_id,
            db=db
        )

    @classmethod
    def send_registration_document_email(
        cls,
        to_email: str,
        client_name: str,
        enquiry_id: str,
        document_download_url: str,
        document_attachment: Optional[dict] = None,
        db: Optional[Session] = None
    ) -> dict:
        """Sends the formal Royal Knot client registration dossier with optional attachment."""
        subject = f"The Royal Knot — Client Registration Document (Ref: {enquiry_id})"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body {{ font-family: 'Georgia', serif; color: #1F2421; background-color: #FAF8F5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #FFFFFF; border: 1px solid #E5E0D8; padding: 40px; }}
            .header {{ text-align: center; border-bottom: 1px solid #E5E0D8; padding-bottom: 20px; }}
            .brand {{ font-size: 24px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; color: #1F2421; }}
            .tagline {{ font-size: 11px; text-transform: uppercase; letter-spacing: 3px; color: #9E7D3B; margin-top: 5px; }}
            .content {{ padding: 30px 0; font-size: 14px; line-height: 1.8; color: #4A4640; }}
            .btn {{ display: inline-block; padding: 12px 24px; background: #1F2421; color: #FAF8F5 !important; text-decoration: none; font-size: 12px; text-transform: uppercase; letter-spacing: 1.5px; font-weight: bold; margin: 20px 0; border: 1px solid #1F2421; }}
            .footer {{ border-top: 1px solid #E5E0D8; padding-top: 20px; font-size: 11px; color: #8C877D; text-align: center; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <div class="brand">The Royal Knot</div>
              <div class="tagline">Bespoke Destination Weddings · Jaipur & Udaipur</div>
            </div>
            <div class="content">
              <p>Dear {client_name},</p>
              <p>Thank you for connecting with <strong>The Royal Knot</strong> regarding your upcoming luxury destination celebration in Rajasthan.</p>
              <p>To enable our lead concierges to curate tailored palace venues, culinary frameworks, and master production timelines, please complete our formal <strong>Client Registration Document</strong> attached to this email.</p>
              <p style="text-align: center;">
                <a href="{document_download_url}" class="btn">View / Download Registration Document</a>
              </p>
              <p>Once completed, simply reply to this email with your filled document attached. Our team will review your dossier and activate your private planning workspace.</p>
              <p>Warmest regards,<br>
              <strong>The Royal Knot Concierge Team</strong><br>
              <em>Jaipur: Rambagh Enclave · Udaipur: Pichola Promenade</em></p>
            </div>
            <div class="footer">
              Enquiry Reference: {enquiry_id}<br>
              Official Agency Address: {settings.AGENCY_EMAIL}
            </div>
          </div>
        </body>
        </html>
        """

        text_content = (
            f"Dear {client_name},\n\n"
            f"Thank you for contacting The Royal Knot. Please download and complete our client registration document: {document_download_url}\n\n"
            f"Once filled, please reply to this email with your document attached.\n\n"
            f"Enquiry Reference: {enquiry_id}\n"
            f"The Royal Knot Concierge Team"
        )

        attachments = [document_attachment] if document_attachment else None
        return cls.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            attachments=attachments,
            enquiry_id=enquiry_id,
            db=db
        )

    @classmethod
    def send_reply_email(
        cls,
        to_email: str,
        client_name: str,
        subject: str,
        body: str,
        enquiry_id: str,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None,
        attachments: Optional[List[dict]] = None,
        db: Optional[Session] = None
    ) -> dict:
        """Sends a staff reply directly to the client's email thread."""
        clean_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body {{ font-family: 'Georgia', serif; color: #1F2421; background-color: #FAF8F5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #FFFFFF; border: 1px solid #E5E0D8; padding: 40px; }}
            .header {{ text-align: center; border-bottom: 1px solid #E5E0D8; padding-bottom: 20px; }}
            .brand {{ font-size: 22px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; color: #1F2421; }}
            .tagline {{ font-size: 11px; text-transform: uppercase; letter-spacing: 3px; color: #9E7D3B; margin-top: 5px; }}
            .content {{ padding: 25px 0; font-size: 14px; line-height: 1.8; color: #4A4640; white-space: pre-wrap; }}
            .footer {{ border-top: 1px solid #E5E0D8; padding-top: 20px; font-size: 11px; color: #8C877D; text-align: center; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <div class="brand">The Royal Knot</div>
              <div class="tagline">Bespoke Destination Weddings · Jaipur & Udaipur</div>
            </div>
            <div class="content">{body}</div>
            <div class="footer">
              Enquiry Reference: {enquiry_id} · Direct Concierge Communication<br>
              Agency Email: {settings.AGENCY_EMAIL}
            </div>
          </div>
        </body>
        </html>
        """

        return cls.send_email(
            to_email=to_email,
            subject=clean_subject,
            html_content=html_content,
            text_content=body,
            attachments=attachments,
            in_reply_to=in_reply_to,
            references=references or in_reply_to,
            enquiry_id=enquiry_id,
            db=db
        )

    @classmethod
    def send_account_activation_email(
        cls,
        to_email: str,
        client_name: str,
        activation_url: str,
        client_id: str,
        enquiry_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> dict:
        """Sends the secure account activation link to the registered client."""
        subject = f"The Royal Knot — Activate Your Wedding Planning Portal (Ref: {client_id})"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body {{ font-family: 'Georgia', serif; color: #1F2421; background-color: #FAF8F5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #FFFFFF; border: 1px solid #E5E0D8; padding: 40px; }}
            .header {{ text-align: center; border-bottom: 1px solid #E5E0D8; padding-bottom: 20px; }}
            .brand {{ font-size: 24px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; color: #1F2421; }}
            .tagline {{ font-size: 11px; text-transform: uppercase; letter-spacing: 3px; color: #9E7D3B; margin-top: 5px; }}
            .content {{ padding: 30px 0; font-size: 14px; line-height: 1.8; color: #4A4640; }}
            .btn {{ display: inline-block; padding: 14px 28px; background: #1F2421; color: #FAF8F5 !important; text-decoration: none; font-size: 12px; text-transform: uppercase; letter-spacing: 1.5px; font-weight: bold; margin: 25px 0; border: 1px solid #1F2421; }}
            .security-note {{ font-size: 11px; color: #8C877D; background: #FAF8F5; border: 1px solid #E5E0D8; padding: 12px; margin-top: 20px; }}
            .footer {{ border-top: 1px solid #E5E0D8; padding-top: 20px; font-size: 11px; color: #8C877D; text-align: center; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <div class="brand">The Royal Knot</div>
              <div class="tagline">Bespoke Destination Weddings · Jaipur & Udaipur</div>
            </div>
            <div class="content">
              <p>Dear {client_name},</p>
              <p>Your client dossier has been formally registered with <strong>The Royal Knot</strong> under Reference <strong>#{client_id}</strong>.</p>
              <p>Your confidential client portal account is ready for activation. Please click below to set your secure password and access your wedding dossier:</p>
              <p style="text-align: center;">
                <a href="{activation_url}" class="btn">Activate Your Account</a>
              </p>
              <div class="security-note">
                <strong>Security Notice:</strong> This activation link is unique to your registration and expires in 72 hours. Passwords are encrypted with cryptographic Argon2 verification.
              </div>
              <p style="margin-top: 25px;">Warm regards,<br>
              <strong>The Royal Knot Principal Planners</strong></p>
            </div>
            <div class="footer">
              Client Reference: {client_id} · Confidential & Secure<br>
              If the button does not work, visit: {activation_url}
            </div>
          </div>
        </body>
        </html>
        """

        text_content = (
            f"Dear {client_name},\n\n"
            f"Your client dossier is registered under #{client_id}. Please activate your account:\n"
            f"{activation_url}\n\n"
            f"This link expires in 72 hours.\n"
            f"The Royal Knot"
        )

        return cls.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            enquiry_id=enquiry_id,
            db=db
        )
