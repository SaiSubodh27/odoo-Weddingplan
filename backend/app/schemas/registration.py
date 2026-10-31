from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
import re


class ClientRegistrationSubmitRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    token: str = Field(..., description="Secure registration token from invitation link")
    full_name: str = Field(..., min_length=2, max_length=150, alias="fullName")
    partner_name: Optional[str] = Field(None, max_length=150, alias="partnerName")
    email: str = Field(..., min_length=5, max_length=255)
    phone: str = Field(..., min_length=7, max_length=50)
    address: Optional[str] = Field(None, max_length=1000)
    wedding_date: Optional[date] = Field(None, alias="weddingDate")
    wedding_location: Optional[str] = Field(None, max_length=255, alias="weddingLocation")
    expected_guest_count: Optional[int] = Field(None, ge=1, alias="expectedGuestCount")
    estimated_budget: Optional[Decimal] = Field(None, ge=0, alias="estimatedBudget")
    wedding_events: Optional[List[str]] = Field(default_factory=list, alias="weddingEvents")
    preferred_theme: Optional[str] = Field(None, max_length=255, alias="preferredTheme")
    service_package: Optional[str] = Field("Full-Service", alias="servicePackage")
    preferences: Optional[str] = Field(None, max_length=3000)

    @field_validator("email")
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean):
            raise ValueError("Invalid email format.")
        return clean

    @field_validator("phone")
    def validate_phone_format(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 7:
            raise ValueError("Phone number must have at least 7 characters.")
        return clean


class RegistrationVerifyResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    valid: bool
    message: str
    enquiry_id: Optional[str] = Field(None, alias="enquiryId")
    client_name: Optional[str] = Field(None, alias="clientName")
    partner_name: Optional[str] = Field(None, alias="partnerName")
    email: Optional[str] = None
    phone: Optional[str] = None
    wedding_date: Optional[date] = Field(None, alias="weddingDate")
    wedding_location: Optional[str] = Field(None, alias="weddingLocation")
    expected_guest_count: Optional[int] = Field(None, alias="expectedGuestCount")
    estimated_budget: Optional[Decimal] = Field(None, alias="estimatedBudget")
    requirements: Optional[str] = None
    existing_registration: Optional[dict] = Field(None, alias="existingRegistration")


class ClientRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    enquiry_id: str = Field(..., alias="enquiryId")
    full_name: str = Field(..., alias="fullName")
    partner_name: Optional[str] = Field(None, alias="partnerName")
    email: str
    phone: str
    address: Optional[str] = None
    wedding_date: Optional[date] = Field(None, alias="weddingDate")
    wedding_location: Optional[str] = Field(None, alias="weddingLocation")
    expected_guest_count: Optional[int] = Field(None, alias="expectedGuestCount")
    estimated_budget: Optional[Decimal] = Field(None, alias="estimatedBudget")
    wedding_events: Optional[str] = Field(None, alias="weddingEvents")
    preferred_theme: Optional[str] = Field(None, alias="preferredTheme")
    service_package: str = Field(..., alias="servicePackage")
    preferences: Optional[str] = None
    status: str
    reviewed_by: Optional[str] = Field(None, alias="reviewedBy")
    reviewed_at: Optional[datetime] = Field(None, alias="reviewedAt")
    review_notes: Optional[str] = Field(None, alias="reviewNotes")
    correction_notes: Optional[str] = Field(None, alias="correctionNotes")
    submitted_at: datetime = Field(..., alias="submittedAt")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class RegistrationReviewRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    reviewed_by: str = Field("Agency Staff", alias="reviewedBy")
    notes: Optional[str] = None


class RegistrationCorrectionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    staff_name: str = Field("Agency Staff", alias="staffName")
    correction_notes: str = Field(..., min_length=5, alias="correctionNotes")
