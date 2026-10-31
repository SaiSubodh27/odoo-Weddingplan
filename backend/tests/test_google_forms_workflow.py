import io
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.enquiry import Enquiry
from app.models.registration import ClientRegistration
from app.models.client import Client
from app.models.user import UserAccount
from app.services.email_service import DEV_OUTBOX
from app.core.config import settings

client = TestClient(app)


def test_google_forms_configuration_endpoints():
    """Verify staff can view and update Google Forms and Google Sheets configuration."""
    # 1. Get current configuration
    res = client.get("/api/v1/registrations/config")
    assert res.status_code == 200
    data = res.json()
    assert "googleFormsRegistrationUrl" in data
    assert "webhookUrl" in data
    assert "agencyEmail" in data
    assert data["agencyEmail"] == settings.AGENCY_EMAIL

    # 2. Update configuration
    test_form_url = "https://docs.google.com/forms/d/e/1FAIpQLSe_TEST_ROYAL_KNOT_FORM/viewform"
    test_sheet_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
    update_res = client.put("/api/v1/registrations/config", json={
        "googleFormsRegistrationUrl": test_form_url,
        "googleSheetId": test_sheet_id
    })
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["googleFormsRegistrationUrl"] == test_form_url
    assert updated_data["googleSheetId"] == test_sheet_id
    assert settings.GOOGLE_FORMS_REGISTRATION_URL == test_form_url
    assert settings.GOOGLE_SHEET_ID == test_sheet_id


def test_automated_enquiry_to_google_forms_email():
    """Verify incoming email automatically triggers thank-you email with Google Form link."""
    uid = uuid.uuid4().hex[:6]
    client_email = f"maharani.padmini.{uid}@rajputana-weddings.in"
    DEV_OUTBOX.clear()

    # 1. Inbound client enquiry email
    email_sim = client.post("/api/v1/emails/simulate", data={
        "sender_email": client_email,
        "sender_name": "Padmini Rathore",
        "subject": "Destination Wedding at Umaid Bhawan Palace Jodhpur 2027",
        "body_text": "We are planning a 3-day royal celebration for 400 guests at Umaid Bhawan Palace."
    })
    assert email_sim.status_code == 200
    res_data = email_sim.json()
    assert res_data["enquiry_created"] is True
    enquiry_id = res_data["enquiry_id"]

    # 2. Verify enquiry status
    enq_res = client.get(f"/api/v1/enquiries/{enquiry_id}")
    assert enq_res.status_code == 200
    assert enq_res.json()["status"] == "Registration Link Sent"

    # 3. Verify automated thank-you email in outbox
    sent_emails = [e for e in DEV_OUTBOX if e["to"] == client_email]
    assert len(sent_emails) >= 1
    thank_you = sent_emails[-1]

    # Verify required phrasing and tone
    assert "Thank you for contacting The Royal Knot" in thank_you["text"]
    assert "delighted that you are considering us for your special celebration" in thank_you["text"]
    assert "kindly complete the registration form using the link below" in thank_you["text"]
    assert enquiry_id in thank_you["text"]
    assert settings.GOOGLE_FORMS_REGISTRATION_URL in thank_you["text"] or settings.GOOGLE_FORMS_REGISTRATION_URL in thank_you["html"]
    # No plain-text passwords or attachment documents
    assert "password" not in thank_you["text"].lower()


