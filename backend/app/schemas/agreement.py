from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Any, Dict
from datetime import date, datetime
from decimal import Decimal


# --- Sub-schemas ---

class WeddingFunctionSchema(BaseModel):
    name: str = Field(..., description="Function name, e.g., Mehendi, Sangeet, Royal Phera")
    date: Optional[str] = Field(None, description="Date of the function (YYYY-MM-DD)")
    venue: Optional[str] = Field(None, description="Venue name/hall")
    guest_count: Optional[int] = Field(None, description="Expected guests for this function")
    notes: Optional[str] = Field(None, description="Theme or specific setup requirements")


class PaymentMilestoneInput(BaseModel):
    name: str = Field(..., description="Milestone title, e.g., Booking Advance (25%)")
    percentage: Decimal = Field(..., ge=0, le=100, description="Percentage of total contract price")
    amount: Decimal = Field(..., ge=0, description="Exact milestone amount in INR")
    due_date: date = Field(..., description="Due date for this milestone")
    description: Optional[str] = None


class PaymentMilestoneResponse(BaseModel):
    id: str
    agreement_id: str
    version_number: int
    sequence_order: int
    name: str
    percentage: Decimal
    amount: Decimal
    due_date: date
    description: Optional[str] = None

    class Config:
        from_attributes = True


# --- Agreement Schemas ---

class ServiceAgreementCreate(BaseModel):
    client_id: str = Field(..., description="Existing registered client ID (e.g. CLT-2026-001)")
    wedding_date: date
    wedding_location: str
    venue: Optional[str] = None
    guest_count: int = Field(100, ge=1)
    wedding_functions: Optional[List[WeddingFunctionSchema]] = []
    
    service_package: str = Field("Royal Palace Grandeur", description="Approved service package name")
    included_services: Optional[List[str]] = []
    excluded_services: Optional[List[str]] = []
    deliverables: Optional[List[str]] = []
    additional_terms: Optional[str] = None

    # Pricing (decimal safe)
    package_price: Decimal = Field(..., ge=0)
    tax_percentage: Decimal = Field(Decimal("18.00"), ge=0, le=100)
    discount_amount: Decimal = Field(Decimal("0.00"), ge=0)

    # Payment Milestones
    milestones: List[PaymentMilestoneInput] = Field(..., min_length=1)

    created_by: Optional[str] = "Maharani Gayatri Singh"


class ServiceAgreementUpdate(BaseModel):
    wedding_date: Optional[date] = None
    wedding_location: Optional[str] = None
    venue: Optional[str] = None
    guest_count: Optional[int] = None
    wedding_functions: Optional[List[WeddingFunctionSchema]] = None
    service_package: Optional[str] = None
    included_services: Optional[List[str]] = None
    excluded_services: Optional[List[str]] = None
    deliverables: Optional[List[str]] = None
    additional_terms: Optional[str] = None

    package_price: Optional[Decimal] = None
    tax_percentage: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None

    milestones: Optional[List[PaymentMilestoneInput]] = None
    revision_reason: Optional[str] = Field(None, description="Reason for revising/updating agreement")


class ServiceAgreementResponse(BaseModel):
    id: str
    agreement_number: str
    client_id: str
    status: str
    signing_status: str
    wedding_date: date
    wedding_location: str
    venue: Optional[str] = None
    guest_count: int
    wedding_functions: Optional[List[Dict[str, Any]]] = None
    service_package: str
    included_services: Optional[List[str]] = None
    excluded_services: Optional[List[str]] = None
    deliverables: Optional[List[str]] = None
    additional_terms: Optional[str] = None

    package_price: Decimal
    tax_percentage: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    currency: str

    current_version_number: int
    is_internally_approved: bool
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    is_verified: bool
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None

    created_by: str
    created_at: datetime
    updated_at: datetime

    milestones: List[PaymentMilestoneResponse] = []
    
    # Client summary
    client_partner1_name: Optional[str] = None
    client_partner2_name: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None

    class Config:
        from_attributes = True


class ServiceAgreementListResponse(BaseModel):
    items: List[ServiceAgreementResponse]
    total: int
    page: int
    page_size: int


class ServiceAgreementMetricsResponse(BaseModel):
    total_agreements: int
    draft_agreements: int
    pending_approval: int
    signing_pending: int
    signed_agreements: int
    awaiting_verification: int
    verified_agreements: int
    confirmed_bookings: int


# --- Approval & Verification Schemas ---

class AgreementApproveRequest(BaseModel):
    approved_by: str = Field(..., description="Staff member approving agreement")
    notes: Optional[str] = None


class AgreementReviewRequest(BaseModel):
    reviewer_name: str = Field(..., description="Staff reviewer name")
    decision: str = Field(..., description="'VERIFIED' or 'REJECTED' or 'NEEDS_CORRECTION'")
    remarks: str = Field(..., min_length=3, description="Verification observations or rejection reason")


# --- Leegality Integration Schemas ---

class SendForSignatureRequest(BaseModel):
    signer_name: Optional[str] = None
    signer_email: Optional[str] = None
    signer_phone: Optional[str] = None
    signing_reason: Optional[str] = "Service Agreement Execution for Wedding Planning Services"


class SendForSignatureResponse(BaseModel):
    success: bool
    message: str
    agreement_id: str
    agreement_number: str
    version_number: int
    leegality_document_id: Optional[str] = None
    signing_url: Optional[str] = None
    status: str
    sent_at: Optional[datetime] = None


class SigningStatusResponse(BaseModel):
    agreement_id: str
    agreement_number: str
    version_number: int
    signing_status: str
    agreement_status: str
    leegality_document_id: Optional[str] = None
    signing_url: Optional[str] = None
    signer_name: Optional[str] = None
    signer_email: Optional[str] = None
    completed_at: Optional[datetime] = None
    raw_provider_status: Optional[Dict[str, Any]] = None


# --- Booking Confirmation Schemas ---

class BookingConfirmRequest(BaseModel):
    confirmed_by: str = Field(..., description="Authorized Staff Manager confirming booking")
    confirmation_notes: Optional[str] = None


class BookingConfirmResponse(BaseModel):
    success: bool
    message: str
    booking_id: str
    booking_reference: str
    client_id: str
    agreement_id: str
    confirmed_version_number: int
    couple_title: str
    wedding_date: date
    wedding_location: str
    venue: Optional[str] = None
    confirmed_total_amount: Decimal
    advance_amount_agreed: Decimal
    confirmed_by: str
    confirmed_at: datetime
    phase3_handoff_ready: bool

