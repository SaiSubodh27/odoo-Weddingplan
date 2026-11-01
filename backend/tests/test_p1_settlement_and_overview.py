import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.client import Client
from app.models.vendor import Vendor
from app.models.project import WeddingProject, ProjectVendor, PaymentStage, PlanningTask, WeddingFunction

client = TestClient(app)


def test_settlement_extras_and_idempotent_payout(db_session):
    """
    P1 Item 6 Verification:
    - Extras (extra plates, extra DJ hours) added to client invoice
    - Vendor payout = agreed + approved extras - advances
    - Unique constraint/idempotency key prevents duplicate payouts
    - Final settlement view
    """
    uid = uuid.uuid4().hex[:6].upper()
    client_id = f"CL-SET-{uid}"
    project_id = f"PRJ-SET-{uid}"
    project_code = f"PRJ-2026-{uid}"

    # 1. Setup client & project
    db_client = Client(
        id=client_id,
        partner1_name="Dev",
        partner2_name="Priyanka",
        email=f"dev.priyanka.{uid}@example.com",
        phone="+919876543216",
        wedding_date=date.today() + timedelta(days=5),
        wedding_location="Jagmandir Island Palace, Udaipur",
        expected_guest_count=400,
        estimated_budget=Decimal("40000000.00"),  # 4 Crore
        service_package="Full-Service Planning",
        status="Confirmed"
    )
    project = WeddingProject(
        id=project_id,
        project_code=project_code,
        client_id=client_id,
        project_name="Dev & Priyanka Island Palace Wedding",
        wedding_date=date.today() + timedelta(days=5),
        location="Jagmandir Island Palace, Udaipur",
        guest_count=400,
        estimated_budget=Decimal("40000000.00"),
        package_tier="Full-Service",
        status="Completed",
        deposit_paid=True
    )
    # Add paid client milestone
    stage1 = PaymentStage(
        id=f"PAY-SET-1-{uid}",
        project_id=project_id,
        stage_name="Booking Retainer",
        percentage=Decimal("25.00"),
        amount=Decimal("10000000.00"),  # 1 Crore
        due_date=date.today() - timedelta(days=60),
        status="Paid"
    )
    stage2 = PaymentStage(
        id=f"PAY-SET-2-{uid}",
        project_id=project_id,
        stage_name="Advance Milestone",
        percentage=Decimal("40.00"),
        amount=Decimal("16000000.00"),  # 1.6 Crore
        due_date=date.today() - timedelta(days=20),
        status="Paid"
    )
    v_caterer = Vendor(
        id=f"VND-CAT-{uid}",
        name=f"Udaipur Royal Caterers {uid}",
        category="Catering",
        email=f"caterer.{uid}@example.com",
        phone="+919876543217"
    )
    v_dj = Vendor(
        id=f"VND-DJ-{uid}",
        name=f"Jaipur Beats DJ {uid}",
        category="Entertainment",
        email=f"dj.{uid}@example.com",
        phone="+919876543218"
    )
    db_session.add_all([db_client, project, stage1, stage2, v_caterer, v_dj])
    db_session.commit()

    # 2. Add Extras:
    # Extra 1: 60 extra dinner plates @ 3,500 INR = 210,000 INR
    ext1_resp = client.post(
        f"/api/v1/projects/{project_id}/extras",
        json={
            "description": "60 Extra Dinner Plates at Gala Banquet",
            "category": "Catering",
            "quantity": 60.0,
            "unitPrice": 3500.0,
            "clientAmount": 210000.0,
            "vendorAmount": 210000.0,
            "isApproved": True,
            "approvedBy": "Maharani Gayatri Singh",
            "vendorId": v_caterer.id
        }
    )
    assert ext1_resp.status_code == 201, ext1_resp.text
    assert Decimal(str(ext1_resp.json()["clientAmount"])) == Decimal("210000.00")

    # Extra 2: 2 Extra DJ Overtime Hours @ 25,000 INR = 50,000 INR
    ext2_resp = client.post(
        f"/api/v1/projects/{project_id}/extras",
        json={
            "description": "2 Hours Late Night DJ Overtime (Afterparty)",
            "category": "Entertainment",
            "quantity": 2.0,
            "unitPrice": 25000.0,
            "clientAmount": 50000.0,
            "vendorAmount": 50000.0,
            "isApproved": True,
            "approvedBy": "Maharani Gayatri Singh",
            "vendorId": v_dj.id
        }
    )
    assert ext2_resp.status_code == 201
    assert Decimal(str(ext2_resp.json()["clientAmount"])) == Decimal("50000.00")

    # 3. Create Vendor Payout:
    # DJ payout: Agreed = 800,000 INR, approved extras = 50,000 INR, advance = 300,000 INR
    # Net payout = 800,000 + 50,000 - 300,000 = 550,000 INR
    payout_resp = client.post(
        f"/api/v1/projects/{project_id}/settlement/payout",
        json={
            "vendorId": v_dj.id,
            "agreedAmount": 800000.0,
            "approvedExtras": 50000.0,
            "advancePaid": 300000.0,
            "notes": "DJ final settlement after 2hr approved overtime"
        }
    )
    assert payout_resp.status_code == 201, payout_resp.text
    payout_data = payout_resp.json()
    assert Decimal(str(payout_data["finalPayoutAmount"])) == Decimal("550000.00")
    assert payout_data["idempotencyKey"] == f"PAYOUT-{project_id}-{v_dj.id}"

    # 4. DUPLICATE PAYOUT REJECTION (Idempotency test):
    dup_resp = client.post(
        f"/api/v1/projects/{project_id}/settlement/payout",
        json={
            "vendorId": v_dj.id,
            "agreedAmount": 800000.0,
            "approvedExtras": 50000.0,
            "advancePaid": 300000.0,
            "notes": "Attempt duplicate payout"
        }
    )
    assert dup_resp.status_code == 409, f"Expected 409 Conflict on duplicate payout, got {dup_resp.status_code}"
    assert "Duplicate payout rejected" in dup_resp.json()["detail"]

    # 5. Fetch Final Settlement View:
    settlement_resp = client.get(f"/api/v1/projects/{project_id}/settlement")
    assert settlement_resp.status_code == 200, settlement_resp.text
    s_data = settlement_resp.json()

    # Hand-written expected numbers:
    # package_budget = 40,000,000.00
    # extras = 210,000 + 50,000 = 260,000.00
    # total_invoice = 40,260,000.00
    # payments_received = 10,000,000 + 16,000,000 = 26,000,000.00
    # balance_due = 40,260,000 - 26,000,000 = 14,260,000.00
    # total_vendor_payouts = 550,000.00
    inv = s_data["clientInvoice"]
    assert Decimal(str(inv["packageBudget"])) == Decimal("40000000.00")
    assert Decimal(str(inv["approvedExtras"])) == Decimal("260000.00")
    assert Decimal(str(inv["totalInvoice"])) == Decimal("40260000.00")
    assert Decimal(str(inv["paymentsReceived"])) == Decimal("26000000.00")
    assert Decimal(str(inv["balanceDue"])) == Decimal("14260000.00")
    assert Decimal(str(s_data["totalVendorPayouts"])) == Decimal("550000.00")
    assert len(s_data["vendorPayouts"]) == 1


