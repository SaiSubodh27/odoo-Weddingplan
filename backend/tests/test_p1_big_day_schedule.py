import uuid
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.client import Client
from app.models.vendor import Vendor
from app.models.project import WeddingProject, BigDayScheduleEvent

client = TestClient(app)


def test_big_day_live_schedule_and_checkin(db_session):
    """
    P1 Item 5 Verification:
    - Live schedule with times and owners
    - Vendor check-in (arrived_at)
    - Late flag when now > expected + grace and not arrived
    - 30s polling summary payload (total, arrived, late, pending)
    """
    uid = uuid.uuid4().hex[:6].upper()
    client_id = f"CL-BD-{uid}"
    project_id = f"PRJ-BD-{uid}"
    project_code = f"PRJ-2026-{uid}"

    # 1. Setup client and project
    db_client = Client(
        id=client_id,
        partner1_name="Vikram",
        partner2_name="Rhea",
        email=f"vikram.rhea.{uid}@example.com",
        phone="+919876543213",
        wedding_date=date.today(),
        wedding_location="Rambagh Palace, Jaipur",
        expected_guest_count=450,
        estimated_budget=Decimal("60000000.00"),
        service_package="Full-Service Planning",
        status="Confirmed"
    )
    project = WeddingProject(
        id=project_id,
        project_code=project_code,
        client_id=client_id,
        project_name="Vikram & Rhea Royal Jaipur Big Day",
        wedding_date=date.today(),
        location="Rambagh Palace, Jaipur",
        guest_count=450,
        estimated_budget=Decimal("60000000.00"),
        status="In Progress",
        deposit_paid=True
    )
    v1 = Vendor(
        id=f"VND-DJ-{uid}",
        name=f"DJ Shadow Dubai Sound {uid}",
        category="Entertainment",
        email=f"dj.{uid}@example.com",
        phone="+919876543214"
    )
    v2 = Vendor(
        id=f"VND-CAT-{uid}",
        name=f"Rajputana Royal Feast {uid}",
        category="Catering",
        email=f"cater.{uid}@example.com",
        phone="+919876543215"
    )
    db_session.add_all([db_client, project, v1, v2])
    db_session.commit()

    now = datetime.now(timezone.utc)

    # 2. Add Event 1: On-time event (expected in 2 hours)
    e1_resp = client.post(
        f"/api/v1/projects/{project_id}/big-day/schedule",
        json={
            "title": "Evening Baraat Assembly & Royal Elephants",
            "eventTime": "17:30",
            "expectedArrivalTime": (now + timedelta(hours=2)).isoformat(),
            "ownerName": "Maharani Gayatri Singh",
            "vendorId": v1.id,
            "vendorName": v1.name,
            "gracePeriodMinutes": 15,
            "notes": "Assemble outside South Gate."
        }
    )
    assert e1_resp.status_code == 201, e1_resp.text
    ev1_id = e1_resp.json()["id"]

    # 3. Add Event 2: LATE EVENT! Expected 45 minutes ago with 15 min grace (now > expected + 15m)
    past_expected = now - timedelta(minutes=45)
    e2_resp = client.post(
        f"/api/v1/projects/{project_id}/big-day/schedule",
        json={
            "title": "DJ Line-Array Trussing & Sound Console Setup",
            "eventTime": "15:00",
            "expectedArrivalTime": past_expected.isoformat(),
            "ownerName": "Raghav Sharma",
            "vendorId": v1.id,
            "vendorName": v1.name,
            "gracePeriodMinutes": 15,
            "notes": "Sound check must conclude before guest arrivals."
        }
    )
    assert e2_resp.status_code == 201
    ev2_id = e2_resp.json()["id"]

    # 4. Add Event 3: Already checked-in event
    e3_resp = client.post(
        f"/api/v1/projects/{project_id}/big-day/schedule",
        json={
            "title": "Catering Live Chaat Station Preparation",
            "eventTime": "14:00",
            "expectedArrivalTime": (now - timedelta(hours=1)).isoformat(),
            "ownerName": "Pooja Verma",
            "vendorId": v2.id,
            "vendorName": v2.name,
            "gracePeriodMinutes": 15,
            "notes": "Food hygiene audit complete."
        }
    )
    assert e3_resp.status_code == 201
    ev3_id = e3_resp.json()["id"]

    # Check-in Event 3 immediately
    chk3 = client.post(f"/api/v1/projects/{project_id}/big-day/events/{ev3_id}/check-in")
    assert chk3.status_code == 200
    assert chk3.json()["status"] == "Arrived"
    assert chk3.json()["arrivedAt"] is not None

    # 5. Fetch Live Schedule (30s polling endpoint)
    sched_resp = client.get(f"/api/v1/projects/{project_id}/big-day/schedule")
    assert sched_resp.status_code == 200, sched_resp.text
    sched_data = sched_resp.json()

    assert sched_data["totalEvents"] == 3
    assert sched_data["arrivedCount"] == 1
    assert sched_data["lateCount"] == 1
    assert sched_data["pendingCount"] == 2

    # Check late event flags
    ev2_item = next(e for e in sched_data["events"] if e["id"] == ev2_id)
    assert ev2_item["isLate"] is True
    assert ev2_item["status"] == "Late"
    assert ev2_item["minutesLate"] >= 30  # 45m past expected - 15m grace = 30m late

    # Check future event flags
    ev1_item = next(e for e in sched_data["events"] if e["id"] == ev1_id)
    assert ev1_item["isLate"] is False
    assert ev1_item["status"] == "Scheduled"

    # 6. Check-in the Late Vendor and verify Late flag clears
    chk2 = client.post(f"/api/v1/projects/{project_id}/big-day/events/{ev2_id}/check-in")
    assert chk2.status_code == 200
    assert chk2.json()["status"] == "Arrived"
    assert chk2.json()["arrivedAt"] is not None

    # Re-fetch schedule
    sched_after = client.get(f"/api/v1/projects/{project_id}/big-day/schedule").json()
    assert sched_after["arrivedCount"] == 2
    assert sched_after["lateCount"] == 0
    ev2_cleared = next(e for e in sched_after["events"] if e["id"] == ev2_id)
    assert ev2_cleared["isLate"] is False
    assert ev2_cleared["status"] == "Arrived"
