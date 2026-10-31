from typing import Optional, List, Literal
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
import re

EnquirySourceType = Literal["Email", "Phone", "Website"]

EnquiryStatusType = Literal[
    "New",
    "Contacted",
    "Registration Document Sent",
    "Registration Received",
    "Registered",
    "Closed",
]


class EnquiryNoteCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Note content")
    author: Optional[str] = Field("Agency Staff", description="Author of the note")


class EnquiryNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    enquiry_id: str = Field(..., alias="enquiryId")
    author: str
    content: str
    created_at: datetime = Field(..., alias="createdAt")


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    document_type: str = Field(..., alias="documentType")
    original_filename: str = Field(..., alias="originalFilename")
    file_size: int = Field(..., alias="fileSize")
    mime_type: str = Field(..., alias="mimeType")
    created_at: datetime = Field(..., alias="createdAt")


class EnquiryBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    client_name: str = Field(..., alias="clientName", min_length=2, max_length=150, description="Lead or Couple Name")
    email: str = Field(..., min_length=5, max_length=255, description="Client Contact Email")
    phone: str = Field(..., min_length=5, max_length=50, description="Client Phone Number")
    enquiry_source: EnquirySourceType = Field("Email", alias="enquirySource", description="Source of Initial Contact")

    wedding_date: Optional[date] = Field(None, alias="weddingDate", description="Target Wedding Date (YYYY-MM-DD)")
    wedding_location: Optional[str] = Field(None, alias="weddingLocation", max_length=255, description="Target Venue / City")
    expected_guest_count: Optional[int] = Field(None, alias="expectedGuestCount", ge=1, le=10000, description="Estimated Guests")
    estimated_budget: Optional[Decimal] = Field(None, alias="estimatedBudget", ge=0, description="Estimated Budget in INR")
    requirements: Optional[str] = Field(None, description="Client Vision or Requirements")
    assigned_staff: Optional[str] = Field("Maharani Gayatri Singh", alias="assignedStaff", description="Assigned Planner")
    status: EnquiryStatusType = Field("New", description="Current Status")
    internal_notes: Optional[str] = Field(None, alias="internalNotes", description="Internal Staff Notes")

    @field_validator("email")
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", clean):
            raise ValueError("Invalid email format.")
        return clean

    @field_validator("estimated_budget", mode="before")
    def parse_budget_input(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, (int, float, Decimal)):
            return Decimal(str(v))
        if isinstance(v, str):
            clean = v.replace("₹", "").replace(",", "").strip()
            if "cr" in clean.lower():
                num = float(clean.lower().replace("cr", "").strip())
                return Decimal(str(int(num * 10_000_000)))
            if "lakh" in clean.lower():
                num = float(clean.lower().replace("lakh", "").replace("s", "").strip())
                return Decimal(str(int(num * 100_000)))
            return Decimal(clean)
        return v


class EnquiryCreate(EnquiryBase):
    pass


class EnquiryUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    client_name: Optional[str] = Field(None, alias="clientName", min_length=2, max_length=150)
    email: Optional[str] = Field(None, min_length=5, max_length=255)
    phone: Optional[str] = Field(None, min_length=5, max_length=50)
    enquiry_source: Optional[EnquirySourceType] = Field(None, alias="enquirySource")

    wedding_date: Optional[date] = Field(None, alias="weddingDate")
    wedding_location: Optional[str] = Field(None, alias="weddingLocation", max_length=255)
    expected_guest_count: Optional[int] = Field(None, alias="expectedGuestCount", ge=1)
    estimated_budget: Optional[Decimal] = Field(None, alias="estimatedBudget", ge=0)
    requirements: Optional[str] = Field(None)
    assigned_staff: Optional[str] = Field(None, alias="assignedStaff")
    status: Optional[EnquiryStatusType] = Field(None)
    internal_notes: Optional[str] = Field(None, alias="internalNotes")


class EnquiryRegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    partner1_name: Optional[str] = Field(None, alias="partner1Name")
    partner2_name: Optional[str] = Field(None, alias="partner2Name")
    service_package: Optional[str] = Field("Full-Service", alias="servicePackage")
    additional_requirements: Optional[str] = Field(None, alias="additionalRequirements")
    wedding_theme: Optional[str] = Field(None, alias="weddingTheme")


class EnquiryResponse(EnquiryBase):
    id: str
    registration_sent_at: Optional[datetime] = Field(None, alias="registrationSentAt")
    registration_received_at: Optional[datetime] = Field(None, alias="registrationReceivedAt")
    client_id: Optional[str] = Field(None, alias="clientId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    notes_history: List[EnquiryNoteResponse] = Field(default_factory=list, alias="notesHistory")
    documents: List[DocumentSummary] = Field(default_factory=list)


class EnquiryListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[EnquiryResponse]
