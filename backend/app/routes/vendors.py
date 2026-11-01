from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import require_signed_agreement
from app.services.vendor_service import vendor_service
from app.schemas.vendor import (
    VendorCreate,
    VendorUpdate,
    VendorStatusUpdate,
    VendorResponse,
    VendorDetailResponse,
    VendorListResponse,
)

router = APIRouter(dependencies=[Depends(require_signed_agreement)])


@router.get(
    "",
    response_model=VendorListResponse,
    summary="List registered vendors with category filtering, search, and pagination",
    tags=["Vendors"]
)
def list_vendors(
    category: Optional[str] = Query(None, description="Filter by vendor category (e.g. Catering, Decor, Photography)"),
    city: Optional[str] = Query(None, description="Filter by operational city (e.g. Jaipur, Udaipur)"),
    search: Optional[str] = Query(None, description="Search by name, contact, phone, email, or city"),
    is_active: Optional[bool] = Query(None, alias="isActive", description="Filter active or inactive vendors"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, alias="pageSize", description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Returns paginated list of palace vendors, caterers, and decorators.
    Shared across all agency wedding projects.
    """
    total, items = vendor_service.list_vendors(
        db=db,
        category=category,
        city=city,
        search=search,
        is_active=is_active,
        page=page,
        page_size=page_size
    )
    return VendorListResponse(
        total=total,
        page=page,
        pageSize=page_size,
        items=[VendorResponse.model_validate(i) for i in items]
    )


@router.post(
    "",
    response_model=VendorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new luxury vendor",
    tags=["Vendors"]
)
def create_vendor(
    vendor_in: VendorCreate,
    db: Session = Depends(get_db)
):
    """
    Registers a new vendor in the central directory.
    Validates telephone and prevents duplicate entries.
    """
    vendor = vendor_service.create_vendor(db=db, vendor_in=vendor_in)
    return VendorResponse.model_validate(vendor)


@router.get(
    "/{vendor_id}",
    response_model=VendorDetailResponse,
    summary="Retrieve vendor dossier by ID",
    tags=["Vendors"]
)
def get_vendor(
    vendor_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns complete vendor dossier including portfolio counts and ratings.
    """
    vendor = vendor_service.get_vendor_by_id(db, vendor_id)
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor '{vendor_id}' not found."
        )

    return VendorDetailResponse(
        id=vendor.id,
        name=vendor.name,
        category=vendor.category,
        contactPerson=vendor.contact_person,
        phone=vendor.phone,
        email=vendor.email,
        city=vendor.city,
        address=vendor.address,
        rating=vendor.rating,
        notes=vendor.notes,
        isActive=vendor.is_active,
        createdAt=vendor.created_at,
        updatedAt=vendor.updated_at,
        cateringPlansCount=len(vendor.catering_plans) if vendor.catering_plans else 0,
        quotationsCount=len(vendor.quotations) if vendor.quotations else 0,
    )


@router.put(
    "/{vendor_id}",
    response_model=VendorResponse,
    summary="Update vendor contact and operational details",
    tags=["Vendors"]
)
def update_vendor(
    vendor_id: str,
    vendor_in: VendorUpdate,
    db: Session = Depends(get_db)
):
    """
    Updates vendor contact person, telephone (WhatsApp), address, notes, or rating.
    """
    vendor = vendor_service.update_vendor(db=db, vendor_id=vendor_id, vendor_in=vendor_in)
    return VendorResponse.model_validate(vendor)


@router.patch(
    "/{vendor_id}/status",
    response_model=VendorResponse,
    summary="Toggle vendor active/inactive operational status",
    tags=["Vendors"]
)
def set_vendor_status(
    vendor_id: str,
    status_in: VendorStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Activates or deactivates a vendor in the active palace directory.
    """
    vendor = vendor_service.set_vendor_status(
        db=db, vendor_id=vendor_id, is_active=status_in.is_active, notes=status_in.notes
    )
    return VendorResponse.model_validate(vendor)

