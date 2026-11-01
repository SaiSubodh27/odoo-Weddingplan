import uuid
import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.models.client import Client
from app.models.project import WeddingProject, WeddingFunction, ProjectVendor
from app.models.vendor import Vendor
from app.models.catering import CateringPlan, CateringQuotation
from app.services.catering_service import catering_service
from app.schemas.catering import (
    CateringRFQCreate,
    CateringQuotationCreate,
)

client = TestClient(app)


@pytest.fixture
def quote_setup(db_session: Session):
    """Seed client, wedding project, function, catering plan, and 3 catering vendors."""
    uid = uuid.uuid4().hex[:6]
    clt = Client(
        id=f"CLT-Q-{uid}",
        partner1_name="Princess Gayatri",
        partner2_name="Prince Digvijay",
        email=f"digvijay_{uid}@royaltest.in",
        phone="+91 98290 88776",
        wedding_date=date(2027, 1, 20),
        wedding_location="Jaipur, Rajasthan",
        status="Client"
    )
    db_session.add(clt)
    db_session.commit()

    prj = WeddingProject(
        id=f"PRJ-Q-{uid}",
        project_code=f"PRJ-2027-{uid}",
        client_id=clt.id,
        project_name="Gayatri & Digvijay Royal Udaipur Wedding",
        wedding_date=date(2027, 1, 20),
        location="City Palace, Udaipur",
        guest_count=400,
        estimated_budget=Decimal("15000000.00"),
        status="Planning"
    )
    db_session.add(prj)
    db_session.commit()

    func = WeddingFunction(
        id=f"FUNC-Q-{uid}",
        project_id=prj.id,
        function_name="Royal Grand Banquet",
        function_date=date(2027, 1, 20),
        start_time="19:00",
        end_time="23:30",
        venue="Zenana Mahal Courtyard",
        status="Scheduled"
    )
    db_session.add(func)
    db_session.commit()

    plan = CateringPlan(
        id=f"CAT-Q-{uid}",
        project_id=prj.id,
        function_id=func.id,
        service_style="Silver Platter Degustation",
        guest_count=400,
        budget=Decimal("2000000.00"),
        status="Draft"
    )
    db_session.add(plan)

    v1 = Vendor(
        id=f"VND-M-{uid}",
        name="Mewar Royal Palace Caterers",
        category="Catering",
        phone="+91 98290 11111",
        city="Udaipur",
        rating=Decimal("4.90"),
        is_active=True
    )
    v2 = Vendor(
        id=f"VND-R-{uid}",
        name="Rajputana Heritage Feasts",
        category="Catering",
        phone="+91 98290 22222",
        city="Jaipur",
        rating=Decimal("4.75"),
        is_active=True
    )
    v3 = Vendor(
        id=f"VND-J-{uid}",
        name="Jaigarh Imperial Banquets",
        category="Catering",
        phone="+91 98290 33333",
        city="Jaipur",
        rating=Decimal("4.85"),
        is_active=True
    )
    db_session.add_all([v1, v2, v3])
    db_session.commit()

    return {
        "client": clt,
        "project": prj,
        "function": func,
        "plan": plan,
        "vendors": [v1, v2, v3]
    }


def _seed_sample_quotes(db: Session, plan_id: str, vendors: list):
    v1, v2, v3 = vendors
    q1 = catering_service.create_quotation(
        db=db, catering_id=plan_id, quotation_in=CateringQuotationCreate(
            vendor_id=v1.id,
            quotation_reference="QUO-MEWAR-001",
            per_person_rate=Decimal("3500.00"),
            total_guest_count=400,
            equipment_charges=Decimal("150000.00"),
            gst_rate_percent=Decimal("18.00"),
            line_items=[
                {"item_name": "7-Course Royal Mewari Degustation", "quantity": 400, "unit_price": 3500.00, "total_price": 1400000.00},
                {"item_name": "Silver Chafing & Palace Tableware Setup", "quantity": 1, "unit_price": 150000.00, "total_price": 150000.00}
            ],
            notes="Includes 12 master chefs and authentic copper handi cooking."
        )
    )
    q2 = catering_service.create_quotation(
        db=db, catering_id=plan_id, quotation_in=CateringQuotationCreate(
            vendor_id=v2.id,
            quotation_reference="QUO-RAJPUT-002",
            per_person_rate=Decimal("3200.00"),
            total_guest_count=400,
            equipment_charges=Decimal("100000.00"),
            gst_rate_percent=Decimal("18.00"),
            line_items=[
                {"item_name": "Heritage Rajputana Buffet", "quantity": 400, "unit_price": 3200.00, "total_price": 1280000.00},
                {"item_name": "Live Artisanal Chaat Counter", "quantity": 1, "unit_price": 100000.00, "total_price": 100000.00}
            ]
        )
    )
    q3 = catering_service.create_quotation(
        db=db, catering_id=plan_id, quotation_in=CateringQuotationCreate(
            vendor_id=v3.id,
            quotation_reference="QUO-JAIGARH-003",
            per_person_rate=Decimal("3000.00"),
            total_guest_count=400,
            equipment_charges=Decimal("80000.00"),
            gst_rate_percent=Decimal("18.00"),
            line_items=[
                {"item_name": "Imperial Banquet Buffet", "quantity": 400, "unit_price": 3000.00, "total_price": 1200000.00}
            ]
        )
    )
    return [q1, q2, q3]


