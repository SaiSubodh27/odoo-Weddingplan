from typing import Optional, List, Any
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
import uuid
import secrets
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.database.session import get_db
from app.models.vendor import Vendor
from app.models.project import WeddingProject, ProjectVendor
from app.models.catering import CateringPlan, CateringQuotation
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter()


class VendorLoginRequest(BaseModel):
    identifier: str = Field(..., description="Vendor email, telephone, or name", min_length=2)


class VendorLoginResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    vendor_id: str = Field(..., alias="vendorId")
    name: str
    category: str
    email: Optional[str] = None
    phone: str
    city: Optional[str] = None
    token: str
    message: str


class AssignedWeddingItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    project_id: str = Field(..., alias="projectId")
    project_code: str = Field(..., alias="projectCode")
    project_name: str = Field(..., alias="projectName")
    wedding_date: date = Field(..., alias="weddingDate")
    location: str
    category: str
    contract_amount: Decimal = Field(..., alias="contractAmount")
    status: str  # Contracted, Won, Completed


class VendorRfqItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    quotation_id: str = Field(..., alias="quotationId")
    catering_plan_id: str = Field(..., alias="cateringPlanId")
    plan_title: str = Field(..., alias="planTitle")
    wedding_date: Optional[date] = Field(None, alias="weddingDate")
    location: Optional[str] = None
    guest_count: int = Field(..., alias="guestCount")
    meal_type: Optional[str] = Field(None, alias="mealType")
    price_per_plate: Optional[Decimal] = Field(None, alias="pricePerPlate")
    line_items: List[dict] = Field([], alias="lineItems")
    total_cost: Decimal = Field(Decimal("0.00"), alias="totalCost")
    status: str  # Quotation Requested, Quotation Received, Accepted, Closed
    created_at: datetime = Field(..., alias="createdAt")


class VendorDashboardResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    vendor_id: str = Field(..., alias="vendorId")
    name: str
    category: str
    phone: str
    email: Optional[str] = None
    rating: float
    total_contract_value: Decimal = Field(..., alias="totalContractValue")
    won_contracts_count: int = Field(..., alias="wonContractsCount")
    closed_quotes_count: int = Field(..., alias="closedQuotesCount")
    pending_rfqs_count: int = Field(..., alias="pendingRfqsCount")
    assigned_weddings: List[AssignedWeddingItem] = Field([], alias="assignedWeddings")
    rfqs_received: List[VendorRfqItem] = Field([], alias="rfqsReceived")


class VendorSubmitQuoteRequest(BaseModel):
    catering_plan_id: str = Field(..., alias="cateringPlanId")
    price_per_plate: Decimal = Field(..., alias="pricePerPlate", ge=0)
    line_items: List[dict] = Field([], alias="lineItems")
    notes: Optional[str] = None


