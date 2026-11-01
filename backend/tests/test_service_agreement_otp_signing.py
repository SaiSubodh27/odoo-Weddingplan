import uuid
import pytest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import SessionLocal
from app.models.client import Client
from app.models.user import UserAccount
from app.models.agreement import ServiceAgreement
from app.core.security import hash_password
from app.services.agreement_service import agreement_service, hash_otp

client = TestClient(app)


@pytest.fixture
def db_session():
    from app.database.base import Base
    import app.models
    Base.metadata.create_all(bind=SessionLocal().get_bind())
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def agreement_test_client(db_session: Session):
    """Creates a sample luxury wedding client and linked user account with unique IDs."""
    uid = uuid.uuid4().hex[:6]
    client_id = f"TRK-2026-{uid}"
    email = f"couple_{uid}@royaltest.in"

    client_obj = Client(
        id=client_id,
        partner1_name="Princess Ananya",
        partner2_name="Prince Vikram",
        email=email,
        phone="+91 98290 12345",
        wedding_date=date(2026, 12, 15),
        wedding_location="Umaid Bhawan Palace, Jodhpur",
        expected_guest_count=250,
        estimated_budget=Decimal("12000000.00"),
        service_package="Royal Palace Grandeur",
        enquiry_source="Website",
        status="Client"
    )
    db_session.add(client_obj)

    user = UserAccount(
        id=f"USR-{uid}",
        client_id=client_obj.id,
        email=email,
        hashed_password=hash_password("RoyalPassword2026!"),
        role="client",
        status="ACTIVE",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(client_obj)
    db_session.refresh(user)
    return {"client": client_obj, "user": user}


def test_get_or_create_agreement_from_client_db(db_session: Session, agreement_test_client):
    c = agreement_test_client["client"]
    res = client.get(f"/api/v1/agreements/my-agreement?client_id={c.id}")
    assert res.status_code == 200
    data = res.json()

    assert data["client_id"] == c.id
    assert data["client_name"] == "Princess Ananya & Prince Vikram"
    assert data["wedding_location"] == "Umaid Bhawan Palace, Jodhpur"
    assert data["guest_count"] == 250
    assert data["service_package"] == "Royal Palace Grandeur"
    assert Decimal(str(data["package_price"])) == Decimal("12000000.00")
    assert Decimal(str(data["tax_percentage"])) == Decimal("18.00")
    assert Decimal(str(data["total_amount"])) == Decimal("14160000.00")
    assert data["status"] == "PENDING_SIGNATURE"
    assert len(data["milestones"]) == 3


def test_send_and_verify_signing_otp(db_session: Session, agreement_test_client):
    c = agreement_test_client["client"]
    agr = agreement_service.get_or_create_agreement_for_client(db_session, c.id)

    # 1. Send OTP
    res_send = client.post(f"/api/v1/agreements/{agr.id}/send-otp")
    assert res_send.status_code == 200
    send_data = res_send.json()
    assert send_data["success"] is True
    assert send_data["email_destination"] == c.email

    # Verify state in DB
    db_session.refresh(agr)
    assert agr.signing_otp_hash is not None
    assert agr.signing_otp_verified is False

    # 2. Test Invalid OTP
    res_invalid = client.post(f"/api/v1/agreements/{agr.id}/verify-otp", json={"otp": "000000"})
    assert res_invalid.status_code == 400
    assert "Invalid verification code" in res_invalid.json()["detail"]

    # 3. Simulate known OTP
    test_otp = "789123"
    agr.signing_otp_hash = hash_otp(test_otp)
    agr.signing_otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db_session.commit()

    # 4. Verify valid OTP
    res_valid = client.post(f"/api/v1/agreements/{agr.id}/verify-otp", json={"otp": test_otp})
    assert res_valid.status_code == 200
    assert res_valid.json()["verified"] is True

    db_session.refresh(agr)
    assert agr.signing_otp_verified is True


def test_digital_signing_and_pdf_generation(db_session: Session, agreement_test_client):
    c = agreement_test_client["client"]
    agr = agreement_service.get_or_create_agreement_for_client(db_session, c.id)

    # Pre-verify OTP
    test_otp = "654321"
    agr.signing_otp_hash = hash_otp(test_otp)
    agr.signing_otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    agr.signing_otp_verified = True
    db_session.commit()

    # Reject without consent
    res_no_consent = client.post(f"/api/v1/agreements/{agr.id}/sign", json={
        "signature_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "consent": False
    })
    assert res_no_consent.status_code == 400

    # Sign successfully
    sign_payload = {
        "signature_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "consent": True,
        "signer_name": "Prince Vikram Singh"
    }
    res_sign = client.post(f"/api/v1/agreements/{agr.id}/sign", json=sign_payload)
    assert res_sign.status_code == 200
    sign_data = res_sign.json()
    assert sign_data["success"] is True
    assert sign_data["status"] == "SIGNED"
    assert sign_data["has_signed_agreement"] is True

    # Check DB state
    db_session.refresh(agr)
    assert agr.status == "SIGNED"
    assert agr.is_verified is True
    assert agr.signed_by_name == "Prince Vikram Singh"
    assert agr.signed_at is not None

    # Test PDF download
    res_pdf = client.get(f"/api/v1/agreements/{agr.id}/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert res_pdf.content.startswith(b"%PDF-")


def test_login_enforces_agreement_and_gating(db_session: Session, agreement_test_client):
    user = agreement_test_client["user"]
    c = agreement_test_client["client"]

    # 1. Login before agreement signing -> hasSignedAgreement must be False
    res_login_before = client.post("/api/v1/auth/login", json={
        "email": user.email,
        "password": "RoyalPassword2026!"
    })
    assert res_login_before.status_code == 200
    data_before = res_login_before.json()
    assert data_before["hasSignedAgreement"] is False

    # 2. Staff login -> hasSignedAgreement must be True
    res_staff = client.post("/api/v1/auth/login", json={
        "email": "planner@theroyalknot.in",
        "password": "RoyalKnot2026"
    })
    assert res_staff.status_code == 200
    assert res_staff.json()["hasSignedAgreement"] is True

    # 3. Sign agreement for client
    agr = agreement_service.get_or_create_agreement_for_client(db_session, c.id)
    agr.status = "SIGNED"
    agr.is_verified = True
    agr.signed_at = datetime.now(timezone.utc)
    db_session.commit()

    # 4. Login after agreement signing -> hasSignedAgreement must be True
    res_login_after = client.post("/api/v1/auth/login", json={
        "email": user.email,
        "password": "RoyalPassword2026!"
    })
    assert res_login_after.status_code == 200
    assert res_login_after.json()["hasSignedAgreement"] is True


def test_agreement_gate_middleware_blocks_client_until_signed(db_session: Session, agreement_test_client):
    user = agreement_test_client["user"]
    c = agreement_test_client["client"]

    # Client is not signed yet
    headers = {"Authorization": f"Bearer trk_token_{user.id}"}
    res_blocked = client.get("/api/v1/vendors", headers=headers)
    assert res_blocked.status_code == 403
    assert res_blocked.json()["detail"] == "AGREEMENT_REQUIRED"
    assert res_blocked.headers.get("X-Agreement-Required") == "true"

    # Now sign the agreement
    agr = agreement_service.get_or_create_agreement_for_client(db_session, c.id)
    agr.status = "SIGNED"
    agr.is_verified = True
    agr.signed_at = datetime.now(timezone.utc)
    db_session.commit()

    # Now access to vendors succeeds
    res_allowed = client.get("/api/v1/vendors", headers=headers)
    assert res_allowed.status_code == 200


def test_signing_twice_returns_existing_record(db_session: Session, agreement_test_client):
    c = agreement_test_client["client"]
    agr = agreement_service.get_or_create_agreement_for_client(db_session, c.id)

    # Pre-verify OTP
    test_otp = "112233"
    agr.signing_otp_hash = hash_otp(test_otp)
    agr.signing_otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    agr.signing_otp_verified = True
    db_session.commit()

    # First sign
    res1 = client.post(f"/api/v1/agreements/{agr.id}/sign", json={
        "signature_data": "data:image/png;base64,sample_sig_data",
        "consent": True,
        "signer_name": "Princess Ananya"
    })
    assert res1.status_code == 200
    assert res1.json()["status"] == "SIGNED"

    # Second sign -> idempotent, returns existing record without error
    res2 = client.post(f"/api/v1/agreements/{agr.id}/sign", json={
        "signature_data": "data:image/png;base64,sample_sig_data",
        "consent": True,
        "signer_name": "Princess Ananya"
    })
    assert res2.status_code == 200
    assert res2.json()["status"] == "SIGNED"
    assert res2.json()["agreement_id"] == agr.id


def test_planner_can_open_signed_pdf(db_session: Session, agreement_test_client):
    c = agreement_test_client["client"]
    agr = agreement_service.get_or_create_agreement_for_client(db_session, c.id)
    agr.status = "SIGNED"
    agr.signed_at = datetime.now(timezone.utc)
    agr.signed_by_name = "Princess Ananya"
    db_session.commit()

    # Planner requests PDF with staff header
    headers = {"Authorization": "Bearer trk_staff_session_token_2026"}
    res_pdf = client.get(f"/api/v1/agreements/{agr.id}/pdf", headers=headers)
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert res_pdf.content.startswith(b"%PDF-")
