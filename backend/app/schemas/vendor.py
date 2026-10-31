from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class VendorBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    name: str = Field(..., min_length=2, max_length=150, description="Vendor business name")
    category: str = Field("Catering", max_length=50, description="Vendor category (e.g. Catering, Decor, Photography)")
    contact_person: Optional[str] = Field(None, alias="contactPerson", max_length=100)
    phone: Optional[str] = Field("", max_length=50, description="WhatsApp-enabled phone number")
    email: Optional[str] = Field(None, max_length=255)
    city: str = Field("Jaipur", max_length=100)
    address: Optional[str] = None
    rating: Optional[Decimal] = Field(Decimal("5.00"), ge=0, le=5, description="Quality rating between 0 and 5")
    notes: Optional[str] = None
    is_active: bool = Field(True, alias="isActive")

    @field_validator("rating", mode="before")
    def parse_rating(cls, v):
        if v is None or v == "":
            return None
        return Decimal(str(v))


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    name: Optional[str] = Field(None, min_length=2, max_length=150)
    category: Optional[str] = Field(None, max_length=50)
    contact_person: Optional[str] = Field(None, alias="contactPerson", max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    rating: Optional[Decimal] = Field(None, ge=0, le=5)
    notes: Optional[str] = None
    is_active: Optional[bool] = Field(None, alias="isActive")

    @field_validator("rating", mode="before")
    def parse_rating(cls, v):
        if v is None or v == "":
            return None
        return Decimal(str(v))


class VendorStatusUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    is_active: bool = Field(..., alias="isActive")
    notes: Optional[str] = None


class VendorResponse(VendorBase):
    id: str
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class VendorDetailResponse(VendorResponse):
    catering_plans_count: int = Field(0, alias="cateringPlansCount")
    quotations_count: int = Field(0, alias="quotationsCount")


class VendorListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    total: int
    page: int
    page_size: int = Field(..., alias="pageSize")
    items: List[VendorResponse]

