import sys
import uuid
import os
from pathlib import Path
from decimal import Decimal
from datetime import date, datetime

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

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
from app.services.leegality_service import leegality_client
from app.schemas.agreement import (
    ServiceAgreementCreate,
    PaymentMilestoneInput,
    AgreementApproveRequest,
    AgreementReviewRequest,
    BookingConfirmRequest,
)

# In-memory SQLite test engine for isolated unit testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Seed a registered client
    test_client = Client(
        id="CLT-TEST-001",
        partner1_name="Yuvraj Singh",
        partner2_name="Devika Rathore",
        email="yuvraj.devika@testheritage.in",
        phone="+91 98200 44556",
        wedding_date=date(2027, 2, 14),
        wedding_location="Udaipur, Rajasthan",
        expected_guest_count=250,
        estimated_budget=Decimal("3500000.00"),
        service_package="Royal Palace Grandeur",
        status="Registered"
    )
    session.add(test_client)
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_01_create_agreement_with_decimal_reconciliation(db_session):
    """Test agreement draft creation and decimal calculation validation."""
    pkg_price = Decimal("3000000.00")
    tax_pct = Decimal("18.00")
    tax_amt = Decimal("540000.00")
    disc = Decimal("100000.00")
    total_expected = Decimal("3440000.00")

    milestones = [
        PaymentMilestoneInput(
            name="1. Advance Retainer (25%)",
            percentage=Decimal("25.00"),
            amount=Decimal("860000.00"),
            due_date=date(2026, 11, 15)
        ),
        PaymentMilestoneInput(
            name="2. Production Advance (50%)",
            percentage=Decimal("50.00"),
            amount=Decimal("1720000.00"),
            due_date=date(2026, 12, 15)
        ),
        PaymentMilestoneInput(
            name="3. Final Settlement (25%)",
            percentage=Decimal("25.00"),
            amount=Decimal("860000.00"),
            due_date=date(2027, 2, 1)
        ),
    ]

    req = ServiceAgreementCreate(
        client_id="CLT-TEST-001",
        wedding_date=date(2027, 2, 14),
        wedding_location="Udaipur, Rajasthan",
        venue="The Oberoi Udaivilas",
        guest_count=250,
        service_package="Royal Palace Grandeur",
        package_price=pkg_price,
        tax_percentage=tax_pct,
        discount_amount=disc,
        milestones=milestones,
        created_by="Maharani Gayatri Singh"
    )

    agreement = agreement_service.create_agreement(db=db_session, req=req)

    assert agreement.id.startswith("SA-")
    assert agreement.agreement_number.startswith("RK-SA-")
    assert agreement.total_amount == total_expected
    assert agreement.status == "DRAFT"
    assert agreement.signing_status == "NOT_CREATED"
    assert len(agreement.milestones) == 3
    assert len(agreement.versions) == 1
    assert agreement.versions[0].version_number == 1


def test_02_pdf_generation(db_session):
    """Test ReportLab PDF creation with SHA-256 calculation."""
    agreement = db_session.query(ServiceAgreement).first()
    assert agreement is not None

    doc = agreement_service.generate_agreement_pdf(db=db_session, agreement_id=agreement.id)
    assert doc.id.startswith("DOC-")
    assert doc.document_type == "generated_unsigned_pdf"
    assert doc.file_size > 1000
    assert len(doc.file_hash_sha256) == 64
    assert os.path.exists(doc.file_path)


def test_03_internal_approval(db_session):
    """Test internal staff approval workflow."""
    agreement = db_session.query(ServiceAgreement).first()
    req = AgreementApproveRequest(
        approved_by="Maharani Gayatri Singh",
        notes="Verified financial totals, venue permissions, and GST invoicing lines."
    )
    approved = agreement_service.approve_agreement(db=db_session, agreement_id=agreement.id, req=req)

    assert approved.is_internally_approved is True
    assert approved.status == "APPROVED_TO_SEND"
    assert approved.approved_by == "Maharani Gayatri Singh"


def test_04_send_for_leegality_signature(db_session):
    """Test Leegality electronic signing invitation submission and URL capture."""
    agreement = db_session.query(ServiceAgreement).first()
    res = agreement_service.send_for_signature(db=db_session, agreement_id=agreement.id)

    assert res["success"] is True
    assert res["status"] == "SENT"
    assert res["leegality_document_id"] is not None
    assert "sandbox.leegality.com" in res["signing_url"]

    # Verify db status
    db_session.refresh(agreement)
    assert agreement.status == "SIGNING_PENDING"
    assert agreement.signing_status == "SENT"


def test_05_leegality_webhook_mac_verification_and_signed_retrieval(db_session):
    """Test Leegality Webhook processing with HMAC-SHA1 MAC validation and document retrieval."""
    sig_req = db_session.query(AgreementSignatureRequest).first()
    doc_id = sig_req.leegality_document_id

    # Compute valid MAC using test salt
    valid_mac = leegality_client.compute_webhook_mac(doc_id)

    payload = {
        "documentId": doc_id,
        "status": "COMPLETED",
        "mac": valid_mac,
        "irn": sig_req.leegality_request_id,
        "completedAt": "2026-10-31T18:30:00Z"
    }

    webhook_res = agreement_service.process_leegality_webhook(
        db=db_session,
        payload=payload,
        is_success=True
    )
    assert webhook_res["status"] == "ok"

    # Re-fetch agreement
    agreement = db_session.query(ServiceAgreement).first()
    assert agreement.signing_status == "COMPLETED"
    assert agreement.status == "UNDER_VERIFICATION"

    # Verify duplicate webhook is idempotently rejected
    dup_res = agreement_service.process_leegality_webhook(
        db=db_session,
        payload=payload,
        is_success=True
    )
    assert "Duplicate webhook" in dup_res["message"]


def test_06_employee_verification(db_session):
    """Test employee review and sign-off on executed agreement."""
    agreement = db_session.query(ServiceAgreement).first()
    req = AgreementReviewRequest(
        reviewer_name="Maharani Gayatri Singh",
        decision="VERIFIED",
        remarks="Executed document hash and Leegality audit certificate matched. Approved for booking."
    )
    verified = agreement_service.review_agreement(db=db_session, agreement_id=agreement.id, req=req)

    assert verified.is_verified is True
    assert verified.status == "VERIFIED"
    assert verified.verified_by == "Maharani Gayatri Singh"


def test_07_wedding_booking_confirmation(db_session):
    """Test explicit booking confirmation, duplicate prevention, and Phase 3 handoff."""
    agreement = db_session.query(ServiceAgreement).first()
    req = BookingConfirmRequest(
        confirmed_by="Maharani Gayatri Singh",
        confirmation_notes="Dates locked for Udaivilas palace mandap. Handoff to Phase 3 operations."
    )
    booking = agreement_service.confirm_booking(db=db_session, agreement_id=agreement.id, req=req)

    assert booking.id.startswith("BK-")
    assert booking.booking_reference.startswith("TRK-BK-")
    assert booking.client_id == agreement.client_id
    assert booking.agreement_id == agreement.id
    assert booking.status == "CONFIRMED"
    assert booking.phase3_handoff_ready is True

    # Check agreement status updated
    db_session.refresh(agreement)
    assert agreement.status == "BOOKING_CONFIRMED"

    # Verify duplicate confirmation attempt is blocked
    with pytest.raises(Exception) as excinfo:
        agreement_service.confirm_booking(db=db_session, agreement_id=agreement.id, req=req)
    assert "already confirmed" in str(excinfo.value.detail)

