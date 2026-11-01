import sys
import uuid
import os
import time
from pathlib import Path
from decimal import Decimal
from datetime import date, datetime, timezone, timedelta
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
    AgreementPaymentMilestone,
    AgreementDocument,
    AgreementSignatureRequest,
    AgreementWebhookEvent,
    WeddingBooking,
)
from app.services.agreement_service import agreement_service
from app.services.zoho_sign_service import (
    zoho_sign_client,
    ZohoSignClient,
    ZohoRateLimitError,
    ZohoNotFoundError,
)
from app.services.zoho_polling_service import zoho_polling_service, ZohoSignPollingService
from app.schemas.agreement import (
    ServiceAgreementCreate,
    PaymentMilestoneInput,
    AgreementApproveRequest,
    AgreementReviewRequest,
    BookingConfirmRequest,
)
from app.core.config import settings
from app.main import app

from sqlalchemy.pool import StaticPool

# Isolated in-memory SQLite database for unit tests
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    # Seed registered luxury client
    client = Client(
        id="CLT-POLL-001",
        partner1_name="Aditya Singhania",
        partner2_name="Kareena Mehra",
        email="aditya.kareena@singhania-weddings.in",
        phone="+91 99000 11223",
        wedding_date=date(2027, 4, 18),
        wedding_location="Udaipur, Rajasthan",
        expected_guest_count=400,
        estimated_budget=Decimal("5000000.00"),
        service_package="Royal Palace Grandeur",
        status="Registered"
    )
    session.add(client)
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def test_client():
    from app.database.session import get_db
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def _create_and_approve_agreement(db, client_id="CLT-POLL-001") -> ServiceAgreement:
    milestones = [
        PaymentMilestoneInput(
            name="1. Retainer (25%)",
            percentage=Decimal("25.00"),
            amount=Decimal("1180000.00"),
            due_date=date(2026, 12, 1)
        ),
        PaymentMilestoneInput(
            name="2. Production Stage (75%)",
            percentage=Decimal("75.00"),
            amount=Decimal("3540000.00"),
            due_date=date(2027, 3, 1)
        ),
    ]
    req = ServiceAgreementCreate(
        client_id=client_id,
        wedding_date=date(2027, 4, 18),
        wedding_location="Udaipur, Rajasthan",
        venue="City Palace Udaipur",
        guest_count=400,
        service_package="Royal Palace Grandeur",
        package_price=Decimal("4000000.00"),
        tax_percentage=Decimal("18.00"),
        discount_amount=Decimal("0.00"),
        milestones=milestones,
        created_by="Maharani Gayatri Singh"
    )
    agreement = agreement_service.create_agreement(db=db, req=req)
    agreement_service.generate_agreement_pdf(db=db, agreement_id=agreement.id)
    agreement_service.approve_agreement(
        db=db,
        agreement_id=agreement.id,
        req=AgreementApproveRequest(approved_by="Maharani Gayatri Singh", notes="Approved.")
    )
    return agreement


# 1. Polling enabled configuration
def test_01_polling_enabled_configuration():
    assert settings.ZOHO_SIGN_POLLING_ENABLED is True
    assert settings.ZOHO_SIGN_POLLING_INTERVAL_SECONDS > 0
    assert settings.ZOHO_SIGN_POLLING_TIMEOUT_SECONDS > 0


# 2. Polling disabled configuration
def test_02_polling_disabled_configuration(monkeypatch):
    monkeypatch.setattr(settings, "ZOHO_SIGN_POLLING_ENABLED", False)
    assert settings.ZOHO_SIGN_POLLING_ENABLED is False


# 3. Pending signing status
def test_03_pending_signing_status(db_session):
    agreement = _create_and_approve_agreement(db_session)
    res = agreement_service.send_for_signature(db=db_session, agreement_id=agreement.id)
    assert res["success"] is True
    assert res["status"] == "SENT"

    db_session.refresh(agreement)
    assert agreement.status == "SIGNING_PENDING"
    assert agreement.signing_status == "SENT"


# 4. Sent signing status via polling
def test_04_sent_signing_status(db_session):
    agreement = db_session.query(ServiceAgreement).first()
    sig_req = db_session.query(AgreementSignatureRequest).filter(
        AgreementSignatureRequest.agreement_id == agreement.id
    ).first()

    # Configure mock provider to report SENT
    zoho_sign_client.set_mock_request_state(
        sig_req.provider_request_id,
        status="SENT",
        actions=[{"recipient_name": sig_req.signer_name, "action_status": "UNOPENED"}]
    )

    poll_res = zoho_polling_service.poll_agreement_status(db=db_session, agreement_id=agreement.id)
    assert poll_res["signing_status"] == "SENT"
    assert poll_res["is_completed"] is False
    assert poll_res["next_status_check_at"] is not None