@router.post(
    "/login",
    response_model=VendorLoginResponse,
    summary="Authenticate vendor via email, phone, or name",
    tags=["Vendor Portal"]
)
def vendor_login(
    req: VendorLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Vendor workspace login. Identifies registered partner by phone, email, or company name.
    Returns session token and vendor profile.
    """
    ident = req.identifier.strip()
    vendor = db.query(Vendor).filter(
        or_(
            Vendor.email.ilike(ident),
            Vendor.phone == ident,
            Vendor.name.ilike(f"%{ident}%")
        ),
        Vendor.is_active == True
    ).first()

    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor partner '{ident}' not found in registered directory."
        )

    token = f"vnd_tok_{secrets.token_hex(16)}"

    return VendorLoginResponse(
        vendor_id=vendor.id,
        name=vendor.name,
        category=vendor.category,
        email=vendor.email,
        phone=vendor.phone,
        city=vendor.city,
        token=token,
        message=f"Welcome back, {vendor.name}."
    )


@router.get(
    "/{vendor_id}/dashboard",
    response_model=VendorDashboardResponse,
    summary="Vendor real workspace dashboard (RFQs received, quotes, won/closed contracts, assigned weddings)",
    tags=["Vendor Portal"]
)
def get_vendor_dashboard(
    vendor_id: str,
    db: Session = Depends(get_db)
):
    """
    Live vendor workspace delivering:
    - Requests received (RFQs)
    - Submitted quotes and contract statuses (Won vs Closed)
    - Real assigned wedding projects
    """
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor '{vendor_id}' not found."
        )

    # 1. Assigned Weddings from ProjectVendor
    pv_assignments = db.query(ProjectVendor).filter(
        ProjectVendor.vendor_id == vendor.id
    ).all()

    assigned_items = []
    total_contract_value = Decimal("0.00")
    for pv in pv_assignments:
        p = pv.project
        amt = Decimal(str(pv.contract_amount or 0.00))
        total_contract_value += amt
        assigned_items.append(AssignedWeddingItem(
            project_id=p.id,
            project_code=p.project_code,
            project_name=p.project_name,
            wedding_date=p.wedding_date,
            location=p.location,
            category=pv.category,
            contract_amount=amt,
            status=pv.status
        ))

    # 2. RFQs & Quotations from CateringQuotation
    quotes = db.query(CateringQuotation).filter(
        CateringQuotation.vendor_id == vendor.id
    ).order_by(desc(CateringQuotation.created_at)).all()

    rfq_items = []
    won_count = len([q for q in quotes if q.status == "Accepted"])
    closed_count = len([q for q in quotes if q.status == "Closed"])
    pending_count = len([q for q in quotes if q.status in ["Quotation Requested", "Quotation Received"]])

    for q in quotes:
        plan = q.plan
        w_date = plan.project.wedding_date if (plan and plan.project) else None
        loc = plan.project.location if (plan and plan.project) else None
        p_title = plan.title if plan else "Royal Banquet Catering"
        g_count = plan.guest_count if plan else 400
        m_type = plan.meal_type if plan else "Grand Buffet"

        rfq_items.append(VendorRfqItem(
            quotation_id=q.id,
            catering_plan_id=q.catering_plan_id,
            plan_title=p_title,
            wedding_date=w_date,
            location=loc,
            guest_count=g_count,
            meal_type=m_type,
            price_per_plate=Decimal(str(q.price_per_plate)) if q.price_per_plate else None,
            line_items=q.line_items or [],
            total_cost=Decimal(str(q.total_cost or 0.00)),
            status="Won" if q.status == "Accepted" else q.status,
            created_at=q.created_at
        ))

    return VendorDashboardResponse(
        vendor_id=vendor.id,
        name=vendor.name,
        category=vendor.category,
        phone=vendor.phone,
        email=vendor.email,
        rating=float(vendor.rating or 5.0),
        total_contract_value=total_contract_value,
        won_contracts_count=won_count + len(assigned_items),
        closed_quotes_count=closed_count,
        pending_rfqs_count=pending_count,
        assigned_weddings=assigned_items,
        rfqs_received=rfq_items
    )


@router.post(
    "/{vendor_id}/quotes",
    response_model=VendorRfqItem,
    status_code=status.HTTP_201_CREATED,
    summary="Submit or update a real quotation with line items for an assigned RFQ",
    tags=["Vendor Portal"]
)
def submit_vendor_quote(
    vendor_id: str,
    quote_in: VendorSubmitQuoteRequest,
    db: Session = Depends(get_db)
):
    """
    Submits an itemized vendor quotation with breakdown line items, price-per-plate,
    and automatic total computation.
    """
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vendor '{vendor_id}' not found.")

    plan = db.query(CateringPlan).filter(CateringPlan.id == quote_in.catering_plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Catering plan '{quote_in.catering_plan_id}' not found.")

    # Find existing quote or create new
    quote = db.query(CateringQuotation).filter(
        CateringQuotation.catering_plan_id == plan.id,
        CateringQuotation.vendor_id == vendor.id
    ).first()

    guest_count = plan.guest_count or 400
    base_cost = quote_in.price_per_plate * Decimal(str(guest_count))

    # Add any line items cost
    addon_cost = Decimal("0.00")
    for item in quote_in.line_items:
        addon_cost += Decimal(str(item.get("total_price", item.get("totalPrice", 0))))

    total_cost = base_cost + addon_cost

    if not quote:
        quote = CateringQuotation(
            id=f"QUO-{uuid.uuid4().hex[:8].upper()}",
            catering_plan_id=plan.id,
            vendor_id=vendor.id,
            quotation_reference=f"RFQ-{vendor.name[:3].upper()}-{secrets.token_hex(3).upper()}",
            price_per_plate=quote_in.price_per_plate,
            total_cost=total_cost,
            line_items=quote_in.line_items,
            status="Quotation Received",
            notes=quote_in.notes
        )
        db.add(quote)
    else:
        quote.price_per_plate = quote_in.price_per_plate
        quote.total_cost = total_cost
        quote.line_items = quote_in.line_items
        quote.status = "Quotation Received"
        if quote_in.notes:
            quote.notes = quote_in.notes

    # Update plan status if in RFQ requested
    if plan.status == "Quotation Requested":
        plan.status = "Quotation Received"

    db.commit()
    db.refresh(quote)

    w_date = plan.project.wedding_date if (plan.project) else None
    loc = plan.project.location if (plan.project) else None

    return VendorRfqItem(
        quotation_id=quote.id,
        catering_plan_id=plan.id,
        plan_title=plan.title,
        wedding_date=w_date,
        location=loc,
        guest_count=guest_count,
        meal_type=plan.meal_type,
        price_per_plate=quote.price_per_plate,
        line_items=quote.line_items or [],
        total_cost=quote.total_cost,
        status=quote.status,
        created_at=quote.created_at
    )
