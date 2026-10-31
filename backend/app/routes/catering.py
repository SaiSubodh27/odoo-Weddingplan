from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session, joinedload

from app.database.session import get_db
from app.models.catering import CateringPlan, CateringQuotation
from app.services.catering_service import catering_service
from app.services.pdf_service import pdf_service
from app.schemas.catering import (
    CateringPlanCreate,
    CateringPlanUpdate,
    CateringStatusUpdate,
    CateringPlanResponse,
    CateringPlanDetailResponse,
    CateringMenuItemCreate,
    CateringMenuItemUpdate,
    CateringMenuItemResponse,
    MenuItemReorderRequest,
    PresetSummaryResponse,
    PresetDetailResponse,
    ApplyPresetRequest,
    CateringQuotationCreate,
    CateringQuotationUpdate,
    CateringQuotationResponse,
    CateringQuotationSelectResponse,
    CateringWhatsAppShareRequest,
    CateringWhatsAppShareResponse,
)

router = APIRouter()


# =====================================================================
# Preset Templates (Must precede /catering/{catering_id} to avoid collision)
# =====================================================================

@router.get(
    "/catering/presets",
    response_model=List[PresetSummaryResponse],
    summary="List available luxury catering starting templates",
    tags=["Catering Presets"]
)
def list_presets():
    """
    Returns curated luxury menu preset templates:
    1. Royal Rajputana Mewari Feast
    2. Mughal Sheesh Mahal Degustation
    3. Contemporary Pan-Asian Luxury
    """
    return catering_service.list_presets()


@router.get(
    "/catering/presets/{preset_id}",
    response_model=PresetDetailResponse,
    summary="Get luxury menu preset template details",
    tags=["Catering Presets"]
)
def get_preset(preset_id: str):
    """
    Returns complete course and dish breakdown for a starting template.
    """
    return catering_service.get_preset_details(preset_id)


# =====================================================================
# Project & Function Event Catering Plans
# =====================================================================