# 5. Viewed signing status via polling
def test_05_viewed_signing_status(db_session):
    agreement = db_session.query(ServiceAgreement).first()
    sig_req = db_session.query(AgreementSignatureRequest).filter(
        AgreementSignatureRequest.agreement_id == agreement.id
    ).first()

    # Configure mock provider to report VIEWED
    zoho_sign_client.set_mock_request_state(
        sig_req.provider_request_id,
        status="VIEWED",
        actions=[{"recipient_name": sig_req.signer_name, "action_status": "VIEWED"}]
    )

    poll_res = zoho_polling_service.poll_agreement_status(db=db_session, agreement_id=agreement.id)
    assert poll_res["signing_status"] == "VIEWED"
    assert poll_res["is_completed"] is False


# 6. Completed signing status via polling
def test_06_completed_signing_status(db_session):
    agreement = db_session.query(ServiceAgreement).first()
    sig_req = db_session.query(AgreementSignatureRequest).filter(
        AgreementSignatureRequest.agreement_id == agreement.id
    ).first()

    # Configure mock provider to report COMPLETED
    zoho_sign_client.set_mock_request_state(
        sig_req.provider_request_id,
        status="COMPLETED",
        actions=[{"recipient_name": sig_req.signer_name, "action_status": "SIGNED"}],
        completed_at="2026-11-01T00:00:00Z"
    )

    poll_res = zoho_polling_service.poll_agreement_status(db=db_session, agreement_id=agreement.id)
    assert poll_res["signing_status"] == "COMPLETED"
    assert poll_res["is_completed"] is True

    db_session.refresh(agreement)
    assert agreement.status == "UNDER_VERIFICATION"
    assert agreement.signing_status == "COMPLETED"


# 7. Declined signing status via polling
def test_07_declined_signing_status(db_session):
    agreement = _create_and_approve_agreement(db_session)
    res = agreement_service.send_for_signature(db=db_session, agreement_id=agreement.id)
    sig_req = db_session.query(AgreementSignatureRequest).filter(
        AgreementSignatureRequest.agreement_id == agreement.id
    ).first()

    zoho_sign_client.set_mock_request_state(
        sig_req.provider_request_id,
        status="DECLINED",
        actions=[{"recipient_name": sig_req.signer_name, "action_status": "DECLINED"}]
    )

    poll_res = zoho_polling_service.poll_agreement_status(db=db_session, agreement_id=agreement.id)
    assert poll_res["signing_status"] == "DECLINED"
    assert poll_res["is_completed"] is False

    db_session.refresh(agreement)
    assert agreement.signing_status == "DECLINED"


# 8. Expired signing status via polling
def test_08_expired_signing_status(db_session):
    agreement = _create_and_approve_agreement(db_session)
    res = agreement_service.send_for_signature(db=db_session, agreement_id=agreement.id)
    sig_req = db_session.query(AgreementSignatureRequest).filter(
        AgreementSignatureRequest.agreement_id == agreement.id
    ).first()

    zoho_sign_client.set_mock_request_state(
        sig_req.provider_request_id,
        status="EXPIRED",
        actions=[{"recipient_name": sig_req.signer_name, "action_status": "EXPIRED"}]
    )

    poll_res = zoho_polling_service.poll_agreement_status(db=db_session, agreement_id=agreement.id)
    assert poll_res["signing_status"] == "EXPIRED"

    db_session.refresh(agreement)
    assert agreement.signing_status == "EXPIRED"


# 9. Invalid provider request ID
def test_09_invalid_provider_request_id():
    with pytest.raises(ZohoNotFoundError):
        zoho_sign_client.get_signing_status("")


# 10. Invalid OAuth credentials
def test_10_invalid_oauth_credentials():
    custom_client = ZohoSignClient(env="sandbox", client_id="", client_secret="", refresh_token="")
    with pytest.raises(RuntimeError):
        custom_client.get_access_token()


# 11. OAuth token refresh
def test_11_oauth_token_refresh(monkeypatch):
    custom_client = ZohoSignClient(env="sandbox", client_id="test_id", client_secret="test_sec", refresh_token="test_ref")
    
    # Mock httpx response for refresh
    class MockResponse:
        status_code = 200
        def json(self):
            return {"access_token": "fresh_access_token_123", "expires_in": 3600, "api_domain": "https://sign.zoho.in"}

    class MockHttpxClient:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, url, params=None, **kwargs):
            return MockResponse()

    import httpx
    monkeypatch.setattr(httpx, "Client", MockHttpxClient)
    token = custom_client.get_access_token()
    assert token == "fresh_access_token_123"
    assert custom_client.api_base_url == "https://sign.zoho.in/api/v1"


