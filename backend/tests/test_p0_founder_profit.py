import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.client import Client
from app.models.vendor import Vendor
from app.models.project import WeddingProject, ProjectVendor, PaymentStage, TeamTimeEntry

client = TestClient(app)


def test_founder_profit_per_wedding(db_session):
    """
    P0 Item 4 Verification:
    - Founder profit per wedding = client payments received - vendor costs - team cost (hours x rate)
    - Minimal time tracking entries (hours x rate)
    - Verification with hand-written expected numbers
    """
    uid = uuid.uuid4().hex[:6].upper()
    client_id = f"CL-PROF-{uid}"
    project_id = f"PRJ-PROF-{uid}"
    project_code = f"PRJ-2026-{uid}"

    wedding_target_date = date.today() + timedelta(days=60)
    db_client = Client(
        id=client_id,
        partner1_name="Rohan",
        partner2_name="Ishita",
        email=f"rohan.ishita.{uid}@example.com",
        phone="+919876543212",
        wedding_date=wedding_target_date,
        wedding_location="Umaid Bhawan Palace, Jodhpur",
        expected_guest_count=350,
        estimated_budget=Decimal("50000000.00"),  # 5 Crore INR
        service_package="Full-Service Planning",
        status="Confirmed"
    )
    db_session.add(db_client)

    project = WeddingProject(
        id=project_id,
        project_code=project_code,
        client_id=client_id,
        project_name="Rohan & Ishita Royal Jodhpur Wedding",
        wedding_date=wedding_target_date,
        location="Umaid Bhawan Palace, Jodhpur",
        guest_count=350,
        estimated_budget=Decimal("50000000.00"),
        package_tier="Full-Service",
        status="In Progress",
        deposit_paid=True
    )
    db_session.add(project)

    # 1. Client Payments Received: 2 Paid Payment Stages
    # Retainer (25%) = 12,500,000 INR
    stage1 = PaymentStage(
        id=f"PAY-1-{uid}",
        project_id=project_id,
        stage_name="Booking Retainer",
        percentage=Decimal("25.00"),
        amount=Decimal("12500000.00"),
        due_date=date.today() - timedelta(days=30),
        status="Paid"
    )
    # Advance (40%) = 20,000,000 INR
    stage2 = PaymentStage(
        id=f"PAY-2-{uid}",
        project_id=project_id,
        stage_name="Advance Production Milestone",
        percentage=Decimal("40.00"),
        amount=Decimal("20000000.00"),
        due_date=date.today() - timedelta(days=5),
        status="Paid"
    )
    # Final (35%) = 17,500,000 INR (Pending - not received yet)
    stage3 = PaymentStage(
        id=f"PAY-3-{uid}",
        project_id=project_id,
        stage_name="Final Settlement Balance",
        percentage=Decimal("35.00"),
        amount=Decimal("17500000.00"),
        due_date=wedding_target_date + timedelta(days=3),
        status="Pending"
    )
    db_session.add_all([stage1, stage2, stage3])

    # 2. Vendors Contracted:
    # Vendor 1: Catering = 8,000,000 INR
    v1 = Vendor(
        id=f"VND-1-{uid}",
        name=f"Royal Mewar Caterers {uid}",
        category="Catering",
        email=f"caterer.{uid}@example.com",
        phone="+919876543210"
    )
    # Vendor 2: Sound & Production = 1,500,000 INR
    v2 = Vendor(
        id=f"VND-2-{uid}",
        name=f"Jaipur Sound & Light Co {uid}",
        category="Sound & Lighting",
        email=f"sound.{uid}@example.com",
        phone="+919876543211"
    )
    db_session.add_all([v1, v2])
    db_session.flush()

    pv1 = ProjectVendor(
        id=f"PV-1-{uid}",
        project_id=project_id,
        vendor_id=v1.id,
        category="Catering",
        contract_amount=Decimal("8000000.00"),
        status="Contracted"
    )
    pv2 = ProjectVendor(
        id=f"PV-2-{uid}",
        project_id=project_id,
        vendor_id=v2.id,
        category="Sound & Lighting",
        contract_amount=Decimal("1500000.00"),
        status="Contracted"
    )
    db_session.add_all([pv1, pv2])
    db_session.commit()

    # 3. Add Team Time Entries via API
    # Entry 1: Lead Planner - 40 hours @ 2,500 INR/hr = 100,000 INR
    t1_resp = client.post(
        f"/api/v1/projects/{project_id}/time-entries",
        json={
            "employeeName": "Maharani Gayatri Singh",
            "role": "Lead Wedding Designer",
            "hours": 40.0,
            "hourlyRate": 2500.0,
            "taskDescription": "Client consultations, palace recce, vendor negotiations",
            "entryDate": str(date.today() - timedelta(days=10))
        }
    )
    assert t1_resp.status_code == 201, t1_resp.text
    assert Decimal(str(t1_resp.json()["totalCost"])) == Decimal("100000.00")

    # Entry 2: Senior Production Coordinator - 60 hours @ 1,500 INR/hr = 90,000 INR
    t2_resp = client.post(
        f"/api/v1/projects/{project_id}/time-entries",
        json={
            "employeeName": "Raghav Sharma",
            "role": "Production Coordinator",
            "hours": 60.0,
            "hourlyRate": 1500.0,
            "taskDescription": "Floor plan CAD drawings, trussing safety supervision",
            "entryDate": str(date.today() - timedelta(days=2))
        }
    )
    assert t2_resp.status_code == 201
    assert Decimal(str(t2_resp.json()["totalCost"])) == Decimal("90000.00")

    # 4. Fetch Profitability Analysis via API
    prof_resp = client.get(f"/api/v1/projects/{project_id}/profitability")
    assert prof_resp.status_code == 200, prof_resp.text
    data = prof_resp.json()

    # Hand-written expected numbers:
    # client_payments_received = 12,500,000 + 20,000,000 = 32,500,000.00
    expected_client_received = Decimal("32500000.00")
    # vendor_contracted_costs = 8,000,000 + 1,500,000 = 9,500,000.00
    expected_vendor_costs = Decimal("9500000.00")
    # team_labor_costs = 100,000 + 90,000 = 190,000.00
    expected_team_costs = Decimal("190000.00")
    # founder_gross_profit = 32,500,000 - 9,500,000 - 190,000 = 22,810,000.00
    expected_gross_profit = Decimal("22810000.00")
    # margin = (22,810,000 / 32,500,000) * 100 = 70.18%
    expected_margin = Decimal("70.18")

    assert Decimal(str(data["clientPaymentsReceived"])) == expected_client_received
    assert Decimal(str(data["vendorContractedCosts"])) == expected_vendor_costs
    assert Decimal(str(data["teamLaborCosts"])) == expected_team_costs
    assert Decimal(str(data["founderGrossProfit"])) == expected_gross_profit
    assert Decimal(str(data["profitMarginPercentage"])) == expected_margin
    assert data["timeEntriesCount"] == 2
    assert Decimal(str(data["totalTeamHours"])) == Decimal("100.00")
