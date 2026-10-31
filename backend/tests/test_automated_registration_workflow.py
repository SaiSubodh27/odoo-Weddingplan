import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.enquiry import Enquiry, EnquiryNote
from app.models.registration import ClientRegistration
from app.models.client import Client
from app.models.user import UserAccount, ActivationToken
from app.services.email_service import DEV_OUTBOX

client = TestClient(app)


def test_automated_email_enquiry_to_client_registration_lifecycle():
    """
    Complete end-to-end test of the automated workflow:
    1. Incoming email creates enquiry + auto-sends thank-you email with online registration link.
    2. Token verification returns pre-filled enquiry data.
    3. Client submits online registration form.
    4. Data stored in PostgreSQL + enquiry updated.
    5. Staff reviews and requests corrections.
    6. Client updates registration with corrected parameters.
    7. Staff approves registration -> Client record created, User account created in PENDING_ACTIVATION, activation link emailed.
    8. Client sets password and activates account.
    9. Client logs in with email & password.
    10. Booking workflow (weddings/contracts) remains cleanly separated.
    """
    uid = uuid.uuid4().hex[:6]
    client_email = f"princess.ananya.{uid}@udaipur-estates.com"

    # Clear DEV_OUTBOX to accurately trace outbound emails
    DEV_OUTBOX.clear()

    # --- STEP 1: Incoming Email Enquiry ---
    email_sim = client.post("/api/v1/emails/simulate", data={
        "sender_email": client_email,
        "sender_name": "Princess Ananya Singh",
        "subject": "Wedding Celebration Enquiry — Jagmandir Island Palace Udaipur",
        "body_text": "We are seeking bespoke luxury wedding planning for 450 guests in Udaipur in November 2027. Budget approx 4 Crores."
    })
    assert email_sim.status_code == 200
    sim_data = email_sim.json()
    assert sim_data["processed"] is True
    assert sim_data["status"] == "ENQUIRY_CREATED"
    assert sim_data["enquiry_created"] is True
    enquiry_id = sim_data["enquiry_id"]

    # Verify Enquiry was created with token and status 'Registration Link Sent'
    enquiry_res = client.get(f"/api/v1/enquiries/{enquiry_id}")
    assert enquiry_res.status_code == 200
    enq = enquiry_res.json()
    assert enq["status"] == "Registration Link Sent"
    assert enq["registrationToken"] is not None
    reg_token = enq["registrationToken"]

    # --- STEP 2: Automated Thank-You Email Dispatched ---
    # Outbox should contain the automated thank-you email with Google Form / registration link
    thank_you_emails = [e for e in DEV_OUTBOX if e["to"] == client_email and "Thank You" in e["subject"]]
    assert len(thank_you_emails) >= 1
    thank_you = thank_you_emails[-1]
    assert enquiry_id in thank_you["subject"]
    assert "Thank you for contacting The Royal Knot" in thank_you["text"]
    # Verify no credentials or plain-text passwords
    assert "password" not in thank_you["text"].lower()

    # --- STEP 3: Client Opens Online Registration Link ---
    # Verify valid token
    verify_res = client.get(f"/api/v1/registrations/verify?token={reg_token}")
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["valid"] is True
    assert v_data["enquiryId"] == enquiry_id
    assert v_data["email"] == client_email
    assert "Princess Ananya" in v_data["clientName"]

    # Verify invalid token check
    invalid_verify = client.get("/api/v1/registrations/verify?token=INVALID_RANDOM_TOKEN_123")
    assert invalid_verify.status_code == 200
    assert invalid_verify.json()["valid"] is False

    # --- STEP 4: Client Submits Online Registration Form ---
    submit_payload = {
        "token": reg_token,
        "fullName": "Princess Ananya Singh",
        "partnerName": "Yuvraj Devendra Rathore",
        "email": client_email,
        "phone": "+91 98290 11223",
        "address": "City Palace Enclave, Udaipur, Rajasthan 313001",
        "weddingDate": "2027-11-20",
        "weddingLocation": "Jagmandir Island Palace, Udaipur",
        "expectedGuestCount": 450,
        "estimatedBudget": 40000000,
        "weddingEvents": [
            "Welcome Dinner & Royal Rajasthani Mehendi",
            "Sangeet & Musical Evening",
            "Haldi & Phoolon Ki Holi",
            "Sacred Vedic Mandap & Pheras",
            "Grand Reception Banquet"
        ],
        "preferredTheme": "Regal Rajputana Heritage & Floating Palace Splendor",
        "servicePackage": "Full-Service",
        "preferences": "Royal boat processions on Lake Pichola, Michelin-star Rajasthani royal dining, acoustic Sufi artists."
    }

    submit_res = client.post("/api/v1/registrations/submit", json=submit_payload)
    assert submit_res.status_code == 201
    sub_data = submit_res.json()
    assert sub_data["success"] is True
    reg_id = sub_data["registration_id"]

    # Verify Enquiry updated to 'Registration Submitted'
    updated_enq = client.get(f"/api/v1/enquiries/{enquiry_id}").json()
    assert updated_enq["status"] == "Registration Submitted"
    assert "Devendra" in updated_enq["clientName"]
    assert updated_enq["expectedGuestCount"] == 450

    # Verify database storage in client_registrations
    db = SessionLocal()
    try:
        reg_db = db.query(ClientRegistration).filter(ClientRegistration.id == reg_id).first()
        assert reg_db is not None
        assert reg_db.enquiry_id == enquiry_id
        assert reg_db.partner_name == "Yuvraj Devendra Rathore"
        assert reg_db.status == "SUBMITTED"
        assert "Floating Palace" in reg_db.preferred_theme
    finally:
        db.close()

    # --- STEP 5: Employee Reviews Submitted Registration in Dashboard ---
    review_check = client.get(f"/api/v1/enquiries/{enquiry_id}/registration")
    assert review_check.status_code == 200
    reg_details = review_check.json()
    assert reg_details["id"] == reg_id
    assert reg_details["fullName"] == "Princess Ananya Singh"
    assert reg_details["status"] == "SUBMITTED"

    # Employee marks Under Review
    review_res = client.post(f"/api/v1/enquiries/{enquiry_id}/registration/review", json={
        "reviewedBy": "Maharani Gayatri Singh",
        "notes": "Reviewed Jagmandir parameters. Requesting confirmation of guest boat logistics."
    })
    assert review_res.status_code == 200
    assert review_res.json()["status"] == "UNDER_REVIEW"

    # Employee requests correction from client
    corr_res = client.post(f"/api/v1/enquiries/{enquiry_id}/registration/request-corrections", json={
        "staffName": "Maharani Gayatri Singh",
        "correctionNotes": "Kindly confirm whether guest count includes international VIP delegates requiring heritage charter transfers."
    })
    assert corr_res.status_code == 200
    assert corr_res.json()["registration_status"] == "CORRECTIONS_REQUESTED"

    # Verify corrections email dispatched
    corr_emails = [e for e in DEV_OUTBOX if e["to"] == client_email and "Action Requested" in e["subject"]]
    assert len(corr_emails) >= 1
    assert "charter transfers" in corr_emails[-1]["html"]

    # Client updates registration with clarification
    submit_payload["preferences"] = "Confirmed: 450 guests includes 80 international VIPs requiring luxury boat and private charter transfers."
    client.post("/api/v1/registrations/submit", json=submit_payload)

    # --- STEP 6: Employee Approves Registration & Initiates Account Activation ---
    approve_res = client.post(f"/api/v1/enquiries/{enquiry_id}/registration/approve?reviewed_by=Maharani Gayatri Singh")
    assert approve_res.status_code == 200
    app_data = approve_res.json()
    assert app_data["success"] is True
    assert app_data["registration_status"] == "APPROVED"
    assert app_data["enquiry_status"] == "Registered"
    client_id = app_data["client_id"]
    activation_token = app_data["activation_token"]
    assert client_id.startswith("TRK-")
    assert activation_token is not None

    # Verify Client record was created in database
    client_check = client.get(f"/api/v1/clients/{client_id}")
    assert client_check.status_code == 200
    cl_data = client_check.json()
    assert cl_data["partner1Name"] == "Princess Ananya Singh"
    assert cl_data["partner2Name"] == "Yuvraj Devendra Rathore"
    assert cl_data["weddingLocation"] == "Jagmandir Island Palace, Udaipur"
    assert cl_data["status"] == "Registered"

    # Verify UserAccount is in PENDING_ACTIVATION
    db = SessionLocal()
    try:
        user_db = db.query(UserAccount).filter(UserAccount.email == client_email).first()
        assert user_db is not None
        assert user_db.status == "PENDING_ACTIVATION"
        assert user_db.is_active is False
        assert user_db.hashed_password is None  # Never store or email plain-text password
    finally:
        db.close()

    # Verify activation email dispatched to client
    act_emails = [e for e in DEV_OUTBOX if e["to"] == client_email and "Activate Your Wedding Planning Portal" in e["subject"]]
    assert len(act_emails) >= 1
    act_email = act_emails[-1]
    assert activation_token in act_email["html"] or activation_token in act_email["text"]

    # --- STEP 7: Client Activates Account with Secure Password ---
    # Client verifies activation token
    token_verify = client.get(f"/api/v1/auth/verify-token?token={activation_token}")
    assert token_verify.status_code == 200
    assert token_verify.json()["valid"] is True
    assert token_verify.json()["email"] == client_email

    # Client activates with secure confidential password
    activate_res = client.post("/api/v1/auth/activate", json={
        "token": activation_token,
        "password": "RoyalKnot@2027Udaipur",
        "confirmPassword": "RoyalKnot@2027Udaipur"
    })
    assert activate_res.status_code == 200
    assert activate_res.json()["success"] is True

    # Activation token cannot be reused
    reuse_res = client.get(f"/api/v1/auth/verify-token?token={activation_token}")
    assert reuse_res.json()["valid"] is False

    # --- STEP 8: Client Authenticates / Logs In ---
    login_res = client.post("/api/v1/auth/login", json={
        "email": client_email,
        "password": "RoyalKnot@2027Udaipur"
    })
    assert login_res.status_code == 200
    log_data = login_res.json()
    assert log_data["success"] is True
    assert log_data["role"] == "client"
    assert log_data["clientId"] == client_id

    # --- STEP 9: Booking Workflow Separation ---
    # Client registration does not create an active wedding project or signed agreement
    # The client status remains 'Registered' until Phase 2 contracts/agreements are executed
    client_after = client.get(f"/api/v1/clients/{client_id}").json()
    assert client_after["status"] == "Registered"

