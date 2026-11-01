import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.client import Client
from app.models.project import WeddingProject, PlanningTask, PaymentStage

client = TestClient(app)


def test_deposit_paid_generates_tasks_and_stages_idempotent(db_session):
    """
    P0 Item 3 Verification:
    - Marking deposit paid generates 25+ tasks from package template (Full: 28, Partial: 25)
    - Covers Venue, Design, Vendors, Mehendi, Sangeet, Wedding Day, Reception
    - Each task has an owner and stage
    - 3 payment stages created: advance due = wedding_date - 30 days, final after event
    - Idempotent: replaying deposit_paid creates no duplicate tasks or payment stages
    """
    uid = uuid.uuid4().hex[:6].upper()
    client_id = f"CL-DEP-{uid}"
    project_id = f"PRJ-DEP-{uid}"
    project_code = f"PRJ-2026-{uid}"

    # 1. Create client and project
    wedding_target_date = date.today() + timedelta(days=120)
    db_client = Client(
        id=client_id,
        partner1_name="Aarav",
        partner2_name="Meera",
        email=f"aarav.meera.{uid}@example.com",
        phone="+919876543210",
        wedding_date=wedding_target_date,
        wedding_location="City Palace, Udaipur",
        expected_guest_count=400,
        estimated_budget=Decimal("50000000.00"),
        service_package="Full-Service Planning",
        status="Confirmed"
    )
    db_session.add(db_client)

    project = WeddingProject(
        id=project_id,
        project_code=project_code,
        client_id=client_id,
        project_name="Aarav & Meera Royal Destination Wedding",
        wedding_date=wedding_target_date,
        location="City Palace, Udaipur",
        guest_count=400,
        estimated_budget=Decimal("50000000.00"),
        package_tier="Full-Service",
        status="Planning",
        deposit_paid=False
    )
    db_session.add(project)
    db_session.commit()

    # 2. Trigger deposit-paid via API
    resp = client.post(f"/api/v1/projects/{project_id}/deposit-paid")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["depositPaid"] is True
    assert data["tasksCount"] == 28  # Full package has 28 tasks >= 25
    assert data["paymentStagesCount"] == 3

    # 3. Verify tasks in DB
    tasks = db_session.query(PlanningTask).filter_by(project_id=project_id).all()
    assert len(tasks) == 28

    categories = {t.category for t in tasks}
    required_categories = {"Venue", "Design", "Vendors", "Mehendi", "Sangeet", "Wedding Day", "Reception"}
    assert required_categories.issubset(categories), f"Missing categories: {required_categories - categories}"

    for t in tasks:
        assert t.assigned_to is not None and len(t.assigned_to) > 0
        assert t.stage in ["To Plan", "In Progress", "Review", "Done"]
        assert t.due_date is not None

    # 4. Verify 3 Payment Stages
    stages = db_session.query(PaymentStage).filter_by(project_id=project_id).order_by(PaymentStage.due_date.asc()).all()
    assert len(stages) == 3

    # Retainer: 25%, Paid
    retainer = next(s for s in stages if "Retainer" in s.stage_name)
    assert retainer.percentage == Decimal("25.00")
    assert retainer.amount == Decimal("12500000.00")  # 25% of 5 Cr
    assert retainer.status == "Paid"
    assert retainer.paid_at is not None

    # Advance due = wedding date - 30 days
    advance = next(s for s in stages if "Advance" in s.stage_name)
    assert advance.percentage == Decimal("40.00")
    assert advance.amount == Decimal("20000000.00")  # 40% of 5 Cr
    assert advance.due_date == wedding_target_date - timedelta(days=30)
    assert advance.status == "Pending"

    # Final post-event = wedding date + 3 days
    final_stage = next(s for s in stages if "Final" in s.stage_name)
    assert final_stage.percentage == Decimal("35.00")
    assert final_stage.amount == Decimal("17500000.00")  # 35% of 5 Cr
    assert final_stage.due_date == wedding_target_date + timedelta(days=3)
    assert final_stage.status == "Pending"

    # 5. IDEMPOTENCY TEST: Replay deposit-paid API call
    replay_resp = client.post(f"/api/v1/projects/{project_id}/deposit-paid")
    assert replay_resp.status_code == 200
    replay_data = replay_resp.json()

    assert replay_data["tasksCount"] == 28  # Unchanged!
    assert replay_data["paymentStagesCount"] == 3  # Unchanged!

    tasks_after_replay = db_session.query(PlanningTask).filter_by(project_id=project_id).all()
    assert len(tasks_after_replay) == 28, "Duplicate tasks were created during replay!"

    stages_after_replay = db_session.query(PaymentStage).filter_by(project_id=project_id).all()
    assert len(stages_after_replay) == 3, "Duplicate payment stages were created during replay!"

    # 6. Test Task Stage Progression (To Plan -> In Progress -> Done)
    first_task = tasks[0]
    patch_resp = client.patch(
        f"/api/v1/projects/{project_id}/tasks/{first_task.id}",
        json={"stage": "In Progress"}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["stage"] == "In Progress"

    patch_done_resp = client.patch(
        f"/api/v1/projects/{project_id}/tasks/{first_task.id}",
        json={"stage": "Done"}
    )
    assert patch_done_resp.status_code == 200
    assert patch_done_resp.json()["stage"] == "Done"
    assert patch_done_resp.json()["isCompleted"] is True
    assert patch_done_resp.json()["completedAt"] is not None


def test_partial_package_generates_25_tasks(db_session):
    """Verify partial package tier generates at least 25 tasks."""
    uid = uuid.uuid4().hex[:6].upper()
    client_id = f"CL-PART-{uid}"
    project_id = f"PRJ-PART-{uid}"
    project_code = f"PRJ-2026-{uid}"

    wedding_target_date = date.today() + timedelta(days=90)
    db_client = Client(
        id=client_id,
        partner1_name="Kabir",
        partner2_name="Ananya",
        email=f"kabir.ananya.{uid}@example.com",
        phone="+919876543211",
        wedding_date=wedding_target_date,
        wedding_location="Taj Lake Palace, Udaipur",
        expected_guest_count=250,
        estimated_budget=Decimal("25000000.00"),
        service_package="Partial Planning",
        status="Confirmed"
    )
    db_session.add(db_client)

    project = WeddingProject(
        id=project_id,
        project_code=project_code,
        client_id=client_id,
        project_name="Kabir & Ananya Lake Palace Wedding",
        wedding_date=wedding_target_date,
        location="Taj Lake Palace, Udaipur",
        guest_count=250,
        estimated_budget=Decimal("25000000.00"),
        package_tier="Partial Planning",
        status="Planning"
    )
    db_session.add(project)
    db_session.commit()

    resp = client.post(f"/api/v1/projects/{project_id}/deposit-paid")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tasksCount"] == 25
    assert data["paymentStagesCount"] == 3
