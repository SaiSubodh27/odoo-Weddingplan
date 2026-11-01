import uuid
from datetime import date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.client import Client
from app.models.project import WeddingProject, WeddingFunction
from app.models.vendor import Vendor
from app.models.catering import CateringPlan, CateringMenuItem

client = TestClient(app)


@pytest.fixture
def db_session():
    """Provides a transactional database session for tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def setup_wedding_project_and_functions(db_session):
    """Sets up a test client, wedding project, and two ceremony functions."""
    uid = uuid.uuid4().hex[:6].upper()
    test_client = Client(
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
    db_session.add(test_client)
    db_session.flush()

    project = WeddingProject(
        id=f"PRJ-TEST-{uid}",
        project_code=f"PRJ-2027-{uid}",
        client_id=test_client.id,
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

    sangeet_func = WeddingFunction(
        id=f"FUNC-SANG-{uid}",
        project_id=project.id,
        function_name="Royal Sangeet & Musical Extravaganza",
        function_date=date(2027, 2, 13),
        start_time="19:00",
        end_time="23:30",
        venue="Jagmandir Island Palace Courtyard",
        status="Scheduled",
        estimated_cost=Decimal("250000.00")
    )
    db_session.add(sangeet_func)

    reception_func = WeddingFunction(
        id=f"FUNC-RECP-{uid}",
        project_id=project.id,
        function_name="Grand Royal Reception Banquet",
        function_date=date(2027, 2, 14),
        start_time="19:30",
        end_time="23:30",
        venue="Manek Chowk Courtyard",
        status="Scheduled",
        estimated_cost=Decimal("350000.00")
    )
    db_session.add(reception_func)
    db_session.commit()

    return project, sangeet_func, reception_func


# =====================================================================
# 1. Vendor API Tests
# =====================================================================

def test_vendor_api_lifecycle(db_session):
    """Verifies creating, listing, getting, updating, and deactivating vendors."""
    uid = uuid.uuid4().hex[:6].upper()
    vendor_payload = {
        "name": f"Royal Mewar Khansama Caterers {uid}",
        "category": "Catering",
        "contactPerson": "Master Chef Raghuveer Singh",
        "phone": f"+91 98290 {uid[:5]}",
        "email": f"raghuveer.{uid}@mewarcaterers.in",
        "city": "Udaipur",
        "address": "12 City Palace Road, Udaipur, Rajasthan",
        "rating": 4.95,
        "notes": "Specialists in 8-hour slow-cooked Laal Maas and royal Mewari thali service.",
        "isActive": True
    }

    # 1. Create vendor
    create_res = client.post("/api/v1/vendors", json=vendor_payload)
    assert create_res.status_code == 201, create_res.text
    created = create_res.json()
    assert created["name"] == vendor_payload["name"]
    assert created["category"] == "Catering"
    assert created["city"] == "Udaipur"
    assert created["isActive"] is True
    vendor_id = created["id"]

    # 2. Prevent duplicate vendor by phone
    dup_res = client.post("/api/v1/vendors", json=vendor_payload)
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 3. Retrieve vendor dossier
    get_res = client.get(f"/api/v1/vendors/{vendor_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == vendor_id
    assert get_res.json()["contactPerson"] == "Master Chef Raghuveer Singh"

    # 4. List vendors with category and city filtering
    list_res = client.get(f"/api/v1/vendors?category=Catering&city=Udaipur&search={uid}")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(v["id"] == vendor_id for v in list_data["items"])

    # 5. Update vendor
    update_res = client.put(f"/api/v1/vendors/{vendor_id}", json={
        "contactPerson": "Chef Maharaj Raghuveer",
        "rating": 5.0
    })
    assert update_res.status_code == 200
    assert update_res.json()["contactPerson"] == "Chef Maharaj Raghuveer"
    assert float(update_res.json()["rating"]) == 5.0

    # 6. Deactivate vendor via status patch
    status_res = client.patch(f"/api/v1/vendors/{vendor_id}/status", json={
        "isActive": False,
        "notes": "Temporarily booked out for royal wedding season."
    })
    assert status_res.status_code == 200
    assert status_res.json()["isActive"] is False

    # 7. Invalid vendor request: non-existent vendor ID
    not_found = client.get("/api/v1/vendors/VND-NONEXISTENT")
    assert not_found.status_code == 404


# =====================================================================
# 2. Catering Plans API Tests
# =====================================================================

def test_catering_plan_creation_with_defaults(setup_wedding_project_and_functions):
    """
    Verifies that when guest_count is omitted in CateringPlanCreate:
    1. It automatically defaults to parent wedding project's guest_count (450).
    2. Master project's guest count remains untouched.
    """
    project, sangeet_func, _ = setup_wedding_project_and_functions

    plan_payload = {
        "serviceStyle": "Silver Platter Degustation",
        "cuisinePreferences": "Royal Mewari & Awadhi Nawabi",
        # guestCount is omitted -> must default to project.guest_count (450)
        "vegCount": 250,
        "nonVegCount": 200,
        "jainCount": 30,
        "budget": 1500000.00,
        "notes": "Welcome drink bar to feature live rose elixir station."
    }

    res = client.post(
        f"/api/v1/projects/{project.id}/functions/{sangeet_func.id}/catering",
        json=plan_payload
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["projectId"] == project.id
    assert data["functionId"] == sangeet_func.id
    assert data["guestCount"] == 450  # Defaulted from project
    assert data["projectGuestCount"] == 450
    assert data["status"] == "Draft"
    assert data["location"] == sangeet_func.venue  # Defaulted from function


def test_catering_plan_creation_with_event_guest_override(setup_wedding_project_and_functions, db_session):
    """
    Verifies:
    1. Supplying an event-specific guest_count override succeeds.
    2. Parent project's master guest count remains 450.
    3. Flexible dietary counts (sum != total) are accepted without errors.
    """
    project, _, reception_func = setup_wedding_project_and_functions

    override_payload = {
        "serviceStyle": "Royal Thali & Plated Service",
        "cuisinePreferences": "Mewari Feast",
        "guestCount": 380,  # Specific ceremony override
        "vegCount": 220,    # Flexible estimate
        "nonVegCount": 130, # Flexible estimate
        "jainCount": 25,    # Flexible estimate (220+130+25 = 375 != 380)
        "budget": 2000000.00
    }

    res = client.post(
        f"/api/v1/projects/{project.id}/functions/{reception_func.id}/catering",
        json=override_payload
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["guestCount"] == 380
    assert data["vegCount"] == 220
    assert data["nonVegCount"] == 130
    assert data["jainCount"] == 25

    # Check database: project master guest count remains 450
    db_project = db_session.query(WeddingProject).filter(WeddingProject.id == project.id).first()
    assert db_project.guest_count == 450


def test_catering_plan_unique_constraint_and_cross_project_validation(setup_wedding_project_and_functions, db_session):
    """
    Verifies:
    1. Attempting to create a second catering plan for the same function returns 400 Bad Request.
    2. Attempting to create for a function belonging to another project returns 400 Bad Request.
    3. Non-existent project returns 404.
    """
    project, sangeet_func, _ = setup_wedding_project_and_functions

    # Create another project
    other_client = Client(
        id=f"TRK-OTH-{uuid.uuid4().hex[:4].upper()}",
        partner1_name="Other Couple",
        partner2_name="Other Partner",
        email=f"other.{uuid.uuid4().hex[:4]}@example.com",
        phone="+91 99999 11111",
        wedding_date=date(2027, 3, 1),
        wedding_location="Udaipur",
        status="Confirmed"
    )
    db_session.add(other_client)
    db_session.flush()

    other_project = WeddingProject(
        id=f"PRJ-OTH-{uuid.uuid4().hex[:4].upper()}",
        project_code=f"PRJ-OTH-{uuid.uuid4().hex[:3]}",
        client_id=other_client.id,
        project_name="Other Wedding Project",
        wedding_date=date(2027, 3, 1),
        location="Udaipur",
        guest_count=200,
        status="Planning"
    )
    db_session.add(other_project)
    db_session.commit()

    # 1. First catering plan succeeds
    plan_payload = {
        "serviceStyle": "Silver Platter Degustation",
        "guestCount": 250
    }
    res1 = client.post(
        f"/api/v1/projects/{project.id}/functions/{sangeet_func.id}/catering",
        json=plan_payload
    )
    assert res1.status_code == 201

    # 2. Duplicate catering plan for same function returns 400
    res_dup = client.post(
        f"/api/v1/projects/{project.id}/functions/{sangeet_func.id}/catering",
        json=plan_payload
    )
    assert res_dup.status_code == 400
    assert "already exists for function" in res_dup.json()["detail"]

    # 3. Cross-project function mismatch returns 400
    res_mismatch = client.post(
        f"/api/v1/projects/{other_project.id}/functions/{sangeet_func.id}/catering",
        json=plan_payload
    )
    assert res_mismatch.status_code == 400
    assert "does not belong to project" in res_mismatch.json()["detail"]

    # 4. Non-existent project returns 404
    res_no_proj = client.post(
        f"/api/v1/projects/PRJ-NONEXISTENT/functions/{sangeet_func.id}/catering",
        json=plan_payload
    )
    assert res_no_proj.status_code == 404


def test_list_and_get_project_catering_plans(setup_wedding_project_and_functions):
    """Verifies listing all catering plans for a project and retrieving by ID and function."""
    project, sangeet_func, reception_func = setup_wedding_project_and_functions

    # Create catering plan for both functions
    res1 = client.post(
        f"/api/v1/projects/{project.id}/functions/{sangeet_func.id}/catering",
        json={"serviceStyle": "Buffet", "guestCount": 300}
    )
    res2 = client.post(
        f"/api/v1/projects/{project.id}/functions/{reception_func.id}/catering",
        json={"serviceStyle": "Plated", "guestCount": 450}
    )
    assert res1.status_code == 201
    assert res2.status_code == 201
    cat1_id = res1.json()["id"]

    # List for project
    list_res = client.get(f"/api/v1/projects/{project.id}/catering")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) == 2

    # Get by function
    func_get = client.get(f"/api/v1/projects/{project.id}/functions/{sangeet_func.id}/catering")
    assert func_get.status_code == 200
    assert func_get.json()["id"] == cat1_id
    assert func_get.json()["functionName"] == sangeet_func.function_name

    # Get directly by catering_id
    direct_get = client.get(f"/api/v1/catering/{cat1_id}")
    assert direct_get.status_code == 200
    assert direct_get.json()["id"] == cat1_id


def test_update_catering_plan(setup_wedding_project_and_functions):
    """Verifies updating catering requirements via PUT."""
    project, sangeet_func, _ = setup_wedding_project_and_functions

    create_res = client.post(
        f"/api/v1/projects/{project.id}/functions/{sangeet_func.id}/catering",
        json={"serviceStyle": "Buffet", "budget": 500000.00}
    )
    cat_id = create_res.json()["id"]

    update_res = client.put(
        f"/api/v1/catering/{cat_id}",
        json={
            "serviceStyle": "Royal Silver Platter Degustation",
            "budget": 750000.00,
            "dietaryNotes": "Separate live chaat counter for strict Jain guests."
        }
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["serviceStyle"] == "Royal Silver Platter Degustation"
    assert float(updated["budget"]) == 750000.00
    assert "Jain" in updated["dietaryNotes"]


# =====================================================================
# 3. Menu Items API Tests
# =====================================================================

def test_menu_item_crud_and_cross_plan_isolation(setup_wedding_project_and_functions):
    """Verifies creating, listing, updating, deleting dishes and prevents cross-plan modifications."""
    project, sangeet_func, reception_func = setup_wedding_project_and_functions

    # Plan 1 (Sangeet) and Plan 2 (Reception)
    res1 = client.post(
        f"/api/v1/projects/{project.id}/functions/{sangeet_func.id}/catering",
        json={"serviceStyle": "Buffet"}
    )
    res2 = client.post(
        f"/api/v1/projects/{project.id}/functions/{reception_func.id}/catering",
        json={"serviceStyle": "Plated"}
    )
    cat1_id = res1.json()["id"]
    cat2_id = res2.json()["id"]

    # 1. Add menu item to Plan 1
    dish_payload = {
        "courseCategory": "Royal Appetizers & Starters",
        "itemName": "Ker Sangri Tartlets with Fig Glaze",
        "description": "Desert beans and wild berries in savory filo pastry.",
        "dietaryTag": "Vegetarian",
        "quantityNote": "Passed cocktail canapé",
        "displayOrder": 1
    }
    add_res = client.post(f"/api/v1/catering/{cat1_id}/menu-items", json=dish_payload)
    assert add_res.status_code == 201, add_res.text
    item_id = add_res.json()["id"]
    assert add_res.json()["itemName"] == dish_payload["itemName"]
    assert add_res.json()["cateringPlanId"] == cat1_id

    # 2. List items for Plan 1
    list_res = client.get(f"/api/v1/catering/{cat1_id}/menu-items")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # Plan 2 must have 0 items (isolation)
    list2_res = client.get(f"/api/v1/catering/{cat2_id}/menu-items")
    assert list2_res.status_code == 200
    assert len(list2_res.json()) == 0

    # 3. Cross-plan modification prevention: attempting to update Plan 1's item via Plan 2 returns 404
    cross_update = client.put(
        f"/api/v1/catering/{cat2_id}/menu-items/{item_id}",
        json={"itemName": "Hacked Dish"}
    )
    assert cross_update.status_code == 404

    # 4. Valid update on Plan 1
    update_res = client.put(
        f"/api/v1/catering/{cat1_id}/menu-items/{item_id}",
        json={"quantityNote": "Plated in silver thali for VIP row"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["quantityNote"] == "Plated in silver thali for VIP row"

    # 5. Cross-plan deletion prevention
    cross_del = client.delete(f"/api/v1/catering/{cat2_id}/menu-items/{item_id}")
    assert cross_del.status_code == 404

    # 6. Valid delete on Plan 1
    del_res = client.delete(f"/api/v1/catering/{cat1_id}/menu-items/{item_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Confirm item deleted
    after_del = client.get(f"/api/v1/catering/{cat1_id}/menu-items")
    assert len(after_del.json()) == 0


def test_menu_items_reordering(setup_wedding_project_and_functions):
    """Verifies batch reordering of menu courses."""
    project, sangeet_func, _ = setup_wedding_project_and_functions
    create_plan = client.post(
        f"/api/v1/projects/{project.id}/functions/{sangeet_func.id}/catering",
        json={"serviceStyle": "Buffet"}
    )
    cat_id = create_plan.json()["id"]

    # Add 2 items
    item1 = client.post(f"/api/v1/catering/{cat_id}/menu-items", json={
        "courseCategory": "Welcome Drinks",
        "itemName": "Kesar Kasturi Royal Elixir",
        "displayOrder": 1
    }).json()

    item2 = client.post(f"/api/v1/catering/{cat_id}/menu-items", json={
        "courseCategory": "Desserts",
        "itemName": "Kundan Kalakand",
        "displayOrder": 2
    }).json()

    # Reorder swapping display orders
    reorder_res = client.post(f"/api/v1/catering/{cat_id}/menu-items/reorder", json={
        "items": [
            {"id": item1["id"], "displayOrder": 5},
            {"id": item2["id"], "displayOrder": 1}
        ]
    })
    assert reorder_res.status_code == 200
    reordered_items = reorder_res.json()
    assert reordered_items[0]["id"] == item2["id"]
    assert reordered_items[0]["displayOrder"] == 1


# =====================================================================
# 4. Presets API Tests
# =====================================================================

def test_menu_presets_endpoints():
    """Verifies listing presets and retrieving details for all three luxury templates."""
    list_res = client.get("/api/v1/catering/presets")
    assert list_res.status_code == 200
    presets = list_res.json()
    assert len(presets) == 3
    preset_ids = [p["id"] for p in presets]
    assert "mewari_feast" in preset_ids
    assert "sheesh_mahal" in preset_ids
    assert "pan_asian" in preset_ids
    preset_names = [p["name"] for p in presets]
    assert "Contemporary Pan-Asian Luxury" in preset_names

    # Detail check
    mewari = client.get("/api/v1/catering/presets/mewari_feast")
    assert mewari.status_code == 200
    mewari_data = mewari.json()
    assert mewari_data["name"] == "Royal Rajputana Mewari Feast"
    assert len(mewari_data["items"]) == 13

    # Non-existent preset returns 404
    non_existent = client.get("/api/v1/catering/presets/unknown_preset")
    assert non_existent.status_code == 404


def test_apply_preset_append_and_replace_modes(setup_wedding_project_and_functions):
    """
    Verifies applying a luxury preset to a catering plan:
    1. Resulting dishes become editable CateringMenuItems.
    2. Shared preset is not modified.
    3. Mode 'append' preserves existing dishes.
    4. Mode 'replace' explicitly and safely clears old dishes.
    """
    project, sangeet_func, _ = setup_wedding_project_and_functions
    create_plan = client.post(
        f"/api/v1/projects/{project.id}/functions/{sangeet_func.id}/catering",
        json={"serviceStyle": "Silver Platter Degustation"}
    )
    cat_id = create_plan.json()["id"]

    # 1. Add a custom dish
    custom_dish = client.post(f"/api/v1/catering/{cat_id}/menu-items", json={
        "courseCategory": "Welcome Drinks",
        "itemName": "Special Welcome Champagne",
        "displayOrder": 1
    }).json()

    # 2. Apply 'mewari_feast' preset in mode='append'
    apply_res = client.post(f"/api/v1/catering/{cat_id}/apply-preset", json={
        "presetId": "mewari_feast",
        "mode": "append"
    })
    assert apply_res.status_code == 200
    items = apply_res.json()
    # 1 custom dish + 13 preset dishes = 14 items
    assert len(items) == 14
    dish_names = [i["itemName"] for i in items]
    assert "Special Welcome Champagne" in dish_names
    assert "Royal Mewari Laal Maas" in dish_names

    # 3. Check that preset dishes are editable without changing preset definition
    mewari_item = next(i for i in items if i["itemName"] == "Royal Mewari Laal Maas")
    edit_res = client.put(f"/api/v1/catering/{cat_id}/menu-items/{mewari_item['id']}", json={
        "description": "Customized extra spicy with heirloom Mathania chilies"
    })
    assert edit_res.status_code == 200
    assert "Customized extra spicy" in edit_res.json()["description"]

    # Verify shared preset is intact
    preset_check = client.get("/api/v1/catering/presets/mewari_feast").json()
    orig_laal_maas = next(i for i in preset_check["items"] if i["item_name"] == "Royal Mewari Laal Maas")
    assert "Customized" not in orig_laal_maas["description"]

    # 4. Apply 'pan_asian_luxury' in mode='replace'
    replace_res = client.post(f"/api/v1/catering/{cat_id}/apply-preset", json={
        "presetId": "pan_asian_luxury",
        "mode": "replace"
    })
    assert replace_res.status_code == 200
    new_items = replace_res.json()
    # Exactly 13 items from pan_asian_luxury, old items safely cleared
    assert len(new_items) == 13
    new_dish_names = [i["itemName"] for i in new_items]
    assert "Special Welcome Champagne" not in new_dish_names
    assert "Chilean Sea Bass in Mirin-Miso Glaze" in new_dish_names


# =====================================================================
# 5. Quotations & Costing Engine Tests (Stage 3)
# =====================================================================

def test_create_and_list_quotations_costing_math(setup_wedding_project_and_functions, db_session):
    """
    Verifies:
    1. Creating a quotation defaults guest count from catering plan if omitted.
    2. Transparent costing calculations:
       - food_subtotal = per_person_rate * guest_count
       - taxable_subtotal = food_subtotal + equipment_charges
       - gst_amount = taxable_subtotal * (gst_rate / 100)
       - total_amount = taxable_subtotal + gst_amount
    3. Listing quotations returns all submitted vendor bids.
    """
    project, sangeet_func, _ = setup_wedding_project_and_functions
    uid = uuid.uuid4().hex[:6].upper()

    # Create vendor
    vendor = Vendor(
        id=f"VND-{uid}-1",
        name=f"Rajputana Khansama Caterers {uid}",
        category="Catering",
        phone=f"+91 98290 {uid[:5]}",
        city="Jaipur",
        rating=Decimal("4.90"),
        is_active=True
    )
    db_session.add(vendor)
    db_session.commit()

    # Create catering plan (guest count = 350)
    create_plan = client.post(
        f"/api/v1/projects/{project.id}/functions/{sangeet_func.id}/catering",
        json={"serviceStyle": "Silver Platter Degustation", "guestCount": 350}
    )
    cat_id = create_plan.json()["id"]

    # 1. Post quotation with 18% standard luxury catering GST
    # Rate: 2,500.00, Pax: omitted (defaults to 350) -> Food = 8,75,000.00
    # Equipment = 1,25,000.00 -> Taxable = 10,00,000.00
    # GST 18% = 1,80,000.00 -> Total = 11,80,000.00
    quo_payload = {
        "vendorId": vendor.id,
        "quotationReference": f"QUO-RAJ-{uid}",
        "perPersonRate": 2500.00,
        "equipmentCharges": 125000.00,
        "gstRatePercent": 18.00,
        "validityDate": "2027-02-01",
        "notes": "Includes antique silver chafing dishes and live charcoal sigri setup."
    }
    quo_res = client.post(f"/api/v1/catering/{cat_id}/quotations", json=quo_payload)
    assert quo_res.status_code == 201, quo_res.text
    quo_data = quo_res.json()

    assert quo_data["cateringPlanId"] == cat_id
    assert quo_data["vendorId"] == vendor.id
    assert quo_data["totalGuestCount"] == 350  # Defaulted from catering plan
    assert float(quo_data["foodSubtotal"]) == 875000.00
    assert float(quo_data["equipmentCharges"]) == 125000.00
    assert float(quo_data["gstRatePercent"]) == 18.00
    assert float(quo_data["gstAmount"]) == 180000.00
    assert float(quo_data["totalAmount"]) == 1180000.00
    assert quo_data["status"] == "Received"
    assert quo_data["vendorName"] == vendor.name

    # 2. List quotations
    list_res = client.get(f"/api/v1/catering/{cat_id}/quotations")
    assert list_res.status_code == 200
    quotations = list_res.json()
    assert len(quotations) >= 1
    assert quotations[0]["id"] == quo_data["id"]


def test_configurable_gst_rates_and_decimal_rounding(setup_wedding_project_and_functions, db_session):
    """
    Verifies that GST is configurable per quotation:
    1. 0% GST (tax-exempt or SEZ billing).
    2. 5% GST (standalone caterer concession rate).
    3. Custom GST rate (e.g. 7.25% or 14.5%) with fractional paise testing ROUND_HALF_UP.
    """
    project, sangeet_func, _ = setup_wedding_project_and_functions
    uid = uuid.uuid4().hex[:6].upper()

    vendor = Vendor(
        id=f"VND-{uid}-2",
        name=f"Mewari Sweet & Savory {uid}",
        category="Catering",
        phone=f"+91 98291 {uid[:5]}",
        city="Udaipur",
        rating=Decimal("4.80"),
        is_active=True
    )
    db_session.add(vendor)
    db_session.commit()

    create_plan = client.post(
        f"/api/v1/projects/{project.id}/functions/{sangeet_func.id}/catering",
        json={"guestCount": 100}
    )
    cat_id = create_plan.json()["id"]

    # Test 1: 0% GST rate
    # Rate: 1,500.00, Pax: 100 -> Food: 1,50,000.00
    # Equipment: 20,000.00 -> Taxable: 1,70,000.00
    # GST 0% -> GST: 0.00 -> Total: 1,70,000.00
    res_0 = client.post(f"/api/v1/catering/{cat_id}/quotations", json={
        "vendorId": vendor.id,
        "perPersonRate": 1500.00,
        "totalGuestCount": 100,
        "equipmentCharges": 20000.00,
        "gstRatePercent": 0.00
    })
    assert res_0.status_code == 201
    d0 = res_0.json()
    assert float(d0["gstRatePercent"]) == 0.0
    assert float(d0["gstAmount"]) == 0.00
    assert float(d0["totalAmount"]) == 170000.00

    # Test 2: 5% GST rate
    # Taxable: 1,70,000.00 -> GST 5% = 8,500.00 -> Total: 1,78,500.00
    res_5 = client.post(f"/api/v1/catering/{cat_id}/quotations", json={
        "vendorId": vendor.id,
        "perPersonRate": 1500.00,
        "totalGuestCount": 100,
        "equipmentCharges": 20000.00,
        "gstRatePercent": 5.00
    })
    assert res_5.status_code == 201
    d5 = res_5.json()
    assert float(d5["gstRatePercent"]) == 5.0
    assert float(d5["gstAmount"]) == 8500.00
    assert float(d5["totalAmount"]) == 178500.00

    # Test 3: Custom GST rate with rounding verification
    # Rate: 1,333.33 * 3 guests = 3,999.99 food subtotal
    # Equipment: 100.00 -> Taxable = 4,099.99
    # Custom GST: 7.25% -> 4,099.99 * 0.0725 = 297.249275 -> Rounds to 297.25
    # Total = 4,099.99 + 297.25 = 4,397.24
    res_custom = client.post(f"/api/v1/catering/{cat_id}/quotations", json={
        "vendorId": vendor.id,
        "perPersonRate": 1333.33,
        "totalGuestCount": 3,
        "equipmentCharges": 100.00,
        "gstRatePercent": 7.25
    })
    assert res_custom.status_code == 201
    d_cust = res_custom.json()
    assert float(d_cust["foodSubtotal"]) == 3999.99
    assert float(d_cust["gstAmount"]) == 297.25
    assert float(d_cust["totalAmount"]) == 4397.24


def test_multiple_quotations_and_winning_selection(setup_wedding_project_and_functions, db_session):
    """
    Verifies competing vendor quotation bids and winning selection:
    1. Multiple vendors submit bids for one catering plan.
    2. Selecting winning quotation updates catering plan's selected_vendor_id and agreed_cost.
    3. Winning quotation status transitions to 'Accepted'.
    4. Competing quotations transition to 'Rejected'.
    """
    project, sangeet_func, _ = setup_wedding_project_and_functions
    uid = uuid.uuid4().hex[:6].upper()

    # Create 3 vendors
    v1 = Vendor(id=f"VND-{uid}-A", name=f"Vendor Alpha {uid}", phone=f"+91 98000 {uid[:5]}", city="Jaipur", is_active=True)
    v2 = Vendor(id=f"VND-{uid}-B", name=f"Vendor Beta {uid}", phone=f"+91 98001 {uid[:5]}", city="Udaipur", is_active=True)
    v3 = Vendor(id=f"VND-{uid}-C", name=f"Vendor Gamma {uid}", phone=f"+91 98002 {uid[:5]}", city="Jaipur", is_active=True)
    db_session.add_all([v1, v2, v3])
    db_session.commit()

    create_plan = client.post(
        f"/api/v1/projects/{project.id}/functions/{sangeet_func.id}/catering",
        json={"guestCount": 200, "serviceStyle": "Silver Platter"}
    )
    cat_id = create_plan.json()["id"]

    # Vendor 1 submits quote: ₹3,000/pax, 18% GST -> Total: 7,08,000.00
    q1 = client.post(f"/api/v1/catering/{cat_id}/quotations", json={
        "vendorId": v1.id,
        "perPersonRate": 3000.00,
        "equipmentCharges": 0.00,
        "gstRatePercent": 18.00
    }).json()

    # Vendor 2 submits quote: ₹2,800/pax, ₹50,000 equipment, 18% GST -> Taxable: 6,10,000 -> GST: 1,09,800 -> Total: 7,19,800.00
    q2 = client.post(f"/api/v1/catering/{cat_id}/quotations", json={
        "vendorId": v2.id,
        "perPersonRate": 2800.00,
        "equipmentCharges": 50000.00,
        "gstRatePercent": 18.00
    }).json()

    # Vendor 3 submits quote: ₹2,600/pax, ₹40,000 equipment, 18% GST -> Taxable: 5,60,000 -> GST: 1,00,800 -> Total: 6,60,800.00
    q3 = client.post(f"/api/v1/catering/{cat_id}/quotations", json={
        "vendorId": v3.id,
        "perPersonRate": 2600.00,
        "equipmentCharges": 40000.00,
        "gstRatePercent": 18.00
    }).json()

    # Verify 3 quotations exist and are all 'Received'
    quotes = client.get(f"/api/v1/catering/{cat_id}/quotations").json()
    assert len(quotes) == 3
    assert all(q["status"] == "Received" for q in quotes)

    # Agency selects Vendor 3 (q3) as winner
    select_res = client.post(f"/api/v1/catering/{cat_id}/quotations/{q3['id']}/select")
    assert select_res.status_code == 200, select_res.text
    sel_data = select_res.json()

    assert sel_data["success"] is True
    assert sel_data["cateringPlanId"] == cat_id
    assert sel_data["selectedVendorId"] == v3.id
    assert float(sel_data["agreedCost"]) == 660800.00
    assert sel_data["selectedQuotationId"] == q3["id"]
    assert sel_data["selectedQuotation"]["status"] == "Accepted"

    # Verify database state for catering plan
    plan_data = client.get(f"/api/v1/catering/{cat_id}").json()
    assert plan_data["selectedVendorId"] == v3.id
    assert float(plan_data["agreedCost"]) == 660800.00

    # Verify other quotations are marked 'Rejected'
    quotes_after = client.get(f"/api/v1/catering/{cat_id}/quotations").json()
    q1_after = next(q for q in quotes_after if q["id"] == q1["id"])
    q2_after = next(q for q in quotes_after if q["id"] == q2["id"])
    q3_after = next(q for q in quotes_after if q["id"] == q3["id"])

    assert q3_after["status"] == "Accepted"
    assert q1_after["status"] in ["Rejected", "Closed"]
    assert q2_after["status"] in ["Rejected", "Closed"]


def test_quotation_validation_and_cross_plan_prevention(setup_wedding_project_and_functions, db_session):
    """
    Verifies error handling and isolation:
    1. Unknown vendor returns 404.
    2. Unknown catering plan returns 404.
    3. Selecting a quotation that belongs to Plan 1 via Plan 2 returns 404.
    """
    project, sangeet_func, reception_func = setup_wedding_project_and_functions
    uid = uuid.uuid4().hex[:6].upper()

    vendor = Vendor(id=f"VND-{uid}-X", name=f"Vendor X {uid}", phone=f"+91 98300 {uid[:5]}", city="Jaipur", is_active=True)
    db_session.add(vendor)
    db_session.commit()

    # Plan 1 (Sangeet) and Plan 2 (Reception)
    p1 = client.post(f"/api/v1/projects/{project.id}/functions/{sangeet_func.id}/catering", json={"guestCount": 100}).json()
    p2 = client.post(f"/api/v1/projects/{project.id}/functions/{reception_func.id}/catering", json={"guestCount": 200}).json()

    # 1. Unknown vendor ID returns 404
    bad_vendor = client.post(f"/api/v1/catering/{p1['id']}/quotations", json={
        "vendorId": "VND-NONEXISTENT",
        "perPersonRate": 2000.00
    })
    assert bad_vendor.status_code == 404

    # 2. Unknown catering plan returns 404
    bad_plan = client.post("/api/v1/catering/CAT-NONEXISTENT/quotations", json={
        "vendorId": vendor.id,
        "perPersonRate": 2000.00
    })
    assert bad_plan.status_code == 404

    # 3. Create quotation on Plan 1
    q1 = client.post(f"/api/v1/catering/{p1['id']}/quotations", json={
        "vendorId": vendor.id,
        "perPersonRate": 2500.00
    }).json()

    # Attempting to select Plan 1's quotation via Plan 2 returns 404
    cross_select = client.post(f"/api/v1/catering/{p2['id']}/quotations/{q1['id']}/select")
    assert cross_select.status_code == 404


def test_quotation_update_recalculates_costing(setup_wedding_project_and_functions, db_session):
    """
    Verifies that updating a quotation's perPersonRate, equipmentCharges, or gstRatePercent
    properly recalculates all subtotals and total amounts.
    """
    project, sangeet_func, _ = setup_wedding_project_and_functions
    uid = uuid.uuid4().hex[:6].upper()

    vendor = Vendor(id=f"VND-{uid}-U", name=f"Vendor Update {uid}", phone=f"+91 98400 {uid[:5]}", city="Udaipur", is_active=True)
    db_session.add(vendor)
    db_session.commit()

    p = client.post(f"/api/v1/projects/{project.id}/functions/{sangeet_func.id}/catering", json={"guestCount": 100}).json()
    q = client.post(f"/api/v1/catering/{p['id']}/quotations", json={
        "vendorId": vendor.id,
        "perPersonRate": 2000.00,
        "totalGuestCount": 100,
        "equipmentCharges": 0.00,
        "gstRatePercent": 18.00
    }).json()

    # Initial: 2000 * 100 = 2,00,000 + 18% (36,000) = 2,36,000.00
    assert float(q["totalAmount"]) == 236000.00

    # Negotiate rate down to 1800 and add 25000 equipment charges with 12% GST
    # Food: 1,80,000.00, Equip: 25,000.00 -> Taxable: 2,05,000.00
    # GST 12% = 24,600.00 -> Total: 2,29,600.00
    up_res = client.put(f"/api/v1/catering/{p['id']}/quotations/{q['id']}", json={
        "perPersonRate": 1800.00,
        "equipmentCharges": 25000.00,
        "gstRatePercent": 12.00
    })
    assert up_res.status_code == 200
    up_data = up_res.json()
    assert float(up_data["foodSubtotal"]) == 180000.00
    assert float(up_data["equipmentCharges"]) == 25000.00
    assert float(up_data["gstRatePercent"]) == 12.00
    assert float(up_data["gstAmount"]) == 24600.00
    assert float(up_data["totalAmount"]) == 229600.00


# =====================================================================
# 6. Catering Status Lifecycle Tests (Stage 4)
# =====================================================================

def test_catering_status_lifecycle_progression_and_prerequisites(setup_wedding_project_and_functions, db_session):
    """
    Verifies the complete catering lifecycle progression:
    Draft -> Requirements Confirmed -> Quotation Requested -> Vendor Selected ->
    Menu Finalized -> Sent to Vendor -> Vendor Confirmed

    Also verifies:
    1. Skipping stages returns 400.
    2. 'Vendor Selected' without winning quotation returns 400.
    3. 'Menu Finalized' without menu items returns 400.
    4. Rollback to earlier status is permitted.
    5. Audit notes are appended.
    """
    project, sangeet_func, _ = setup_wedding_project_and_functions
    uid = uuid.uuid4().hex[:6].upper()

    vendor = Vendor(
        id=f"VND-{uid}-LC",
        name=f"Lifecycle Caterer {uid}",
        phone=f"+91 98500 {uid[:5]}",
        city="Udaipur",
        is_active=True
    )
    db_session.add(vendor)
    db_session.commit()

    # Create plan (Starts in 'Draft')
    plan = client.post(
        f"/api/v1/projects/{project.id}/functions/{sangeet_func.id}/catering",
        json={"guestCount": 200, "budget": 500000.00}
    ).json()
    cat_id = plan["id"]
    assert plan["status"] == "Draft"

    # 1. Skipping stage: Draft directly to 'Vendor Selected' returns 400
    bad_jump = client.patch(f"/api/v1/catering/{cat_id}/status", json={"status": "Vendor Selected"})
    assert bad_jump.status_code == 400
    assert "cannot transition directly" in bad_jump.json()["detail"]

    # 2. Transition: Draft -> Requirements Confirmed (Valid)
    req_res = client.patch(f"/api/v1/catering/{cat_id}/status", json={
        "status": "Requirements Confirmed",
        "notes": "Client signed off on 200 pax and silver platter style."
    })
    assert req_res.status_code == 200
    assert req_res.json()["status"] == "Requirements Confirmed"

    # 3. Transition: Requirements Confirmed -> Quotation Requested (Valid)
    quo_req_res = client.patch(f"/api/v1/catering/{cat_id}/status", json={
        "status": "Quotation Requested"
    })
    assert quo_req_res.status_code == 200
    assert quo_req_res.json()["status"] == "Quotation Requested"

    # 4. Attempt Quotation Requested -> Vendor Selected WITHOUT an accepted quotation returns 400
    bad_sel = client.patch(f"/api/v1/catering/{cat_id}/status", json={"status": "Vendor Selected"})
    assert bad_sel.status_code == 400

    # Submit and select a winning quotation
    q = client.post(f"/api/v1/catering/{cat_id}/quotations", json={
        "vendorId": vendor.id,
        "perPersonRate": 2500.00,
        "totalGuestCount": 200,
        "gstRatePercent": 18.00
    }).json()
    client.post(f"/api/v1/catering/{cat_id}/quotations/{q['id']}/select")

    # Now transition to Vendor Selected succeeds
    sel_res = client.patch(f"/api/v1/catering/{cat_id}/status", json={
        "status": "Vendor Selected",
        "notes": f"Winning quotation {q['id']} approved."
    })
    assert sel_res.status_code == 200
    assert sel_res.json()["status"] == "Vendor Selected"

    # 5. Attempt Vendor Selected -> Menu Finalized WITHOUT menu items returns 400
    bad_menu = client.patch(f"/api/v1/catering/{cat_id}/status", json={"status": "Menu Finalized"})
    assert bad_menu.status_code == 400
    assert "zero dishes" in bad_menu.json()["detail"]

    # Add a dish
    client.post(f"/api/v1/catering/{cat_id}/menu-items", json={
        "courseCategory": "Welcome Drinks",
        "itemName": "Kesar Royal Elixir",
        "dietaryTag": "Vegetarian"
    })

    # Now Menu Finalized succeeds
    menu_res = client.patch(f"/api/v1/catering/{cat_id}/status", json={"status": "Menu Finalized"})
    assert menu_res.status_code == 200
    assert menu_res.json()["status"] == "Menu Finalized"

    # 6. Menu Finalized -> Sent to Vendor
    sent_res = client.patch(f"/api/v1/catering/{cat_id}/status", json={"status": "Sent to Vendor"})
    assert sent_res.status_code == 200
    assert sent_res.json()["status"] == "Sent to Vendor"

    # 7. Sent to Vendor -> Vendor Confirmed
    conf_res = client.patch(f"/api/v1/catering/{cat_id}/status", json={"status": "Vendor Confirmed"})
    assert conf_res.status_code == 200
    assert conf_res.json()["status"] == "Vendor Confirmed"

    # 8. Verify audit trail was appended to plan.notes
    plan_final = client.get(f"/api/v1/catering/{cat_id}").json()
    assert "[Status Transition" in plan_final["notes"]
    assert "Vendor Confirmed" in plan_final["notes"]

    # 9. Verify rollback is permitted (e.g. from Vendor Confirmed back to Menu Finalized)
    rollback_res = client.patch(f"/api/v1/catering/{cat_id}/status", json={
        "status": "Menu Finalized",
        "notes": "Client requested dessert adjustment."
    })
    assert rollback_res.status_code == 200
    assert rollback_res.json()["status"] == "Menu Finalized"


# =====================================================================
# 7. PDF Quotation Generation Tests (Stage 5)
# =====================================================================

def test_pdf_generation_endpoints(setup_wedding_project_and_functions, db_session):
    """
    Verifies:
    1. GET /catering/{catering_id}/quotations/{quotation_id}/pdf generates valid PDF bytes starting with %PDF-.
    2. Response headers include attachment filename and Content-Length.
    3. GET /catering/{catering_id}/pdf generates valid event spec PDF.
    4. Non-existent quotation returns 404.
    """
    project, sangeet_func, _ = setup_wedding_project_and_functions
    uid = uuid.uuid4().hex[:6].upper()

    vendor = Vendor(
        id=f"VND-{uid}-PDF",
        name=f"Royal Udaipur Caterers {uid}",
        phone=f"+91 98600 {uid[:5]}",
        city="Udaipur",
        is_active=True
    )
    db_session.add(vendor)
    db_session.commit()

    create_plan = client.post(
        f"/api/v1/projects/{project.id}/functions/{sangeet_func.id}/catering",
        json={"guestCount": 300, "serviceStyle": "Silver Platter"}
    )
    cat_id = create_plan.json()["id"]

    # Add a menu item to test menu rendering in PDF
    client.post(f"/api/v1/catering/{cat_id}/menu-items", json={
        "courseCategory": "Mains",
        "itemName": "Mewari Laal Maas",
        "description": "Slow-simmered lamb with Mathania chilies",
        "dietaryTag": "Non-Vegetarian"
    })

    # Create quotation
    q = client.post(f"/api/v1/catering/{cat_id}/quotations", json={
        "vendorId": vendor.id,
        "perPersonRate": 3000.00,
        "totalGuestCount": 300,
        "equipmentCharges": 50000.00,
        "gstRatePercent": 18.00,
        "notes": "Includes royal silver chafing vessels."
    }).json()

    # 1. Download quotation PDF
    pdf_res = client.get(f"/api/v1/catering/{cat_id}/quotations/{q['id']}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["Content-Type"] == "application/pdf"
    assert "attachment; filename=" in pdf_res.headers["Content-Disposition"]
    assert pdf_res.content.startswith(b"%PDF-")
    assert len(pdf_res.content) > 2000  # Valid multi-section PDF document

    # 2. Download general catering plan PDF
    plan_pdf_res = client.get(f"/api/v1/catering/{cat_id}/pdf")
    assert plan_pdf_res.status_code == 200
    assert plan_pdf_res.headers["Content-Type"] == "application/pdf"
    assert plan_pdf_res.content.startswith(b"%PDF-")

    # 3. Non-existent quotation returns 404
    bad_pdf = client.get(f"/api/v1/catering/{cat_id}/quotations/QUO-NONEXISTENT/pdf")
    assert bad_pdf.status_code == 404


# =====================================================================
# 8. WhatsApp Sharing & Communications Tests (Stage 6)
# =====================================================================

def test_whatsapp_sharing_and_audit_logging(setup_wedding_project_and_functions, db_session):
    """
    Verifies:
    1. POST /catering/{catering_id}/share-whatsapp generates authentic wa.me deep-link with encoded parameters.
    2. Accurately records communication log in database with status='Initiated' (no fake delivery claim).
    3. Missing vendor phone returns 400.
    4. GET /catering/{catering_id}/communications lists logged activity.
    """
    project, sangeet_func, _ = setup_wedding_project_and_functions
    uid = uuid.uuid4().hex[:6].upper()

    vendor = Vendor(
        id=f"VND-{uid}-WA",
        name=f"Maharaja Catering {uid}",
        phone="+91 98765 43210",
        city="Jaipur",
        is_active=True
    )
    db_session.add(vendor)
    db_session.commit()

    create_plan = client.post(
        f"/api/v1/projects/{project.id}/functions/{sangeet_func.id}/catering",
        json={"guestCount": 250, "serviceStyle": "Silver Platter"}
    )
    cat_id = create_plan.json()["id"]

    q = client.post(f"/api/v1/catering/{cat_id}/quotations", json={
        "vendorId": vendor.id,
        "perPersonRate": 2800.00,
        "totalGuestCount": 250,
        "equipmentCharges": 25000.00,
        "gstRatePercent": 18.00
    }).json()

    # 1. Generate WhatsApp share
    share_res = client.post(f"/api/v1/catering/{cat_id}/quotations/{q['id']}/share-whatsapp", json={
        "customMessage": "Please review the guest pax and dietary requirements."
    })
    assert share_res.status_code == 200, share_res.text
    share_data = share_res.json()

    assert share_data["success"] is True
    assert share_data["mode"] == "manual_whatsapp_link"
    assert "https://wa.me/919876543210?text=" in share_data["shareUrl"]
    assert "Maharaja Catering" in share_data["messageText"]
    assert "250 Pax" in share_data["messageText"]
    assert "COM-" in share_data["communicationId"]

    # 2. List communications
    comm_res = client.get(f"/api/v1/catering/{cat_id}/communications")
    assert comm_res.status_code == 200
    comm_logs = comm_res.json()
    assert len(comm_logs) >= 1
    assert comm_logs[0]["id"] == share_data["communicationId"]
    assert comm_logs[0]["status"] == "Initiated"  # Not fake delivered!
    assert comm_logs[0]["communicationType"] == "WhatsApp Manual Share"

    # 3. Missing vendor phone error handling
    v_no_phone = Vendor(id=f"VND-{uid}-NOP", name="No Phone Vendor", phone="", city="Jaipur", is_active=True)
    db_session.add(v_no_phone)
    db_session.commit()

    bad_wa = client.post(f"/api/v1/catering/{cat_id}/share-whatsapp", json={
        "vendorId": v_no_phone.id,
        "recipientPhone": ""
    })
    assert bad_wa.status_code == 400


