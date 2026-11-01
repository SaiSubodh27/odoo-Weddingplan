import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.client import Client
from app.models.vendor import Vendor
from app.models.project import WeddingProject, ProjectVendor, PaymentStage, WeddingFunction
from app.models.catering import CateringPlan, CateringQuotation, CateringMenuItem

client = TestClient(app)


def test_p2_founder_season_overview_and_export(db_session):
    """
    P2 Item 8 Verification:
    - Founder season view of all weddings
    - Vendor performance scorecards
    - Upcoming dues for the next 4 weeks
    - Shareable read-only report export with token validation
    """
    uid = uuid.uuid4().hex[:6].upper()
    client_id = f"CL-FND-{uid}"
    project_id = f"PRJ-FND-{uid}"
    project_code = f"PRJ-2026-{uid}"

    today = date.today()
    wedding_target_date = today + timedelta(days=20)  # within 4 weeks

    # 1. Setup client and project
    db_client = Client(
        id=client_id,
        partner1_name="Ranveer",
        partner2_name="Deepika",
        email=f"ranveer.deepika.{uid}@example.com",
        phone="+919876543221",
        wedding_date=wedding_target_date,
        wedding_location="Lake Palace, Udaipur",
        expected_guest_count=500,
        estimated_budget=Decimal("80000000.00"),  # 8 Crore
        service_package="Full-Service Planning",
        status="Confirmed"
    )
    project = WeddingProject(
        id=project_id,
        project_code=project_code,
        client_id=client_id,
        project_name="Ranveer & Deepika Palace Wedding",
        wedding_date=wedding_target_date,
        location="Lake Palace, Udaipur",
        guest_count=500,
        estimated_budget=Decimal("80000000.00"),
        status="In Progress",
        deposit_paid=True
    )
    # Paid retainer
    p1 = PaymentStage(
        id=f"PS-FND-1-{uid}",
        project_id=project_id,
        stage_name="Booking Retainer",
        percentage=Decimal("25.00"),
        amount=Decimal("20000000.00"),
        due_date=today - timedelta(days=30),
        status="Paid"
    )
    # Upcoming milestone due in 10 days (within next 4 weeks!)
    p2 = PaymentStage(
        id=f"PS-FND-2-{uid}",
        project_id=project_id,
        stage_name="Advance Production Milestone",
        percentage=Decimal("40.00"),
        amount=Decimal("32000000.00"),
        due_date=today + timedelta(days=10),
        status="Pending"
    )
    v = Vendor(
        id=f"VND-FND-{uid}",
        name=f"Jaipur Palace Decorators {uid}",
        category="Decor",
        email=f"decor.{uid}@example.com",
        phone="+919876543222",
        rating=4.9
    )
    db_session.add_all([db_client, project, p1, p2, v])
    db_session.flush()

    pv = ProjectVendor(
        id=f"PV-FND-{uid}",
        project_id=project_id,
        vendor_id=v.id,
        category="Decor",
        contract_amount=Decimal("12000000.00"),
        status="Contracted"
    )
    db_session.add(pv)
    db_session.commit()

    # 2. Call Founder Season Overview API
    resp = client.get("/api/v1/founder/season-overview")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["weddingsCount"] >= 1
    assert Decimal(str(data["totalClientPaymentsReceived"])) >= Decimal("20000000.00")
    assert Decimal(str(data["totalVendorCosts"])) >= Decimal("12000000.00")
    assert Decimal(str(data["netFounderProfit"])) > Decimal("0.00")
    assert "token" in data["shareableReportUrl"]

    # Verify upcoming dues
    due_found = any(d["projectId"] == project_id and d["stageName"] == "Advance Production Milestone" for d in data["upcomingDuesNext4Weeks"])
    assert due_found, "Upcoming due within next 4 weeks was not found in overview!"

    # Verify vendor performance scorecard
    v_scorecard = next((s for s in data["vendorPerformance"] if s["vendorId"] == v.id), None)
    assert v_scorecard is not None
    assert v_scorecard["jobsContracted"] >= 1

    # 3. Test Shareable Report Export View (HTML)
    token = data["shareableReportToken"]
    export_resp = client.get(f"/api/v1/founder/season-overview/export?token={token}")
    assert export_resp.status_code == 200
    assert "text/html" in export_resp.headers["content-type"]
    assert "The Royal Knot — Founder Executive Report" in export_resp.text
    assert "Ranveer & Deepika" in export_resp.text


