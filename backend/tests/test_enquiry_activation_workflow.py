import sys
import uuid
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models.enquiry import Enquiry
from app.models.client import Client
from app.models.user import UserAccount, ActivationToken
from app.core.security import hash_password, hash_token, verify_password

client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["database_connected"] is True


def test_email_enquiry_workflow():
    uid = uuid.uuid4().hex[:6]
    test_email = f"gayatri.{uid}@testheritage.in"

    # 1. Staff creates Email enquiry
    enquiry_payload = {
        "clientName": "Princess Gayatri Rao",
        "email": test_email,
        "phone": "+91 98200 11223",
        "enquirySource": "Email",
        "weddingDate": "2027-01-20",
        "weddingLocation": "City Palace, Udaipur",
        "expectedGuestCount": 350,
        "estimatedBudget": "₹ 2.0 Cr",
        "requirements": "Grand lakeside mandap with floating candle displays",
        "internalNotes": "Initial VIP inquiry received via concierge desk."
    }
    create_res = client.post("/api/v1/enquiries", json=enquiry_payload)
    assert create_res.status_code == 201
    enquiry = create_res.json()
    enquiry_id = enquiry["id"]
    assert enquiry["status"] == "New"
    assert enquiry["enquirySource"] == "Email"

    # 2. Staff adds internal note
    note_res = client.post(f"/api/v1/enquiries/{enquiry_id}/notes", json={
        "content": "Called family coordinator to discuss royal procession permissions.",
        "author": "Maharani Gayatri Singh"
    })
    assert note_res.status_code == 201

    # 3. Staff downloads prefilled registration template
    template_res = client.get(f"/api/v1/enquiries/{enquiry_id}/registration-template")
    assert template_res.status_code == 200
    assert "The Royal Knot" in template_res.text
    assert enquiry_id in template_res.text

    # 4. Staff uploads sent registration document
    upload_res = client.post(
        f"/api/v1/enquiries/{enquiry_id}/documents/upload",
        data={"document_type": "sent_to_client", "uploaded_by": "Staff Lead"},
        files={"file": ("TheRoyalKnot_Registration_Gayatri.pdf", b"%PDF-1.4 test registration document", "application/pdf")}
    )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    doc_id = doc_data["id"]

    # 5. Staff downloads uploaded document
    download_res = client.get(f"/api/v1/enquiries/{enquiry_id}/documents/{doc_id}/download")
    assert download_res.status_code == 200
    assert download_res.content == b"%PDF-1.4 test registration document"

    # 6. Staff dispatches document via email
    send_res = client.post(f"/api/v1/enquiries/{enquiry_id}/send-document")
    assert send_res.status_code == 200
    assert send_res.json()["enquiry_status"] == "Registration Document Sent"

    # 7. Staff uploads completed returned document
    upload_returned_res = client.post(
        f"/api/v1/enquiries/{enquiry_id}/documents/upload",
        data={"document_type": "completed_by_client", "uploaded_by": "Staff Lead"},
        files={"file": ("Completed_Dossier_Gayatri.pdf", b"%PDF-1.4 completed client form", "application/pdf")}
    )
    assert upload_returned_res.status_code == 201

    # 8. Staff registers client from enquiry
    reg_res = client.post(f"/api/v1/enquiries/{enquiry_id}/register", json={
        "partner1Name": "Gayatri Rao",
        "partner2Name": "Vikramaditya Barman",
        "servicePackage": "Full-Service",
        "weddingTheme": "Lakeside Royal Mewar"
    })
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert reg_data["success"] is True
    client_id = reg_data["client_id"]
    activation_token = reg_data["activation_token"]

    # Verify enquiry status updated to Registered
    get_enquiry = client.get(f"/api/v1/enquiries/{enquiry_id}").json()
    assert get_enquiry["status"] == "Registered"
    assert get_enquiry["clientId"] == client_id

    # 9. Verify activation token endpoint
    verify_res = client.get(f"/api/v1/auth/verify-token?token={activation_token}")
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is True

    # 10. Attempt login before activation (Must fail with 403 Forbidden)
    login_before = client.post("/api/v1/auth/login", json={
        "email": test_email,
        "password": "RoyalPassword123!"
    })
    assert login_before.status_code == 403

    # 11. Client activates account with secure password
    activate_res = client.post("/api/v1/auth/activate", json={
        "token": activation_token,
        "password": "RoyalPassword123!",
        "confirmPassword": "RoyalPassword123!"
    })
    assert activate_res.status_code == 200
    assert activate_res.json()["success"] is True

    # 12. Attempt to reuse activation token (Must fail)
    reuse_res = client.get(f"/api/v1/auth/verify-token?token={activation_token}")
    assert reuse_res.json()["valid"] is False

    # 13. Client logs in successfully
    login_after = client.post("/api/v1/auth/login", json={
        "email": test_email,
        "password": "RoyalPassword123!"
    })
    assert login_after.status_code == 200
    login_data = login_after.json()
    assert login_data["success"] is True
    assert login_data["role"] == "client"
    assert login_data["clientId"] == client_id


