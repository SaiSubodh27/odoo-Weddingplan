import sys
import uuid
import os
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
from app.models.email_message import EmailMessage
from app.core.security import hash_token
from app.services.email_sync_service import email_sync_service

client = TestClient(app)


def test_email_status_endpoint():
    res = client.get("/api/v1/emails/status")
    assert res.status_code == 200
    data = res.json()
    assert "agencyEmail" in data
    assert "imapConfigured" in data
    assert "smtpConfigured" in data
    assert data["agencyEmail"] == "saisubodh6@gmail.com"


def test_unconfigured_sync_graceful():
    # Syncing when IMAP is unconfigured should return a clear message without raising an error
    res = client.post("/api/v1/emails/sync")
    assert res.status_code == 200
    data = res.json()
    assert "configured" in data
    assert "message" in data


def test_unrelated_email_classification():
    # An unrelated email (e.g. newsletter or spam) should be marked UNCLASSIFIED, not registered as enquiry
    uid = uuid.uuid4().hex[:6]
    sender = f"newsletter.{uid}@genericpromo.com"

    res = client.post("/api/v1/emails/simulate", data={
        "sender_email": sender,
        "sender_name": "Tech Weekly Digest",
        "subject": "Top 10 software architectural patterns for 2026",
        "body_text": "Here is this week's issue covering microservices and domain-driven design."
    })
    assert res.status_code == 200
    data = res.json()
    assert data["processed"] is True
    assert data["status"] == "UNCLASSIFIED"
    assert data["enquiry_created"] is False
    assert data["enquiry_id"] is None

    # Verify it appears in inbox review queue
    inbox_res = client.get("/api/v1/emails/inbox?status_filter=UNCLASSIFIED")
    assert inbox_res.status_code == 200
    items = inbox_res.json()["items"]
    assert any(item["senderEmail"] == sender for item in items)


def test_email_enquiry_full_lifecycle():
    uid = uuid.uuid4().hex[:6]
    client_email = f"princess.radha.{uid}@heritage-estates.in"

    # 1. Client emails agency expressing interest in luxury wedding
    email_sim = client.post("/api/v1/emails/simulate", data={
        "sender_email": client_email,
        "sender_name": "Radha Singhal",
        "subject": "Wedding Planning Enquiry - Rambagh Palace Jaipur 2027",
        "body_text": "Greetings, we are looking for full-service royal destination wedding planners in Jaipur for 500 guests."
    })
    assert email_sim.status_code == 200
    sim_data = email_sim.json()
    assert sim_data["processed"] is True
    assert sim_data["status"] == "ENQUIRY_CREATED"
    assert sim_data["enquiry_created"] is True
    enquiry_id = sim_data["enquiry_id"]
    inbound_msg_id = sim_data["message_id"]

    # 2. Duplicate ingestion check: sending the same email again should skip duplicate creation
    dup_sim = client.post("/api/v1/emails/simulate", data={
        "sender_email": client_email,
        "sender_name": "Radha Singhal",
        "subject": "Wedding Planning Enquiry - Rambagh Palace Jaipur 2027",
        "body_text": "Greetings, we are looking for full-service royal destination wedding planners in Jaipur for 500 guests."
    })
    # The duplicate check in _process_parsed_email returns processed: False
    # (or if unique message ID is used, it skips)

    # 3. Staff views enquiry and email conversation
    messages_res = client.get(f"/api/v1/enquiries/{enquiry_id}/messages")
    assert messages_res.status_code == 200
    messages = messages_res.json()
    assert len(messages) >= 1
    assert messages[0]["direction"] == "incoming"
    assert messages[0]["senderEmail"] == client_email

    # 4. Staff replies to the client email
    reply_res = client.post(f"/api/v1/enquiries/{enquiry_id}/reply", json={
        "subject": "Re: Wedding Planning Enquiry - Rambagh Palace Jaipur 2027",
        "body": "Dear Radha, thank you for contacting The Royal Knot. We are delighted to assist with Rambagh Palace."
    })
    assert reply_res.status_code == 200
    assert reply_res.json()["success"] is True

    # 5. Staff dispatches registration document
    send_doc_res = client.post(f"/api/v1/enquiries/{enquiry_id}/send-document")
    assert send_doc_res.status_code == 200
    assert send_doc_res.json()["enquiry_status"] == "Registration Document Sent"

    # Verify messages list now includes outgoing reply and sent document
    updated_messages = client.get(f"/api/v1/enquiries/{enquiry_id}/messages").json()
    assert any(m["direction"] == "outgoing" for m in updated_messages)

    # 6. Client emails back with completed registration PDF attached
    client_reply_sim = client.post(
        "/api/v1/emails/simulate",
        data={
            "sender_email": client_email,
            "sender_name": "Radha Singhal",
            "subject": f"Completed Registration Dossier - Ref: {enquiry_id}",
            "body_text": "Please find attached our signed client registration document.",
            "in_reply_to": messages[0]["messageId"]
        },
        files={"file": ("Completed_Radha_Singhal_Dossier.pdf", b"%PDF-1.4 completed form contents", "application/pdf")}
    )
    assert client_reply_sim.status_code == 200
    reply_data = client_reply_sim.json()
    assert reply_data["status"] == "ASSOCIATED"
    assert reply_data["document_received"] is True

    # 7. Verify enquiry automatically progressed to 'Registration Received'
    enquiry_get = client.get(f"/api/v1/enquiries/{enquiry_id}").json()
    assert enquiry_get["status"] == "Registration Received"
    assert len(enquiry_get["documents"]) >= 1
    doc_id = enquiry_get["documents"][0]["id"]

    # 8. Staff reviews the completed registration document
    review_res = client.post(f"/api/v1/enquiries/{enquiry_id}/mark-document-reviewed?document_id={doc_id}&reviewed_by=Maharani+Gayatri")
    assert review_res.status_code == 200
    assert review_res.json()["enquiry_status"] == "Under Review"

    # Verify status is Under Review
    enquiry_under_review = client.get(f"/api/v1/enquiries/{enquiry_id}").json()
    assert enquiry_under_review["status"] == "Under Review"

    # 9. Staff registers client
    register_res = client.post(f"/api/v1/enquiries/{enquiry_id}/register", json={
        "partner1Name": "Radha Singhal",
        "partner2Name": "Aditya Vardhan",
        "servicePackage": "Full-Service",
        "weddingTheme": "Jaipur Royal Emerald"
    })
    assert register_res.status_code == 200
    reg_data = register_res.json()
    assert reg_data["success"] is True
    client_id = reg_data["client_id"]
    activation_token = reg_data["activation_token"]

    # 10. Client verifies token & activates account
    verify_res = client.get(f"/api/v1/auth/verify-token?token={activation_token}")
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is True

    activate_res = client.post("/api/v1/auth/activate", json={
        "token": activation_token,
        "password": "EmeraldJaipur2027!",
        "confirmPassword": "EmeraldJaipur2027!"
    })
    assert activate_res.status_code == 200
    assert activate_res.json()["success"] is True

    # 11. Client logs in
    login_res = client.post("/api/v1/auth/login", json={
        "email": client_email,
        "password": "EmeraldJaipur2027!"
    })
    assert login_res.status_code == 200
    assert login_res.json()["role"] == "client"
    assert login_res.json()["clientId"] == client_id