def test_p2_vendor_portal_real_flow(db_session):
    """
    P2 Item 9 Verification:
    - Vendor login via phone/email/name
    - Real vendor dashboard with assigned weddings, RFQs received, and won/closed stats
    - Submit quote with itemized line items
    """
    uid = uuid.uuid4().hex[:6].upper()
    v_phone = f"+9198765{uid[:5]}"
    v_email = f"caterer.{uid}@example.com"

    # 1. Create registered vendor
    v = Vendor(
        id=f"VND-PORTAL-{uid}",
        name=f"Udaipur Royal Spice Feast {uid}",
        category="Catering",
        email=v_email,
        phone=v_phone,
        rating=5.0
    )
    # Create project, function, and catering plan
    project = WeddingProject(
        id=f"PRJ-VP-{uid}",
        project_code=f"PRJ-2026-{uid}",
        client_id=f"CL-VP-{uid}",
        project_name="Royal Spice Gala Wedding",
        wedding_date=date.today() + timedelta(days=30),
        location="Udaipur",
        guest_count=400,
        estimated_budget=Decimal("50000000.00"),
        status="Planning"
    )
    fn = WeddingFunction(
        id=f"FN-VP-{uid}",
        project_id=project.id,
        function_name="Royal Feast Sangeet Dinner",
        function_date=date.today() + timedelta(days=30),
        start_time="19:00",
        end_time="23:30",
        venue="Zenana Courtyard",
        status="Scheduled"
    )
    db_session.add_all([v, project, fn])
    db_session.flush()

    c_plan = CateringPlan(
        id=f"CP-VP-{uid}",
        project_id=project.id,
        function_id=fn.id,
        service_style="Silver Platter Degustation",
        guest_count=400,
        budget=Decimal("2000000.00"),
        status="Quotation Requested"
    )
    # RFQ quote requested
    quote = CateringQuotation(
        id=f"QUO-VP-{uid}",
        catering_plan_id=c_plan.id,
        vendor_id=v.id,
        quotation_reference=f"RFQ-FEAST-{uid}",
        status="Quotation Requested"
    )
    db_session.add_all([c_plan, quote])
    db_session.commit()

    # 2. Test Vendor Login
    login_resp = client.post(
        "/api/v1/vendor-portal/login",
        json={"identifier": v_email}
    )
    assert login_resp.status_code == 200, login_resp.text
    login_data = login_resp.json()
    assert login_data["vendorId"] == v.id
    assert "vnd_tok_" in login_data["token"]

    # 3. Test Vendor Dashboard
    dash_resp = client.get(f"/api/v1/vendor-portal/{v.id}/dashboard")
    assert dash_resp.status_code == 200, dash_resp.text
    dash = dash_resp.json()

    assert dash["vendorId"] == v.id
    assert len(dash["rfqsReceived"]) == 1
    assert dash["rfqsReceived"][0]["planTitle"] == "Royal Feast Sangeet Dinner"
    assert dash["rfqsReceived"][0]["status"] == "Quotation Requested"

    # 4. Test Vendor Submit Real Quote with Line Items
    submit_resp = client.post(
        f"/api/v1/vendor-portal/{v.id}/quotes",
        json={
            "cateringPlanId": c_plan.id,
            "pricePerPlate": 3500.0,
            "lineItems": [
                {"name": "Rajasthani Live Dal Baati Churma", "quantity": 400, "unit_price": 500, "total_price": 200000},
                {"name": "Imported Belgian Truffle Dessert Counter", "quantity": 1, "unit_price": 150000, "total_price": 150000}
            ],
            "notes": "Includes complimentary traditional brass service ware."
        }
    )
    assert submit_resp.status_code == 201, submit_resp.text
    sq_data = submit_resp.json()

    # Hand-written expected calculation:
    # 3500 * 400 (guest count) = 1,400,000 + 200,000 + 150,000 = 1,750,000.00
    assert Decimal(str(sq_data["pricePerPlate"])) == Decimal("3500.00")
    assert Decimal(str(sq_data["totalCost"])) == Decimal("1750000.00")
    assert sq_data["status"] == "Quotation Received"
    assert len(sq_data["lineItems"]) == 2