def test_client_wedding_overview_read_only(db_session):
    """
    P1 Item 7 Verification:
    - Client wedding overview (read-only): events, task progress, confirmed vendors, payment status, final costs
    """
    uid = uuid.uuid4().hex[:6].upper()
    client_id = f"CL-OV-{uid}"
    project_id = f"PRJ-OV-{uid}"
    project_code = f"PRJ-2026-{uid}"

    db_client = Client(
        id=client_id,
        partner1_name="Karan",
        partner2_name="Simran",
        email=f"karan.simran.{uid}@example.com",
        phone="+919876543219",
        wedding_date=date.today() + timedelta(days=45),
        wedding_location="Fairmont, Jaipur",
        expected_guest_count=500,
        estimated_budget=Decimal("70000000.00"),  # 7 Crore
        service_package="Full-Service Planning",
        status="Confirmed"
    )
    project = WeddingProject(
        id=project_id,
        project_code=project_code,
        client_id=client_id,
        project_name="Karan & Simran Grand Royal Wedding",
        wedding_date=date.today() + timedelta(days=45),
        location="Fairmont, Jaipur",
        guest_count=500,
        estimated_budget=Decimal("70000000.00"),
        package_tier="Full-Service",
        status="In Progress",
        deposit_paid=True
    )
    # Functions
    f1 = WeddingFunction(
        id=f"FN-1-{uid}",
        project_id=project_id,
        function_name="Sangeet Extravaganza",
        function_date=date.today() + timedelta(days=44),
        start_time="19:00",
        end_time="00:00",
        venue="Oasis Lawn",
        status="Scheduled"
    )
    f2 = WeddingFunction(
        id=f"FN-2-{uid}",
        project_id=project_id,
        function_name="Pheras & Royal Varmala",
        function_date=date.today() + timedelta(days=45),
        start_time="17:00",
        end_time="21:00",
        venue="Grand Ballroom",
        status="Scheduled"
    )
    # Tasks: 3 tasks, 2 completed
    t1 = PlanningTask(
        id=f"TK-1-{uid}",
        project_id=project_id,
        title="Approve Mandap 3D Render",
        category="Design",
        stage="Done",
        due_date=date.today(),
        is_completed=True
    )
    t2 = PlanningTask(
        id=f"TK-2-{uid}",
        project_id=project_id,
        title="Finalize Live Counters Menu",
        category="Vendors",
        stage="Done",
        due_date=date.today(),
        is_completed=True
    )
    t3 = PlanningTask(
        id=f"TK-3-{uid}",
        project_id=project_id,
        title="Coordinate Baraat Brass Band",
        category="Wedding Day",
        stage="To Plan",
        due_date=date.today() + timedelta(days=30),
        is_completed=False
    )
    # Payment Stage: 1 paid retainer of 17,500,000 INR
    p_stage = PaymentStage(
        id=f"PS-1-{uid}",
        project_id=project_id,
        stage_name="Booking Retainer (25%)",
        percentage=Decimal("25.00"),
        amount=Decimal("17500000.00"),
        due_date=date.today() - timedelta(days=10),
        status="Paid"
    )
    # Confirmed Vendor
    v = Vendor(
        id=f"VND-PH-{uid}",
        name=f"Stories by Joseph Radhik {uid}",
        category="Photography",
        email=f"photo.{uid}@example.com",
        phone="+919876543220",
        contact_person="Joseph"
    )
    db_session.add_all([db_client, project, f1, f2, t1, t2, t3, p_stage, v])
    db_session.flush()

    pv = ProjectVendor(
        id=f"PV-PH-{uid}",
        project_id=project_id,
        vendor_id=v.id,
        category="Photography",
        contract_amount=Decimal("3500000.00"),
        status="Confirmed"
    )
    db_session.add(pv)
    db_session.commit()

    # Call Client Overview API
    resp = client.get(f"/api/v1/projects/{project_id}/client-overview")
    assert resp.status_code == 200, resp.text
    ov = resp.json()

    # 1. Check Events
    assert len(ov["events"]) == 2
    assert ov["events"][0]["functionName"] == "Sangeet Extravaganza"

    # 2. Check Task Progress
    # 2 out of 3 completed = 66.7%
    tp = ov["taskProgress"]
    assert tp["totalTasks"] == 3
    assert tp["completedTasks"] == 2
    assert Decimal(str(tp["completionPercentage"])) == Decimal("66.7")

    # 3. Check Confirmed Vendors
    assert len(ov["confirmedVendors"]) == 1
    assert ov["confirmedVendors"][0]["name"] == v.name
    assert ov["confirmedVendors"][0]["category"] == "Photography"
    assert ov["confirmedVendors"][0]["contactPerson"] == "Joseph"

    # 4. Check Payment Status
    ps = ov["paymentStatus"]
    assert ps["depositPaid"] is True
    assert Decimal(str(ps["totalBudget"])) == Decimal("70000000.00")
    assert Decimal(str(ps["totalPaid"])) == Decimal("17500000.00")
    assert Decimal(str(ps["balanceRemaining"])) == Decimal("52500000.00")
    assert len(ps["stages"]) == 1

    # 5. Check Final Costs
    fc = ov["finalCosts"]
    assert Decimal(str(fc["baseBudget"])) == Decimal("70000000.00")
    assert Decimal(str(fc["finalTotalCost"])) == Decimal("70000000.00")