# 12. Provider API timeout handling
def test_12_provider_api_timeout(db_session, monkeypatch):
    agreement = _create_and_approve_agreement(db_session)
    res = agreement_service.send_for_signature(db=db_session, agreement_id=agreement.id)
    sig_req = db_session.query(AgreementSignatureRequest).filter(
        AgreementSignatureRequest.agreement_id == agreement.id
    ).first()

    def raise_timeout(*args, **kwargs):
        raise RuntimeError("Zoho Sign API connection timeout: Read timed out.")

    monkeypatch.setattr(zoho_sign_client, "get_signing_status", raise_timeout)
    poll_res = zoho_polling_service.poll_agreement_status(db=db_session, agreement_id=agreement.id)
    assert poll_res["error"] == "polling_failed"
    assert "timeout" in poll_res["details"].lower()


# 13. Provider API rate limiting
def test_13_provider_api_rate_limiting(db_session, monkeypatch):
    agreement = db_session.query(ServiceAgreement).filter(ServiceAgreement.status == 'SIGNING_PENDING').order_by(ServiceAgreement.created_at.desc()).first()

    def raise_rate_limit(*args, **kwargs):
        raise ZohoRateLimitError("Rate limited by Zoho Sign", retry_after=45)

    monkeypatch.setattr(zoho_sign_client, "get_signing_status", raise_rate_limit)
    poll_res = zoho_polling_service.poll_agreement_status(db=db_session, agreement_id=agreement.id)
    assert poll_res["error"] == "rate_limited"
    assert poll_res["retry_after"] == 45


# 14. Exponential backoff
def test_14_exponential_backoff(db_session, monkeypatch):
    agreement = db_session.query(ServiceAgreement).filter(ServiceAgreement.status == 'SIGNING_PENDING').order_by(ServiceAgreement.created_at.desc()).first()
    sig_req = db_session.query(AgreementSignatureRequest).filter(
        AgreementSignatureRequest.agreement_id == agreement.id
    ).first()

    sig_req.polling_attempt_count = 3
    db_session.commit()

    def raise_err(*args, **kwargs):
        raise RuntimeError("Transient upstream connection error")

    monkeypatch.setattr(zoho_sign_client, "get_signing_status", raise_err)
    zoho_polling_service.poll_agreement_status(db=db_session, agreement_id=agreement.id)

    db_session.refresh(sig_req)
    assert sig_req.polling_attempt_count >= 4
    assert sig_req.next_status_check_at is not None


# 15. Duplicate polling prevention (locking)
def test_15_duplicate_polling_prevention(db_session):
    agreement = _create_and_approve_agreement(db_session)
    agreement_service.send_for_signature(db=db_session, agreement_id=agreement.id)
    sig_req = db_session.query(AgreementSignatureRequest).filter(
        AgreementSignatureRequest.agreement_id == agreement.id
    ).first()

    # Artificially lock the active request
    req_id = sig_req.provider_request_id
    zoho_polling_service._active_polls.add(req_id)

    try:
        res = zoho_polling_service.poll_agreement_status(db=db_session, agreement_id=agreement.id)
        assert "currently in progress" in res["message"]
    finally:
        zoho_polling_service._active_polls.discard(req_id)


# 16. Application restart recovery
def test_16_application_restart_recovery(db_session):
    # Create active pending agreement
    agreement = _create_and_approve_agreement(db_session)
    agreement_service.send_for_signature(db=db_session, agreement_id=agreement.id)
    sig_req = db_session.query(AgreementSignatureRequest).filter(
        AgreementSignatureRequest.agreement_id == agreement.id
    ).first()
    sig_req.next_status_check_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    db_session.commit()

    # Re-instantiate polling service to simulate restart
    fresh_service = ZohoSignPollingService()
    scan_res = fresh_service.poll_all_pending_agreements(db_session)
    assert scan_res["checked"] >= 1


