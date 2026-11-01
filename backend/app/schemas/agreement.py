from typing import Optional, List, Any, Dict, Dict
from datetime import date, datetime
from decimal import Decimal
from pydantic import model_validator,  BaseModel, ConfigDict, Field


class WeddingFunctionSchema(BaseModel):
    name: str = Field(..., description="Function name e.g. Mehendi Ceremony, Royal Sangeet")
    date: str = Field(..., description="Date of the function (YYYY-MM-DD)")
    venue: Optional[str] = Field(None, description="Venue or hall name")
    guest_count: int = Field(100, ge=1, description="Expected guest count")
    notes: Optional[str] = Field(None, description="Special instructions")


class PaymentMilestoneInput(BaseModel):
    name: Optional[str] = None
    milestone_name: Optional[str] = None
    percentage: Decimal = Field(..., ge=0, le=100, description="Percentage of total contract price")
    amount: Decimal = Field(..., ge=0, description="Exact milestone amount in INR")
    due_date: Optional[date] = None
    description: Optional[str] = None
    due_description: Optional[str] = None
    sequence_order: int = Field(1, ge=1)

    @model_validator(mode="before")
    @classmethod
    def unify_milestone_fields(cls, values):
        if isinstance(values, dict):
            name_val = values.get("name") or values.get("milestone_name") or "Milestone"
            desc_val = values.get("description") or values.get("due_description") or ""
            values["name"] = name_val
            values["milestone_name"] = name_val
            values["description"] = desc_val
            values["due_description"] = desc_val
        return values


class PaymentMilestoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agreement_id: str
    name: Optional[str] = None
    milestone_name: Optional[str] = None
    percentage: Decimal
    amount: Decimal
    description: Optional[str] = None
    due_description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = "PENDING"
    sequence_order: int = 1

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data):
        if not isinstance(data, dict):
            name_val = getattr(data, "name", None) or getattr(data, "milestone_name", "Milestone")
            desc_val = getattr(data, "description", None) or getattr(data, "due_description", "")
            return {
                "id": str(getattr(data, "id", "")),
                "agreement_id": str(getattr(data, "agreement_id", "")),
                "name": name_val,
                "milestone_name": name_val,
                "percentage": getattr(data, "percentage", Decimal("0")),
                "amount": getattr(data, "amount", Decimal("0")),
                "description": desc_val,
                "due_description": desc_val,
                "due_date": getattr(data, "due_date", None),
                "status": getattr(data, "status", "PENDING"),
                "sequence_order": getattr(data, "sequence_order", 1),
            }
        elif isinstance(data, dict):
            name_val = data.get("name") or data.get("milestone_name") or "Milestone"
            desc_val = data.get("description") or data.get("due_description") or ""
            data["name"] = name_val
            data["milestone_name"] = name_val
            data["description"] = desc_val
            data["due_description"] = desc_val
            return data
        return data


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
    created_by: Optional[str] = "Maharani Gayatri Singh"


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
    @model_validator(mode="before")
    @classmethod
    def set_defaults_for_nulls(cls, data):
        if hasattr(data, "__dict__"):
            vals = dict(data.__dict__)
            pkg = getattr(data, "service_package", None) or "Full-Service"
            price = getattr(data, "package_price", None) or Decimal("25000000.00")
            tax_pct = getattr(data, "tax_percentage", None) or Decimal("18.00")
            tax_amt = getattr(data, "tax_amount", None) or (price * Decimal("0.18"))
            tot_amt = getattr(data, "total_amount", None) or (price + tax_amt)
            vals["service_package"] = pkg
            vals["package_price"] = price
            vals["tax_percentage"] = tax_pct
            vals["tax_amount"] = tax_amt
            vals["discount_amount"] = getattr(data, "discount_amount", None) or Decimal("0.00")
            vals["total_amount"] = tot_amt
            return vals
        return data


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
    agreement_version: Optional[str] = "v1.0"
    is_internally_approved: bool
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    is_verified: bool
    signed_at: Optional[datetime] = None
    signed_by_name: Optional[str] = None
    signed_by_email: Optional[str] = None
    signed_pdf_url: Optional[str] = None
    signing_otp_verified: Optional[bool] = False
    consent_confirmed: Optional[bool] = False
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
    dev_otp: Optional[str] = None


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



class ServiceAgreementMetricsResponse(BaseModel):
    total_agreements: int
    draft_agreements: int
    pending_approval: int
    signing_pending: int
    signed_agreements: int
    awaiting_verification: int
    verified_agreements: int
    confirmed_bookings: int

class AgreementApproveRequest(BaseModel):
    approved_by: str = Field(..., description="Staff member approving agreement")
    notes: Optional[str] = None

class AgreementReviewRequest(BaseModel):
    reviewer_name: str = Field(..., description="Staff reviewer name")
    decision: str = Field(..., description="'VERIFIED' or 'REJECTED' or 'NEEDS_CORRECTION'")
    remarks: str = Field(..., min_length=3, description="Verification observations or rejection reason")

class SendForSignatureRequest(BaseModel):
    provider: Optional[str] = Field(None, description="Electronic signature provider override ('zoho_sign' or 'leegality')")
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
    provider: str = "Zoho Sign"
    environment: str = "sandbox"
    provider_request_id: Optional[str] = None
    provider_document_id: Optional[str] = None
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
    provider: str = "Zoho Sign"
    environment: str = "sandbox"
    provider_request_id: Optional[str] = None
    provider_document_id: Optional[str] = None
    leegality_document_id: Optional[str] = None
    signing_url: Optional[str] = None
    signer_name: Optional[str] = None
    signer_email: Optional[str] = None
    completed_at: Optional[datetime] = None
    last_status_checked_at: Optional[datetime] = None
    next_status_check_at: Optional[datetime] = None
    polling_attempt_count: int = 0
    last_polling_error: Optional[str] = None
    has_signed_pdf: bool = False
    has_audit_certificate: bool = False
    raw_provider_status: Optional[Dict[str, Any]] = None

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