@router.get(
    "/projects/{project_id}/catering",
    response_model=List[CateringPlanResponse],
    summary="List all event catering requirement plans for a wedding project",
    tags=["Catering Requirements"]
)
def list_project_catering_plans(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns all event-specific catering plans configured across ceremonies in a wedding project.
    """
    plans = catering_service.list_catering_plans_for_project(db=db, project_id=project_id)
    return [CateringPlanResponse.model_validate(p) for p in plans]


@router.get(
    "/projects/{project_id}/functions/{func_id}/catering",
    response_model=CateringPlanDetailResponse,
    summary="Get catering requirements dossier for a ceremony function",
    tags=["Catering Requirements"]
)
def get_function_catering_plan(
    project_id: str,
    func_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves the catering requirements dossier, guest breakdown, and menu for a specific ceremony.
    """
    plan = catering_service.get_catering_plan_for_function(db=db, project_id=project_id, function_id=func_id)
    return CateringPlanDetailResponse.model_validate(plan)


@router.post(
    "/projects/{project_id}/functions/{func_id}/catering",
    response_model=CateringPlanDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Define catering requirements for a wedding ceremony function",
    tags=["Catering Requirements"]
)
def create_function_catering_plan(
    project_id: str,
    func_id: str,
    plan_in: CateringPlanCreate,
    db: Session = Depends(get_db)
):
    """
    Initializes catering requirements for an event ceremony:
    - Automatically defaults guest count from parent wedding project if omitted.
    - Permits event-specific guest override without modifying parent project count.
    - Keeps dietary counts as flexible non-negative estimates without rigid total constraints.
    - Enforces 1-to-1 function-to-catering-plan constraint.
    """
    plan = catering_service.create_catering_plan(
        db=db, project_id=project_id, function_id=func_id, plan_in=plan_in
    )
    return CateringPlanDetailResponse.model_validate(plan)


@router.put(
    "/projects/{project_id}/functions/{func_id}/catering",
    response_model=CateringPlanDetailResponse,
    summary="Update catering requirements for a wedding ceremony function",
    tags=["Catering Requirements"]
)
def update_function_catering_plan(
    project_id: str,
    func_id: str,
    plan_in: CateringPlanUpdate,
    db: Session = Depends(get_db)
):
    """
    Updates catering requirements for a function.
    """
    existing = catering_service.get_catering_plan_for_function(db=db, project_id=project_id, function_id=func_id)
    plan = catering_service.update_catering_plan(db=db, catering_id=existing["id"], plan_in=plan_in)
    return CateringPlanDetailResponse.model_validate(plan)


# =====================================================================
# Direct Catering Plan Access
# =====================================================================

@router.get(
    "/catering/{catering_id}",
    response_model=CateringPlanDetailResponse,
    summary="Get catering plan details by plan ID",
    tags=["Catering Requirements"]
)
def get_catering_plan_by_id(
    catering_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves catering requirements, selected vendor, and menu items by plan ID.
    """
    plan = catering_service.get_catering_plan_by_id(db=db, catering_id=catering_id)
    return CateringPlanDetailResponse.model_validate(plan)


@router.put(
    "/catering/{catering_id}",
    response_model=CateringPlanDetailResponse,
    summary="Update catering plan specifications by plan ID",
    tags=["Catering Requirements"]
)
def update_catering_plan_by_id(
    catering_id: str,
    plan_in: CateringPlanUpdate,
    db: Session = Depends(get_db)
):
    """
    Directly updates catering requirements by catering plan ID.
    """
    plan = catering_service.update_catering_plan(db=db, catering_id=catering_id, plan_in=plan_in)
    return CateringPlanDetailResponse.model_validate(plan)


# =====================================================================
# Menu Items
# =====================================================================

@router.get(
    "/catering/{catering_id}/menu-items",
    response_model=List[CateringMenuItemResponse],
    summary="List organized courses and dishes for a catering plan",
    tags=["Catering Menus"]
)
def list_menu_items(
    catering_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns menu items for a catering plan grouped by courses.
    """
    items = catering_service.list_menu_items(db=db, catering_id=catering_id)
    return [CateringMenuItemResponse.model_validate(i) for i in items]


@router.post(
    "/catering/{catering_id}/menu-items",
    response_model=CateringMenuItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a dish or course item to the event menu",
    tags=["Catering Menus"]
)
def create_menu_item(
    catering_id: str,
    item_in: CateringMenuItemCreate,
    db: Session = Depends(get_db)
):
    """
    Appends a new dish with dietary tag, category, and quantity notes.
    """
    item = catering_service.create_menu_item(db=db, catering_id=catering_id, item_in=item_in)
    return CateringMenuItemResponse.model_validate(item)


@router.put(
    "/catering/{catering_id}/menu-items/{item_id}",
    response_model=CateringMenuItemResponse,
    summary="Update a menu item",
    tags=["Catering Menus"]
)
def update_menu_item(
    catering_id: str,
    item_id: str,
    item_in: CateringMenuItemUpdate,
    db: Session = Depends(get_db)
):
    """
    Updates a dish's name, description, dietary tag, or course category.
    Prevents cross-plan modification.
    """
    item = catering_service.update_menu_item(
        db=db, catering_id=catering_id, item_id=item_id, item_in=item_in
    )
    return CateringMenuItemResponse.model_validate(item)


@router.delete(
    "/catering/{catering_id}/menu-items/{item_id}",
    summary="Delete a dish from the catering menu",
    tags=["Catering Menus"]
)
def delete_menu_item(
    catering_id: str,
    item_id: str,
    db: Session = Depends(get_db)
):
    """
    Removes a dish from the menu. Prevents cross-plan deletion.
    """
    catering_service.delete_menu_item(db=db, catering_id=catering_id, item_id=item_id)
    return {"success": True, "message": f"Menu item '{item_id}' deleted."}


@router.post(
    "/catering/{catering_id}/menu-items/reorder",
    response_model=List[CateringMenuItemResponse],
    summary="Reorder courses and dishes within the menu",
    tags=["Catering Menus"]
)
def reorder_menu_items(
    catering_id: str,
    reorder_in: MenuItemReorderRequest,
    db: Session = Depends(get_db)
):
    """
    Updates the sequential display order of dishes.
    """
    items = catering_service.reorder_menu_items(db=db, catering_id=catering_id, reorder_in=reorder_in)
    return [CateringMenuItemResponse.model_validate(i) for i in items]


# =====================================================================
# Apply Presets to Menu
# =====================================================================

@router.post(
    "/catering/{catering_id}/apply-preset",
    response_model=List[CateringMenuItemResponse],
    summary="Apply luxury banquet template to a catering plan",
    tags=["Catering Presets"]
)
def apply_preset(
    catering_id: str,
    request: ApplyPresetRequest,
    db: Session = Depends(get_db)
):
    """
    Seeds a catering plan with dishes from a luxury preset template:
    - Mode 'append': keeps existing dishes and appends the preset dishes.
    - Mode 'replace': explicitly clears existing dishes and replaces them with preset dishes.
    - Items created are fully editable. Shared preset definition is never modified.
    """
    items = catering_service.apply_preset_to_plan(
        db=db, catering_id=catering_id, preset_id=request.preset_id, mode=request.mode
    )
    return [CateringMenuItemResponse.model_validate(i) for i in items]


# =====================================================================
# Catering Quotations & Costing Engine
# =====================================================================

@router.get(
    "/catering/{catering_id}/quotations",
    response_model=List[CateringQuotationResponse],
    summary="List competing vendor quotations for a catering plan",
    tags=["Catering Quotations"]
)
def list_quotations(
    catering_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns all submitted vendor quotation bids for a ceremony catering plan.
    Includes per-person rates, food subtotals, equipment charges, GST%, and total amounts.
    """
    quotations = catering_service.list_quotations(db=db, catering_id=catering_id)
    return [CateringQuotationResponse.model_validate(q) for q in quotations]


@router.post(
    "/catering/{catering_id}/quotations",
    response_model=CateringQuotationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a vendor quotation with transparent costing & configurable GST",
    tags=["Catering Quotations"]
)
def create_quotation(
    catering_id: str,
    quotation_in: CateringQuotationCreate,
    db: Session = Depends(get_db)
):
    """
    Records a vendor quotation bid:
    - Calculates food subtotal = round(perPersonRate * totalGuestCount, 2).
    - Applies configurable GST rate (0%, 5%, 12%, 18%, or any custom rate) to (food subtotal + equipment charges).
    - Computes total amount = food subtotal + equipment charges + gst amount with decimal rounding.
    """
    quotation = catering_service.create_quotation(
        db=db, catering_id=catering_id, quotation_in=quotation_in
    )
    return CateringQuotationResponse.model_validate(quotation)


@router.get(
    "/catering/{catering_id}/quotations/{quotation_id}",
    response_model=CateringQuotationResponse,
    summary="Retrieve vendor quotation dossier by ID",
    tags=["Catering Quotations"]
)
def get_quotation(
    catering_id: str,
    quotation_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves full breakdown of a single vendor quotation.
    """
    quotation = catering_service.get_quotation(
        db=db, catering_id=catering_id, quotation_id=quotation_id
    )
    return CateringQuotationResponse.model_validate(quotation)


@router.put(
    "/catering/{catering_id}/quotations/{quotation_id}",
    response_model=CateringQuotationResponse,
    summary="Update quotation terms and recalculate costing",
    tags=["Catering Quotations"]
)
def update_quotation(
    catering_id: str,
    quotation_id: str,
    quotation_in: CateringQuotationUpdate,
    db: Session = Depends(get_db)
):
    """
    Updates quotation terms (e.g. negotiated per-person rate, equipment fee, or GST rate)
    and automatically recalculates totals with decimal precision.
    """
    quotation = catering_service.update_quotation(
        db=db, catering_id=catering_id, quotation_id=quotation_id, quotation_in=quotation_in
    )
    return CateringQuotationResponse.model_validate(quotation)


@router.post(
    "/catering/{catering_id}/quotations/{quotation_id}/select",
    response_model=CateringQuotationSelectResponse,
    summary="Select winning vendor quotation and lock agreed contract pricing",
    tags=["Catering Quotations"]
)
def select_winning_quotation(
    catering_id: str,
    quotation_id: str,
    db: Session = Depends(get_db)
):
    """
    Selects winning caterer quotation for an event:
    1. Locks `catering_plans.selected_vendor_id` to the winning vendor.
    2. Locks `catering_plans.agreed_cost` to the quotation's total amount.
    3. Sets winning quotation status to 'Accepted'.
    4. Automatically transitions other active quotations for this plan to 'Rejected'.
    5. Preserves full audit trail and prevents cross-plan or cross-project contamination.
    """
    result = catering_service.select_winning_quotation(
        db=db, catering_id=catering_id, quotation_id=quotation_id
    )
    return CateringQuotationSelectResponse.model_validate(result)


# =====================================================================
# Catering Status Lifecycle (Stage 4)
# =====================================================================

@router.patch(
    "/catering/{catering_id}/status",
    response_model=CateringPlanDetailResponse,
    summary="Update catering lifecycle status with stage progression checks",
    tags=["Catering Lifecycle"]
)
def update_catering_status(
    catering_id: str,
    status_in: CateringStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Transitions catering requirements through the luxury wedding lifecycle:
    Draft -> Requirements Confirmed -> Quotation Requested -> Vendor Selected ->
    Menu Finalized -> Sent to Vendor -> Vendor Confirmed

    Enforces required stage validation, prerequisites, and logs an audit note.
    """
    plan = catering_service.update_catering_status(
        db=db, catering_id=catering_id, new_status=status_in.status, notes=status_in.notes
    )
    return CateringPlanDetailResponse.model_validate(plan)


# =====================================================================
# PDF Quotation Generation (Stage 5)
# =====================================================================

@router.get(
    "/catering/{catering_id}/quotations/{quotation_id}/pdf",
    summary="Download formatted luxury catering quotation PDF",
    tags=["Catering PDF"]
)
def download_quotation_pdf(
    catering_id: str,
    quotation_id: str,
    db: Session = Depends(get_db)
):
    """
    Generates and returns an elegant, branded wedding catering specification PDF.
    Reflects live database records without mock details.
    """
    plan = (
        db.query(CateringPlan)
        .filter(CateringPlan.id == catering_id)
        .options(
            joinedload(CateringPlan.function),
            joinedload(CateringPlan.project),
            joinedload(CateringPlan.menu_items),
        )
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Catering plan '{catering_id}' not found.")

    quotation = (
        db.query(CateringQuotation)
        .filter(CateringQuotation.id == quotation_id, CateringQuotation.catering_plan_id == catering_id)
        .options(joinedload(CateringQuotation.vendor))
        .first()
    )
    if not quotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quotation '{quotation_id}' not found under catering plan '{catering_id}'."
        )

    pdf_bytes = pdf_service.generate_catering_quotation_pdf(plan=plan, quotation=quotation)
    ref = quotation.quotation_reference or quotation.id
    filename = f"royal_knot_quotation_{ref.replace(' ', '_')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        }
    )


@router.get(
    "/catering/{catering_id}/pdf",
    summary="Download formal catering specification PDF for event",
    tags=["Catering PDF"]
)
def download_catering_plan_pdf(
    catering_id: str,
    db: Session = Depends(get_db)
):
    """
    Generates PDF for the event catering plan using the selected or latest quotation.
    """
    plan = (
        db.query(CateringPlan)
        .filter(CateringPlan.id == catering_id)
        .options(
            joinedload(CateringPlan.function),
            joinedload(CateringPlan.project),
            joinedload(CateringPlan.selected_vendor),
            joinedload(CateringPlan.menu_items),
            joinedload(CateringPlan.quotations),
        )
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Catering plan '{catering_id}' not found.")

    # Find accepted quote or latest quote or fallback mock quote
    quotation = None
    if plan.quotations:
        quotation = next((q for q in plan.quotations if q.status == "Accepted"), plan.quotations[0])

    if not quotation:
        # Create a transient quotation representation from plan attributes
        vendor = plan.selected_vendor
        rate = (plan.budget / plan.guest_count) if (plan.budget and plan.guest_count) else 0
        food = plan.budget or 0
        quotation = CateringQuotation(
            id=f"SPEC-{plan.id}",
            catering_plan_id=plan.id,
            vendor_id=vendor.id if vendor else "VND-TBD",
            quotation_reference=f"SPEC-{plan.id}",
            per_person_rate=rate,
            total_guest_count=plan.guest_count,
            food_subtotal=food,
            equipment_charges=0.00,
            gst_rate_percent=18.00,
            gst_amount=round(float(food) * 0.18, 2),
            total_amount=round(float(food) * 1.18, 2),
            status=plan.status,
            notes=plan.notes,
        )
        quotation.vendor = vendor

    pdf_bytes = pdf_service.generate_catering_quotation_pdf(plan=plan, quotation=quotation)
    filename = f"royal_knot_catering_spec_{catering_id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        }
    )


# =====================================================================
# WhatsApp Sharing & Communication Logging (Stage 6)
# =====================================================================

@router.post(
    "/catering/{catering_id}/share-whatsapp",
    response_model=CateringWhatsAppShareResponse,
    summary="Generate authentic WhatsApp deep-link and record communication event",
    tags=["Catering Communications"]
)
def share_catering_whatsapp(
    catering_id: str,
    share_in: CateringWhatsAppShareRequest,
    db: Session = Depends(get_db)
):
    """
    Generates a pre-filled WhatsApp wa.me link with live event specs and logs the action.
    """
    return catering_service.share_quotation_via_whatsapp(
        db=db,
        catering_id=catering_id,
        quotation_id=share_in.quotation_id,
        vendor_id=share_in.vendor_id,
        recipient_phone=share_in.recipient_phone,
        custom_message=share_in.custom_message,
    )


@router.post(
    "/catering/{catering_id}/quotations/{quotation_id}/share-whatsapp",
    response_model=CateringWhatsAppShareResponse,
    summary="Generate WhatsApp deep-link for a specific vendor quotation",
    tags=["Catering Communications"]
)
def share_quotation_whatsapp(
    catering_id: str,
    quotation_id: str,
    share_in: CateringWhatsAppShareRequest,
    db: Session = Depends(get_db)
):
    """
    Generates a pre-filled WhatsApp wa.me link for a specific vendor quotation and logs communication.
    """
    return catering_service.share_quotation_via_whatsapp(
        db=db,
        catering_id=catering_id,
        quotation_id=quotation_id,
        vendor_id=share_in.vendor_id,
        recipient_phone=share_in.recipient_phone,
        custom_message=share_in.custom_message,
    )


@router.get(
    "/catering/{catering_id}/communications",
    summary="List all communication logs for a catering plan",
    tags=["Catering Communications"]
)
def list_catering_communications(
    catering_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns audit trail of communication events (e.g. WhatsApp manual share link generation).
    """
    return catering_service.list_communications(db=db, catering_id=catering_id)



