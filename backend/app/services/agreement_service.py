import secrets
import os
import uuid
import base64
import hashlib
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
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
from app.services.zoho_sign_service import zoho_sign_client
from app.services.leegality_service import leegality_client
from app.services.email_service import EmailService



import random
from app.services.agreement_pdf_service import generate_service_agreement_pdf
from app.schemas.agreement import (
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    SignAgreementRequest,
    SignAgreementResponse,
    AgreementMetricsResponse,
)


def hash_otp(raw_otp: str) -> str:
    return hashlib.sha256(raw_otp.strip().encode("utf-8")).hexdigest()

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
            created_by=getattr(req, "created_by", None) or "Maharani Gayatri Singh"
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

        # Select provider based on override or configuration (default: Zoho Sign)
        selected_provider = None
        if req_body and hasattr(req_body, "provider") and req_body.provider:
            selected_provider = req_body.provider.lower()
        elif isinstance(req_body, dict) and req_body.get("provider"):
            selected_provider = str(req_body["provider"]).lower()
        else:
            selected_provider = (settings.ESIGN_PROVIDER or "zoho_sign").lower()

        if selected_provider in ("zoho", "zoho_sign"):
            sign_res = zoho_sign_client.create_signing_request(
                document_bytes=pdf_bytes,
                document_filename=doc.original_filename,
                signer_name=signer_name,
                signer_email=signer_email,
                signer_phone=signer_phone
            )
            provider_name = "Zoho Sign"
            env_name = zoho_sign_client.env
            provider_req_id = sign_res.get("provider_request_id")
            provider_doc_id = sign_res.get("provider_document_id")
            provider_act_id = sign_res.get("provider_action_id")
            sign_url = sign_res.get("signing_url")
            raw_resp = sign_res.get("raw_response")
        else:
            # Fallback to Leegality
            pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
            leegality_res = leegality_client.create_signing_request(
                document_base64=pdf_base64,
                document_filename=doc.original_filename,
                signer_name=signer_name,
                signer_email=signer_email,
                signer_phone=signer_phone
            )
            provider_name = "Leegality"
            env_name = leegality_client.env if leegality_client.is_live_configured() else "mock"
            provider_req_id = (
                leegality_res.get("data", {}).get("documentId")
                or leegality_res.get("response", {}).get("documentId")
                or leegality_res.get("documentId")
            )
            provider_doc_id = provider_req_id
            provider_act_id = None
            invitations = (
                leegality_res.get("data", {}).get("invitations")
                or leegality_res.get("response", {}).get("invitations", [])
            )
            sign_url = invitations[0].get("signUrl") if invitations else None
            raw_resp = leegality_res

        # Record signature request
        sig_req = AgreementSignatureRequest(
            id=f"SIG-{uuid.uuid4().hex[:10].upper()}",
            agreement_id=agreement.id,
            version_number=agreement.current_version_number,
            provider=provider_name,
            environment=env_name,
            provider_request_id=provider_req_id,
            provider_document_id=provider_doc_id,
            provider_action_id=provider_act_id,
            leegality_document_id=provider_req_id,  # preserved for compatibility
            signer_name=signer_name,
            signer_email=signer_email,
            signer_phone=signer_phone,
            signing_url=sign_url,
            status="SENT",
            raw_response=raw_resp,
            sent_at=datetime.now(timezone.utc)
        )
        db.add(sig_req)

        agreement.signing_status = "SENT"
        cls._record_status_history(db, agreement, "SIGNING_PENDING", "System", f"Dispatched to {provider_name} for eSignature.")
        db.commit()

        is_real_sandbox = sig_req.environment in ("sandbox", "production")
        msg = (
            f"Service agreement successfully submitted to real {provider_name} {sig_req.environment.upper()} API! Invitation active."
            if is_real_sandbox
            else f"Service agreement signing request created in {provider_name} Simulation Mock mode."
        )

        return {
            "success": True,
            "message": msg,
            "agreement_id": agreement.id,
            "agreement_number": agreement.agreement_number,
            "version_number": agreement.current_version_number,
            "provider": sig_req.provider,
            "environment": sig_req.environment,
            "provider_request_id": provider_req_id,
            "provider_document_id": provider_doc_id,
            "leegality_document_id": provider_req_id,
            "signing_url": sign_url,
            "status": "SENT",
            "sent_at": sig_req.sent_at
        }

    @classmethod
    def process_zoho_webhook(
        cls,
        db: Session,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Receives and processes official Zoho Sign webhook callbacks.
        Handles: RequestCompleted, RequestSent, RequestViewed, RequestDeclined, RequestExpired.
        Verifies authenticity, enforces event idempotency, downloads signed PDF & audit certificate.
        """
        headers = headers or {}

        # Zoho Sign notifications may be inside 'notifications' object or top-level
        notifications = payload.get("notifications")
        if isinstance(notifications, str):
            try:
                import json
                notifications = json.loads(notifications)
            except Exception:
                notifications = {}
        notifications = notifications or {}

        req_id = (
            str(notifications.get("request_id") or "")
            or str(payload.get("request_id") or "")
            or str(payload.get("requests", {}).get("request_id") or "")
        )
        if not req_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing request_id in Zoho Sign webhook payload."
            )

        status_str = str(
            notifications.get("request_status")
            or payload.get("request_status")
            or payload.get("status")
            or notifications.get("operation_type")
            or "COMPLETED"
        ).upper()

        # Find matching signature request
        sig_req = db.query(AgreementSignatureRequest).filter(
            (AgreementSignatureRequest.provider_request_id == req_id) |
            (AgreementSignatureRequest.leegality_document_id == req_id)
        ).first()

        # Idempotency check: hash payload + request_id
        canon_payload = str(sorted(payload.items()))
        fingerprint = hashlib.sha256(f"zoho_{req_id}_{canon_payload}".encode("utf-8")).hexdigest()

        existing_event = db.query(AgreementWebhookEvent).filter(
            AgreementWebhookEvent.event_fingerprint == fingerprint
        ).first()
        if existing_event:
            return {"status": "ok", "message": "Duplicate Zoho Sign webhook notification safely ignored (Idempotent)."}

        # Webhook authenticity verification
        is_verified = zoho_sign_client.verify_webhook(payload, headers)

        event = AgreementWebhookEvent(
            id=f"EVT-{uuid.uuid4().hex[:10].upper()}",
            signature_request_id=sig_req.id if sig_req else None,
            document_id=req_id,
            provider_request_id=req_id,
            event_type=f"zoho_{status_str.lower()}",
            mac_received=headers.get("x-zoho-webhook-secret") or headers.get("token"),
            mac_verified=is_verified,
            event_fingerprint=fingerprint,
            raw_payload=payload,
            is_processed=True,
            processing_notes=f"Zoho Sign webhook processed with status: {status_str}"
        )
        db.add(event)

        is_completed = status_str in ("COMPLETED", "SIGNED", "REQUESTCOMPLETED", "REQUESTSIGNINGSUCCESS")
        is_declined = status_str in ("DECLINED", "REJECTED", "REQUESTREJECTED")
        is_expired = status_str in ("EXPIRED", "REQUESTEXPIRED")

        if sig_req and is_completed:
            agreement = sig_req.agreement
            sig_req.status = "SIGNED"
            sig_req.completed_at = datetime.now(timezone.utc)
            agreement.signing_status = "COMPLETED"

            # Retrieve and persist executed PDF from Zoho Sign
            try:
                signed_bytes = zoho_sign_client.retrieve_signed_document(req_id)
                signed_filename = f"{agreement.agreement_number}_v{sig_req.version_number}_ZOHO_SIGNED.pdf"
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
                    source="Zoho Sign Webhook"
                )
                db.add(doc_record)
            except Exception as e:
                event.processing_notes = f"Executed document download deferred: {e}"

            # Also retrieve completion certificate / audit trail
            try:
                cert_bytes = zoho_sign_client.retrieve_audit_trail(req_id)
                if cert_bytes:
                    cert_filename = f"{agreement.agreement_number}_v{sig_req.version_number}_ZOHO_AUDIT_TRAIL.pdf"
                    cert_path = os.path.join(settings.UPLOAD_DIR, "agreements", cert_filename)
                    with open(cert_path, "wb") as f:
                        f.write(cert_bytes)

                    cert_doc = AgreementDocument(
                        id=f"DOC-{uuid.uuid4().hex[:10].upper()}",
                        agreement_id=agreement.id,
                        version_number=sig_req.version_number,
                        document_type="signature_audit_trail",
                        original_filename=cert_filename,
                        stored_filename=cert_filename,
                        file_path=cert_path,
                        file_size=len(cert_bytes),
                        file_hash_sha256=hashlib.sha256(cert_bytes).hexdigest(),
                        mime_type="application/pdf",
                        source="Zoho Sign Audit Trail"
                    )
                    db.add(cert_doc)
            except Exception as e:
                logger.warning(f"Completion certificate retrieval deferred: {e}")

            cls._record_status_history(
                db, agreement, "UNDER_VERIFICATION", "Zoho Sign Webhook",
                "Client electronic signature completed via Zoho Sign."
            )

        elif sig_req and (is_declined or is_expired):
            agreement = sig_req.agreement
            fail_state = "DECLINED" if is_declined else "EXPIRED"
            sig_req.status = fail_state
            agreement.signing_status = fail_state
            cls._record_status_history(
                db, agreement, "NEEDS_CORRECTION", "Zoho Sign Webhook",
                f"Signature {fail_state.lower()} by client."
            )

        db.commit()
        return {"status": "success", "processed": True, "request_id": req_id, "signing_status": status_str}

    @classmethod
    def process_leegality_webhook(cls, db: Session, payload: Dict[str, Any], is_success: bool) -> Dict[str, Any]:
        doc_id = (
            payload.get("data", {}).get("documentId")
            or payload.get("documentId")
            or payload.get("document_id")
            or payload.get("response", {}).get("documentId")
        )
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

        elif sig_req and not is_success:
            agreement = sig_req.agreement
            fail_reason = payload.get("reason") or payload.get("message") or "Signing rejected, expired, or failed"
            sig_req.status = "FAILED"
            agreement.signing_status = "FAILED"
            cls._record_status_history(db, agreement, "NEEDS_CORRECTION", "Leegality Webhook", f"eSignature failed: {fail_reason}")

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


    # --- IN-APP CLIENT OTP & PORTAL SIGNING METHODS ---
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
        ref_wedding_date = client.wedding_date or (datetime.now().date() + timedelta(days=180))
        m1 = AgreementPaymentMilestone(
            id=f"{agreement_id}-M1",
            agreement_id=agreement.id,
            name="Initial Advance Retainer",
            milestone_name="Initial Advance Retainer",
            percentage=Decimal("25.00"),
            amount=(total_amt * Decimal("0.25")).quantize(Decimal("0.01")),
            description="Due immediately upon contract signing to lock calendar",
            due_description="Due immediately upon contract signing to lock calendar",
            due_date=ref_wedding_date - timedelta(days=120),
            status="PENDING",
            sequence_order=1
        )
        m2 = AgreementPaymentMilestone(
            id=f"{agreement_id}-M2",
            agreement_id=agreement.id,
            name="Design Approval & Vendor Locks",
            milestone_name="Design Approval & Vendor Locks",
            percentage=Decimal("35.00"),
            amount=(total_amt * Decimal("0.35")).quantize(Decimal("0.01")),
            description="Due 90 days prior to wedding date",
            due_description="Due 90 days prior to wedding date",
            due_date=ref_wedding_date - timedelta(days=90),
            status="PENDING",
            sequence_order=2
        )
        m3 = AgreementPaymentMilestone(
            id=f"{agreement_id}-M3",
            agreement_id=agreement.id,
            name="Final Palace Balance",
            milestone_name="Final Palace Balance",
            percentage=Decimal("40.00"),
            amount=(total_amt * Decimal("0.40")).quantize(Decimal("0.01")),
            description="Due 30 days prior to celebration launch",
            due_description="Due 30 days prior to celebration launch",
            due_date=ref_wedding_date - timedelta(days=30),
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

        if not EmailService.is_smtp_configured():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Email verification is temporarily unavailable. SMTP delivery is not configured; please contact the administrator.")

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
            email_result = EmailService.send_email(
                to_email=client.email,
                subject=f"[The Royal Knot] Verification Code for Agreement {agreement.agreement_number}",
                html_content=email_body
            )
            if not email_result.get("success") or email_result.get("mode") != "live_smtp":
                raise RuntimeError("SMTP delivery was not confirmed")
        except Exception as e:
            import logging
            logging.getLogger("royal_knot.otp").error("OTP email dispatch failed: %s", type(e).__name__)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not send verification email. Please try again later or contact the administrator.") from e

        # Never log, print, or return the verification code.
        dev_otp_val = None

        return SendOTPResponse(
            success=True,
            message="Verification code successfully dispatched to your registered email.",
            email_destination=client.email,
            expires_in_seconds=600,
            dev_otp=dev_otp_val
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
            document_type="signed_agreement_pdf",
            original_filename=pdf_filename,
            stored_filename=pdf_filename,
            file_path=pdf_path,
            file_size=len(pdf_bytes),
            file_hash_sha256=hashlib.sha256(pdf_bytes).hexdigest(),
            mime_type="application/pdf",
            version_number=agreement.current_version_number or 1
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

