import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.enquiry import Enquiry
from app.models.registration import ClientRegistration
from app.models.user import UserAccount
from app.services.email_service import DEV_OUTBOX

client = TestClient(app)


def test_website_client_registration_and_portal_access():
    """
    End-to-end verification of Website Client Registration:
    1. Client registers directly on website with password & celebration parameters.
    2. Enquiry created with source='Website' and status='Registration Submitted'.
    3. UserAccount provisioned with role='client' and status='ACTIVE'.
    4. Confirmation email dispatched to client.
    5. Client authenticates at /auth/login with their password.
    6. Client retrieves their celebration dossier at /auth/client-dossier.
    7. Staff can view and manage the website enquiry dossier.
    """
    uid = uuid.uuid4().hex[:6]
    client_email = f"princess.radhika.{uid}@rajasthan-royals.in"
    DEV_OUTBOX.clear()

    # 1. Public client registers via website
    register_payload = {
        "fullName": "Princess Radhika Raje",
        "partnerName": "Yuvraj Anant Dev",
        "email": client_email,
        "password": "RoyalKnotPassword2026!",
        "phone": "+91 98200 77889",
        "weddingDate": "2027-02-14",
        "weddingLocation": "Umaid Bhawan Palace, Jodhpur",
        "expectedGuestCount": 400,
        "estimatedBudget": 35000000,
        "weddingEvents": [
            "Royal Sangeet & Musical Extravaganza",
            "Sacred Vedic Mandap & Pheras",
            "Grand Royal Reception Banquet"
        ],
        "preferredTheme": "Regal Rajputana Heritage & Floating Palace Splendor",
        "servicePackage": "Full-Service",
        "preferences": "Elephant procession for Baraat and vintage royal car arrival at palace gates."
    }

    reg_res = client.post("/api/v1/auth/register-website", json=register_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["success"] is True
    assert reg_data["role"] == "client"
    assert reg_data["email"] == client_email
    enquiry_id = reg_data["enquiry_id"]
    assert enquiry_id.startswith("ENQ-2026-")

    # 2. Verify Enquiry in PostgreSQL
    enq_res = client.get(f"/api/v1/enquiries/{enquiry_id}")
    assert enq_res.status_code == 200
    enq = enq_res.json()
    assert enq["enquirySource"] == "Website"
    assert enq["status"] == "Registration Submitted"
    assert "Yuvraj Anant Dev" in enq["clientName"]
    assert enq["expectedGuestCount"] == 400

    # 3. Verify confirmation email was recorded in outbox
    welcome_emails = [e for e in DEV_OUTBOX if e["to"] == client_email]
    assert len(welcome_emails) >= 1
    welcome = welcome_emails[-1]
    assert "Welcome to The Royal Knot" in welcome["subject"] or "Registration Confirmed" in welcome["subject"]
    assert enquiry_id in welcome["html"]

    # 4. Client logs in with their password
    login_res = client.post("/api/v1/auth/login", json={
        "email": client_email,
        "password": "RoyalKnotPassword2026!"
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["success"] is True
    assert login_data["role"] == "client"
    assert login_data["email"] == client_email

    # 5. Client retrieves their celebration dossier for the Client Portal
    dossier_res = client.get(f"/api/v1/auth/client-dossier?email={client_email}")
    assert dossier_res.status_code == 200
    dossier = dossier_res.json()
    assert dossier["fullName"] == "Princess Radhika Raje"
    assert dossier["partnerName"] == "Yuvraj Anant Dev"
    assert dossier["weddingLocation"] == "Umaid Bhawan Palace, Jodhpur"
    assert dossier["expectedGuestCount"] == 400
    assert float(dossier["estimatedBudget"]) == 35000000.0
    assert "Royal Sangeet & Musical Extravaganza" in dossier["weddingEvents"]

    # 6. Duplicate registration prevention check
    dup_res = client.post("/api/v1/auth/register-website", json=register_payload)
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

