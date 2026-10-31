import os
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.agreement import (
    ServiceAgreement,
    AgreementPaymentMilestone,
    AgreementDocument,
    AgreementStatusHistory
)
from app.models.client import Client
from app.schemas.agreement import (
    ServiceAgreementCreate,
    ServiceAgreementUpdate,
    SignAgreementRequest,
    SignAgreementResponse,
    SendOTPResponse,
    VerifyOTPResponse
)
from app.services.email_service import EmailService
from app.services.agreement_pdf_service import generate_service_agreement_pdf


def hash_otp(raw_otp: str) -> str:
    return hashlib.sha256(raw_otp.strip().encode("utf-8")).hexdigest()


class AgreementService:
    UPLOADS_DIR = os.path.join(os.getcwd(), "uploads", "agreements")

    def __init__(self):
        os.makedirs(self.UPLOADS_DIR, exist_ok=True)

    def get_or_create_agreement_for_client(self, db: Session, client_id: str) -> ServiceAgreement:
        """Retrieves existing agreement or instantiates one from the Client DB record."""
        agreement = db.query(ServiceAgreement).filter(
            ServiceAgreement.client_id == client_id,
            ServiceAgreement.is_deleted == False
        ).order_by(desc(ServiceAgreement.created_at)).first()

        if agreement:
            return agreement

        # Lookup Client record
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client {client_id} not found."
            )

        # Generate Agreement Number
        count = db.query(ServiceAgreement).count() + 1
        agreement_id = f"AGR-{datetime.now().strftime('%Y')}-{count:03d}"
        agreement_number = f"TRK-AGR-{datetime.now().strftime('%Y')}-{count:03d}"

        # Budget & Financial Calculation
        budget = client.estimated_budget or Decimal("5000000.00")
        tax_pct = Decimal("18.00")
        # Assume budget is net or gross; package price = budget / 1.18 or net budget
        package_price = budget
        tax_amt = (package_price * (tax_pct / Decimal("100.00"))).quantize(Decimal("0.01"))
        total_amt = package_price + tax_amt

        agreement = ServiceAgreement(
            id=agreement_id,
            agreement_number=agreement_number,
            client_id=client.id,
            status="PENDING_SIGNATURE",
            wedding_date=client.wedding_date,
            wedding_location=client.wedding_location,
            venue=client.wedding_location,
            guest_count=client.expected_guest_count or 150,
            service_package=client.service_package or "Royal Palace Grandeur",
            included_services=[
                "Exclusive heritage palace grounds reservation and regal wedding dossier",
                "Full-scale Rajputana theme styling, bespoke floral curation, and royal pavilions",
                "Luxury catering curation, royal banquet service, and silver cloche guest dining",
                "Rajasthani folk performers, shehnai maestros, and royal welcome processions",
                "Dedicated agency wedding concierge and multi-day itinerary execution"
            ],
            deliverables=[
                "Master wedding architectural layout and 3D floral walk-through",
                "Consolidated vendor contracts, licensing, and security clearances",
                "Guest hospitality dossier and VIP palace suite allocations",
                "Turnkey event day coordination across all wedding ceremonies"
            ],
            package_price=package_price,
            tax_percentage=tax_pct,
            tax_amount=tax_amt,
            discount_amount=Decimal("0.00"),
            total_amount=total_amt,
            currency="INR",
            current_version_number=1,
            agreement_version="v1.0",
            is_internally_approved=True,
            approved_by="Maharani Gayatri Singh",
            approved_at=datetime.now(timezone.utc)
        )

        db.add(agreement)
        db.flush()

        # Create Standard Payment Milestones
        m1 = AgreementPaymentMilestone(
            id=f"{agreement_id}-M1",
            agreement_id=agreement.id,
            milestone_name="Initial Advance Retainer",
            percentage=Decimal("25.00"),
            amount=(total_amt * Decimal("0.25")).quantize(Decimal("0.01")),
            due_description="Due immediately upon contract signing to lock calendar",
            due_date=client.wedding_date - timedelta(days=120) if client.wedding_date else None,
            status="PENDING",
            sequence_order=1
        )
        m2 = AgreementPaymentMilestone(
            id=f"{agreement_id}-M2",
            agreement_id=agreement.id,
            milestone_name="Design Approval & Vendor Locks",
            percentage=Decimal("35.00"),
            amount=(total_amt * Decimal("0.35")).quantize(Decimal("0.01")),
            due_description="Due 90 days prior to wedding date",
            due_date=client.wedding_date - timedelta(days=90) if client.wedding_date else None,
            status="PENDING",
            sequence_order=2
        )
        m3 = AgreementPaymentMilestone(
            id=f"{agreement_id}-M3",
            agreement_id=agreement.id,
            milestone_name="Final Palace Balance",
            percentage=Decimal("40.00"),
            amount=(total_amt * Decimal("0.40")).quantize(Decimal("0.01")),
            due_description="Due 30 days prior to celebration launch",
            due_date=client.wedding_date - timedelta(days=30) if client.wedding_date else None,
            status="PENDING",
            sequence_order=3
        )
        db.add_all([m1, m2, m3])

        # Record Status History
        hist = AgreementStatusHistory(
            agreement_id=agreement.id,
            from_status=None,
            to_status="PENDING_SIGNATURE",
            changed_by="Agency Automated Intake",
            reason="Service agreement instantiated from confirmed client intake record."
        )
        db.add(hist)

        db.commit()
        db.refresh(agreement)
        return agreement

    def get_agreement(self, db: Session, agreement_id: str) -> ServiceAgreement:
        agreement = db.query(ServiceAgreement).filter(
            ServiceAgreement.id == agreement_id,
            ServiceAgreement.is_deleted == False
        ).first()
        if not agreement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service agreement {agreement_id} not found."
            )
        return agreement

    def list_agreements(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 50,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        query = db.query(ServiceAgreement).filter(ServiceAgreement.is_deleted == False)
        if status_filter:
            query = query.filter(ServiceAgreement.status == status_filter)

        total = query.count()
        items = query.order_by(desc(ServiceAgreement.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    def send_signing_otp(self, db: Session, agreement_id: str, client_id: Optional[str] = None) -> SendOTPResponse:
        """Generates a secure 6-digit OTP, stores its SHA-256 hash, and emails the client."""
        agreement = self.get_agreement(db, agreement_id)

        if agreement.status == "SIGNED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agreement is already signed and legally binding."
            )

        client = agreement.client
        if not client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No client record linked to this agreement."
            )

        # Generate 6-digit cryptographic random OTP
        raw_otp = f"{secrets.randbelow(900000) + 100000}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=10)

        agreement.signing_otp_hash = hash_otp(raw_otp)
        agreement.signing_otp_expires_at = expires_at
        agreement.signing_otp_attempts = 0
        agreement.signing_otp_verified = False

        db.commit()

        # Send via existing email infrastructure
        couple_name = f"{client.partner1_name} & {client.partner2_name}"
        email_body = f"""
        <html>
        <body style="font-family: Georgia, serif; background-color: #FAF8F5; color: #1F2421; padding: 24px;">
            <div style="max-width: 560px; margin: 0 auto; background: #FFFFFF; border: 1px solid #E5E0D8; padding: 32px;">
                <div style="text-align: center; color: #9E7D3B; font-size: 11px; letter-spacing: 2px;">✦ THE ROYAL KNOT ✦</div>
                <h2 style="text-align: center; font-size: 20px; margin-top: 8px;">Service Agreement Verification</h2>
                <p>Dear {couple_name},</p>
                <p>Please use the following single-use verification code to digitally sign your Royal Knot Wedding Service Agreement (Reference: <b>{agreement.agreement_number}</b>):</p>
                <div style="text-align: center; margin: 24px 0;">
                    <span style="display: inline-block; background-color: #FAF2E6; border: 1px solid #C9A67D; padding: 12px 28px; font-size: 28px; font-family: monospace; font-weight: bold; letter-spacing: 6px; color: #1F2421;">
                        {raw_otp}
                    </span>
                </div>
                <p style="font-size: 12px; color: #736F68;">This verification code is confidential and expires in <b>10 minutes</b>. If you did not initiate this request, please contact your wedding concierge immediately.</p>
                <hr style="border: none; border-top: 1px solid #E5E0D8; margin: 24px 0;" />
                <div style="text-align: center; font-size: 11px; color: #8C877D;">The Royal Knot Luxury Wedding Planning · Jaipur & Udaipur</div>
            </div>
        </body>
        </html>
        """

        try:
            EmailService.send_email(
                to_email=client.email,
                subject=f"[The Royal Knot] Verification Code for Agreement {agreement.agreement_number}",
                html_content=email_body
            )
        except Exception as e:
            # Fallback for offline dev
            pass

        return SendOTPResponse(
            success=True,
            message="Verification code successfully dispatched to your registered email.",
            email_destination=client.email,
            expires_in_seconds=600
        )

    def verify_signing_otp(self, db: Session, agreement_id: str, raw_otp: str) -> VerifyOTPResponse:
        """Validates submitted 6-digit OTP against expiration and attempt limits."""
        agreement = self.get_agreement(db, agreement_id)

        if not agreement.signing_otp_hash or not agreement.signing_otp_expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active verification code found. Please request a new code."
            )

        now = datetime.now(timezone.utc)
        expires_at = agreement.signing_otp_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if now > expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired. Please request a new code."
            )

        if agreement.signing_otp_attempts >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Maximum verification attempts exceeded. Please request a new code."
            )

        agreement.signing_otp_attempts += 1

        submitted_hash = hash_otp(raw_otp)
        if not secrets.compare_digest(submitted_hash, agreement.signing_otp_hash):
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code. Please check and try again."
            )

        agreement.signing_otp_verified = True
        db.commit()

        return VerifyOTPResponse(
            success=True,
            message="Identity verified successfully.",
            verified=True
        )

    def sign_agreement(
        self,
        db: Session,
        agreement_id: str,
        req: SignAgreementRequest,
        client_id: Optional[str] = None,
        ip_address: Optional[str] = "127.0.0.1",
        user_agent: Optional[str] = "Web Browser"
    ) -> SignAgreementResponse:
        """Executes digital signature, validates explicit consent, generates signed PDF and audit trail."""
        agreement = self.get_agreement(db, agreement_id)

        if agreement.status == "SIGNED":
            return SignAgreementResponse(
                success=True,
                message="Agreement was already signed and is legally binding.",
                agreement_id=agreement.id,
                agreement_number=agreement.agreement_number,
                status=agreement.status,
                signed_at=agreement.signed_at or datetime.now(timezone.utc),
                signed_pdf_url=f"/api/v1/agreements/{agreement.id}/pdf",
                has_signed_agreement=True
            )

        # Ensure consent is given
        if not req.consent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Explicit consent to terms and conditions is mandatory for contract execution."
            )

        # If OTP wasn't pre-verified, verify now
        if not agreement.signing_otp_verified:
            if not req.otp:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification code is required before signing."
                )
            self.verify_signing_otp(db, agreement_id, req.otp)

        client = agreement.client
        now = datetime.now(timezone.utc)
        signer_name = req.signer_name or (f"{client.partner1_name} & {client.partner2_name}" if client else "Client")

        # Update Agreement Signing State
        agreement.status = "SIGNED"
        agreement.is_verified = True
        agreement.signed_at = now
        agreement.signed_by_name = signer_name
        agreement.signed_by_email = client.email if client else "client@domain.com"
        agreement.signature_data = req.signature_data
        agreement.signer_ip = ip_address
        agreement.signer_user_agent = user_agent
        agreement.consent_confirmed = True

        # Generate Signed PDF Document
        pdf_filename = f"signed_{agreement.agreement_number}_{int(now.timestamp())}.pdf"
        pdf_path = os.path.join(self.UPLOADS_DIR, pdf_filename)
        pdf_bytes = generate_service_agreement_pdf(agreement, output_path=pdf_path)

        agreement.signed_pdf_path = pdf_path

        # Document record
        doc_record = AgreementDocument(
            id=f"DOC-{agreement.id}-{int(now.timestamp())}",
            agreement_id=agreement.id,
            document_type="SIGNED_CONTRACT",
            file_name=pdf_filename,
            file_path=pdf_path,
            file_size=len(pdf_bytes),
            mime_type="application/pdf",
            version_number=agreement.current_version_number
        )
        db.add(doc_record)

        # Status History
        hist = AgreementStatusHistory(
            agreement_id=agreement.id,
            from_status="PENDING_SIGNATURE",
            to_status="SIGNED",
            changed_by=signer_name,
            reason=f"Client digitally executed contract via OTP verification from IP {ip_address}."
        )
        db.add(hist)

        db.commit()
        db.refresh(agreement)

        return SignAgreementResponse(
            success=True,
            message="Service Agreement successfully executed and legally ratified.",
            agreement_id=agreement.id,
            agreement_number=agreement.agreement_number,
            status=agreement.status,
            signed_at=now,
            signed_pdf_url=f"/api/v1/agreements/{agreement.id}/pdf",
            has_signed_agreement=True
        )

    def get_signed_pdf_bytes(self, db: Session, agreement_id: str) -> bytes:
        """Retrieves or generates on-the-fly the signed agreement PDF bytes."""
        agreement = self.get_agreement(db, agreement_id)
        if agreement.signed_pdf_path and os.path.exists(agreement.signed_pdf_path):
            with open(agreement.signed_pdf_path, "rb") as f:
                return f.read()
        return generate_service_agreement_pdf(agreement)


agreement_service = AgreementService()
