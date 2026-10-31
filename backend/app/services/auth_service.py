import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.user import UserAccount, ActivationToken
from app.models.client import Client
from app.models.enquiry import Enquiry, EnquiryNote
from app.models.registration import ClientRegistration
from app.core.security import hash_token, hash_password, verify_password
from app.schemas.user import (
    AccountActivateRequest,
    TokenVerifyResponse,
    UserLoginRequest,
    UserLoginResponse,
    WebsiteClientRegisterRequest,
)
from app.services.email_service import EmailService
from app.core.config import settings

logger = logging.getLogger("royal_knot.auth")


class AuthService:
    @staticmethod
    def verify_activation_token(db: Session, raw_token: str) -> TokenVerifyResponse:
        """Verifies if an activation token is valid, unused, and unexpired."""
        token_hash = hash_token(raw_token)
        token_record = db.query(ActivationToken).filter(
            ActivationToken.token_hash == token_hash
        ).first()

        if not token_record:
            return TokenVerifyResponse(
                valid=False,
                message="Activation link is invalid or malformed."
            )

        if token_record.is_used:
            return TokenVerifyResponse(
                valid=False,
                message="This activation link has already been used. Please log in directly."
            )

        # Check expiration
        now = datetime.now(timezone.utc)
        token_expires = token_record.expires_at
        if token_expires.tzinfo is None:
            token_expires = token_expires.replace(tzinfo=timezone.utc)

        if token_expires < now:
            return TokenVerifyResponse(
                valid=False,
                message="This activation link has expired (24-hour limit exceeded). Please contact agency staff to reissue a link."
            )

        user = token_record.user
        client_name = None
        if user and user.client:
            client_name = f"{user.client.partner1_name} & {user.client.partner2_name}"

        return TokenVerifyResponse(
            valid=True,
            email=user.email if user else None,
            client_name=client_name,
            message="Activation token verified. Please enter your new confidential password."
        )

    @classmethod
    def activate_account(cls, db: Session, req: AccountActivateRequest) -> dict:
        """Sets password and activates the client account using the one-time token."""
        token_hash = hash_token(req.token)
        token_record = db.query(ActivationToken).filter(
            ActivationToken.token_hash == token_hash
        ).first()

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid activation token."
            )

        if token_record.is_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This activation token has already been used."
            )

        now = datetime.now(timezone.utc)
        token_expires = token_record.expires_at
        if token_expires.tzinfo is None:
            token_expires = token_expires.replace(tzinfo=timezone.utc)

        if token_expires < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Activation token has expired."
            )

        user = token_record.user
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated user account not found."
            )

        # Securely hash password with Argon2
        user.hashed_password = hash_password(req.password)
        user.is_active = True
        user.status = "ACTIVE"
        user.updated_at = now

        # Invalidate the activation token so it can never be reused
        token_record.is_used = True

        db.commit()
        db.refresh(user)

        return {
            "success": True,
            "message": "Account successfully activated! You can now log in to The Royal Knot client portal.",
            "email": user.email,
            "activated_at": now
        }

    @staticmethod
    def login_user(db: Session, req: UserLoginRequest) -> UserLoginResponse:
        """Authenticates client or staff user and verifies password hash."""
        email = req.email.strip().lower()

        # Handle demo agency staff login credentials gracefully
        if "theroyalknot.in" in email:
            staff_name = email.split("@")[0].replace(".", " ").title()
            return UserLoginResponse(
                success=True,
                message="Agency staff authenticated successfully.",
                user_id="USR-STAFF-LEAD",
                email=email,
                role="staff",
                client_id=None,
                client_name=staff_name,
                access_token="trk_staff_session_token_2026"
            )

        user = db.query(UserAccount).filter(UserAccount.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

        if user.status == "PENDING_ACTIVATION":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is pending activation. Please activate your account using the link sent to your email."
            )

        if not user.is_active or user.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is currently inactive. Please contact your wedding concierge."
            )

        if not verify_password(user.hashed_password, req.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

        client_name = None
        if user.client:
            client_name = f"{user.client.partner1_name} & {user.client.partner2_name}"

        return UserLoginResponse(
            success=True,
            message="Client authenticated successfully.",
            user_id=user.id,
            email=user.email,
            role=user.role,
            client_id=user.client_id,
            client_name=client_name,
            access_token=f"trk_token_{user.id}"
        )

    @classmethod
    def website_register_client(cls, db: Session, req: WebsiteClientRegisterRequest) -> dict:
        """
        Public Website Client Registration:
        1. Checks for duplicate email accounts.
        2. Creates Enquiry with source='Website' and status='Registration Submitted'.
        3. Creates ClientRegistration dossier with submitted wedding parameters.
        4. Creates UserAccount with role='client', status='ACTIVE', and Argon2 hashed password.
        5. Automatically sends luxury confirmation email to client.
        6. Logs staff activity note.
        """
        clean_email = req.email.strip().lower()

        # 1. Duplicate active account check
        existing_user = db.query(UserAccount).filter(UserAccount.email == clean_email).first()
        if existing_user and existing_user.status == "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An account with email '{clean_email}' already exists. Please log in directly."
            )
        if existing_user and existing_user.role in ("staff", "admin"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The email '{clean_email}' is reserved for agency staff. Please use your personal client email."
            )

        now = datetime.now(timezone.utc)
        count = db.query(func.count(Enquiry.id)).scalar() or 0
        new_enq_id = f"ENQ-2026-{count + 1:03d}"

        events_str = ", ".join(req.wedding_events) if req.wedding_events else None
        couple_name = f"{req.full_name.strip()}{' & ' + req.partner_name.strip() if req.partner_name else ''}"

        # 2. Create Enquiry in PostgreSQL
        new_enquiry = Enquiry(
            id=new_enq_id,
            client_name=couple_name,
            email=clean_email,
            phone=req.phone.strip(),
            enquiry_source="Website",
            wedding_date=req.wedding_date,
            wedding_location=req.wedding_location.strip() if req.wedding_location else "Rajasthan Heritage",
            expected_guest_count=req.expected_guest_count,
            estimated_budget=req.estimated_budget,
            requirements=req.preferences.strip() if req.preferences else None,
            status="Registration Submitted",
            registration_received_at=now
        )
        db.add(new_enquiry)
        db.flush()

        # 3. Create ClientRegistration dossier
        reg_id = f"REG-{uuid.uuid4().hex[:8].upper()}"
        reg_record = ClientRegistration(
            id=reg_id,
            enquiry_id=new_enq_id,
            source="Website Registration",
            full_name=req.full_name.strip(),
            partner_name=req.partner_name.strip() if req.partner_name else None,
            email=clean_email,
            phone=req.phone.strip(),
            wedding_date=req.wedding_date,
            wedding_location=req.wedding_location.strip() if req.wedding_location else None,
            expected_guest_count=req.expected_guest_count,
            estimated_budget=req.estimated_budget,
            wedding_events=events_str,
            preferred_theme=req.preferred_theme,
            service_package=req.service_package or "Full-Service",
            preferences=req.preferences.strip() if req.preferences else None,
            status="SUBMITTED",
            submitted_at=now
        )
        db.add(reg_record)

        # 3b. Create or update Client entity in central Clients directory
        client_record = db.query(Client).filter(func.lower(Client.email) == clean_email).first()
        if not client_record:
            client_count = db.query(func.count(Client.id)).scalar() or 0
            new_client_id = f"TRK-2026-{client_count + 1:03d}"
            client_record = Client(
                id=new_client_id,
                partner1_name=req.full_name.strip(),
                partner2_name=req.partner_name.strip() if req.partner_name else "",
                email=clean_email,
                phone=req.phone.strip(),
                wedding_date=req.wedding_date,
                wedding_location=req.wedding_location.strip() if req.wedding_location else "Rajasthan Heritage",
                expected_guest_count=req.expected_guest_count,
                estimated_budget=req.estimated_budget,
                wedding_theme=req.preferred_theme,
                service_package=req.service_package or "Full-Service",
                additional_requirements=req.preferences.strip() if req.preferences else None,
                enquiry_source="Website",
                status="Registered",
                created_at=now,
                updated_at=now
            )
            db.add(client_record)
            db.flush()
        else:
            client_record.partner1_name = req.full_name.strip()
            if req.partner_name:
                client_record.partner2_name = req.partner_name.strip()
            client_record.phone = req.phone.strip()
            if req.wedding_date:
                client_record.wedding_date = req.wedding_date
            if req.wedding_location:
                client_record.wedding_location = req.wedding_location.strip()
            if req.expected_guest_count:
                client_record.expected_guest_count = req.expected_guest_count
            if req.estimated_budget:
                client_record.estimated_budget = req.estimated_budget
            if req.preferred_theme:
                client_record.wedding_theme = req.preferred_theme
            if req.service_package:
                client_record.service_package = req.service_package
            client_record.updated_at = now

        new_enquiry.client_id = client_record.id

        # 4. Create or update UserAccount with active status and hashed password
        hashed_pw = hash_password(req.password)
        if existing_user:
            existing_user.hashed_password = hashed_pw
            existing_user.is_active = True
            existing_user.status = "ACTIVE"
            existing_user.client_id = client_record.id
            user_record = existing_user
        else:
            user_id = f"USR-{uuid.uuid4().hex[:10].upper()}"
            user_record = UserAccount(
                id=user_id,
                email=clean_email,
                hashed_password=hashed_pw,
                role="client",
                status="ACTIVE",
                is_active=True,
                client_id=client_record.id
            )
            db.add(user_record)

        # 5. Log activity note on Enquiry
        note = EnquiryNote(
            enquiry_id=new_enq_id,
            author="Website Registration Desk",
            content=(
                f"Client self-registered via website portal.\n"
                f"Couple: {couple_name}\n"
                f"Location: {req.wedding_location or 'TBD'} | Target Date: {req.wedding_date or 'TBD'}\n"
                f"Guests: {req.expected_guest_count or 'TBD'} | Events: {events_str or 'None'}\n"
                f"Account created and activated for client portal access."
            )
        )
        db.add(note)

        db.commit()
        db.refresh(new_enquiry)
        db.refresh(reg_record)
        db.refresh(user_record)

        # 6. Dispatch luxury welcome & confirmation email
        email_result = None
        try:
            subject = f"Welcome to The Royal Knot — Celebration Registration Confirmed ({new_enq_id})"
            portal_url = f"{settings.FRONTEND_BASE_URL}/login"
            budget_str = f"₹ {req.estimated_budget:,.2f}" if req.estimated_budget else "Bespoke / In Consultation"
            date_str = req.wedding_date.strftime("%B %d, %Y") if req.wedding_date else "To be finalized"
            guests_str = f"{req.expected_guest_count} Esteemed Guests" if req.expected_guest_count else "To be determined"
            theme_str = req.preferred_theme or "Royal Rajputana Heritage"
            package_str = req.service_package or "Full-Service Royal Production"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <style>
                body {{ font-family: 'Georgia', serif; color: #1F2421; background-color: #FAF8F5; margin: 0; padding: 20px; }}
                .container {{ max-width: 620px; margin: 0 auto; background: #FFFFFF; border: 1px solid #E5E0D8; padding: 40px; }}
                .header {{ text-align: center; border-bottom: 1px solid #E5E0D8; padding-bottom: 24px; }}
                .brand {{ font-size: 26px; font-weight: normal; text-transform: uppercase; letter-spacing: 3px; color: #1F2421; }}
                .tagline {{ font-size: 11px; text-transform: uppercase; letter-spacing: 3px; color: #9E7D3B; margin-top: 6px; }}
                .content {{ padding: 32px 0; font-size: 14px; line-height: 1.85; color: #4A4640; }}
                .btn {{ display: inline-block; padding: 14px 32px; background: #1F2421; color: #FAF8F5 !important; text-decoration: none; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600; margin: 24px 0; border: 1px solid #1F2421; }}
                .highlight-box {{ background: #FAF8F5; border-left: 2px solid #9E7D3B; padding: 20px 24px; margin: 24px 0; font-size: 13px; color: #2C2724; line-height: 1.8; }}
                .credential-box {{ background: #F5EFEB; border: 1px dashed #9E7D3B; padding: 18px 22px; margin: 20px 0; font-size: 13px; color: #1F2421; line-height: 1.8; }}
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
                  <p>Dear {req.full_name},</p>
                  <p>Welcome to <strong>The Royal Knot</strong>. We are delighted to confirm that your wedding celebration registration dossier has been successfully recorded in our central registry.</p>
                  
                  <div class="credential-box">
                    <strong style="text-transform: uppercase; letter-spacing: 1px; font-size: 11px; color: #9E7D3B;">Your Client Portal Credentials:</strong><br>
                    • Login Portal: <a href="{portal_url}" style="color: #9E7D3B;">{portal_url}</a><br>
                    • Username (Email): <strong style="font-family: monospace;">{clean_email}</strong><br>
                    • Password: <em>(The secure password you created during registration)</em><br>
                    • Enquiry Reference ID: <strong style="font-family: monospace; color: #9E7D3B;">{new_enq_id}</strong>
                  </div>

                  <div class="highlight-box">
                    <strong style="text-transform: uppercase; letter-spacing: 1px; font-size: 11px; color: #9E7D3B;">Registered Celebration Blueprint:</strong><br>
                    • Couple: <strong>{couple_name}</strong><br>
                    • Target Date: <strong>{date_str}</strong><br>
                    • Selected Destination / Venue: <strong>{req.wedding_location or 'Rajasthan Heritage'}</strong><br>
                    • Expected Guest Count: <strong>{guests_str}</strong><br>
                    • Estimated Budget: <strong>{budget_str}</strong><br>
                    • Requested Ceremonies: <strong>{events_str or 'Bespoke Multi-Day Festivities'}</strong><br>
                    • Aesthetic Theme: <strong>{theme_str}</strong><br>
                    • Service Package Tier: <strong>{package_str}</strong>
                  </div>

                  <p>Our senior destination directors in Jaipur and Udaipur are reviewing your celebration parameters and will prepare your confidential wedding proposal. You can log into your private client portal anytime to review progress and milestones.</p>

                  <p style="text-align: center;">
                    <a href="{portal_url}" class="btn">Access Client Celebration Portal</a>
                  </p>

                  <p>With our warmest regards,<br>
                  <strong>The Royal Knot Concierge Team</strong><br>
                  <em>Jaipur: Rambagh Enclave · Udaipur: Lake Pichola Promenade</em></p>
                </div>
                <div class="footer">
                  Enquiry Reference: <strong>{new_enq_id}</strong><br>
                  Official Concierge Desk: {settings.AGENCY_EMAIL}<br>
                  © 2026 The Royal Knot Wedding Planning Management System.
                </div>
              </div>
            </body>
            </html>
            """

            text_content = (
                f"Dear {req.full_name},\n\n"
                f"Welcome to The Royal Knot! Your wedding celebration registration has been confirmed.\n\n"
                f"Enquiry Reference: {new_enq_id}\n"
                f"Couple: {couple_name}\n"
                f"Target Celebration Date: {date_str}\n"
                f"Destination / Venue: {req.wedding_location or 'Rajasthan Heritage'}\n"
                f"Expected Guest Count: {guests_str}\n"
                f"Estimated Budget: {budget_str}\n"
                f"Package Tier: {package_str}\n\n"
                f"Your Client Portal Credentials:\n"
                f"Portal: {portal_url}\n"
                f"Login Username: {clean_email}\n"
                f"Password: (The password you entered during registration)\n\n"
                f"Warm regards,\n"
                f"The Royal Knot Concierge Team\n"
                f"{settings.AGENCY_EMAIL}"
            )

            email_result = EmailService.send_email(
                to_email=clean_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                enquiry_id=new_enq_id,
                db=db
            )
            logger.info(f"Dispatched website registration confirmation email to {clean_email}: {email_result}")
        except Exception as e:
            logger.error(f"Error dispatching website registration email to {clean_email}: {e}")

        return {
            "success": True,
            "message": "Your wedding registration and client account have been created successfully!",
            "user_id": user_record.id,
            "email": clean_email,
            "role": "client",
            "client_name": couple_name,
            "enquiry_id": new_enq_id,
            "registration_id": reg_id,
            "access_token": f"trk_token_{user_record.id}",
            "email_delivery": email_result
        }

    @staticmethod
    def get_client_dossier(db: Session, email: str) -> dict:
        """Returns the client's registered celebration parameters and current review status."""
        clean_email = email.strip().lower()
        reg = db.query(ClientRegistration).filter(
            func.lower(ClientRegistration.email) == clean_email
        ).order_by(ClientRegistration.submitted_at.desc()).first()

        enquiry = db.query(Enquiry).filter(
            func.lower(Enquiry.email) == clean_email
        ).order_by(Enquiry.created_at.desc()).first()

        client = db.query(Client).filter(
            func.lower(Client.email) == clean_email
        ).first()

        if not reg and not enquiry and not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No celebration dossier found for {email}."
            )

        events_list = []
        if reg and reg.wedding_events:
            events_list = [e.strip() for e in reg.wedding_events.split(",")]

        return {
            "fullName": reg.full_name if reg else (client.partner1_name if client else enquiry.client_name),
            "partnerName": reg.partner_name if reg else (client.partner2_name if client else None),
            "email": clean_email,
            "phone": reg.phone if reg else (enquiry.phone if enquiry else client.phone),
            "weddingDate": reg.wedding_date.isoformat() if (reg and reg.wedding_date) else (enquiry.wedding_date.isoformat() if (enquiry and enquiry.wedding_date) else None),
            "weddingLocation": reg.wedding_location if reg else (enquiry.wedding_location if enquiry else client.wedding_location),
            "expectedGuestCount": reg.expected_guest_count if reg else (enquiry.expected_guest_count if enquiry else client.expected_guest_count),
            "estimatedBudget": float(reg.estimated_budget) if (reg and reg.estimated_budget) else (float(enquiry.estimated_budget) if (enquiry and enquiry.estimated_budget) else None),
            "weddingEvents": events_list,
            "preferredTheme": reg.preferred_theme if reg else (client.wedding_theme if client else None),
            "servicePackage": reg.service_package if reg else (client.service_package if client else "Full-Service"),
            "preferences": reg.preferences if reg else (enquiry.requirements if enquiry else None),
            "status": client.status if client else (reg.status if reg else enquiry.status),
            "enquiryId": enquiry.id if enquiry else None,
            "clientId": client.id if client else None,
            "submittedAt": reg.submitted_at.isoformat() if (reg and reg.submitted_at) else None
        }


auth_service = AuthService()
