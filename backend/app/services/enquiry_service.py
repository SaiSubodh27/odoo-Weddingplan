import uuid
from typing import Optional, Tuple, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from fastapi import HTTPException, status

from app.models.enquiry import Enquiry, EnquiryNote
from app.models.client import Client
from app.models.user import UserAccount, ActivationToken
from app.schemas.enquiry import EnquiryCreate, EnquiryUpdate, EnquiryRegisterRequest
from app.core.security import generate_activation_token
from app.services.email_service import EmailService
from app.core.config import settings


class EnquiryService:
    @staticmethod
    def generate_next_id(db: Session) -> str:
        """Generates the next sequential enquiry ID (e.g. ENQ-2026-001)."""
        count = db.query(func.count(Enquiry.id)).scalar() or 0
        return f"ENQ-2026-{count + 1:03d}"

    @classmethod
    def create_enquiry(cls, db: Session, enquiry_in: EnquiryCreate) -> Enquiry:
        enquiry_id = cls.generate_next_id(db)
        enquiry_data = enquiry_in.model_dump()

        internal_notes = enquiry_data.pop("internal_notes", None)

        db_enquiry = Enquiry(
            id=enquiry_id,
            internal_notes=internal_notes,
            **enquiry_data
        )

        db.add(db_enquiry)
        db.flush()

        if internal_notes:
            initial_note = EnquiryNote(
                enquiry_id=enquiry_id,
                author=db_enquiry.assigned_staff or "Agency Staff",
                content=internal_notes
            )
            db.add(initial_note)

        db.commit()
        db.refresh(db_enquiry)
        return db_enquiry

    @staticmethod
    def get_enquiry(db: Session, enquiry_id: str) -> Optional[Enquiry]:
        return db.query(Enquiry).filter(
            Enquiry.id == enquiry_id,
            Enquiry.is_deleted == False
        ).first()

    @staticmethod
    def list_enquiries(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        source_filter: Optional[str] = None
    ) -> Tuple[List[Enquiry], int]:
        query = db.query(Enquiry).filter(Enquiry.is_deleted == False)

        if status_filter and status_filter != "All":
            query = query.filter(Enquiry.status == status_filter)

        if source_filter and source_filter != "All":
            query = query.filter(Enquiry.enquiry_source == source_filter)

        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Enquiry.client_name.ilike(pattern),
                    Enquiry.email.ilike(pattern),
                    Enquiry.phone.ilike(pattern),
                    Enquiry.wedding_location.ilike(pattern),
                    Enquiry.id.ilike(pattern)
                )
            )

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(Enquiry.created_at.desc()).offset(offset).limit(page_size).all()
        return items, total

    @staticmethod
    def update_enquiry(db: Session, enquiry_id: str, enquiry_in: EnquiryUpdate) -> Optional[Enquiry]:
        db_enquiry = db.query(Enquiry).filter(
            Enquiry.id == enquiry_id,
            Enquiry.is_deleted == False
        ).first()

        if not db_enquiry:
            return None

        update_data = enquiry_in.model_dump(exclude_unset=True)

        # If a new internal note is included in update, also append it to history
        new_note = update_data.get("internal_notes")
        if new_note and new_note != db_enquiry.internal_notes:
            note_record = EnquiryNote(
                enquiry_id=enquiry_id,
                author=db_enquiry.assigned_staff or "Agency Staff",
                content=new_note
            )
            db.add(note_record)

        for field, value in update_data.items():
            setattr(db_enquiry, field, value)

        db.commit()
        db.refresh(db_enquiry)
        return db_enquiry

    @staticmethod
    def add_internal_note(db: Session, enquiry_id: str, content: str, author: str = "Agency Staff") -> EnquiryNote:
        enquiry = db.query(Enquiry).filter(
            Enquiry.id == enquiry_id,
            Enquiry.is_deleted == False
        ).first()

        if not enquiry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enquiry '{enquiry_id}' not found."
            )

        note = EnquiryNote(
            enquiry_id=enquiry_id,
            author=author,
            content=content
        )
        db.add(note)
        # Also update current internal_notes field
        enquiry.internal_notes = content
        db.commit()
        db.refresh(note)
        return note

    @staticmethod
    def mark_document_sent(db: Session, enquiry_id: str) -> Enquiry:
        enquiry = db.query(Enquiry).filter(
            Enquiry.id == enquiry_id,
            Enquiry.is_deleted == False
        ).first()

        if not enquiry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enquiry '{enquiry_id}' not found."
            )

        enquiry.registration_sent_at = datetime.now(timezone.utc)
        enquiry.status = "Registration Document Sent"
        db.commit()
        db.refresh(enquiry)
        return enquiry

    @staticmethod
    def mark_document_received(db: Session, enquiry_id: str) -> Enquiry:
        enquiry = db.query(Enquiry).filter(
            Enquiry.id == enquiry_id,
            Enquiry.is_deleted == False
        ).first()

        if not enquiry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enquiry '{enquiry_id}' not found."
            )

        enquiry.registration_received_at = datetime.now(timezone.utc)
        enquiry.status = "Registration Received"
        db.commit()
        db.refresh(enquiry)
        return enquiry

    @classmethod
    def register_client_from_enquiry(
        cls,
        db: Session,
        enquiry_id: str,
        register_data: EnquiryRegisterRequest
    ) -> dict:
        """
        Explicit Staff Action: Registers an enquiry into a full Client record,
        creates a pending Client Account, generates a secure activation token,
        and dispatches the activation email.
        """
        enquiry = db.query(Enquiry).filter(
            Enquiry.id == enquiry_id,
            Enquiry.is_deleted == False
        ).first()

        if not enquiry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enquiry '{enquiry_id}' not found."
            )

        # 1. Prevent duplicate client account for the same email address
        existing_user = db.query(UserAccount).filter(UserAccount.email == enquiry.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A user account with email '{enquiry.email}' already exists. Duplicate client accounts are not permitted."
            )

        # 2. Check if a Client model already exists with this email
        client = db.query(Client).filter(Client.email == enquiry.email).first()
        if not client:
            client_count = db.query(func.count(Client.id)).scalar() or 0
            client_id = f"TRK-2026-0{80 + client_count + 1}"

            p1_name = register_data.partner1_name or enquiry.client_name
            p2_name = register_data.partner2_name or "Partner 2"

            client = Client(
                id=client_id,
                partner1_name=p1_name,
                partner2_name=p2_name,
                email=enquiry.email,
                phone=enquiry.phone,
                wedding_date=enquiry.wedding_date or datetime.now().date(),
                wedding_location=enquiry.wedding_location or "Jaipur / Udaipur Heritage Palace",
                expected_guest_count=enquiry.expected_guest_count or 100,
                estimated_budget=enquiry.estimated_budget or 0,
                wedding_theme=register_data.wedding_theme or "Bespoke Royal Heritage",
                service_package=register_data.service_package or "Full-Service",
                additional_requirements=register_data.additional_requirements or enquiry.requirements,
                enquiry_source=enquiry.enquiry_source,
                notes=enquiry.internal_notes,
                status="Registered"
            )
            db.add(client)
            db.flush()
        else:
            client.status = "Registered"

        # 3. Associate Enquiry with Client
        enquiry.client_id = client.id
        enquiry.status = "Registered"

        # 4. Create UserAccount in PENDING_ACTIVATION status
        user_id = f"USR-{uuid.uuid4().hex[:10].upper()}"
        user_account = UserAccount(
            id=user_id,
            client_id=client.id,
            email=enquiry.email,
            hashed_password=None,  # Null until client sets password
            role="client",
            status="PENDING_ACTIVATION",
            is_active=False
        )
        db.add(user_account)
        db.flush()

        # 5. Generate secure, one-time activation token
        raw_token, token_hash = generate_activation_token()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACTIVATION_TOKEN_EXPIRY_MINUTES)

        activation_token_record = ActivationToken(
            id=f"ACT-{uuid.uuid4().hex[:10].upper()}",
            user_id=user_account.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_used=False
        )
        db.add(activation_token_record)

        # 6. Commit transaction
        db.commit()
        db.refresh(enquiry)
        db.refresh(client)
        db.refresh(user_account)

        # 7. Send activation email
        activation_url = f"{settings.FRONTEND_BASE_URL}/activate?token={raw_token}"
        email_result = EmailService.send_account_activation_email(
            to_email=enquiry.email,
            client_name=enquiry.client_name,
            activation_url=activation_url,
            client_id=client.id
        )

        return {
            "success": True,
            "message": f"Client successfully registered under #{client.id}. Account created in pending activation.",
            "client_id": client.id,
            "user_id": user_account.id,
            "email": enquiry.email,
            "activation_url": activation_url,
            "activation_token": raw_token,
            "email_status": email_result
        }


enquiry_service = EnquiryService()
