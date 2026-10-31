from typing import Optional, List, Any
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class WeddingFunctionSchema(BaseModel):
    name: str = Field(..., description="Function name e.g. Mehendi Ceremony, Royal Sangeet")
    date: str = Field(..., description="Date of the function (YYYY-MM-DD)")
    venue: Optional[str] = Field(None, description="Venue or hall name")
    guest_count: int = Field(100, ge=1, description="Expected guest count")
    notes: Optional[str] = Field(None, description="Special instructions")


class PaymentMilestoneInput(BaseModel):
    milestone_name: str = Field(..., description="Milestone title")
    percentage: Decimal = Field(..., ge=0, le=100, description="Percentage of total")
    amount: Decimal = Field(..., ge=0, description="Amount in INR")
    due_description: str = Field(..., description="When the payment is due")
    due_date: Optional[date] = None
    sequence_order: int = Field(1, ge=1)


class PaymentMilestoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agreement_id: str
    milestone_name: str
    percentage: Decimal
    amount: Decimal
    due_description: str
    due_date: Optional[date] = None
    status: str
    sequence_order: int


class ServiceAgreementCreate(BaseModel):
    client_id: str = Field(..., description="ID of the client e.g. TRK-2026-001")
    wedding_date: date
    wedding_location: str
    venue: Optional[str] = None
    guest_count: int = Field(100, ge=1)
    wedding_functions: Optional[List[WeddingFunctionSchema]] = None
    service_package: str = Field("Royal Palace Grandeur", description="Service package name")
    included_services: Optional[List[str]] = None
    excluded_services: Optional[List[str]] = None
    deliverables: Optional[List[str]] = None
    package_price: Decimal = Field(..., ge=0)
    tax_percentage: Decimal = Field(Decimal("18.00"), ge=0)
    discount_amount: Decimal = Field(Decimal("0.00"), ge=0)
    additional_terms: Optional[str] = None
    milestones: Optional[List[PaymentMilestoneInput]] = None


class ServiceAgreementUpdate(BaseModel):
    wedding_date: Optional[date] = None
    wedding_location: Optional[str] = None
    venue: Optional[str] = None
    guest_count: Optional[int] = Field(None, ge=1)
    wedding_functions: Optional[List[WeddingFunctionSchema]] = None
    service_package: Optional[str] = None
    included_services: Optional[List[str]] = None
    excluded_services: Optional[List[str]] = None
    deliverables: Optional[List[str]] = None
    package_price: Optional[Decimal] = Field(None, ge=0)
    tax_percentage: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    additional_terms: Optional[str] = None
    milestones: Optional[List[PaymentMilestoneInput]] = None


class ServiceAgreementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agreement_number: str
    client_id: str
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    status: str
    wedding_date: date
    wedding_location: str
    venue: Optional[str] = None
    guest_count: int
    wedding_functions: Optional[Any] = None
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
    agreement_version: str
    is_internally_approved: bool
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    is_verified: bool
    signed_at: Optional[datetime] = None
    signed_by_name: Optional[str] = None
    signed_by_email: Optional[str] = None
    signed_pdf_url: Optional[str] = None
    signing_otp_verified: bool
    consent_confirmed: bool
    created_at: datetime
    updated_at: datetime
    milestones: List[PaymentMilestoneResponse] = []


class ServiceAgreementListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ServiceAgreementResponse]


class SendOTPRequest(BaseModel):
    client_id: Optional[str] = None


class SendOTPResponse(BaseModel):
    success: bool
    message: str
    email_destination: str
    expires_in_seconds: int = 600


class VerifyOTPRequest(BaseModel):
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")


class VerifyOTPResponse(BaseModel):
    success: bool
    message: str
    verified: bool


class SignAgreementRequest(BaseModel):
    otp: Optional[str] = Field(None, min_length=6, max_length=6, description="6-digit OTP if not pre-verified")
    signature_data: str = Field(..., description="Base64 data URL or digital signature representation")
    consent: bool = Field(..., description="Must explicitly consent to terms")
    signer_name: Optional[str] = None


class SignAgreementResponse(BaseModel):
    success: bool
    message: str
    agreement_id: str
    agreement_number: str
    status: str
    signed_at: datetime
    signed_pdf_url: str
    has_signed_agreement: bool = True


class AgreementMetricsResponse(BaseModel):
    total_agreements: int
    draft_count: int
    pending_signature_count: int
    signed_count: int
    verified_count: int
    total_contract_value: Decimal