def test_google_forms_webhook_matched_by_enquiry_ref():
    """Verify Google Forms webhook submission matches open enquiry by enquiry reference."""
    uid = uuid.uuid4().hex[:6]
    client_email = f"yuvraj.karan.{uid}@heritage-estates.com"

    # 1. Create enquiry first
    create_enq = client.post("/api/v1/enquiries", json={
        "clientName": "Karan Singhania",
        "email": client_email,
        "phone": "+91 98111 22334",
        "enquirySource": "Email",
        "weddingLocation": "Jaipur"
    })
    assert create_enq.status_code == 201
    enquiry_id = create_enq.json()["id"]

    # 2. Client fills Google Form with enquiry reference ID
    webhook_payload = {
        "response_id": f"RESP-{uid}",
        "Timestamp": "2026-10-31 16:30:00",
        "Full Name": "Karan Singhania",
        "Partner's Full Name": "Tara Kapoor",
        "Email": client_email,
        "Phone": "+91 98111 22334",
        "Current City / Address": "Mumbai & Jaipur",
        "Wedding Date": "2027-02-18",
        "Wedding Destination / Location": "Rambagh Palace, Jaipur",
        "Expected Guest Count": "450 guests",
        "Estimated Budget": "₹ 3.5 Crores",
        "Wedding Events / Ceremonies": "Mehendi, Sangeet, Vedic Pheras, Royal Reception",
        "Preferred Theme / Aesthetic": "Regal Rajputana Heritage & Floating Palace Splendor",
        "Service Package": "Full-Service",
        "Special Requests / Preferences": "Require elephant procession for Baraat and vintage royal car arrivals.",
        "Enquiry Reference ID": enquiry_id
    }

    webhook_res = client.post("/api/v1/registrations/google-forms-webhook", json=webhook_payload)
    assert webhook_res.status_code == 200
    res_data = webhook_res.json()
    assert res_data["success"] is True
    assert res_data["matched"] is True
    assert res_data["enquiry_id"] == enquiry_id
    assert res_data["status"] == "SUBMITTED"

    # 3. Check that Enquiry is updated with Google Form details
    updated_enq = client.get(f"/api/v1/enquiries/{enquiry_id}").json()
    assert updated_enq["status"] == "Registration Submitted"
    assert "Tara Kapoor" in updated_enq["clientName"]
    assert updated_enq["weddingDate"] == "2027-02-18"
    assert updated_enq["weddingLocation"] == "Rambagh Palace, Jaipur"
    assert updated_enq["expectedGuestCount"] == 450
    assert float(updated_enq["estimatedBudget"]) == 35000000.0

    # 4. Check submitted registration record via enquiry registration endpoint
    reg_res = client.get(f"/api/v1/enquiries/{enquiry_id}/registration")
    assert reg_res.status_code == 200
    reg = reg_res.json()
    assert reg["fullName"] == "Karan Singhania"
    assert reg["partnerName"] == "Tara Kapoor"
    assert reg["email"] == client_email
    assert reg["status"] == "SUBMITTED"
    assert reg["source"] == "Google Forms Webhook"


def test_google_forms_duplicate_prevention():
    """Verify that submitting the same response again does not create duplicate records."""
    uid = uuid.uuid4().hex[:6]
    client_email = f"dup.test.{uid}@theroyalknot.test"
    resp_id = f"RESP-DUP-{uid}"

    payload = {
        "response_id": resp_id,
        "Timestamp": "2026-10-31 17:00:00",
        "Full Name": "Sameera Reddy",
        "Partner's Full Name": "Aditya Varma",
        "Email": client_email,
        "Phone": "+91 99887 76655",
        "Wedding Destination / Location": "Udaipur",
        "Expected Guest Count": "200",
        "Estimated Budget": "1 Crore"
    }

    # First submission
    first_res = client.post("/api/v1/registrations/google-forms-webhook", json=payload)
    assert first_res.status_code == 200
    assert first_res.json()["success"] is True

    # Second submission with same response_id
    second_res = client.post("/api/v1/registrations/google-forms-webhook", json=payload)
    assert second_res.status_code == 200
    assert second_res.json()["status"] == "DUPLICATE_SKIPPED"


def test_unmatched_google_forms_and_manual_association():
    """Verify unmatched submissions are flagged UNMATCHED and can be manually associated by staff."""
    uid = uuid.uuid4().hex[:6]
    random_email = f"unmatched.{uid}@unknown-domain.org"

    # Submit without an existing enquiry and without reference ID
    payload = {
        "response_id": f"RESP-UNM-{uid}",
        "Timestamp": "2026-10-31 17:15:00",
        "Full Name": "Devendra Shah",
        "Partner's Full Name": "Aarti Shah",
        "Email": random_email,
        "Phone": "+91 91234 56789",
        "Wedding Destination / Location": "Alsisar Mahal, Shekhawati",
        "Expected Guest Count": "300",
        "Estimated Budget": "80 Lakh",
        "Preferences": "Historical haveli wedding with traditional puppet artists"
    }

    webhook_res = client.post("/api/v1/registrations/google-forms-webhook", json=payload)
    assert webhook_res.status_code == 200
    res_data = webhook_res.json()
    assert res_data["success"] is True
    assert res_data["matched"] is False
    assert res_data["enquiry_id"] is None
    assert res_data["status"] == "UNMATCHED"
    reg_id = res_data["registration_id"]

    # Verify it appears in the UNMATCHED list
    unmatched_list = client.get("/api/v1/registrations?status=UNMATCHED").json()
    assert any(r["id"] == reg_id for r in unmatched_list)

    # Now staff creates or chooses an Enquiry to associate with
    enq_res = client.post("/api/v1/enquiries", json={
        "clientName": "Devendra Shah",
        "email": f"different.email.{uid}@domain.com",  # Client previously contacted from work email
        "phone": "+91 91234 56789",
        "enquirySource": "Phone"
    })
    target_enquiry_id = enq_res.json()["id"]

    # Staff links the unmatched registration
    assoc_res = client.post(f"/api/v1/registrations/{reg_id}/associate", json={
        "enquiryId": target_enquiry_id,
        "staffName": "Maharani Concierge Director"
    })
    assert assoc_res.status_code == 200
    assert assoc_res.json()["success"] is True
    assert assoc_res.json()["status"] == "SUBMITTED"

    # Verify Enquiry is now updated
    enq_after = client.get(f"/api/v1/enquiries/{target_enquiry_id}").json()
    assert enq_after["status"] == "Registration Submitted"
    assert enq_after["weddingLocation"] == "Alsisar Mahal, Shekhawati"
    assert enq_after["expectedGuestCount"] == 300


