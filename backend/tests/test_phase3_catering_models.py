import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError

from app.database.session import SessionLocal
from app.models.client import Client
from app.models.project import WeddingProject, WeddingFunction
from app.models.vendor import Vendor
from app.models.catering import (
    CateringPlan,
    CateringMenuItem,
    CateringQuotation,
    CateringCommunicationLog
)
from app.services.catering_presets import (
    get_available_presets,
    get_preset_by_id,
    get_preset_items,
    LUXURY_MENU_PRESETS
)


@pytest.fixture
def db_session():
    """Provides a transactional database session for tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_project_and_function(db_session):
    """Sets up an isolated test client, wedding project, and ceremony function."""
    uid = uuid.uuid4().hex[:6].upper()
    client = Client(
        id=f"TRK-TEST-{uid}",
        partner1_name="Princess Gayatri",
        partner2_name="Yuvraj Vikram",
        email=f"gayatri.{uid}@testroyalknot.in",
        phone="+91 98200 11223",
        wedding_date=date(2027, 2, 14),
        wedding_location="Taj Lake Palace, Udaipur",
        expected_guest_count=450,
        estimated_budget=Decimal("35000000.00"),
        service_package="Full-Service",
        status="Confirmed"
    )
    db_session.add(client)
    db_session.flush()

    project = WeddingProject(
        id=f"PRJ-TEST-{uid}",
        project_code=f"PRJ-2027-{uid[:3]}",
        client_id=client.id,
        project_name="Gayatri & Vikram Palace Wedding",
        wedding_date=date(2027, 2, 14),
        location="Taj Lake Palace, Udaipur",
        guest_count=450,
        estimated_budget=Decimal("35000000.00"),
        package_tier="Full-Service",
        status="Planning"
    )
    db_session.add(project)
    db_session.flush()

    function = WeddingFunction(
        id=f"FUNC-TEST-{uid}",
        project_id=project.id,
        function_name="Grand Royal Reception",
        function_date=date(2027, 2, 14),
        start_time="19:30",
        end_time="23:30",
        venue="Manek Chowk Courtyard",
        status="Scheduled",
        estimated_cost=Decimal("350000.00")
    )
    db_session.add(function)
    db_session.commit()

    return project, function


def test_shared_vendor_model(db_session):
    """Verifies Vendor model creation, categories, rating, and defaults."""
    uid = uuid.uuid4().hex[:6].upper()
    vendor = Vendor(
        id=f"VND-{uid}",
        name="Royal Mewar Khansama Caterers",
        category="Catering",
        contact_person="Master Chef Raghuveer Singh",
        phone="+91 98290 55443",
        email=f"raghuveer.{uid}@mewarcaterers.in",
        city="Udaipur",
        address="12 City Palace Road, Udaipur, Rajasthan",
        rating=Decimal("4.95"),
        notes="Specialists in 8-hour slow-cooked Laal Maas and royal Mewari thali service.",
        is_active=True
    )
    db_session.add(vendor)
    db_session.commit()

    fetched = db_session.query(Vendor).filter(Vendor.id == vendor.id).first()
    assert fetched is not None
    assert fetched.name == "Royal Mewar Khansama Caterers"
    assert fetched.category == "Catering"
    assert fetched.city == "Udaipur"
    assert float(fetched.rating) == 4.95
    assert fetched.is_active is True

    # Cleanup
    db_session.delete(fetched)
    db_session.commit()


def test_catering_plan_association_and_guest_override(db_session, sample_project_and_function):
    """
    Verifies:
    1. CateringPlan links to WeddingProject and WeddingFunction.
    2. Event-specific guest count override does NOT modify the master project guest count.
    3. Flexible dietary estimates (veg + non_veg != total) are accepted without constraint errors.
    """
    project, function = sample_project_and_function
    uid = uuid.uuid4().hex[:6].upper()

    # Master project has 450 guests. We specify an intimate reception override of 380 guests.
    catering_plan = CateringPlan(
        id=f"CAT-{uid}",
        project_id=project.id,
        function_id=function.id,
        service_style="Silver Platter Degustation",
        cuisine_preferences="Rajasthani Mewari Heritage & Awadhi Dum",
        guest_count=380,  # Event override
        veg_count=220,    # Flexible estimate
        non_veg_count=130, # Flexible estimate
        jain_count=25,    # Flexible estimate (220 + 130 + 25 = 375 != 380 pax: flexible and accepted)
        dietary_notes="Strict Jain pavilion setup requested on western lawn.",
        service_timings="19:30 - 23:30",
        location=function.venue,
        budget=Decimal("1200000.00"),
        status="Draft"
    )
    db_session.add(catering_plan)
    db_session.commit()

    fetched_plan = db_session.query(CateringPlan).filter(CateringPlan.id == catering_plan.id).first()
    assert fetched_plan is not None
    assert fetched_plan.project_id == project.id
    assert fetched_plan.function_id == function.id
    assert fetched_plan.guest_count == 380
    assert fetched_plan.veg_count == 220
    assert fetched_plan.non_veg_count == 130
    assert fetched_plan.jain_count == 25
    assert fetched_plan.status == "Draft"

    # Confirm master wedding project guest count remained unchanged at 450
    refreshed_project = db_session.query(WeddingProject).filter(WeddingProject.id == project.id).first()
    assert refreshed_project.guest_count == 450

    # Verify 1:1 relationship between function and catering_plan
    refreshed_function = db_session.query(WeddingFunction).filter(WeddingFunction.id == function.id).first()
    assert refreshed_function.catering_plan is not None
    assert refreshed_function.catering_plan.id == catering_plan.id


def test_unique_function_catering_plan_constraint(db_session, sample_project_and_function):
    """Verifies that an event function cannot have duplicate catering plans."""
    project, function = sample_project_and_function
    uid1 = uuid.uuid4().hex[:6].upper()
    uid2 = uuid.uuid4().hex[:6].upper()

    plan1 = CateringPlan(
        id=f"CAT-{uid1}",
        project_id=project.id,
        function_id=function.id,
        guest_count=450
    )
    db_session.add(plan1)
    db_session.commit()

    # Attempting to associate another catering plan to the SAME function_id must fail unique constraint
    plan2 = CateringPlan(
        id=f"CAT-{uid2}",
        project_id=project.id,
        function_id=function.id,
        guest_count=450
    )
    db_session.add(plan2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_catering_menu_items_relationship(db_session, sample_project_and_function):
    """Verifies CateringMenuItem creation under course categories with dietary tags."""
    project, function = sample_project_and_function
    uid = uuid.uuid4().hex[:6].upper()

    plan = CateringPlan(
        id=f"CAT-{uid}",
        project_id=project.id,
        function_id=function.id,
        guest_count=function.project.guest_count
    )
    db_session.add(plan)
    db_session.flush()

    dish1 = CateringMenuItem(
        id=f"ITM-{uid}-1",
        catering_plan_id=plan.id,
        course_category="Welcome Drinks",
        item_name="Kesar Kasturi Royal Elixir",
        description="Infused saffron, rose petals, and sparkling water.",
        dietary_tag="Vegetarian",
        quantity_note="1 glass per guest upon arrival",
        display_order=1
    )
    dish2 = CateringMenuItem(
        id=f"ITM-{uid}-2",
        catering_plan_id=plan.id,
        course_category="Main Degustation Courses",
        item_name="Royal Mewari Laal Maas",
        description="Slow-cooked mutton with Mathania chilies.",
        dietary_tag="Non-Vegetarian",
        quantity_note="380 portions",
        display_order=2
    )
    db_session.add(dish1)
    db_session.add(dish2)
    db_session.commit()

    refreshed_plan = db_session.query(CateringPlan).filter(CateringPlan.id == plan.id).first()
    assert len(refreshed_plan.menu_items) == 2
    assert refreshed_plan.menu_items[0].item_name == "Kesar Kasturi Royal Elixir"
    assert refreshed_plan.menu_items[1].dietary_tag == "Non-Vegetarian"


def test_catering_quotation_with_configurable_gst(db_session, sample_project_and_function):
    """Verifies CateringQuotation creation, vendor link, and configurable GST rate."""
    project, function = sample_project_and_function
    uid = uuid.uuid4().hex[:6].upper()

    vendor = Vendor(
        id=f"VND-{uid}",
        name="Udaipur Imperial Banquet Services",
        phone="+91 98200 44556"
    )
    db_session.add(vendor)

    plan = CateringPlan(
        id=f"CAT-{uid}",
        project_id=project.id,
        function_id=function.id,
        guest_count=400
    )
    db_session.add(plan)
    db_session.flush()

    # Quotation 1: 5% GST rate (Composite catering rate)
    rate1 = Decimal("2500.00")
    pax1 = 400
    food1 = rate1 * pax1  # 10,00,000
    equip1 = Decimal("150000.00")
    sub1 = food1 + equip1  # 11,50,000
    gst_rate1 = Decimal("5.00")  # 5%
    gst_amt1 = sub1 * (gst_rate1 / Decimal("100.00"))  # 57,500
    total1 = sub1 + gst_amt1  # 12,07,500

    q1 = CateringQuotation(
        id=f"QUO-{uid}-1",
        catering_plan_id=plan.id,
        vendor_id=vendor.id,
        quotation_reference="QUO-IMP-2027-01",
        per_person_rate=rate1,
        total_guest_count=pax1,
        food_subtotal=food1,
        equipment_charges=equip1,
        gst_rate_percent=gst_rate1,
        gst_amount=gst_amt1,
        total_amount=total1,
        status="Received"
    )
    db_session.add(q1)

    # Quotation 2: 18% GST rate (Standard luxury palace catering rate)
    rate2 = Decimal("3200.00")
    food2 = rate2 * pax1  # 12,80,000
    equip2 = Decimal("200000.00")
    sub2 = food2 + equip2  # 14,80,000
    gst_rate2 = Decimal("18.00")  # 18%
    gst_amt2 = sub2 * (gst_rate2 / Decimal("100.00"))  # 2,66,400
    total2 = sub2 + gst_amt2  # 17,46,400

    q2 = CateringQuotation(
        id=f"QUO-{uid}-2",
        catering_plan_id=plan.id,
        vendor_id=vendor.id,
        quotation_reference="QUO-IMP-2027-02",
        per_person_rate=rate2,
        total_guest_count=pax1,
        food_subtotal=food2,
        equipment_charges=equip2,
        gst_rate_percent=gst_rate2,
        gst_amount=gst_amt2,
        total_amount=total2,
        status="Under Review"
    )
    db_session.add(q2)
    db_session.commit()

    refreshed_plan = db_session.query(CateringPlan).filter(CateringPlan.id == plan.id).first()
    assert len(refreshed_plan.quotations) == 2

    # Verify configurable GST was saved without being overridden to 18%
    assert float(q1.gst_rate_percent) == 5.0
    assert float(q1.gst_amount) == 57500.0
    assert float(q1.total_amount) == 1207500.0

    assert float(q2.gst_rate_percent) == 18.0
    assert float(q2.gst_amount) == 266400.0
    assert float(q2.total_amount) == 1746400.0


def test_catering_communication_log(db_session, sample_project_and_function):
    """Verifies CateringCommunicationLog creation and vendor association."""
    project, function = sample_project_and_function
    uid = uuid.uuid4().hex[:6].upper()

    vendor = Vendor(
        id=f"VND-{uid}",
        name="Lake Palace Food Artisans",
        phone="+91 98290 12345"
    )
    db_session.add(vendor)

    plan = CateringPlan(
        id=f"CAT-{uid}",
        project_id=project.id,
        function_id=function.id
    )
    db_session.add(plan)
    db_session.flush()

    comm = CateringCommunicationLog(
        id=f"COM-{uid}",
        catering_plan_id=plan.id,
        vendor_id=vendor.id,
        communication_type="WhatsApp Manual Share",
        recipient_phone=vendor.phone,
        message_text="Catering specification dossier for Grand Royal Reception.",
        pdf_download_url=f"/api/v1/catering/{plan.id}/pdf",
        status="Initiated",
        initiated_by="Senior Wedding Concierge"
    )
    db_session.add(comm)
    db_session.commit()

    fetched = db_session.query(CateringCommunicationLog).filter(CateringCommunicationLog.id == comm.id).first()
    assert fetched is not None
    assert fetched.communication_type == "WhatsApp Manual Share"
    assert fetched.status == "Initiated"
    assert fetched.vendor.name == "Lake Palace Food Artisans"


def test_luxury_menu_presets_structure():
    """Verifies that all three approved starting presets exist and are structured correctly."""
    available = get_available_presets()
    assert len(available) == 3

    preset_ids = [p["id"] for p in available]
    assert "mewari_feast" in preset_ids
    assert "sheesh_mahal" in preset_ids
    assert "pan_asian" in preset_ids

    # Test 1: Royal Rajputana Mewari Feast
    mewari = get_preset_by_id("mewari_feast")
    assert mewari["name"] == "Royal Rajputana Mewari Feast"
    assert len(mewari["items"]) >= 10
    categories = set(item["course_category"] for item in mewari["items"])
    assert "Welcome Drinks" in categories
    assert "Main Degustation Courses" in categories
    assert "Dessert Atelier" in categories

    # Test 2: Mughal Sheesh Mahal Degustation
    sheesh = get_preset_by_id("sheesh_mahal")
    assert sheesh["name"] == "Mughal Sheesh Mahal Degustation"
    assert any("Galouti" in item["item_name"] for item in sheesh["items"])

    # Test 3: Contemporary Pan-Asian Luxury
    asian = get_preset_by_id("pan_asian")
    assert asian["name"] == "Contemporary Pan-Asian Luxury"
    assert any("Dim Sum" in item["item_name"] for item in asian["items"])

    # Test deep-copy immutability: modifying returned preset items must not alter master template
    items_copy = get_preset_items("mewari_feast")
    items_copy[0]["item_name"] = "MODIFIED DISH NAME"
    fresh_preset = get_preset_by_id("mewari_feast")
    assert fresh_preset["items"][0]["item_name"] != "MODIFIED DISH NAME"

    # Test unknown preset handling
    with pytest.raises(ValueError):
        get_preset_by_id("unknown_preset")


def test_cascade_delete_integrity(db_session, sample_project_and_function):
    """
    Verifies that deleting a WeddingFunction cascades to its CateringPlan and associated
    menu items, quotations, and communication logs without leaving orphan records.
    """
    project, function = sample_project_and_function
    uid = uuid.uuid4().hex[:6].upper()

    vendor = Vendor(
        id=f"VND-{uid}",
        name="Cascade Test Caterer",
        phone="+91 99999 11111"
    )
    db_session.add(vendor)

    plan = CateringPlan(
        id=f"CAT-{uid}",
        project_id=project.id,
        function_id=function.id,
        selected_vendor_id=vendor.id
    )
    db_session.add(plan)
    db_session.flush()

    dish = CateringMenuItem(
        id=f"ITM-{uid}",
        catering_plan_id=plan.id,
        course_category="Main Degustation Courses",
        item_name="Cascade Mutton Curry"
    )
    quotation = CateringQuotation(
        id=f"QUO-{uid}",
        catering_plan_id=plan.id,
        vendor_id=vendor.id,
        total_amount=Decimal("50000.00")
    )
    comm = CateringCommunicationLog(
        id=f"COM-{uid}",
        catering_plan_id=plan.id,
        vendor_id=vendor.id
    )
    db_session.add_all([dish, quotation, comm])
    db_session.commit()

    # Now delete the WeddingFunction
    db_session.delete(function)
    db_session.commit()

    # The CateringPlan and all child entities must be cascade-deleted
    assert db_session.query(CateringPlan).filter(CateringPlan.id == plan.id).first() is None
    assert db_session.query(CateringMenuItem).filter(CateringMenuItem.id == dish.id).first() is None
    assert db_session.query(CateringQuotation).filter(CateringQuotation.id == quotation.id).first() is None
    assert db_session.query(CateringCommunicationLog).filter(CateringCommunicationLog.id == comm.id).first() is None

    # Vendor should NOT be deleted, but remains intact
    assert db_session.query(Vendor).filter(Vendor.id == vendor.id).first() is not None

