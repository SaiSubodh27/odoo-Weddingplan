import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.enquiry import Enquiry, EnquiryNote
from app.models.registration import ClientRegistration
from app.models.client import Client
from app.models.user import UserAccount, ActivationToken
from app.schemas.registration import (
    ClientRegistrationSubmitRequest,
    RegistrationVerifyResponse,
    ClientRegistrationResponse,
)
from app.core.security import generate_activation_token
from app.services.email_service import EmailService
from app.core.config import settings


class RegistrationService:
    @staticmethod
    def verify_token(db: Session, token: str) -> RegistrationVerifyResponse:
        """
        Validates the online registration token and returns pre-fillable enquiry details.
        """
        if not token or not token.strip():
            return RegistrationVerifyResponse(
                valid=False,
                message="No registration token provided. Please use the link provided in your welcome email."
            )

        clean_token = token.strip()
        enquiry = db.query(Enquiry).filter(
            Enquiry.registration_token == clean_token,
            Enquiry.is_deleted == False
        ).first()

        if not enquiry:
            return RegistrationVerifyResponse(
                valid=False,
                message="The registration link is invalid or unrecognized."
            )

        now = datetime.now(timezone.utc)
        if enquiry.registration_token_expires_at:
            exp = enquiry.registration_token_expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp < now:
                return RegistrationVerifyResponse(
                    valid=False,
                    message="This registration link has expired. Please contact concierge staff to reissue a link."
                )

        existing_reg_data = None
        if enquiry.registration:
            reg = enquiry.registration
            existing_reg_data = {
                "id": reg.id,
                "fullName": reg.full_name,
                "partnerName": reg.partner_name,
                "email": reg.email,
                "phone": reg.phone,
                "address": reg.address,
                "weddingDate": reg.wedding_date.isoformat() if reg.wedding_date else None,
                "weddingLocation": reg.wedding_location,
                "expectedGuestCount": reg.expected_guest_count,
                "estimatedBudget": float(reg.estimated_budget) if reg.estimated_budget else None,
                "weddingEvents": [e.strip() for e in reg.wedding_events.split(",")] if reg.wedding_events else [],
                "preferredTheme": reg.preferred_theme,
                "servicePackage": reg.service_package,
                "preferences": reg.preferences,
                "status": reg.status,
                "correctionNotes": reg.correction_notes,
                "submittedAt": reg.submitted_at.isoformat() if reg.submitted_at else None
            }

        return RegistrationVerifyResponse(
            valid=True,
            message="Registration token verified. You may now complete your bespoke wedding registration.",
            enquiry_id=enquiry.id,
            client_name=enquiry.client_name,
            partner_name=enquiry.registration.partner_name if enquiry.registration else None,
            email=enquiry.email,
            phone=enquiry.phone,
            wedding_date=enquiry.wedding_date,
            wedding_location=enquiry.wedding_location,
            expected_guest_count=enquiry.expected_guest_count,
            estimated_budget=enquiry.estimated_budget,
            requirements=enquiry.requirements,
            existing_registration=existing_reg_data
        )

    @classmethod
    def submit_registration(
        cls,
        db: Session,
        req: ClientRegistrationSubmitRequest
    ) -> Dict[str, Any]:
        """
        Validates and records client registration data in PostgreSQL, associating it with the enquiry.
        Prevents duplicate accounts and duplicate client records.
        """
        enquiry = db.query(Enquiry).filter(
            Enquiry.registration_token == req.token.strip(),
            Enquiry.is_deleted == False
        ).first()

        if not enquiry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid registration token."
            )

        now = datetime.now(timezone.utc)
        if enquiry.registration_token_expires_at:
            exp = enquiry.registration_token_expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp < now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Registration link has expired. Please contact concierge staff."
                )

        # Check if an active user account already exists with this email
        existing_user = db.query(UserAccount).filter(UserAccount.email == req.email.strip().lower()).first()
        if existing_user and existing_user.status == "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An active client account already exists for {req.email}. Please log in directly."
            )

        events_str = ", ".join(req.wedding_events) if req.wedding_events else None

        existing_reg = db.query(ClientRegistration).filter(
            ClientRegistration.enquiry_id == enquiry.id
        ).first()

        if existing_reg:
            if existing_reg.status == "APPROVED":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This registration has already been approved by our concierge team."
                )

            # Update existing registration record
            existing_reg.full_name = req.full_name.strip()
            existing_reg.partner_name = req.partner_name.strip() if req.partner_name else None
            existing_reg.email = req.email.strip().lower()
            existing_reg.phone = req.phone.strip()
            existing_reg.address = req.address.strip() if req.address else None
            existing_reg.wedding_date = req.wedding_date
            existing_reg.wedding_location = req.wedding_location.strip() if req.wedding_location else None
            existing_reg.expected_guest_count = req.expected_guest_count
            existing_reg.estimated_budget = req.estimated_budget
            existing_reg.wedding_events = events_str
            existing_reg.preferred_theme = req.preferred_theme
            existing_reg.service_package = req.service_package or "Full-Service"
            existing_reg.preferences = req.preferences.strip() if req.preferences else None
            existing_reg.status = "SUBMITTED"
            existing_reg.submitted_at = now
            reg_record = existing_reg
        else:
            reg_id = f"REG-{uuid.uuid4().hex[:8].upper()}"
            reg_record = ClientRegistration(
                id=reg_id,
                enquiry_id=enquiry.id,
                full_name=req.full_name.strip(),
                partner_name=req.partner_name.strip() if req.partner_name else None,
                email=req.email.strip().lower(),
                phone=req.phone.strip(),
                address=req.address.strip() if req.address else None,
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

        # Synchronize core enquiry fields with verified registration data
        enquiry.client_name = f"{req.full_name.strip()}{' & ' + req.partner_name.strip() if req.partner_name else ''}"
        enquiry.phone = req.phone.strip()
        if req.wedding_date:
            enquiry.wedding_date = req.wedding_date
        if req.wedding_location:
            enquiry.wedding_location = req.wedding_location.strip()
        if req.expected_guest_count:
            enquiry.expected_guest_count = req.expected_guest_count
        if req.estimated_budget:
            enquiry.estimated_budget = req.estimated_budget
        if req.preferences:
            enquiry.requirements = req.preferences.strip()

        enquiry.status = "Registration Submitted"
        enquiry.registration_received_at = now

        note = EnquiryNote(
            enquiry_id=enquiry.id,
            author="Client (Online Registration)",
            content=(
                f"Client submitted online registration dossier.\n"
                f"Couple: {req.full_name} & {req.partner_name or 'Partner'}\n"
                f"Location: {req.wedding_location or 'TBD'} | Date: {req.wedding_date or 'TBD'}\n"
                f"Guests: {req.expected_guest_count or 'TBD'} | Events: {events_str or 'None specified'}"
            )
        )
        db.add(note)

        db.commit()
        db.refresh(reg_record)
        db.refresh(enquiry)

        return {
            "success": True,
            "message": "Your registration has been submitted successfully! Our lead wedding concierges will review your celebration parameters and issue your portal activation credentials.",
            "registration_id": reg_record.id,
            "enquiry_id": enquiry.id,
            "status": reg_record.status,
            "submitted_at": reg_record.submitted_at
        }

    @staticmethod
    def get_registration(db: Session, enquiry_id: str) -> Optional[ClientRegistration]:
        return db.query(ClientRegistration).filter(
            ClientRegistration.enquiry_id == enquiry_id
        ).first()

    @classmethod
    def review_registration(
        cls,
        db: Session,
        enquiry_id: str,
        reviewed_by: str = "Agency Staff",
        notes: Optional[str] = None
    ) -> ClientRegistration:
        reg = cls.get_registration(db, enquiry_id)
        if not reg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No registration dossier found for enquiry '{enquiry_id}'."
            )

        now = datetime.now(timezone.utc)
        reg.status = "UNDER_REVIEW"
        reg.reviewed_by = reviewed_by
        reg.reviewed_at = now
        reg.review_notes = notes

        enquiry = reg.enquiry
        enquiry.status = "Under Review"
        enquiry.registration_reviewed_at = now

        note_content = f"Registration marked 'Under Review' by {reviewed_by}."
        if notes:
            note_content += f"\nReview Notes: {notes}"

        db.add(EnquiryNote(
            enquiry_id=enquiry.id,
            author=reviewed_by,
            content=note_content
        ))

        db.commit()
        db.refresh(reg)
        return reg

    @classmethod
    def request_corrections(
        cls,
        db: Session,
        enquiry_id: str,
        correction_notes: str,
        staff_name: str = "Agency Staff"
    ) -> Dict[str, Any]:
        reg = cls.get_registration(db, enquiry_id)
        if not reg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No registration dossier found for enquiry '{enquiry_id}'."
            )

        now = datetime.now(timezone.utc)
        reg.status = "CORRECTIONS_REQUESTED"
        reg.correction_notes = correction_notes
        reg.reviewed_by = staff_name
        reg.reviewed_at = now

        enquiry = reg.enquiry
        enquiry.status = "Corrections Requested"

        # Dispatch email requesting corrections with Google Forms link
        form_url = settings.GOOGLE_FORMS_REGISTRATION_URL
        registration_url = f"{form_url}?enquiry_ref={enquiry.id}" if "?" not in form_url else f"{form_url}&enquiry_ref={enquiry.id}"
        email_res = EmailService.send_corrections_requested_email(
            to_email=reg.email,
            client_name=reg.full_name,
            enquiry_id=enquiry.id,
            registration_url=registration_url,
            correction_notes=correction_notes,
            db=db
        )

        db.add(EnquiryNote(
            enquiry_id=enquiry.id,
            author=staff_name,
            content=f"Requested registration corrections from client:\n\"{correction_notes}\""
        ))

        db.commit()
        db.refresh(reg)

        return {
            "success": True,
            "message": f"Correction request sent to {reg.email}.",
            "registration_status": reg.status,
            "email_status": email_res
        }

    @classmethod
    def approve_and_activate(
        cls,
        db: Session,
        enquiry_id: str,
        reviewed_by: str = "Agency Staff"
    ) -> Dict[str, Any]:
        """
        Approves client registration, creates Client dossier in PostgreSQL,
        creates user account in PENDING_ACTIVATION, and sends secure activation email.
        """
        reg = cls.get_registration(db, enquiry_id)
        if not reg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No registration found for enquiry '{enquiry_id}'."
            )

        enquiry = reg.enquiry
        now = datetime.now(timezone.utc)

        # 1. Prevent duplicate client account for the same email address
        existing_user = db.query(UserAccount).filter(UserAccount.email == reg.email).first()
        if existing_user and existing_user.status == "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An active user account with email '{reg.email}' already exists."
            )

        # 2. Create or link Client model
        client = db.query(Client).filter(Client.email == reg.email).first()
        if not client:
            client_count = db.query(func.count(Client.id)).scalar() or 0
            client_id = f"TRK-2026-0{80 + client_count + 1}"

            client = Client(
                id=client_id,
                partner1_name=reg.full_name,
                partner2_name=reg.partner_name or "Partner",
                email=reg.email,
                phone=reg.phone,
                wedding_date=reg.wedding_date or datetime.now().date(),
                wedding_location=reg.wedding_location or "Jaipur / Udaipur Heritage Palace",
                expected_guest_count=reg.expected_guest_count or 100,
                estimated_budget=reg.estimated_budget or 0,
                wedding_theme=reg.preferred_theme or "Bespoke Royal Heritage",
                service_package=reg.service_package or "Full-Service",
                additional_requirements=reg.preferences or enquiry.requirements,
                enquiry_source=enquiry.enquiry_source,
                notes=enquiry.internal_notes,
                status="Registered"
            )
            db.add(client)
            db.flush()
        else:
            client.status = "Registered"

        # 3. Mark registration approved
        reg.status = "APPROVED"
        reg.reviewed_by = reviewed_by
        reg.reviewed_at = now

        # 4. Associate Enquiry with Client and update status
        enquiry.client_id = client.id
        enquiry.status = "Registered"
        enquiry.registration_reviewed_at = now

        # 5. Create UserAccount in PENDING_ACTIVATION
        if not existing_user:
            user_id = f"USR-{uuid.uuid4().hex[:10].upper()}"
            user_account = UserAccount(
                id=user_id,
                client_id=client.id,
                email=reg.email,
                hashed_password=None,
                role="client",
                status="PENDING_ACTIVATION",
                is_active=False
            )
            db.add(user_account)
            db.flush()
        else:
            user_account = existing_user
            user_account.client_id = client.id
            user_account.status = "PENDING_ACTIVATION"
            user_account.is_active = False

        # 6. Generate secure, one-time activation token
        raw_token, token_hash = generate_activation_token()
        expires_at = now + timedelta(minutes=settings.ACTIVATION_TOKEN_EXPIRY_MINUTES)

        activation_token_record = ActivationToken(
            id=f"ACT-{uuid.uuid4().hex[:10].upper()}",
            user_id=user_account.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_used=False
        )
        db.add(activation_token_record)

        # 7. Add Staff Note
        db.add(EnquiryNote(
            enquiry_id=enquiry.id,
            author=reviewed_by,
            content=f"Registration approved by {reviewed_by}. Client record #{client.id} created and account activation invitation sent to {reg.email}."
        ))

        db.commit()
        db.refresh(reg)
        db.refresh(enquiry)
        db.refresh(client)
        db.refresh(user_account)

        # 8. Send activation email
        activation_url = f"{settings.FRONTEND_BASE_URL}/activate?token={raw_token}"
        email_result = EmailService.send_account_activation_email(
            to_email=reg.email,
            client_name=f"{reg.full_name} & {reg.partner_name or 'Partner'}",
            activation_url=activation_url,
            client_id=client.id,
            enquiry_id=enquiry.id,
            db=db
        )

        return {
            "success": True,
            "message": f"Registration approved! Client dossier #{client.id} created and account activation link dispatched to {reg.email}.",
            "client_id": client.id,
            "user_id": user_account.id,
            "email": reg.email,
            "activation_url": activation_url,
            "activation_token": raw_token,
            "email_status": email_result,
            "registration_status": "APPROVED",
            "enquiry_status": "Registered"
        }


registration_service = RegistrationService()