def test_p2_catering_pdf_and_whatsapp_share_working(db_session):
    """
    P2 Item 10 Verification:
    - Catering quotation PDF generation and download
    - WhatsApp deep-link generation and communication audit logging
    """
    uid = uuid.uuid4().hex[:6].upper()

    v = Vendor(
        id=f"VND-PDF-{uid}",
        name=f"Jaipur Royal Caterers {uid}",
        category="Catering",
        email=f"caterer.{uid}@example.com",
        phone="+919876543210"
    )
    project = WeddingProject(
        id=f"PRJ-PDF-{uid}",
        project_code=f"PRJ-2026-{uid}",
        client_id=f"CL-PDF-{uid}",
        project_name="Royal Heritage Gala",
        wedding_date=date.today() + timedelta(days=50),
        location="Jaipur",
        guest_count=400,
        estimated_budget=Decimal("50000000.00"),
        status="Planning"
    )
    fn = WeddingFunction(
        id=f"FN-PDF-{uid}",
        project_id=project.id,
        function_name="Heritage Gala Dinner",
        function_date=date.today() + timedelta(days=50),
        start_time="19:00",
        end_time="23:30",
        venue="Maan Singh Courtyard",
        status="Scheduled"
    )
    db_session.add_all([v, project, fn])
    db_session.flush()

    plan = CateringPlan(
        id=f"CP-PDF-{uid}",
        project_id=project.id,
        function_id=fn.id,
        service_style="Plated Thali",
        guest_count=400,
        budget=Decimal("2500000.00"),
        status="Quotation Received"
    )
    quote = CateringQuotation(
        id=f"QUO-PDF-{uid}",
        catering_plan_id=plan.id,
        vendor_id=v.id,
        quotation_reference=f"RFQ-JPR-{uid}",
        price_per_plate=Decimal("3800.00"),
        total_cost=Decimal("1520000.00"),
        status="Quotation Received"
    )
    menu_item = CateringMenuItem(
        id=f"MI-PDF-{uid}",
        catering_plan_id=plan.id,
        item_name="Laal Maas Royale",
        course_category="Main Course",
        dietary_tag="Non-Vegetarian"
    )
    db_session.add_all([plan, quote, menu_item])
    db_session.commit()

    # 1. Test Catering PDF Download
    pdf_resp = client.get(f"/api/v1/catering/{plan.id}/quotations/{quote.id}/pdf")
    assert pdf_resp.status_code == 200, pdf_resp.text
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF-"), "Generated content is not a valid PDF binary"

    # 2. Test WhatsApp Deep-Link Share
    wa_resp = client.post(
        f"/api/v1/catering/{plan.id}/quotations/{quote.id}/share-whatsapp",
        json={"recipientPhone": "+919876543210"}
    )
    assert wa_resp.status_code == 200, wa_resp.text
    wa_data = wa_resp.json()

    share_link = wa_data.get("shareUrl") or wa_data.get("share_url", "")
    msg = wa_data.get("messageText") or wa_data.get("message_text", "")
    assert "wa.me/919876543210" in share_link or "api.whatsapp.com" in share_link
    assert "Heritage Gala Dinner" in msg or "Heritage Gala Dinner" in share_link
    assert wa_data["mode"] == "manual_whatsapp_link"