def test_google_forms_csv_import():
    """Verify staff can upload a Google Forms CSV file to batch-import responses."""
    uid = uuid.uuid4().hex[:6]
    csv_content = f"""Timestamp,Full Name,Partner's Full Name,Email,Phone,Current City / Address,Wedding Date,Wedding Destination / Location,Expected Guest Count,Estimated Budget,Wedding Events / Ceremonies,Preferred Theme / Aesthetic,Service Package,Special Requests / Preferences,Enquiry Reference ID
2026-10-31 14:00:00,Rohan Mehra,Isha Ambani,rohan.{uid}@mehra-textiles.com,+91 98765 43210,Delhi,2027-03-15,Taj Lake Palace Udaipur,500,₹ 5 Crores,"Sangeet, Pheras, Reception",Mughal Opulence,Full-Service,Waterfront palace mandap,
2026-10-31 14:05:00,Vikram Birla,Ananya Birla,vikram.{uid}@birla-group.in,+91 97654 32109,Mumbai,2027-04-20,City Palace Jaipur,350,₹ 3 Crores,"Haldi, Mehendi, Pheras",Regal Rajputana,Full-Service,Fireworks display,
"""
    files = {"file": ("google_forms_responses.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    import_res = client.post("/api/v1/registrations/import-csv", files=files)
    assert import_res.status_code == 200
    data = import_res.json()
    assert data["success"] is True
    stats = data["stats"]
    assert stats["total_rows"] == 2
    assert stats["imported"] == 2


def test_google_forms_approval_and_account_activation():
    """Verify staff reviews Google Form submission, approves, sends 72h activation email, and client activates account."""
    uid = uuid.uuid4().hex[:6]
    client_email = f"princess.dia.{uid}@royalknot.test"
    DEV_OUTBOX.clear()

    # 1. Enquiry created
    enq = client.post("/api/v1/enquiries", json={
        "clientName": "Dia Mirza",
        "email": client_email,
        "phone": "+91 99999 88888",
        "enquirySource": "Email",
        "weddingLocation": "Udaipur"
    }).json()
    enquiry_id = enq["id"]

    # 2. Client submits Google Form matching by email
    client.post("/api/v1/registrations/google-forms-webhook", json={
        "response_id": f"RESP-DIA-{uid}",
        "Timestamp": "2026-10-31 18:00:00",
        "Full Name": "Dia Mirza",
        "Partner's Full Name": "Vaibhav Rekhi",
        "Email": client_email,
        "Phone": "+91 99999 88888",
        "Wedding Date": "2027-05-10",
        "Wedding Destination / Location": "The Leela Palace Udaipur",
        "Expected Guest Count": "250",
        "Estimated Budget": "₹ 2 Crores",
        "Service Package": "Full-Service",
        "Preferences": "Private lakeside vows and acoustic Rajasthani folk music."
    })

    # 3. Staff reviews submission
    review_res = client.post(f"/api/v1/enquiries/{enquiry_id}/registration/review", json={
        "reviewedBy": "Senior Concierge Director",
        "notes": "Excellent celebration aesthetic. Palace availability verified for May 2027."
    })
    assert review_res.status_code == 200
    assert review_res.json()["status"] == "UNDER_REVIEW"

    # 4. Staff approves registration -> Client record created, UserAccount created, activation email sent
    approve_res = client.post(f"/api/v1/enquiries/{enquiry_id}/registration/approve", json={
        "reviewedBy": "Senior Concierge Director"
    })
    assert approve_res.status_code == 200
    approve_data = approve_res.json()
    assert approve_data["success"] is True
    client_id = approve_data["client_id"]
    activation_token = approve_data["activation_token"]
    assert client_id.startswith("TRK-2026-")

    # Verify activation email was sent
    act_emails = [e for e in DEV_OUTBOX if e["to"] == client_email and "Activate" in e["subject"]]
    assert len(act_emails) >= 1
    act_email = act_emails[-1]
    assert activation_token in act_email["html"]
    assert client_id in act_email["html"]

    # 5. Client activates account by setting password
    activate_res = client.post("/api/v1/auth/activate", json={
        "token": activation_token,
        "password": "RoyalKnotPassword2026!",
        "confirmPassword": "RoyalKnotPassword2026!"
    })
    assert activate_res.status_code == 200
    assert activate_res.json()["success"] is True

    # 6. Client logs in with their credentials
    login_res = client.post("/api/v1/auth/login", json={
        "email": client_email,
        "password": "RoyalKnotPassword2026!"
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["success"] is True
    assert login_data["clientId"] == client_id
    assert login_data["role"] == "client"