def test_01_rfq_dispatch_to_several_vendors(db_session: Session, quote_setup):
    """Test issuing RFQ to multiple caterers simultaneously."""
    plan = quote_setup["plan"]
    v1, v2, v3 = quote_setup["vendors"]

    rfq_payload = {
        "vendorIds": [v1.id, v2.id, v3.id],
        "notes": "Exclusive 7-course royal Rajputana degustation for 400 palace guests."
    }
    res = client.post(f"/api/v1/catering/{plan.id}/rfq", json=rfq_payload)
    assert res.status_code == 200
    quotes = res.json()
    assert len(quotes) == 3

    # Plan status updated to Quotation Requested
    db_session.refresh(plan)
    assert plan.status == "Quotation Requested"


def test_02_quote_submission_with_line_items_and_costing(db_session: Session, quote_setup):
    """Test vendor quotes with itemized line items and decimal-safe price per plate."""
    plan = quote_setup["plan"]
    quotes = _seed_sample_quotes(db_session, plan.id, quote_setup["vendors"])
    q1 = quotes[0]
    q2 = quotes[1]
    q3 = quotes[2]

    # Food subtotal: 3500 * 400 = 1,400,000.00
    # Taxable: 1,400,000 + 150,000 = 1,550,000.00
    # GST (18%): 279,000.00
    # Total: 1,829,000.00
    assert q1["foodSubtotal"] == Decimal("1400000.00")
    assert q1["gstAmount"] == Decimal("279000.00")
    assert q1["totalAmount"] == Decimal("1829000.00")
    assert len(q1["lineItems"]) == 2

    # Vendor 2 total: (1280000 + 100000) * 1.18 = 1628400.00
    assert q2["totalAmount"] == Decimal("1628400.00")

    # Vendor 3 total: (1200000 + 80000) * 1.18 = 1510400.00
    assert q3["totalAmount"] == Decimal("1510400.00")


def test_03_side_by_side_compare_with_normalized_price_per_plate(db_session: Session, quote_setup):
    """Test side-by-side comparison endpoint normalizing price per plate."""
    plan = quote_setup["plan"]
    _seed_sample_quotes(db_session, plan.id, quote_setup["vendors"])

    res = client.get(f"/api/v1/catering/{plan.id}/quotations/compare")
    assert res.status_code == 200
    data = res.json()

    assert data["cateringPlanId"] == plan.id
    assert data["guestCount"] == 400
    assert len(data["quotations"]) == 3

    # Lowest price quote is Vendor 3 (QUO-JAIGARH-003)
    assert data["lowestPriceQuotationId"] is not None
    lowest = next(q for q in data["quotations"] if q["isLowestPrice"])
    assert lowest["vendorName"] == "Jaigarh Imperial Banquets"

    # Normalized price per plate verification:
    # Vendor 1: Total 1,829,000 / 400 guests = 4572.50 per plate fully loaded
    v1_q = next(q for q in data["quotations"] if q["vendorName"] == "Mewar Royal Palace Caterers")
    assert Decimal(str(v1_q["normalizedPricePerPlate"])) == Decimal("4572.50")
    assert len(v1_q["lineItems"]) == 2


def test_04_select_winner_atomic_transaction(db_session: Session, quote_setup):
    """
    Test select winner in ONE DB transaction:
    - Winner quote -> Accepted
    - Others -> Closed / Rejected
    - CateringPlan.selected_vendor_id set to winner
    - Vendor linked to wedding project as ProjectVendor
    """
    plan = quote_setup["plan"]
    v1 = quote_setup["vendors"][0]
    prj = quote_setup["project"]
    _seed_sample_quotes(db_session, plan.id, quote_setup["vendors"])

    # Select Vendor 1 as winner
    q1 = db_session.query(CateringQuotation).filter(
        CateringQuotation.catering_plan_id == plan.id,
        CateringQuotation.vendor_id == v1.id
    ).first()
    assert q1 is not None

    res = client.post(f"/api/v1/catering/{plan.id}/quotations/{q1.id}/select")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["selectedVendorId"] == v1.id
    assert Decimal(str(body["agreedCost"])) == q1.total_amount

    # Verify atomic state in database
    db_session.refresh(plan)
    assert plan.selected_vendor_id == v1.id
    assert plan.agreed_cost == q1.total_amount
    assert plan.status == "Vendor Selected"

    # Winning quote is Accepted
    db_session.refresh(q1)
    assert q1.status == "Accepted"

    # Other quotes for this plan are Closed
    other_quotes = db_session.query(CateringQuotation).filter(
        CateringQuotation.catering_plan_id == plan.id,
        CateringQuotation.id != q1.id
    ).all()
    assert len(other_quotes) == 2
    for oq in other_quotes:
        assert oq.status in ("Closed", "Rejected")

    # Winner vendor is linked directly to wedding project in project_vendors
    pv = db_session.query(ProjectVendor).filter(
        ProjectVendor.project_id == prj.id,
        ProjectVendor.vendor_id == v1.id
    ).first()
    assert pv is not None
    assert pv.category == "Catering"
    assert pv.contract_amount == q1.total_amount
    assert pv.status == "Contracted"
