import uuid
import re
import urllib.parse
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.project import WeddingProject, WeddingFunction
from app.models.vendor import Vendor
from app.models.catering import CateringPlan, CateringMenuItem, CateringQuotation, CateringCommunicationLog
from app.schemas.catering import (
    CateringPlanCreate,
    CateringPlanUpdate,
    CateringMenuItemCreate,
    CateringMenuItemUpdate,
    MenuItemReorderRequest,
    CateringPlanResponse,
    CateringPlanDetailResponse,
    CateringMenuItemResponse,
    CateringQuotationCreate,
    CateringQuotationUpdate,
    CateringQuotationResponse,
    CateringQuotationSelectResponse,
)
from app.schemas.vendor import VendorResponse
from app.services.catering_presets import (
    get_available_presets,
    get_preset_by_id,
    get_preset_items,
)


class CateringService:

    @staticmethod
    def generate_catering_id() -> str:
        uid = uuid.uuid4().hex[:6].upper()
        return f"CAT-{uid}"

    @staticmethod
    def generate_item_id() -> str:
        uid = uuid.uuid4().hex[:6].upper()
        return f"ITM-{uid}"

    # =====================================================================
    # Helpers & Serializers
    # =====================================================================

    def serialize_catering_plan(self, plan: CateringPlan, include_items: bool = False) -> Dict[str, Any]:
        """Serializes CateringPlan with joined metadata into schema response dict."""
        selected_vendor_dict = None
        if plan.selected_vendor:
            selected_vendor_dict = VendorResponse.model_validate(plan.selected_vendor)

        data = {
            "id": plan.id,
            "projectId": plan.project_id,
            "functionId": plan.function_id,
            "serviceStyle": plan.service_style,
            "cuisinePreferences": plan.cuisine_preferences,
            "guestCount": plan.guest_count,
            "vegCount": plan.veg_count,
            "nonVegCount": plan.non_veg_count,
            "jainCount": plan.jain_count,
            "dietaryNotes": plan.dietary_notes,
            "serviceTimings": plan.service_timings,
            "location": plan.location,
            "budget": plan.budget,
            "selectedVendorId": plan.selected_vendor_id,
            "agreedCost": plan.agreed_cost,
            "status": plan.status,
            "notes": plan.notes,
            "createdAt": plan.created_at,
            "updatedAt": plan.updated_at,
            "functionName": plan.function.function_name if plan.function else None,
            "functionDate": plan.function.function_date if plan.function else None,
            "functionVenue": plan.function.venue if plan.function else None,
            "projectName": plan.project.project_name if plan.project else None,
            "projectGuestCount": plan.project.guest_count if plan.project else None,
            "selectedVendor": selected_vendor_dict,
            "menuItemsCount": len(plan.menu_items) if plan.menu_items else 0,
            "quotationsCount": len(plan.quotations) if plan.quotations else 0,
        }

        if include_items:
            data["menuItems"] = [
                CateringMenuItemResponse.model_validate(i)
                for i in sorted(plan.menu_items, key=lambda x: x.display_order)
            ] if plan.menu_items else []

        return data

    def _verify_project_and_function(
        self, db: Session, project_id: str, function_id: Optional[str] = None
    ) -> tuple[WeddingProject, Optional[WeddingFunction]]:
        """Ensures wedding project and ceremony function exist and are validly related."""
        project = db.query(WeddingProject).filter(WeddingProject.id == project_id).first()
        if not project or project.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Wedding project '{project_id}' not found."
            )

        if project.status == "Cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Wedding project '{project_id}' is cancelled. Cannot manage catering plans for cancelled projects."
            )

        function = None
        if function_id:
            function = db.query(WeddingFunction).filter(WeddingFunction.id == function_id).first()
            if not function:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Wedding ceremony function '{function_id}' not found."
                )
            if function.project_id != project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Wedding function '{function_id}' does not belong to project '{project_id}'."
                )

        return project, function

    # =====================================================================
    # Catering Plans Operations
    # =====================================================================

    def list_catering_plans_for_project(self, db: Session, project_id: str) -> List[Dict[str, Any]]:
        """Lists all event-linked catering plans for a given wedding project."""
        self._verify_project_and_function(db, project_id)
        plans = (
            db.query(CateringPlan)
            .filter(CateringPlan.project_id == project_id)
            .options(
                joinedload(CateringPlan.function),
                joinedload(CateringPlan.project),
                joinedload(CateringPlan.selected_vendor),
                joinedload(CateringPlan.menu_items),
                joinedload(CateringPlan.quotations),
            )
            .all()
        )
        return [self.serialize_catering_plan(p, include_items=False) for p in plans]

    def get_catering_plan_for_function(
        self, db: Session, project_id: str, function_id: str
    ) -> Dict[str, Any]:
        """Retrieves catering requirements dossier for a specific ceremony event."""
        self._verify_project_and_function(db, project_id, function_id)
        plan = (
            db.query(CateringPlan)
            .filter(CateringPlan.project_id == project_id, CateringPlan.function_id == function_id)
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No catering plan registered for function '{function_id}' in project '{project_id}'."
            )
        return self.serialize_catering_plan(plan, include_items=True)

    def get_catering_plan_by_id(self, db: Session, catering_id: str) -> Dict[str, Any]:
        """Retrieves catering plan by plan ID."""
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catering plan '{catering_id}' not found."
            )
        return self.serialize_catering_plan(plan, include_items=True)

    def create_catering_plan(
        self, db: Session, project_id: str, function_id: str, plan_in: CateringPlanCreate
    ) -> Dict[str, Any]:
        """
        Creates event-specific catering plan.
        - Defaults guest_count from wedding project if omitted.
        - Keeps dietary guest counts as flexible estimates.
        - Enforces unique function-to-catering-plan constraint.
        """
        project, function = self._verify_project_and_function(db, project_id, function_id)

        # Check unique constraint
        existing = db.query(CateringPlan).filter(CateringPlan.function_id == function_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A catering plan already exists for function '{function_id}' ({existing.id}). Use PUT to update."
            )

        # Default guest_count from project if omitted
        effective_guest_count = plan_in.guest_count if (plan_in.guest_count and plan_in.guest_count > 0) else project.guest_count

        # Default venue location from function if omitted
        effective_location = plan_in.location or function.venue

        # Check vendor if selected
        if plan_in.selected_vendor_id:
            vendor = db.query(Vendor).filter(Vendor.id == plan_in.selected_vendor_id).first()
            if not vendor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Selected vendor '{plan_in.selected_vendor_id}' not found."
                )

        plan = CateringPlan(
            id=self.generate_catering_id(),
            project_id=project_id,
            function_id=function_id,
            service_style=plan_in.service_style,
            cuisine_preferences=plan_in.cuisine_preferences,
            guest_count=effective_guest_count,
            veg_count=plan_in.veg_count,
            non_veg_count=plan_in.non_veg_count,
            jain_count=plan_in.jain_count,
            dietary_notes=plan_in.dietary_notes,
            service_timings=plan_in.service_timings or f"{function.start_time or ''} - {function.end_time or ''}".strip(" - "),
            location=effective_location,
            budget=plan_in.budget or 0,
            selected_vendor_id=plan_in.selected_vendor_id,
            agreed_cost=plan_in.agreed_cost,
            status="Draft",
            notes=plan_in.notes,
        )

        db.add(plan)
        db.commit()
        db.refresh(plan)

        # Fetch with relationships for response
        return self.get_catering_plan_by_id(db, plan.id)

    def update_catering_plan(
        self, db: Session, catering_id: str, plan_in: CateringPlanUpdate
    ) -> Dict[str, Any]:
        """Updates catering requirements without altering master project metrics."""
        plan = db.query(CateringPlan).filter(CateringPlan.id == catering_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catering plan '{catering_id}' not found."
            )

        if plan_in.selected_vendor_id:
            vendor = db.query(Vendor).filter(Vendor.id == plan_in.selected_vendor_id).first()
            if not vendor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Selected vendor '{plan_in.selected_vendor_id}' not found."
                )
            plan.selected_vendor_id = plan_in.selected_vendor_id
        elif plan_in.selected_vendor_id is not None:
            plan.selected_vendor_id = None

        if plan_in.service_style is not None:
            plan.service_style = plan_in.service_style
        if plan_in.cuisine_preferences is not None:
            plan.cuisine_preferences = plan_in.cuisine_preferences
        if plan_in.guest_count is not None:
            plan.guest_count = plan_in.guest_count
        if plan_in.veg_count is not None:
            plan.veg_count = plan_in.veg_count
        if plan_in.non_veg_count is not None:
            plan.non_veg_count = plan_in.non_veg_count
        if plan_in.jain_count is not None:
            plan.jain_count = plan_in.jain_count
        if plan_in.dietary_notes is not None:
            plan.dietary_notes = plan_in.dietary_notes
        if plan_in.service_timings is not None:
            plan.service_timings = plan_in.service_timings
        if plan_in.location is not None:
            plan.location = plan_in.location
        if plan_in.budget is not None:
            plan.budget = plan_in.budget
        if plan_in.agreed_cost is not None:
            plan.agreed_cost = plan_in.agreed_cost
        if plan_in.status is not None:
            plan.status = plan_in.status
        if plan_in.notes is not None:
            plan.notes = plan_in.notes

        db.commit()
        db.refresh(plan)
        return self.get_catering_plan_by_id(db, plan.id)

    # =====================================================================
    # Menu Items Operations
    # =====================================================================

    def list_menu_items(self, db: Session, catering_id: str) -> List[CateringMenuItem]:
        """Lists all dishes and courses for a catering plan."""
        # Verify plan exists
        plan = db.query(CateringPlan).filter(CateringPlan.id == catering_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catering plan '{catering_id}' not found."
            )
        return (
            db.query(CateringMenuItem)
            .filter(CateringMenuItem.catering_plan_id == catering_id)
            .order_by(CateringMenuItem.display_order.asc(), CateringMenuItem.course_category.asc())
            .all()
        )

    def create_menu_item(
        self, db: Session, catering_id: str, item_in: CateringMenuItemCreate
    ) -> CateringMenuItem:
        """Adds a food course item to a catering plan."""
        plan = db.query(CateringPlan).filter(CateringPlan.id == catering_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catering plan '{catering_id}' not found."
            )

        # Calculate display order if default 1 was used and items exist
        display_order = item_in.display_order
        if display_order == 1:
            max_order = (
                db.query(func.max(CateringMenuItem.display_order))
                .filter(CateringMenuItem.catering_plan_id == catering_id)
                .scalar()
            )
            if max_order is not None:
                display_order = max_order + 1

        item = CateringMenuItem(
            id=self.generate_item_id(),
            catering_plan_id=catering_id,
            course_category=item_in.course_category.strip(),
            item_name=item_in.item_name.strip(),
            description=item_in.description.strip() if item_in.description else None,
            dietary_tag=item_in.dietary_tag.strip(),
            quantity_note=item_in.quantity_note.strip() if item_in.quantity_note else None,
            display_order=display_order,
        )

        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def update_menu_item(
        self, db: Session, catering_id: str, item_id: str, item_in: CateringMenuItemUpdate
    ) -> CateringMenuItem:
        """Updates a menu dish ensuring it belongs to the given catering plan."""
        item = (
            db.query(CateringMenuItem)
            .filter(CateringMenuItem.id == item_id, CateringMenuItem.catering_plan_id == catering_id)
            .first()
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu item '{item_id}' not found under catering plan '{catering_id}'."
            )

        if item_in.course_category is not None:
            item.course_category = item_in.course_category.strip()
        if item_in.item_name is not None:
            item.item_name = item_in.item_name.strip()
        if item_in.description is not None:
            item.description = item_in.description.strip() or None
        if item_in.dietary_tag is not None:
            item.dietary_tag = item_in.dietary_tag.strip()
        if item_in.quantity_note is not None:
            item.quantity_note = item_in.quantity_note.strip() or None
        if item_in.display_order is not None:
            item.display_order = item_in.display_order

        db.commit()
        db.refresh(item)
        return item

    def delete_menu_item(self, db: Session, catering_id: str, item_id: str) -> None:
        """Deletes a menu item from the catering plan."""
        item = (
            db.query(CateringMenuItem)
            .filter(CateringMenuItem.id == item_id, CateringMenuItem.catering_plan_id == catering_id)
            .first()
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu item '{item_id}' not found under catering plan '{catering_id}'."
            )
        db.delete(item)
        db.commit()

    def reorder_menu_items(
        self, db: Session, catering_id: str, reorder_in: MenuItemReorderRequest
    ) -> List[CateringMenuItem]:
        """Updates display order for a collection of dishes."""
        plan = db.query(CateringPlan).filter(CateringPlan.id == catering_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catering plan '{catering_id}' not found."
            )

        for ro in reorder_in.items:
            item = (
                db.query(CateringMenuItem)
                .filter(CateringMenuItem.id == ro.id, CateringMenuItem.catering_plan_id == catering_id)
                .first()
            )
            if item:
                item.display_order = ro.display_order

        db.commit()
        return self.list_menu_items(db, catering_id)

    # =====================================================================
    # Menu Presets Operations
    # =====================================================================

    def list_presets(self) -> List[Dict[str, Any]]:
        """Returns catalog of luxury starter banquet templates."""
        return get_available_presets()

    def get_preset_details(self, preset_id: str) -> Dict[str, Any]:
        """Returns detailed template structure."""
        try:
            return get_preset_by_id(preset_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    def apply_preset_to_plan(
        self, db: Session, catering_id: str, preset_id: str, mode: str = "append"
    ) -> List[CateringMenuItem]:
        """
        Applies a luxury menu preset to a catering plan.
        - Does NOT modify the shared preset blueprint.
        - Resulting items are stored as editable CateringMenuItems.
        - If mode == 'replace', safely clears existing items first.
        - If mode == 'append', preserves existing items and offsets display orders.
        """
        plan = db.query(CateringPlan).filter(CateringPlan.id == catering_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catering plan '{catering_id}' not found."
            )

        try:
            preset = get_preset_by_id(preset_id)
            preset_items = get_preset_items(preset_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

        if mode == "replace":
            # Safely clear existing items
            db.query(CateringMenuItem).filter(CateringMenuItem.catering_plan_id == catering_id).delete()
            base_order = 0
        else:
            # Mode == "append": offset display order
            max_order = (
                db.query(func.max(CateringMenuItem.display_order))
                .filter(CateringMenuItem.catering_plan_id == catering_id)
                .scalar()
            )
            base_order = max_order if max_order is not None else 0

        # Update recommended service style & cuisine if not already set
        if not plan.service_style or plan.service_style == "Silver Platter Degustation":
            plan.service_style = preset.get("recommended_service_style", plan.service_style)
        if not plan.cuisine_preferences:
            plan.cuisine_preferences = preset.get("cuisine_preference")

        # Create editable menu item rows
        new_items = []
        for dish in preset_items:
            item = CateringMenuItem(
                id=self.generate_item_id(),
                catering_plan_id=catering_id,
                course_category=dish["course_category"],
                item_name=dish["item_name"],
                description=dish.get("description"),
                dietary_tag=dish.get("dietary_tag", "Vegetarian"),
                quantity_note=dish.get("quantity_note"),
                display_order=base_order + dish["display_order"],
            )
            db.add(item)
            new_items.append(item)

        db.commit()
        return self.list_menu_items(db, catering_id)

    # =====================================================================
    # Quotations & Costing Engine
    # =====================================================================

    @staticmethod
    def generate_quotation_id() -> str:
        uid = uuid.uuid4().hex[:6].upper()
        return f"QUO-{uid}"

    @staticmethod
    def compute_quotation_costing(
        per_person_rate: Decimal,
        total_guest_count: int,
        equipment_charges: Decimal,
        gst_rate_percent: Decimal,
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Executes decimal-safe costing calculation:
        1. food_subtotal = round_2_places(per_person_rate * total_guest_count)
        2. taxable_subtotal = food_subtotal + round_2_places(equipment_charges)
        3. gst_amount = round_2_places(taxable_subtotal * (gst_rate_percent / 100))
        4. total_amount = taxable_subtotal + gst_amount

        NOTE: GST applies to the combined food subtotal and equipment charges,
        which aligns with luxury wedding catering service billing standards in India.
        Configurable GST rate supports 0%, 5%, 12%, 18%, or any custom rate.
        """
        TWO_PLACES = Decimal("0.01")
        rate = Decimal(str(per_person_rate))
        pax = Decimal(str(total_guest_count))
        food_subtotal = (rate * pax).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        equipment = Decimal(str(equipment_charges)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        taxable_subtotal = food_subtotal + equipment

        gst_rate = Decimal(str(gst_rate_percent))
        gst_amount = (taxable_subtotal * (gst_rate / Decimal("100.00"))).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        total_amount = (taxable_subtotal + gst_amount).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        return food_subtotal, gst_amount, total_amount

    def serialize_quotation(self, q: CateringQuotation) -> Dict[str, Any]:
        """Transforms CateringQuotation ORM model into schema-compatible dictionary."""
        return {
            "id": q.id,
            "cateringPlanId": q.catering_plan_id,
            "vendorId": q.vendor_id,
            "quotationReference": q.quotation_reference,
            "perPersonRate": q.per_person_rate,
            "totalGuestCount": q.total_guest_count,
            "foodSubtotal": q.food_subtotal,
            "equipmentCharges": q.equipment_charges,
            "gstRatePercent": q.gst_rate_percent,
            "gstAmount": q.gst_amount,
            "totalAmount": q.total_amount,
            "status": q.status,
            "validityDate": q.validity_date,
            "notes": q.notes,
            "createdAt": q.created_at,
            "updatedAt": q.updated_at,
            "vendorName": q.vendor.name if q.vendor else None,
            "vendorPhone": q.vendor.phone if q.vendor else None,
            "vendorContactPerson": q.vendor.contact_person if q.vendor else None,
            "vendorCity": q.vendor.city if q.vendor else None,
            "vendorRating": q.vendor.rating if q.vendor else None,
        }

    def list_quotations(self, db: Session, catering_id: str) -> List[Dict[str, Any]]:
        """Lists all vendor quotations submitted for a specific catering plan."""
        plan = db.query(CateringPlan).filter(CateringPlan.id == catering_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catering plan '{catering_id}' not found."
            )
        quotations = (
            db.query(CateringQuotation)
            .filter(CateringQuotation.catering_plan_id == catering_id)
            .options(joinedload(CateringQuotation.vendor))
            .order_by(CateringQuotation.created_at.desc())
            .all()
        )
        return [self.serialize_quotation(q) for q in quotations]

    def get_quotation(self, db: Session, catering_id: str, quotation_id: str) -> Dict[str, Any]:
        """Retrieves a specific quotation dossier ensuring plan isolation."""
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
        return self.serialize_quotation(quotation)

    def create_quotation(
        self, db: Session, catering_id: str, quotation_in: CateringQuotationCreate
    ) -> Dict[str, Any]:
        """
        Records a vendor quotation with transparent costing calculations:
        - Defaults guest count from catering plan if omitted.
        - Calculates food subtotal, GST amount, and total amount with decimal-safe rounding.
        - Supports arbitrary configurable GST rates (0%, 5%, 12%, 18%, or custom).
        """
        plan = db.query(CateringPlan).filter(CateringPlan.id == catering_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catering plan '{catering_id}' not found."
            )

        vendor = db.query(Vendor).filter(Vendor.id == quotation_in.vendor_id).first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vendor '{quotation_in.vendor_id}' not found."
            )

        effective_guest_count = quotation_in.total_guest_count or plan.guest_count
        food_subtotal, gst_amount, total_amount = self.compute_quotation_costing(
            per_person_rate=quotation_in.per_person_rate,
            total_guest_count=effective_guest_count,
            equipment_charges=quotation_in.equipment_charges,
            gst_rate_percent=quotation_in.gst_rate_percent,
        )

        quotation = CateringQuotation(
            id=self.generate_quotation_id(),
            catering_plan_id=catering_id,
            vendor_id=quotation_in.vendor_id,
            quotation_reference=quotation_in.quotation_reference or f"QUO-{uuid.uuid4().hex[:4].upper()}",
            per_person_rate=quotation_in.per_person_rate,
            total_guest_count=effective_guest_count,
            food_subtotal=food_subtotal,
            equipment_charges=quotation_in.equipment_charges,
            gst_rate_percent=quotation_in.gst_rate_percent,
            gst_amount=gst_amount,
            total_amount=total_amount,
            status="Received",
            validity_date=quotation_in.validity_date,
            notes=quotation_in.notes,
        )

        db.add(quotation)
        db.commit()
        db.refresh(quotation)
        return self.get_quotation(db, catering_id, quotation.id)

    def update_quotation(
        self, db: Session, catering_id: str, quotation_id: str, quotation_in: CateringQuotationUpdate
    ) -> Dict[str, Any]:
        """Updates quotation details and recalculates costing when pricing or tax terms change."""
        quotation = (
            db.query(CateringQuotation)
            .filter(CateringQuotation.id == quotation_id, CateringQuotation.catering_plan_id == catering_id)
            .first()
        )
        if not quotation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quotation '{quotation_id}' not found under catering plan '{catering_id}'."
            )

        if quotation_in.per_person_rate is not None:
            quotation.per_person_rate = quotation_in.per_person_rate
        if quotation_in.total_guest_count is not None:
            quotation.total_guest_count = quotation_in.total_guest_count
        if quotation_in.equipment_charges is not None:
            quotation.equipment_charges = quotation_in.equipment_charges
        if quotation_in.gst_rate_percent is not None:
            quotation.gst_rate_percent = quotation_in.gst_rate_percent
        if quotation_in.validity_date is not None:
            quotation.validity_date = quotation_in.validity_date
        if quotation_in.notes is not None:
            quotation.notes = quotation_in.notes
        if quotation_in.status is not None:
            quotation.status = quotation_in.status

        # Recalculate costing
        food_subtotal, gst_amount, total_amount = self.compute_quotation_costing(
            per_person_rate=quotation.per_person_rate,
            total_guest_count=quotation.total_guest_count,
            equipment_charges=quotation.equipment_charges,
            gst_rate_percent=quotation.gst_rate_percent,
        )
        quotation.food_subtotal = food_subtotal
        quotation.gst_amount = gst_amount
        quotation.total_amount = total_amount

        db.commit()
        db.refresh(quotation)
        return self.get_quotation(db, catering_id, quotation.id)

    def select_winning_quotation(
        self, db: Session, catering_id: str, quotation_id: str
    ) -> Dict[str, Any]:
        """
        Selects winning quotation for a catering plan:
        1. Validates quotation exists and belongs to this catering plan.
        2. Sets catering_plans.selected_vendor_id to winning vendor.
        3. Sets catering_plans.agreed_cost to winning total amount.
        4. Sets winning quotation status to 'Accepted'.
        5. Sets other quotations for this plan to 'Rejected' (preserving audit trail).
        """
        plan = db.query(CateringPlan).filter(CateringPlan.id == catering_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catering plan '{catering_id}' not found."
            )

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

        # Update catering plan
        plan.selected_vendor_id = quotation.vendor_id
        plan.agreed_cost = quotation.total_amount

        # Mark winning quotation as Accepted
        quotation.status = "Accepted"

        # Mark other quotations as Rejected
        db.query(CateringQuotation).filter(
            CateringQuotation.catering_plan_id == catering_id,
            CateringQuotation.id != quotation_id,
            CateringQuotation.status.in_(["Received", "Under Review"])
        ).update({"status": "Rejected"}, synchronize_session=False)

        db.commit()
        db.refresh(plan)
        db.refresh(quotation)

        return {
            "success": True,
            "message": f"Quotation '{quotation.id}' from '{quotation.vendor.name if quotation.vendor else quotation.vendor_id}' selected as winning caterer.",
            "cateringPlanId": plan.id,
            "selectedVendorId": plan.selected_vendor_id,
            "agreedCost": plan.agreed_cost,
            "selectedQuotationId": quotation.id,
            "selectedQuotation": self.serialize_quotation(quotation),
        }

    # =====================================================================
    # Catering Status Lifecycle Workflow (Stage 4)
    # =====================================================================

    STATUS_LIFECYCLE_ORDER = [
        "Draft",
        "Requirements Confirmed",
        "Quotation Requested",
        "Vendor Selected",
        "Menu Finalized",
        "Sent to Vendor",
        "Vendor Confirmed"
    ]

    def update_catering_status(
        self, db: Session, catering_id: str, new_status: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Manages the formal catering status lifecycle transitions:
        Draft -> Requirements Confirmed -> Quotation Requested -> Vendor Selected ->
        Menu Finalized -> Sent to Vendor -> Vendor Confirmed

        Enforces:
        - Rejection of invalid status strings.
        - Prevention of skipped required stages (cannot jump forward multiple steps).
        - 'Requirements Confirmed' requires positive guest count.
        - 'Vendor Selected' requires winning quotation and selected vendor.
        - 'Menu Finalized' requires at least 1 menu item.
        - 'Sent to Vendor' and 'Vendor Confirmed' require selected vendor.
        - Backwards transitions (rollbacks) are allowed for renegotiations.
        - Appends transition audit trail to plan notes.
        """
        plan = db.query(CateringPlan).filter(CateringPlan.id == catering_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catering plan '{catering_id}' not found."
            )

        if new_status not in self.STATUS_LIFECYCLE_ORDER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid catering status '{new_status}'. Allowed statuses: {', '.join(self.STATUS_LIFECYCLE_ORDER)}"
            )

        old_status = plan.status
        if old_status == new_status:
            return self.get_catering_plan_by_id(db, catering_id)

        curr_idx = self.STATUS_LIFECYCLE_ORDER.index(old_status) if old_status in self.STATUS_LIFECYCLE_ORDER else 0
        target_idx = self.STATUS_LIFECYCLE_ORDER.index(new_status)

        # Disallow skipping forward
        if target_idx > curr_idx + 1:
            next_expected = self.STATUS_LIFECYCLE_ORDER[curr_idx + 1]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status progression: cannot transition directly from '{old_status}' to '{new_status}'. Next required stage is '{next_expected}'."
            )

        # Stage prerequisite validation rules
        if new_status == "Requirements Confirmed":
            if not plan.guest_count or plan.guest_count <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot confirm requirements without specifying a valid positive guest count."
                )

        elif new_status == "Vendor Selected":
            if not plan.selected_vendor_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot advance to 'Vendor Selected' without selecting a winning vendor quotation."
                )
            accepted_quote = db.query(CateringQuotation).filter(
                CateringQuotation.catering_plan_id == catering_id,
                CateringQuotation.status == "Accepted"
            ).first()
            if not accepted_quote:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot advance to 'Vendor Selected' without an accepted winning vendor quotation."
                )

        elif new_status == "Menu Finalized":
            item_count = db.query(CateringMenuItem).filter(CateringMenuItem.catering_plan_id == catering_id).count()
            if item_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot finalize menu with zero dishes. Add courses or apply a starting preset template first."
                )

        elif new_status in ("Sent to Vendor", "Vendor Confirmed"):
            if not plan.selected_vendor_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot transition to '{new_status}' without an assigned vendor."
                )

        # Record audit trail
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        audit_note = f"[Status Transition {timestamp}] Changed from '{old_status}' to '{new_status}'."
        if notes:
            audit_note += f" Notes: {notes.strip()}"
        plan.notes = f"{plan.notes}\n{audit_note}".strip() if plan.notes else audit_note
        plan.status = new_status

        db.commit()
        db.refresh(plan)
        return self.get_catering_plan_by_id(db, catering_id)

    # =====================================================================
    # WhatsApp Sharing & Communication Logging (Stage 6)
    # =====================================================================

    def share_quotation_via_whatsapp(
        self,
        db: Session,
        catering_id: str,
        quotation_id: Optional[str] = None,
        vendor_id: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        custom_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates an authentic WhatsApp manual-share link (wa.me) pre-filled with formal
        palace catering celebration details, and logs an accurate communication event.
        Does NOT fabricate external API deliveries or claim fake delivered statuses.
        """
        plan = db.query(CateringPlan).filter(CateringPlan.id == catering_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catering plan '{catering_id}' not found."
            )

        quotation = None
        if quotation_id:
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
        else:
            # Pick winning quote or latest quote
            quotation = (
                db.query(CateringQuotation)
                .filter(CateringQuotation.catering_plan_id == catering_id)
                .options(joinedload(CateringQuotation.vendor))
                .order_by(CateringQuotation.status == "Accepted", CateringQuotation.created_at.desc())
                .first()
            )

        # Resolve vendor (explicit vendor_id takes precedence, then quotation vendor, then selected vendor)
        target_vendor = None
        if vendor_id:
            target_vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        elif quotation and quotation.vendor:
            target_vendor = quotation.vendor
        elif plan.selected_vendor:
            target_vendor = plan.selected_vendor

        # Resolve phone
        target_phone = None
        if recipient_phone and recipient_phone.strip():
            target_phone = recipient_phone.strip()
        elif target_vendor and target_vendor.phone and target_vendor.phone.strip():
            target_phone = target_vendor.phone.strip()

        if not target_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No telephone number available for WhatsApp communication. Please provide recipientPhone or update vendor phone."
            )

        # Normalize digits for wa.me URL
        raw_digits = re.sub(r"[^\d]", "", target_phone)
        if len(raw_digits) == 10:
            clean_digits = f"91{raw_digits}"
        elif raw_digits.startswith("0") and len(raw_digits) == 11:
            clean_digits = f"91{raw_digits[1:]}"
        else:
            clean_digits = raw_digits

        if len(clean_digits) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Telephone number '{target_phone}' contains insufficient digits for WhatsApp routing."
            )

        # Compose formal concierge invitation text
        project_name = plan.project.project_name if plan.project else "Luxury Wedding Celebration"
        func_name = plan.function.function_name if plan.function else "Ceremony Banquet"
        func_date = plan.function.function_date.strftime("%d %B %Y") if plan.function and plan.function.function_date else "Scheduled"
        func_venue = plan.location or (plan.function.venue if plan.function else "Palace Venue")
        func_pax = quotation.total_guest_count if quotation else plan.guest_count
        quo_ref = quotation.quotation_reference if quotation else "Preliminary Spec"
        cost_str = f"₹{quotation.total_amount:,.2f}" if quotation else (f"₹{plan.agreed_cost:,.2f}" if plan.agreed_cost else "As Agreed")
        vendor_name = target_vendor.name if target_vendor else "Catering Partner"

        message_body = (
            f"Namaste {vendor_name},\n\n"
            f"Greetings from The Royal Knot Luxury Wedding Concierge.\n\n"
            f"Regarding the catering specifications for '{project_name}':\n"
            f"• Ceremony: {func_name}\n"
            f"• Event Date: {func_date} ({plan.service_timings or 'Banquet'})\n"
            f"• Palace Venue: {func_venue}\n"
            f"• Target Guest Count: {func_pax} Pax\n"
            f"• Quotation Ref: {quo_ref}\n"
            f"• Total Quoted Investment: {cost_str} (incl. GST)\n\n"
            f"{custom_message.strip() if custom_message else 'Please review the catering courses and terms. We look forward to executing a memorable celebration.'}\n\n"
            f"Warm regards,\nThe Royal Knot Planning Desk"
        )

        encoded_text = urllib.parse.quote(message_body)
        share_url = f"https://wa.me/{clean_digits}?text={encoded_text}"
        pdf_url = f"/api/v1/catering/{catering_id}/quotations/{quotation.id}/pdf" if quotation else f"/api/v1/catering/{catering_id}/pdf"

        # Accurately record communication event in database
        comm_id = f"COM-{uuid.uuid4().hex[:6].upper()}"
        comm_log = CateringCommunicationLog(
            id=comm_id,
            catering_plan_id=catering_id,
            vendor_id=target_vendor.id if target_vendor else None,
            communication_type="WhatsApp Manual Share",
            recipient_phone=target_phone.strip(),
            message_text=message_body,
            pdf_download_url=pdf_url,
            status="Initiated",
            initiated_by="Agency Staff",
            notes="Manual WhatsApp share link generated for caterer quotation."
        )
        db.add(comm_log)
        db.commit()
        db.refresh(comm_log)

        return {
            "success": True,
            "mode": "manual_whatsapp_link",
            "shareUrl": share_url,
            "recipientPhone": target_phone.strip(),
            "messageText": message_body,
            "communicationId": comm_log.id,
        }

    def list_communications(self, db: Session, catering_id: str) -> List[Dict[str, Any]]:
        """Lists all communication events initiated for this catering plan."""
        plan = db.query(CateringPlan).filter(CateringPlan.id == catering_id).first()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Catering plan '{catering_id}' not found."
            )
        logs = (
            db.query(CateringCommunicationLog)
            .filter(CateringCommunicationLog.catering_plan_id == catering_id)
            .order_by(CateringCommunicationLog.created_at.desc())
            .all()
        )
        return [
            {
                "id": c.id,
                "cateringPlanId": c.catering_plan_id,
                "vendorId": c.vendor_id,
                "communicationType": c.communication_type,
                "recipientPhone": c.recipient_phone,
                "messageText": c.message_text,
                "pdfDownloadUrl": c.pdf_download_url,
                "status": c.status,
                "initiatedBy": c.initiated_by,
                "notes": c.notes,
                "createdAt": c.created_at,
            }
            for c in logs
        ]


catering_service = CateringService()

