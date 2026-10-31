import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, List, Dict
import logging
from app.core.config import settings

logger = logging.getLogger("royal_knot.email")

# In-memory development outbox to preview generated emails when SMTP is not configured
DEV_OUTBOX: List[Dict] = []


class EmailService:
    @staticmethod
    def is_smtp_configured() -> bool:
        """Returns True if minimum required SMTP credentials are present."""
        return bool(settings.SMTP_HOST and settings.SMTP_FROM_EMAIL)

    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[dict]] = None
    ) -> dict:
        """
        Sends an email via SMTP, or records it in the dev outbox if SMTP is not configured.
        Returns a dict indicating success status, message, and dev preview info.
        """
        email_record = {
            "to": to_email,
            "subject": subject,
            "html": html_content,
            "text": text_content,
            "sent_via": "smtp" if cls.is_smtp_configured() else "dev_outbox",
            "has_attachments": bool(attachments)
        }

        # If SMTP is not configured, do not fail silently; log clearly and save to dev outbox
        if not cls.is_smtp_configured():
            DEV_OUTBOX.append(email_record)
            logger.info(f"[DEV EMAIL OUTBOX] Email to {to_email} recorded. Subject: {subject}")
            return {
                "success": True,
                "mode": "development",
                "message": (
                    f"Email recorded in development outbox (SMTP not configured). "
                    f"In production, configure SMTP_HOST in .env to deliver real emails."
                ),
                "preview": {
                    "to": to_email,
                    "subject": subject
                }
            }

        # If SMTP is configured, attempt actual network delivery
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = to_email

            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Handle file attachments if provided
            if attachments:
                for att in attachments:
                    part = MIMEApplication(att["content"], Name=att["filename"])
                    part["Content-Disposition"] = f'attachment; filename="{att["filename"]}"'
                    msg.attach(part)

            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

            server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())
            server.quit()

            DEV_OUTBOX.append(email_record)
            return {
                "success": True,
                "mode": "live_smtp",
                "message": f"Email delivered successfully to {to_email} via SMTP."
            }

        except Exception as e:
            logger.error(f"SMTP delivery failed to {to_email}: {str(e)}")
            return {
                "success": False,
                "mode": "error",
                "message": f"SMTP transmission failed: {str(e)}. Please check your SMTP credentials."
            }

    @classmethod
    def send_registration_document_email(
        cls,
        to_email: str,
        client_name: str,
        enquiry_id: str,
        document_download_url: str,
        document_attachment: Optional[dict] = None
    ) -> dict:
        """Sends the formal Royal Knot client registration dossier to the client."""
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
              <p>Thank you for connecting with <strong>The Royal Knot</strong> regarding your upcoming luxury destination celebration.</p>
              <p>To enable our lead concierges to curate tailored palace venues, culinary frameworks, and master production timelines, please complete our formal <strong>Client Registration Document</strong>.</p>
              <p style="text-align: center;">
                <a href="{document_download_url}" class="btn">Download Registration Document</a>
              </p>
              <p>Once completed, please reply with the filled document so our team may complete your dossier and activate your client planning portal.</p>
              <p>Warmest regards,<br>
              <strong>The Royal Knot Concierge Team</strong><br>
              <em>Jaipur: Rambagh Enclave · Udaipur: Pichola Promenade</em></p>
            </div>
            <div class="footer">
              Enquiry Reference: {enquiry_id}<br>
              This is a formal communication from The Royal Knot Luxury Wedding Management.
            </div>
          </div>
        </body>
        </html>
        """

        text_content = (
            f"Dear {client_name},\n\n"
            f"Thank you for contacting The Royal Knot. Please download and fill our client registration document: {document_download_url}\n\n"
            f"Enquiry Reference: {enquiry_id}\n"
            f"The Royal Knot Concierge Team"
        )

        attachments = [document_attachment] if document_attachment else None
        return cls.send_email(to_email, subject, html_content, text_content, attachments)

    @classmethod
    def send_account_activation_email(
        cls,
        to_email: str,
        client_name: str,
        activation_url: str,
        client_id: str
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
              <p>Your client portal account is ready for activation. Please click below to set your confidential password and access your wedding dossier:</p>
              <p style="text-align: center;">
                <a href="{activation_url}" class="btn">Activate Your Account</a>
              </p>
              <div class="security-note">
                <strong>Security Notice:</strong> This activation link is unique to your registration and expires in 24 hours. If you did not request this registration, please contact our concierge desk.
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
            f"This link expires in 24 hours.\n"
            f"The Royal Knot"
        )

        return cls.send_email(to_email, subject, html_content, text_content)