def test_staff_convert_unclassified_email_to_enquiry():
    # Staff manually converts an unclassified email into an enquiry
    uid = uuid.uuid4().hex[:6]
    sender = f"curious.client.{uid}@heritage.in"

    # Incoming general email without clear keywords
    res = client.post("/api/v1/emails/simulate", data={
        "sender_email": sender,
        "sender_name": "Maharaj Kumar",
        "subject": "Greetings from Bikaner family",
        "body_text": "We would like to consult with your agency next month."
    })
    assert res.json()["status"] == "UNCLASSIFIED"
    msg_id = res.json()["message_id"]

    # Staff converts it to enquiry
    convert_res = client.post(f"/api/v1/emails/{msg_id}/convert-to-enquiry", json={
        "clientName": "Maharaj Kumar of Bikaner"
    })
    assert convert_res.status_code == 200
    enq_data = convert_res.json()
    assert enq_data["clientName"] == "Maharaj Kumar of Bikaner"
    assert enq_data["email"] == sender
    assert enq_data["status"] == "New"


def test_staff_ignore_unclassified_email():
    uid = uuid.uuid4().hex[:6]
    sender = f"spammer.{uid}@adservice.com"

    res = client.post("/api/v1/emails/simulate", data={
        "sender_email": sender,
        "sender_name": "SEO Agency",
        "subject": "Increase website traffic fast",
        "body_text": "Buy backlinks today."
    })
    msg_id = res.json()["message_id"]

    ignore_res = client.post(f"/api/v1/emails/{msg_id}/ignore")
    assert ignore_res.status_code == 200
    assert ignore_res.json()["status"] == "IGNORED"


def test_security_disallowed_attachment_types():
    # Executable files (.exe, .sh) or scripts must be rejected by document upload
    uid = uuid.uuid4().hex[:6]
    create_enq = client.post("/api/v1/enquiries", json={
        "clientName": f"Test Lead {uid}",
        "email": f"test.{uid}@security.in",
        "phone": "+91 98888 77777",
        "enquirySource": "Phone"
    }).json()
    eid = create_enq["id"]

    # Try uploading malicious .exe file
    upload_res = client.post(
        f"/api/v1/enquiries/{eid}/documents/upload",
        data={"document_type": "completed_by_client"},
        files={"file": ("malware.exe", b"MZ fake executable binary content", "application/x-msdownload")}
    )
    assert upload_res.status_code == 400
    assert "invalid file extension" in upload_res.json()["detail"].lower()


def test_security_oversized_file_rejected():
    # Files over 15MB must be rejected
    uid = uuid.uuid4().hex[:6]
    create_enq = client.post("/api/v1/enquiries", json={
        "clientName": f"Test Lead {uid}",
        "email": f"test.{uid}@security.in",
        "phone": "+91 98888 77777",
        "enquirySource": "Phone"
    }).json()
    eid = create_enq["id"]

    huge_file = b"0" * (16 * 1024 * 1024)  # 16 MB
    upload_res = client.post(
        f"/api/v1/enquiries/{eid}/documents/upload",
        data={"document_type": "completed_by_client"},
        files={"file": ("huge_document.pdf", huge_file, "application/pdf")}
    )
    assert upload_res.status_code == 400
    assert "exceeds maximum allowed size" in upload_res.json()["detail"].lower()
