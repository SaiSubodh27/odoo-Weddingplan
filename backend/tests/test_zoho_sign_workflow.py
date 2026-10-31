import sys
import uuid
import os
from pathlib import Path
from decimal import Decimal
from datetime import date, datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.base import Base
from app.models.client import Client
from app.models.agreement import (
    ServiceAgreement,
    ServiceAgreementVersion,
    AgreementPaymentMilestone,
    AgreementDocument,
    AgreementSignatureRequest,
    AgreementWebhookEvent,
    WeddingBooking,
)
from app.services.agreement_service import agreement_service
from app.services.zoho_sign_service import zoho_sign_client, ZohoSignClient
from app.schemas.agreement import (
    ServiceAgreementCreate,
    PaymentMilestoneInput,
    AgreementApproveRequest,
    AgreementReviewRequest,
    BookingConfirmRequest,
)
from app.core.config import settings

# Isolated in-memory SQLite database
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    # Seed client
    client = Client(
        id="CLT-ZOHO-001",
        partner1_name="Siddharth Rao",
        partner2_name="Ananya Sen",
        email="siddharth.ananya@heritage-knot.in",
        phone="+91 98300 77889",
        wedding_date=date(2027, 3, 20),
        wedding_location="Jaipur, Rajasthan",
        expected_guest_count=300,
        estimated_budget=Decimal("4500000.00"),
        service_package="Imperial Heritage Royalty",
        status="Registered"
    )
    session.add(client)
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_01_create_agreement_and_approve(db_session):
    """Create a draft agreement, generate PDF, and internally approve it."""
    milestones = [
        PaymentMilestoneInput(
            name="1. Advance Retainer (30%)",
            percentage=Decimal("30.00"),
            amount=Decimal("1416000.00"),
            due_date=date(2026, 12, 1)
        ),
        PaymentMilestoneInput(
            name="2. Production Stage (40%)",
            percentage=Decimal("40.00"),
            amount=Decimal("1888000.00"),
            due_date=date(2027, 1, 15)
        ),
        PaymentMilestoneInput(
            name="3. Final Settlement (30%)",
            percentage=Decimal("30.00"),
            amount=Decimal("1416000.00"),
            due_date=date(2027, 3, 1)
        ),
    ]

    req = ServiceAgreementCreate(
        client_id="CLT-ZOHO-001",
        wedding_date=date(2027, 3, 20),
        wedding_location="Jaipur, Rajasthan",
        venue="Rambagh Palace",
        guest_count=300,
        service_package="Imperial Heritage Royalty",
        package_price=Decimal("4000000.00"),
        tax_percentage=Decimal("18.00"),
        discount_amount=Decimal("0.00"),
        milestones=milestones,
        created_by="Maharani Gayatri Singh"
    )

    agreement = agreement_service.create_agreement(db=db_session, req=req)
    assert agreement.id.startswith("SA-")
    assert agreement.total_amount == Decimal("4720000.00")
    assert agreement.status == "DRAFT"

    # Generate PDF
    doc = agreement_service.generate_agreement_pdf(db=db_session, agreement_id=agreement.id)
    assert doc.id.startswith("DOC-")
    assert doc.document_type == "generated_unsigned_pdf"
    assert os.path.exists(doc.file_path)

    # Approve agreement
    appr_req = AgreementApproveRequest(
        approved_by="Maharani Gayatri Singh",
        notes="All commercial lines and schedules validated."
    )
    approved = agreement_service.approve_agreement(db=db_session, agreement_id=agreement.id, req=appr_req)
    assert approved.is_internally_approved is True
    assert approved.status == "APPROVED_TO_SEND"


def test_02_zoho_sign_sandbox_without_credentials_raises_error():
    """Verify that setting ZOHO_SIGN_ENV=sandbox without credentials explicitly raises a configuration error."""
    custom_client = ZohoSignClient()
    custom_client.env = "sandbox"
    custom_client.client_id = ""
    custom_client.client_secret = ""
    custom_client.refresh_token = ""

    with pytest.raises(RuntimeError) as excinfo:
        custom_client.create_signing_request(
            document_bytes=b"%PDF-1.4 dummy",
            document_filename="dummy.pdf",
            signer_name="Test Signer",
            signer_email="test@example.com"
        )
    assert "Zoho Sign SANDBOX mode is enabled, but OAuth credentials are not configured" in str(excinfo.value)


