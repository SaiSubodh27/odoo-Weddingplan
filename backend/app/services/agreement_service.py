import os
import uuid
import base64
import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.client import Client
from app.models.agreement import (
    ServiceAgreement,
    ServiceAgreementVersion,
    AgreementPaymentMilestone,
    AgreementDocument,
    AgreementSignatureRequest,
    AgreementWebhookEvent,
    AgreementStatusHistory,
    AgreementReview,
    WeddingBooking,
)
from app.schemas.agreement import (
    ServiceAgreementCreate,
    ServiceAgreementUpdate,
    AgreementApproveRequest,
    AgreementReviewRequest,
    BookingConfirmRequest,
)
from app.services.pdf_service import pdf_service
from app.services.leegality_service import leegality_client


class AgreementService:

    @staticmethod
    def _generate_agreement_number(db: Session) -> str:
        count = db.query(ServiceAgreement).count() + 1
        year = datetime.now().year
        return f"RK-SA-{year}-{count:03d}"

    @staticmethod
    def _record_status_history(
        db: Session,
        agreement: ServiceAgreement,
        to_status: str,
        changed_by: str,
        reason: Optional[str] = None
    ):
        from_status = agreement.status
        if from_status != to_status:
            history = AgreementStatusHistory(
                agreement_id=agreement.id,
                from_status=from_status,
                to_status=to_status,
                changed_by=changed_by,
                reason=reason
            )
            db.add(history)
            agreement.status = to_status

    @classmethod
    def create_agreement(cls, db: Session, req: ServiceAgreementCreate) -> ServiceAgreement:
        # Validate client exists and is registered
        client = db.query(Client).filter(Client.id == req.client_id, Client.is_deleted == False).first()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Registered client '{req.client_id}' does not exist."
            )

        # Financial calculation
        pkg_price = req.package_price
        tax_pct = req.tax_percentage
        disc_amt = req.discount_amount
        tax_amt = (pkg_price * (tax_pct / Decimal("100.00"))).quantize(Decimal("0.01"))
        total_amt = (pkg_price + tax_amt - disc_amt).quantize(Decimal("0.01"))

        # Reconcile milestones with total
        milestone_sum = sum(m.amount for m in req.milestones)
        if abs(milestone_sum - total_amt) > Decimal("1.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Milestone payment total (₹{milestone_sum}) must reconcile with agreement total (₹{total_amt})."
            )

        agreement_id = f"SA-{uuid.uuid4().hex[:10].upper()}"
        agreement_no = cls._generate_agreement_number(db)

        agreement = ServiceAgreement(
            id=agreement_id,
            agreement_number=agreement_no,
            client_id=client.id,
            status="DRAFT",
            signing_status="NOT_CREATED",
            wedding_date=req.wedding_date,
            wedding_location=req.wedding_location,
            venue=req.venue,
            guest_count=req.guest_count,
            wedding_functions=[f.model_dump() for f in req.wedding_functions] if req.wedding_functions else [],
            service_package=req.service_package,
            included_services=req.included_services or [],
            excluded_services=req.excluded_services or [],
            deliverables=req.deliverables or [],
            additional_terms=req.additional_terms,
            package_price=pkg_price,
            tax_percentage=tax_pct,
            tax_amount=tax_amt,
            discount_amount=disc_amt,
            total_amount=total_amt,
            currency="INR",
            current_version_number=1,
            created_by=req.created_by or "Maharani Gayatri Singh"
        )
        db.add(agreement)
        db.flush()

        # Add milestones
        for idx, m in enumerate(req.milestones, start=1):
            ms = AgreementPaymentMilestone(
                id=f"MS-{uuid.uuid4().hex[:8].upper()}",
                agreement_id=agreement.id,
                version_number=1,
                sequence_order=idx,
                name=m.name,
                percentage=m.percentage,
                amount=m.amount,
                due_date=m.due_date,
                description=m.description
            )
            db.add(ms)

        # Snapshot for Version 1
        snapshot = {
            "agreement_number": agreement_no,
            "client_id": client.id,
            "wedding_date": str(req.wedding_date),
            "wedding_location": req.wedding_location,
            "venue": req.venue,
            "guest_count": req.guest_count,
            "package_price": str(pkg_price),
            "tax_amount": str(tax_amt),
            "discount_amount": str(disc_amt),
            "total_amount": str(total_amt),
            "milestones": [m.model_dump(mode="json") for m in req.milestones]
        }
        version = ServiceAgreementVersion(
            id=f"SAV-{uuid.uuid4().hex[:10].upper()}",
            agreement_id=agreement.id,
            version_number=1,
            snapshot_data=snapshot,
            status="DRAFT",
            created_by=agreement.created_by
        )
        db.add(version)

        cls._record_status_history(db, agreement, "DRAFT", agreement.created_by, "Initial draft prepared.")
        db.commit()
        db.refresh(agreement)
        return agreement

    @classmethod
    def generate_agreement_pdf(cls, db: Session, agreement_id: str) -> AgreementDocument:
        agreement = db.query(ServiceAgreement).filter(ServiceAgreement.id == agreement_id).first()
        if not agreement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service agreement not found.")

        client = agreement.client
        client_data = {
            "id": client.id,
            "partner1_name": client.partner1_name,
            "partner2_name": client.partner2_name,
            "email": client.email,
            "phone": client.phone,
            "wedding_date": str(agreement.wedding_date),
            "wedding_location": agreement.wedding_location,
            "wedding_theme": client.wedding_theme or "Bespoke Royal Heritage"
        }

        agreement_data = {
            "agreement_number": agreement.agreement_number,
            "wedding_date": str(agreement.wedding_date),
            "wedding_location": agreement.wedding_location,
            "venue": agreement.venue,
            "guest_count": agreement.guest_count,
            "service_package": agreement.service_package,
            "wedding_functions": agreement.wedding_functions or [],
            "included_services": agreement.included_services or [],
            "excluded_services": agreement.excluded_services or [],
            "package_price": agreement.package_price,
            "tax_percentage": agreement.tax_percentage,
            "tax_amount": agreement.tax_amount,
            "discount_amount": agreement.discount_amount,
            "total_amount": agreement.total_amount,
            "milestones": [
                {
                    "name": ms.name,
                    "percentage": ms.percentage,
                    "amount": ms.amount,
                    "due_date": str(ms.due_date)
                }
                for ms in agreement.milestones
            ]
        }

        filename = f"{agreement.agreement_number}_v{agreement.current_version_number}.pdf"
        output_path = os.path.join(settings.UPLOAD_DIR, "agreements", filename)

        pdf_meta = pdf_service.generate_service_agreement_pdf(
            agreement_data=agreement_data,
            client_data=client_data,
            version_number=agreement.current_version_number,
            output_filepath=output_path
        )

        # Record AgreementDocument
        doc = AgreementDocument(
            id=f"DOC-{uuid.uuid4().hex[:10].upper()}",
            agreement_id=agreement.id,
            version_number=agreement.current_version_number,
            document_type="generated_unsigned_pdf",
            original_filename=filename,
            stored_filename=filename,
            file_path=output_path,
            file_size=pdf_meta["file_size"],
            file_hash_sha256=pdf_meta["file_hash_sha256"],
            mime_type="application/pdf",
            source="System"
        )
        db.add(doc)

        # Update version reference
        ver = db.query(ServiceAgreementVersion).filter(
            ServiceAgreementVersion.agreement_id == agreement.id,
            ServiceAgreementVersion.version_number == agreement.current_version_number
        ).first()
        if ver:
            ver.pdf_document_id = doc.id
            ver.pdf_hash_sha256 = doc.file_hash_sha256
            ver.pdf_file_path = output_path

        db.commit()
        db.refresh(doc)
        return doc

    @classmethod
    def approve_agreement(cls, db: Session, agreement_id: str, req: AgreementApproveRequest) -> ServiceAgreement:
        agreement = db.query(ServiceAgreement).filter(ServiceAgreement.id == agreement_id).first()
        if not agreement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service agreement not found.")

        # Ensure PDF exists before approval
        latest_doc = db.query(AgreementDocument).filter(
            AgreementDocument.agreement_id == agreement.id,
            AgreementDocument.version_number == agreement.current_version_number,
            AgreementDocument.document_type == "generated_unsigned_pdf"
        ).first()
        if not latest_doc:
            # Auto-generate PDF if not yet generated
            cls.generate_agreement_pdf(db, agreement.id)

        agreement.is_internally_approved = True
        agreement.approved_by = req.approved_by
        agreement.approved_at = datetime.now(timezone.utc)
        cls._record_status_history(db, agreement, "APPROVED_TO_SEND", req.approved_by, req.notes or "Internal approval granted.")

        db.commit()
        db.refresh(agreement)
        return agreement

    @classmethod
    def send_for_signature(cls, db: Session, agreement_id: str, req_body: Optional[Any] = None) -> Dict[str, Any]:
        agreement = db.query(ServiceAgreement).filter(ServiceAgreement.id == agreement_id).first()
        if not agreement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service agreement not found.")

        if not agreement.is_internally_approved or agreement.status not in ("APPROVED_TO_SEND", "SIGNING_PENDING"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agreement must be approved internally before sending for electronic signature."
            )

        client = agreement.client
        signer_name = f"{client.partner1_name} & {client.partner2_name}"
        signer_email = client.email
        signer_phone = client.phone

        # Find version PDF
        doc = db.query(AgreementDocument).filter(
            AgreementDocument.agreement_id == agreement.id,
            AgreementDocument.version_number == agreement.current_version_number,
            AgreementDocument.document_type == "generated_unsigned_pdf"
        ).order_by(AgreementDocument.created_at.desc()).first()

        if not doc or not os.path.exists(doc.file_path):
            doc = cls.generate_agreement_pdf(db, agreement.id)

        with open(doc.file_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        # Submit request to Leegality
        leegality_res = leegality_client.create_signing_request(
            document_base64=pdf_base64,
            document_filename=doc.original_filename,
            signer_name=signer_name,
            signer_email=signer_email,
            signer_phone=signer_phone
        )

        doc_id = leegality_res.get("response", {}).get("documentId")
        invitations = leegality_res.get("response", {}).get("invitations", [])
        sign_url = invitations[0].get("signUrl") if invitations else None

        # Record signature request
        sig_req = AgreementSignatureRequest(
            id=f"SIG-{uuid.uuid4().hex[:10].upper()}",
            agreement_id=agreement.id,
            version_number=agreement.current_version_number,
            leegality_document_id=doc_id,
            leegality_request_id=leegality_res.get("response", {}).get("irn"),
            provider="Leegality",
            environment=leegality_client.env,
            signer_name=signer_name,
            signer_email=signer_email,
            signer_phone=signer_phone,
            signing_url=sign_url,
            status="SENT",
            raw_response=leegality_res,
            sent_at=datetime.now(timezone.utc)
        )
        db.add(sig_req)

        agreement.signing_status = "SENT"
        cls._record_status_history(db, agreement, "SIGNING_PENDING", "System", "Dispatched to Leegality for eSignature.")
        db.commit()

        return {
            "success": True,
            "message": "Service agreement successfully submitted to Leegality for client eSignature.",
            "agreement_id": agreement.id,
            "agreement_number": agreement.agreement_number,
            "version_number": agreement.current_version_number,
            "leegality_document_id": doc_id,
            "signing_url": sign_url,
            "status": "SENT",
            "sent_at": sig_req.sent_at
        }

    @classmethod
    def process_leegality_webhook(cls, db: Session, payload: Dict[str, Any], is_success: bool) -> Dict[str, Any]:
        doc_id = payload.get("documentId") or payload.get("document_id") or payload.get("response", {}).get("documentId")
        if not doc_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing documentId in webhook payload.")

        # Find matching signature request
        sig_req = db.query(AgreementSignatureRequest).filter(
            AgreementSignatureRequest.leegality_document_id == doc_id
        ).first()

        # Idempotency check: hash payload
        canon_payload = str(sorted(payload.items()))
        fingerprint = hashlib.sha256(f"{doc_id}_{canon_payload}".encode("utf-8")).hexdigest()

        existing_event = db.query(AgreementWebhookEvent).filter(
            AgreementWebhookEvent.event_fingerprint == fingerprint
        ).first()
        if existing_event:
            return {"status": "ok", "message": "Duplicate webhook notification safely ignored (Idempotent)."}

        # MAC verification
        received_mac = payload.get("mac") or payload.get("MAC") or ""
        mac_valid = leegality_client.verify_webhook_mac(doc_id, received_mac)

        event = AgreementWebhookEvent(
            id=f"EVT-{uuid.uuid4().hex[:10].upper()}",
            signature_request_id=sig_req.id if sig_req else None,
            document_id=doc_id,
            event_type="success" if is_success else "failure",
            mac_received=received_mac,
            mac_verified=mac_valid,
            event_fingerprint=fingerprint,
            raw_payload=payload,
            is_processed=True,
            processing_notes="Webhook verified and processed."
        )
        db.add(event)

        if sig_req and is_success:
            agreement = sig_req.agreement
            sig_req.status = "SIGNED"
            sig_req.completed_at = datetime.now(timezone.utc)
            agreement.signing_status = "COMPLETED"

            # Retrieve and persist executed PDF
            try:
                signed_bytes = leegality_client.retrieve_signed_document(doc_id)
                signed_filename = f"{agreement.agreement_number}_v{sig_req.version_number}_EXECUTED.pdf"
                signed_path = os.path.join(settings.UPLOAD_DIR, "agreements", signed_filename)
                with open(signed_path, "wb") as f:
                    f.write(signed_bytes)

                doc_record = AgreementDocument(
                    id=f"DOC-{uuid.uuid4().hex[:10].upper()}",
                    agreement_id=agreement.id,
                    version_number=sig_req.version_number,
                    document_type="signed_agreement_pdf",
                    original_filename=signed_filename,
                    stored_filename=signed_filename,
                    file_path=signed_path,
                    file_size=len(signed_bytes),
                    file_hash_sha256=hashlib.sha256(signed_bytes).hexdigest(),
                    mime_type="application/pdf",
                    source="Leegality Webhook"
                )
                db.add(doc_record)
            except Exception as e:
                event.processing_notes = f"Executed document download deferred: {e}"

            cls._record_status_history(db, agreement, "UNDER_VERIFICATION", "Leegality Webhook", "Client electronic signature completed.")

        db.commit()
        return {"status": "ok", "processed": True}

    @classmethod
    def review_agreement(cls, db: Session, agreement_id: str, req: AgreementReviewRequest) -> ServiceAgreement:
        agreement = db.query(ServiceAgreement).filter(ServiceAgreement.id == agreement_id).first()
        if not agreement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service agreement not found.")

        review = AgreementReview(
            id=f"REV-{uuid.uuid4().hex[:8].upper()}",
            agreement_id=agreement.id,
            version_number=agreement.current_version_number,
            reviewer_name=req.reviewer_name,
            decision=req.decision,
            remarks=req.remarks
        )
        db.add(review)

        if req.decision == "VERIFIED":
            agreement.is_verified = True
            agreement.verified_by = req.reviewer_name
            agreement.verified_at = datetime.now(timezone.utc)
            agreement.verification_notes = req.remarks
            cls._record_status_history(db, agreement, "VERIFIED", req.reviewer_name, req.remarks)
        elif req.decision == "REJECTED":
            agreement.is_verified = False
            cls._record_status_history(db, agreement, "REJECTED", req.reviewer_name, req.remarks)
        elif req.decision == "NEEDS_CORRECTION":
            cls._record_status_history(db, agreement, "NEEDS_CORRECTION", req.reviewer_name, req.remarks)

        db.commit()
        db.refresh(agreement)
        return agreement

    @classmethod
    def confirm_booking(cls, db: Session, agreement_id: str, req: BookingConfirmRequest) -> WeddingBooking:
        agreement = db.query(ServiceAgreement).filter(ServiceAgreement.id == agreement_id).first()
        if not agreement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service agreement not found.")

        # Guard Conditions for Booking Confirmation
        if not agreement.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking cannot be confirmed until the agreement is employee-verified."
            )

        if agreement.signing_status != "COMPLETED" and agreement.status not in ("VERIFIED", "BOOKING_CONFIRMED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agreement must be signed via Leegality and verified before confirming booking."
            )

        # Prevent duplicate confirmation
        existing_booking = db.query(WeddingBooking).filter(
            WeddingBooking.agreement_id == agreement.id
        ).first()
        if existing_booking:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Wedding booking already confirmed under reference: {existing_booking.booking_reference}"
            )

        client = agreement.client
        advance_ms = next((m for m in agreement.milestones if "advance" in m.name.lower() or m.sequence_order == 1), None)
        advance_amt = advance_ms.amount if advance_ms else (agreement.total_amount * Decimal("0.25")).quantize(Decimal("0.01"))

        year = datetime.now().year
        booking_count = db.query(WeddingBooking).count() + 1
        booking_ref = f"TRK-BK-{year}-{booking_count:03d}"

        booking = WeddingBooking(
            id=f"BK-{uuid.uuid4().hex[:10].upper()}",
            booking_reference=booking_ref,
            client_id=client.id,
            agreement_id=agreement.id,
            confirmed_version_number=agreement.current_version_number,
            couple_title=f"{client.partner1_name} & {client.partner2_name}",
            wedding_date=agreement.wedding_date,
            wedding_location=agreement.wedding_location,
            venue=agreement.venue or "Palace Estate",
            package_name=agreement.service_package,
            confirmed_total_amount=agreement.total_amount,
            advance_amount_agreed=advance_amt,
            confirmed_by=req.confirmed_by,
            confirmation_notes=req.confirmation_notes,
            status="CONFIRMED",
            phase3_handoff_ready=True,
            phase3_handoff_at=datetime.now(timezone.utc)
        )
        db.add(booking)

        cls._record_status_history(db, agreement, "BOOKING_CONFIRMED", req.confirmed_by, "Wedding booking confirmed and handed off to Phase 3.")
        db.commit()
        db.refresh(booking)
        return booking


agreement_service = AgreementService()