# 17. Duplicate webhook delivery
def test_17_duplicate_webhook_delivery(db_session):
    agreement = _create_and_approve_agreement(db_session)
    agreement_service.send_for_signature(db=db_session, agreement_id=agreement.id)
    sig_req = db_session.query(AgreementSignatureRequest).filter(
        AgreementSignatureRequest.agreement_id == agreement.id
    ).first()

    payload = {
        "notifications": {
            "request_id": sig_req.provider_request_id,
            "document_id": sig_req.provider_document_id,
            "request_status": "COMPLETED",
            "operation_type": "RequestCompleted",
            "recipient_name": sig_req.signer_name,
            "recipient_email": sig_req.signer_email
        }
    }

    res1 = agreement_service.process_zoho_webhook(db=db_session, payload=payload)
    assert res1["status"] == "success"

    res2 = agreement_service.process_zoho_webhook(db=db_session, payload=payload)
    assert res2["status"] == "ok"
    assert "Duplicate" in res2["message"]


# 18. Polling and webhook race conditions
def test_18_polling_and_webhook_race_conditions(db_session):
    agreement = _create_and_approve_agreement(db_session)
    agreement_service.send_for_signature(db=db_session, agreement_id=agreement.id)
    sig_req = db_session.query(AgreementSignatureRequest).filter(
        AgreementSignatureRequest.agreement_id == agreement.id
    ).first()

    # 1. Polling completes the document first
    zoho_sign_client.set_mock_request_state(sig_req.provider_request_id, "COMPLETED")
    zoho_polling_service.poll_agreement_status(db=db_session, agreement_id=agreement.id)

    # 2. Subsequent webhook arrives
    webhook_payload = {
        "notifications": {
            "request_id": sig_req.provider_request_id,
            "document_id": sig_req.provider_document_id,
            "request_status": "COMPLETED",
            "operation_type": "RequestCompleted"
        }
    }
    webhook_res = agreement_service.process_zoho_webhook(db=db_session, payload=webhook_payload)
    assert webhook_res["status"] == "success"

    # Status remains UNDER_VERIFICATION and COMPLETED
    db_session.refresh(agreement)
    assert agreement.status == "UNDER_VERIFICATION"
    assert agreement.signing_status == "COMPLETED"


# 19. Signed PDF retrieval
def test_19_signed_pdf_retrieval(db_session):
    agreement = db_session.query(ServiceAgreement).filter(
        ServiceAgreement.status == "UNDER_VERIFICATION"
    ).first()
    assert agreement is not None

    doc = db_session.query(AgreementDocument).filter(
        AgreementDocument.agreement_id == agreement.id,
        AgreementDocument.document_type == "signed_agreement_pdf"
    ).first()
    assert doc is not None
    assert doc.file_size > 0
    assert os.path.exists(doc.file_path)


# 20. Completion certificate retrieval
def test_20_completion_certificate_retrieval(db_session):
    agreement = db_session.query(ServiceAgreement).filter(
        ServiceAgreement.status == "UNDER_VERIFICATION"
    ).first()

    cert = db_session.query(AgreementDocument).filter(
        AgreementDocument.agreement_id == agreement.id,
        AgreementDocument.document_type == "signature_audit_trail"
    ).first()
    assert cert is not None
    assert cert.file_size > 0
    assert os.path.exists(cert.file_path)


# 21. Employee verification
def test_21_employee_verification(db_session):
    agreement = db_session.query(ServiceAgreement).filter(
        ServiceAgreement.status == "UNDER_VERIFICATION"
    ).first()

    req = AgreementReviewRequest(
        reviewer_name="Maharani Gayatri Singh",
        decision="VERIFIED",
        remarks="Polled Zoho Sign executed PDF and Completion Certificate validated."
    )
    verified = agreement_service.review_agreement(db=db_session, agreement_id=agreement.id, req=req)
    assert verified.is_verified is True
    assert verified.status == "VERIFIED"


# 22. Booking confirmation
def test_22_booking_confirmation(db_session):
    agreement = db_session.query(ServiceAgreement).filter(
        ServiceAgreement.status == "VERIFIED"
    ).first()

    req = BookingConfirmRequest(
        confirmed_by="Maharani Gayatri Singh",
        confirmation_notes="Dates confirmed post-polling verification."
    )
    booking = agreement_service.confirm_booking(db=db_session, agreement_id=agreement.id, req=req)
    assert booking.id.startswith("BK-")
    assert booking.booking_reference.startswith("TRK-BK-")
    assert booking.status == "CONFIRMED"
    assert booking.phase3_handoff_ready is True


# 23. Manual refresh endpoint via TestClient
def test_23_manual_refresh_endpoint(test_client, db_session):
    agreement = _create_and_approve_agreement(db_session)
    agreement_service.send_for_signature(db=db_session, agreement_id=agreement.id)

    resp = test_client.post(f"/api/v1/service-agreements/{agreement.id}/refresh-status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["agreement_id"] == agreement.id
    assert data["provider"] == "Zoho Sign"
    assert "last_status_checked_at" in data