def test_03_dispatch_to_zoho_sign_mock(db_session):
    """Test dispatching approved agreement to Zoho Sign in mock mode."""
    agreement = db_session.query(ServiceAgreement).first()
    res = agreement_service.send_for_signature(db=db_session, agreement_id=agreement.id)

    assert res["success"] is True
    assert res["provider"] == "Zoho Sign"
    assert res["environment"] == "mock"
    assert res["status"] == "SENT"
    assert res["provider_request_id"].startswith("zs_mock_")
    assert res["provider_document_id"].startswith("zs_doc_")
    assert "https://sign.zoho.in/signpage?embedtoken=" in res["signing_url"]

    # Verify database state
    db_session.refresh(agreement)
    assert agreement.status == "SIGNING_PENDING"
    assert agreement.signing_status == "SENT"

    sig_req = db_session.query(AgreementSignatureRequest).filter(
        AgreementSignatureRequest.agreement_id == agreement.id
    ).first()
    assert sig_req is not None
    assert sig_req.provider == "Zoho Sign"
    assert sig_req.provider_request_id == res["provider_request_id"]
    assert sig_req.provider_document_id == res["provider_document_id"]
    assert sig_req.provider_action_id is not None


def test_04_zoho_sign_webhook_completion(db_session):
    """Test official Zoho Sign RequestCompleted webhook processing."""
    sig_req = db_session.query(AgreementSignatureRequest).first()
    agreement = db_session.query(ServiceAgreement).first()

    webhook_payload = {
        "notifications": {
            "request_id": sig_req.provider_request_id,
            "document_id": sig_req.provider_document_id,
            "request_status": "COMPLETED",
            "operation_type": "RequestCompleted",
            "action_id": sig_req.provider_action_id,
            "recipient_name": sig_req.signer_name,
            "recipient_email": sig_req.signer_email,
            "performed_at": "2026-10-31T20:15:00Z"
        }
    }

    res = agreement_service.process_zoho_webhook(db=db_session, payload=webhook_payload)
    assert res["status"] == "success"
    assert res["processed"] is True

    # Verify agreement updated to UNDER_VERIFICATION and signing_status to COMPLETED
    db_session.refresh(agreement)
    assert agreement.signing_status == "COMPLETED"
    assert agreement.status == "UNDER_VERIFICATION"

    # Check executed signed PDF and audit certificate documents were registered
    docs = db_session.query(AgreementDocument).filter(
        AgreementDocument.agreement_id == agreement.id
    ).all()
    doc_types = [d.document_type for d in docs]
    assert "signed_agreement_pdf" in doc_types
    assert "signature_audit_trail" in doc_types

    # Verify executed PDF file exists on disk
    executed_doc = next(d for d in docs if d.document_type == "signed_agreement_pdf")
    assert os.path.exists(executed_doc.file_path)
    assert executed_doc.file_size > 0


def test_05_zoho_sign_webhook_idempotency(db_session):
    """Verify that duplicate Zoho Sign webhook submissions are processed idempotently without error."""
    sig_req = db_session.query(AgreementSignatureRequest).first()

    webhook_payload = {
        "notifications": {
            "request_id": sig_req.provider_request_id,
            "document_id": sig_req.provider_document_id,
            "request_status": "COMPLETED",
            "operation_type": "RequestCompleted",
            "action_id": sig_req.provider_action_id,
            "recipient_name": sig_req.signer_name,
            "recipient_email": sig_req.signer_email,
            "performed_at": "2026-10-31T20:15:00Z"
        }
    }

    res = agreement_service.process_zoho_webhook(db=db_session, payload=webhook_payload)
    assert res["status"] == "ok"
    assert "Duplicate" in res["message"]


def test_06_employee_verification_and_booking_confirmation(db_session):
    """Verify executed contract and confirm wedding booking."""
    agreement = db_session.query(ServiceAgreement).first()

    # Employee verification
    rev_req = AgreementReviewRequest(
        reviewer_name="Maharani Gayatri Singh",
        decision="VERIFIED",
        remarks="Zoho Sign digital completion certificate verified against SHA-256 hash."
    )
    verified = agreement_service.review_agreement(db=db_session, agreement_id=agreement.id, req=rev_req)
    assert verified.is_verified is True
    assert verified.status == "VERIFIED"

    # Wedding booking confirmation
    bk_req = BookingConfirmRequest(
        confirmed_by="Maharani Gayatri Singh",
        confirmation_notes="Dates blocked at Rambagh Palace. Handoff to Phase 3 operations."
    )
    booking = agreement_service.confirm_booking(db=db_session, agreement_id=agreement.id, req=bk_req)
    assert booking.id.startswith("BK-")
    assert booking.booking_reference.startswith("TRK-BK-")
    assert booking.status == "CONFIRMED"
    assert booking.phase3_handoff_ready is True

    db_session.refresh(agreement)
    assert agreement.status == "BOOKING_CONFIRMED"