def test_phone_enquiry_workflow():
    uid = uuid.uuid4().hex[:6]
    test_email = f"devendra.{uid}@testroyal.in"

    # 1. Staff creates Phone enquiry
    phone_enquiry = {
        "clientName": "Devendra & Shweta Singhania",
        "email": test_email,
        "phone": "+91 98111 22334",
        "enquirySource": "Phone",
        "weddingDate": "2027-02-14",
        "weddingLocation": "Rambagh Palace, Jaipur",
        "expectedGuestCount": 500,
        "estimatedBudget": "25000000.00",
        "requirements": "Heritage polo grounds welcome cocktail party"
    }
    create_res = client.post("/api/v1/enquiries", json=phone_enquiry)
    assert create_res.status_code == 201
    enquiry_id = create_res.json()["id"]

    # 2. Staff marks document sent
    sent_res = client.post(f"/api/v1/enquiries/{enquiry_id}/send-document")
    assert sent_res.status_code == 200

    # 3. Staff marks document received
    recv_res = client.post(f"/api/v1/enquiries/{enquiry_id}/mark-document-received")
    assert recv_res.status_code == 200
    assert recv_res.json()["status"] == "Registration Received"

    # 4. Staff registers client
    reg_res = client.post(f"/api/v1/enquiries/{enquiry_id}/register", json={
        "partner1Name": "Devendra Singhania",
        "partner2Name": "Shweta Agarwal"
    })
    assert reg_res.status_code == 200
    token = reg_res.json()["activation_token"]

    # 5. Client activates account
    act_res = client.post("/api/v1/auth/activate", json={
        "token": token,
        "password": "JaipurWedding2027!",
        "confirmPassword": "JaipurWedding2027!"
    })
    assert act_res.status_code == 200

    # 6. Client login
    login_res = client.post("/api/v1/auth/login", json={
        "email": test_email,
        "password": "JaipurWedding2027!"
    })
    assert login_res.status_code == 200


def test_duplicate_email_registration_prevention():
    uid = uuid.uuid4().hex[:6]
    first_email = f"first.{uid}@testheritage.in"

    # Register first enquiry
    enq1 = {
        "clientName": f"Client {uid}",
        "email": first_email,
        "phone": "+91 99999 11111",
        "enquirySource": "Email"
    }
    create_res1 = client.post("/api/v1/enquiries", json=enq1)
    assert create_res1.status_code == 201
    eid1 = create_res1.json()["id"]

    reg1 = client.post(f"/api/v1/enquiries/{eid1}/register", json={"partner1Name": "P1", "partner2Name": "P2"})
    assert reg1.status_code == 200

    # Create second enquiry with same email
    enq2 = {
        "clientName": f"Client {uid} Duplicate",
        "email": first_email,
        "phone": "+91 99999 22222",
        "enquirySource": "Phone"
    }
    create_res2 = client.post("/api/v1/enquiries", json=enq2)
    assert create_res2.status_code == 201
    eid2 = create_res2.json()["id"]

    # Registering second enquiry with same email should fail with 400 Bad Request
    reg_dup = client.post(f"/api/v1/enquiries/{eid2}/register", json={})
    assert reg_dup.status_code == 400
    assert "already exists" in reg_dup.json()["detail"].lower() or "duplicate" in reg_dup.json()["detail"].lower()


def test_invalid_or_expired_activation_token():
    # 1. Non-existent token
    res = client.get("/api/v1/auth/verify-token?token=completely_fake_token_123")
    assert res.json()["valid"] is False

    # 2. Expired token simulation
    uid = uuid.uuid4().hex[:6]
    db = SessionLocal()
    try:
        user = UserAccount(
            id=f"USR-EXP-{uid}",
            email=f"expired.{uid}@test.in",
            role="client",
            status="PENDING_ACTIVATION",
            is_active=False
        )
        db.add(user)
        db.flush()

        raw_token = f"expired_token_{uid}"
        t_hash = hash_token(raw_token)
        expired_record = ActivationToken(
            id=f"ACT-EXP-{uid}",
            user_id=user.id,
            token_hash=t_hash,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=2),
            is_used=False
        )
        db.add(expired_record)
        db.commit()

        verify_expired = client.get(f"/api/v1/auth/verify-token?token={raw_token}")
        assert verify_expired.json()["valid"] is False
        assert "expired" in verify_expired.json()["message"].lower()

        act_expired = client.post("/api/v1/auth/activate", json={
            "token": raw_token,
            "password": "TestPassword123!",
            "confirmPassword": "TestPassword123!"
        })
        assert act_expired.status_code == 400
        assert "expired" in act_expired.json()["detail"].lower()
    finally:
        db.close()
