import uuid
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.client import Client
from app.models.project import WeddingProject, WeddingFunction, ProjectMilestone, ProjectStatusHistory
from app.database.session import SessionLocal

client = TestClient(app)


def test_phase3_full_wedding_project_lifecycle():
    """
    Comprehensive Phase 3 Test Suite:
    1. Eligible bookings listing (only status == 'Confirmed' without projects).
    2. Project creation from confirmed client booking.
    3. Auto-generation of unique sequential project code (PRJ-YYYY-XXX).
    4. Auto-seeding of 5 destination wedding milestones & initial status history.
    5. Rejection of unconfirmed client booking (status != 'Confirmed').
    6. Strict prevention of duplicate projects for the same client.
    7. Exclusion of client from eligible bookings once project is created.
    8. Project listing with search, status filtering, and progress metrics.
    9. Wedding functions CRUD (add, update, delete).
    10. Project milestones tracking (add, toggle completion, set completed_at).
    11. Project metadata update.
    12. Status lifecycle transitions and audit history logging.
    """
    db = SessionLocal()
    uid = uuid.uuid4().hex[:6]

    # --- Setup: Create 1 Confirmed Client and 1 Unconfirmed Client ---
    confirmed_client_id = f"TRK-2026-TEST-{uid}A"
    unconfirmed_client_id = f"TRK-2026-TEST-{uid}B"

    client_confirmed = Client(
        id=confirmed_client_id,
        partner1_name="Princess Ananya Singhania",
        partner2_name="Veerendra Rathore",
        email=f"ananya.{uid}@heritage-test.in",
        phone="+91 98201 11223",
        wedding_date=date(2027, 2, 14),
        wedding_location="The Leela Palace, Udaipur",
        expected_guest_count=450,
        estimated_budget=Decimal("25000000.00"),
        wedding_theme="Lake Pichola Royal Splendor",
        service_package="Full-Service",
        enquiry_source="Email",
        status="Confirmed"
    )

    client_unconfirmed = Client(
        id=unconfirmed_client_id,
        partner1_name="Rohan Varma",
        partner2_name="Samaira Deshmukh",
        email=f"rohan.{uid}@test.in",
        phone="+91 98201 44556",
        wedding_date=date(2027, 3, 20),
        wedding_location="Rambagh Palace, Jaipur",
        expected_guest_count=200,
        estimated_budget=Decimal("9500000.00"),
        wedding_theme="Fortress Candlelight",
        service_package="Partial-Service",
        enquiry_source="Phone",
        status="Enquiry"  # NOT confirmed
    )

    db.add(client_confirmed)
    db.add(client_unconfirmed)
    db.commit()
    db.close()

    # --- Step 1: Check Eligible Bookings API ---
    res_eligible = client.get("/api/v1/projects/eligible-bookings")
    assert res_eligible.status_code == 200
    eligible_list = res_eligible.json()
    eligible_ids = [item["clientId"] for item in eligible_list]

    assert confirmed_client_id in eligible_ids
    assert unconfirmed_client_id not in eligible_ids

    # --- Step 2: Rejection of Unconfirmed Client ---
    res_reject = client.post("/api/v1/projects", json={
        "clientId": unconfirmed_client_id,
        "projectName": "Invalid Unconfirmed Project"
    })
    assert res_reject.status_code == 400
    assert "Only confirmed bookings" in res_reject.json()["detail"]

    # --- Step 3: Successfully Create Wedding Project from Confirmed Booking ---
    create_payload = {
        "clientId": confirmed_client_id,
        "projectName": "Ananya & Veerendra Palace Wedding",
        "projectManagerName": "Maharani Gayatri Singh",
        "notes": "VIP security clearance required for lakeside pavilion."
    }
    res_create = client.post("/api/v1/projects", json=create_payload)
    assert res_create.status_code == 201
    project_data = res_create.json()

    project_id = project_data["id"]
    project_code = project_data["projectCode"]

    assert project_code.startswith("PRJ-2027-") or project_code.startswith("PRJ-")
    assert project_data["clientId"] == confirmed_client_id
    assert project_data["status"] == "Planning"
    assert project_data["guestCount"] == 450
    assert project_data["location"] == "The Leela Palace, Udaipur"
    assert Decimal(str(project_data["estimatedBudget"])) == Decimal("25000000")

    # Verify default milestones were seeded
    assert len(project_data["milestones"]) >= 5
    # Verify initial status history was logged
    assert len(project_data["statusHistory"]) >= 1
    assert project_data["statusHistory"][0]["newStatus"] == "Planning"

    # --- Step 4: Strict Duplicate Prevention ---
    res_dup = client.post("/api/v1/projects", json={
        "clientId": confirmed_client_id,
        "projectName": "Duplicate Attempt"
    })
    assert res_dup.status_code == 400
    assert "already been created" in res_dup.json()["detail"]

    # Confirmed client should now be absent from eligible bookings
    res_eligible_after = client.get("/api/v1/projects/eligible-bookings")
    assert confirmed_client_id not in [item["clientId"] for item in res_eligible_after.json()]

    # --- Step 5: List Projects & Search ---
    res_list = client.get("/api/v1/projects", params={"search": "Ananya", "status": "Planning"})
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["total"] >= 1
    found_item = next((p for p in list_data["items"] if p["id"] == project_id), None)
    assert found_item is not None
    assert found_item["projectCode"] == project_code
    assert found_item["totalMilestonesCount"] >= 5

    # --- Step 6: Retrieve Project Details ---
    res_detail = client.get(f"/api/v1/projects/{project_id}")
    assert res_detail.status_code == 200
    detail_data = res_detail.json()
    assert detail_data["coupleName"] == "Princess Ananya Singhania & Veerendra Rathore"
    assert detail_data["client"]["email"] == f"ananya.{uid}@heritage-test.in"

    # --- Step 7: Add Wedding Functions ---
    func1_payload = {
        "functionName": "Royal Sangeet & Sufi Night",
        "functionDate": "2027-02-13",
        "startTime": "18:00",
        "endTime": "23:30",
        "venue": "Manek Chowk Courtyard",
        "description": "Acoustic folk instruments and candlelit palace stage.",
        "status": "Scheduled"
    }
    res_f1 = client.post(f"/api/v1/projects/{project_id}/functions", json=func1_payload)
    assert res_f1.status_code == 201
    f1_data = res_f1.json()
    f1_id = f1_data["id"]
    assert f1_data["functionName"] == "Royal Sangeet & Sufi Night"

    func2_payload = {
        "functionName": "Royal Varmala & Pheras",
        "functionDate": "2027-02-14",
        "startTime": "16:30",
        "endTime": "21:00",
        "venue": "Lake Pichola Floating Mandap",
        "status": "Scheduled"
    }
    res_f2 = client.post(f"/api/v1/projects/{project_id}/functions", json=func2_payload)
    assert res_f2.status_code == 201
    f2_id = res_f2.json()["id"]

    # Verify functions are listed in project details
    res_detail_funcs = client.get(f"/api/v1/projects/{project_id}")
    assert len(res_detail_funcs.json()["functions"]) == 2

    # Update function
    res_update_f = client.put(f"/api/v1/projects/{project_id}/functions/{f1_id}", json={
        "venue": "Zenana Mahal Courtyard",
        "status": "In Progress"
    })
    assert res_update_f.status_code == 200
    assert res_update_f.json()["venue"] == "Zenana Mahal Courtyard"
    assert res_update_f.json()["status"] == "In Progress"

    # --- Step 8: Milestone Management & Progress Toggle ---
    ms_payload = {
        "milestoneName": "Approve Master Flower Shipment from Holland",
        "dueDate": "2027-01-30",
        "description": "Exotic orchids and white hydrangeas.",
        "status": "Pending"
    }
    res_ms = client.post(f"/api/v1/projects/{project_id}/milestones", json=ms_payload)
    assert res_ms.status_code == 201
    ms_id = res_ms.json()["id"]

    # Toggle milestone to Completed
    res_toggle_ms = client.put(f"/api/v1/projects/{project_id}/milestones/{ms_id}", json={
        "status": "Completed"
    })
    assert res_toggle_ms.status_code == 200
    updated_ms = res_toggle_ms.json()
    assert updated_ms["status"] == "Completed"
    assert updated_ms["completedAt"] is not None

    # --- Step 9: Update Project Metadata ---
    res_meta = client.put(f"/api/v1/projects/{project_id}", json={
        "guestCount": 500,
        "notes": "Updated guest count per royal protocol office."
    })
    assert res_meta.status_code == 200
    assert res_meta.json()["guestCount"] == 500

    # --- Step 10: Status Progression & History Logging ---
    # Transition 1: Planning -> In Progress
    res_status1 = client.patch(f"/api/v1/projects/{project_id}/status", json={
        "status": "In Progress",
        "changedBy": "Maharani Gayatri Singh",
        "notes": "Palace production team dispatched to Udaipur."
    })
    assert res_status1.status_code == 200
    assert res_status1.json()["status"] == "In Progress"

    # Transition 2: In Progress -> Completed
    res_status2 = client.patch(f"/api/v1/projects/{project_id}/status", json={
        "status": "Completed",
        "changedBy": "Maharani Gayatri Singh",
        "notes": "Wedding executed successfully. Production wrap finalized."
    })
    assert res_status2.status_code == 200
    assert res_status2.json()["status"] == "Completed"

    # Verify audit history
    history = res_status2.json()["statusHistory"]
    assert len(history) >= 3  # Initial Planning, Planning->In Progress, In Progress->Completed
    newest = history[0]
    assert newest["newStatus"] == "Completed"
    assert newest["oldStatus"] == "In Progress"
    assert "Production wrap" in newest["notes"]

    # --- Step 11: Cleanup/Delete Function & Milestone ---
    del_func = client.delete(f"/api/v1/projects/{project_id}/functions/{f2_id}")
    assert del_func.status_code == 200

    del_ms = client.delete(f"/api/v1/projects/{project_id}/milestones/{ms_id}")
    assert del_ms.status_code == 200

    res_final = client.get(f"/api/v1/projects/{project_id}")
    assert len(res_final.json()["functions"]) == 1

