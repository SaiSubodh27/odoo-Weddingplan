from typing import Optional, List, Literal
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
import re

RegistrationStatusType = str

ServicePackageType = str

EnquirySourceType = str


class ClientBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    partner1_name: str = Field(..., alias="partner1Name", min_length=2, max_length=150, description="Partner 1 Full Name")
    partner2_name: str = Field(..., alias="partner2Name", min_length=2, max_length=150, description="Partner 2 Full Name")
    email: str = Field(..., min_length=5, max_length=255, description="Primary Contact Email")
    phone: str = Field(..., min_length=5, max_length=50, description="Contact Phone Number")

    wedding_date: date = Field(..., alias="weddingDate", description="Target Wedding Date (YYYY-MM-DD)")
    wedding_location: str = Field(..., alias="weddingLocation", min_length=2, max_length=255, description="Palace / Venue Location")
    expected_guest_count: int = Field(..., alias="expectedGuestCount", ge=1, le=10000, description="Expected Guests Count")
    estimated_budget: Decimal = Field(..., alias="estimatedBudget", ge=0, description="Estimated Budget in INR")
    wedding_theme: Optional[str] = Field(None, alias="weddingTheme", max_length=255, description="Aesthetic Theme / Vision")

    service_package: ServicePackageType = Field("Full-Service", alias="servicePackage", description="Service Package Tier")
    additional_requirements: Optional[str] = Field(None, alias="additionalRequirements", description="Special Additions / Requests")

    enquiry_source: EnquirySourceType = Field("Email", alias="enquirySource", description="Channel of Initial Contact")
    notes: Optional[str] = Field(None, description="Confidential Planner Notes")
    status: RegistrationStatusType = Field("Enquiry", description="Current Registration Status")

    @field_validator("email")
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", clean):
            raise ValueError("Invalid email format. Must contain a valid user and domain.")
        return clean

    @field_validator("estimated_budget", mode="before")
    def parse_budget_input(cls, v):
        """Allows strings like '₹ 1.85 Cr', '18500000', or raw decimal numbers."""
        if isinstance(v, (int, float, Decimal)):
            return Decimal(str(v))
        if isinstance(v, str):
            clean = v.replace("₹", "").replace(",", "").strip()
            # If specified in Cr (Crores)
            if "cr" in clean.lower():
                num = float(clean.lower().replace("cr", "").strip())
                return Decimal(str(int(num * 10_000_000)))
            # If specified in Lakhs
            if "lakh" in clean.lower():
                num = float(clean.lower().replace("lakh", "").replace("s", "").strip())
                return Decimal(str(int(num * 100_000)))
            return Decimal(clean)
        return v


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    partner1_name: Optional[str] = Field(None, alias="partner1Name", min_length=2, max_length=150)
    partner2_name: Optional[str] = Field(None, alias="partner2Name", min_length=2, max_length=150)
    email: Optional[str] = Field(None, min_length=5, max_length=255)
    phone: Optional[str] = Field(None, min_length=5, max_length=50)

    wedding_date: Optional[date] = Field(None, alias="weddingDate")
    wedding_location: Optional[str] = Field(None, alias="weddingLocation", min_length=2, max_length=255)
    expected_guest_count: Optional[int] = Field(None, alias="expectedGuestCount", ge=1)
    estimated_budget: Optional[Decimal] = Field(None, alias="estimatedBudget", ge=0)
    wedding_theme: Optional[str] = Field(None, alias="weddingTheme", max_length=255)

    service_package: Optional[ServicePackageType] = Field(None, alias="servicePackage")
    additional_requirements: Optional[str] = Field(None, alias="additionalRequirements")

    enquiry_source: Optional[EnquirySourceType] = Field(None, alias="enquirySource")
    notes: Optional[str] = Field(None)
    status: Optional[RegistrationStatusType] = Field(None)

    @field_validator("estimated_budget", mode="before")
    def parse_budget_update_input(cls, v):
        if v is None:
            return None
        if isinstance(v, (int, float, Decimal)):
            return Decimal(str(v))
        if isinstance(v, str):
            clean = v.replace("₹", "").replace(",", "").strip()
            if not clean:
                return None
            if "cr" in clean.lower():
                num = float(clean.lower().replace("cr", "").strip())
                return Decimal(str(int(num * 10_000_000)))
            if "lakh" in clean.lower():
                num = float(clean.lower().replace("lakh", "").replace("s", "").strip())
                return Decimal(str(int(num * 100_000)))
            return Decimal(clean)
        return v


class ClientResponse(ClientBase):
    id: str
    is_deleted: bool = Field(False, alias="isDeleted")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class ClientListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ClientResponse]


class HealthResponse(BaseModel):
    service: str
    status: str
    database_connected: bool
    operating_regions: List[str]
    version: str

