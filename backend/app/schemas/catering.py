from typing import Optional, List, Literal, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.vendor import VendorResponse

CateringStatusType = Literal[
    "Draft",
    "Requirements Confirmed",
    "Quotation Requested",
    "Vendor Selected",
    "Menu Finalized",
    "Sent to Vendor",
    "Vendor Confirmed"
]


# =====================================================================
# Catering Menu Items
# =====================================================================

class CateringMenuItemBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    course_category: str = Field(..., alias="courseCategory", min_length=2, max_length=100, description="Course section (e.g. Welcome Drinks, Royal Appetizers, Main Courses, Desserts)")
    item_name: str = Field(..., alias="itemName", min_length=2, max_length=255, description="Name of dish or beverage")
    description: Optional[str] = Field(None, description="Culinary description, preparation notes, or ingredients")
    dietary_tag: str = Field("Vegetarian", alias="dietaryTag", max_length=50, description="Dietary classification (e.g. Vegetarian, Non-Vegetarian, Jain, Vegan)")
    quantity_note: Optional[str] = Field(None, alias="quantityNote", max_length=150, description="Serving style, portion estimate, or presentation method")
    display_order: int = Field(1, alias="displayOrder", ge=1, description="Display order within menu")


class CateringMenuItemCreate(CateringMenuItemBase):
    pass


class CateringMenuItemUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    course_category: Optional[str] = Field(None, alias="courseCategory", min_length=2, max_length=100)
    item_name: Optional[str] = Field(None, alias="itemName", min_length=2, max_length=255)
    description: Optional[str] = None
    dietary_tag: Optional[str] = Field(None, alias="dietaryTag", max_length=50)
    quantity_note: Optional[str] = Field(None, alias="quantityNote", max_length=150)
    display_order: Optional[int] = Field(None, alias="displayOrder", ge=1)


class CateringMenuItemResponse(CateringMenuItemBase):
    id: str
    catering_plan_id: str = Field(..., alias="cateringPlanId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class MenuItemReorderItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    display_order: int = Field(..., alias="displayOrder", ge=1)


class MenuItemReorderRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: List[MenuItemReorderItem]


# =====================================================================
# Menu Presets
# =====================================================================

class PresetSummaryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    tagline: str
    description: str
    recommended_service_style: str = Field(..., alias="recommendedServiceStyle")
    cuisine_preference: str = Field(..., alias="cuisinePreference")
    total_items: int = Field(..., alias="totalItems")
    courses_count: int = Field(..., alias="coursesCount")


class PresetDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    tagline: str
    description: str
    recommended_service_style: str = Field(..., alias="recommendedServiceStyle")
    cuisine_preference: str = Field(..., alias="cuisinePreference")
    items: List[Dict[str, Any]]


class ApplyPresetRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    preset_id: str = Field(..., alias="presetId", description="ID or slug of preset (e.g. mewari_feast, sheesh_mahal, pan_asian_luxury)")
    mode: Literal["append", "replace"] = Field("append", description="'append' preserves existing items and adds preset courses; 'replace' clears existing items")


# =====================================================================
# Catering Plans
# =====================================================================

class CateringPlanBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    service_style: str = Field("Silver Platter Degustation", alias="serviceStyle", max_length=100)
    cuisine_preferences: Optional[str] = Field(None, alias="cuisinePreferences")
    guest_count: Optional[int] = Field(None, alias="guestCount", ge=1, description="Event guest count; defaults to wedding project guest count if omitted")
    veg_count: int = Field(0, alias="vegCount", ge=0, description="Flexible estimate of vegetarian guests")
    non_veg_count: int = Field(0, alias="nonVegCount", ge=0, description="Flexible estimate of non-vegetarian guests")
    jain_count: int = Field(0, alias="jainCount", ge=0, description="Flexible estimate of strict Jain guests")
    dietary_notes: Optional[str] = Field(None, alias="dietaryNotes")
    service_timings: Optional[str] = Field(None, alias="serviceTimings", max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    budget: Optional[Decimal] = Field(Decimal("0.00"), ge=0)
    selected_vendor_id: Optional[str] = Field(None, alias="selectedVendorId")
    agreed_cost: Optional[Decimal] = Field(None, alias="agreedCost", ge=0)
    notes: Optional[str] = None

    @field_validator("budget", "agreed_cost", mode="before")
    def parse_decimal(cls, v):
        if v is None or v == "":
            return None
        return Decimal(str(v))


class CateringPlanCreate(CateringPlanBase):
    pass


class CateringPlanUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    service_style: Optional[str] = Field(None, alias="serviceStyle", max_length=100)
    cuisine_preferences: Optional[str] = Field(None, alias="cuisinePreferences")
    guest_count: Optional[int] = Field(None, alias="guestCount", ge=1)
    veg_count: Optional[int] = Field(None, alias="vegCount", ge=0)
    non_veg_count: Optional[int] = Field(None, alias="nonVegCount", ge=0)
    jain_count: Optional[int] = Field(None, alias="jainCount", ge=0)
    dietary_notes: Optional[str] = Field(None, alias="dietaryNotes")
    service_timings: Optional[str] = Field(None, alias="serviceTimings", max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    budget: Optional[Decimal] = Field(None, ge=0)
    selected_vendor_id: Optional[str] = Field(None, alias="selectedVendorId")
    agreed_cost: Optional[Decimal] = Field(None, alias="agreedCost", ge=0)
    status: Optional[CateringStatusType] = None
    notes: Optional[str] = None

    @field_validator("budget", "agreed_cost", mode="before")
    def parse_decimal(cls, v):
        if v is None or v == "":
            return None
        return Decimal(str(v))


class CateringStatusUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    status: CateringStatusType
    notes: Optional[str] = None


class CateringPlanResponse(CateringPlanBase):
    id: str
    project_id: str = Field(..., alias="projectId")
    function_id: str = Field(..., alias="functionId")
    status: CateringStatusType
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    # Joined function/project metadata
    function_name: Optional[str] = Field(None, alias="functionName")
    function_date: Optional[date] = Field(None, alias="functionDate")
    function_venue: Optional[str] = Field(None, alias="functionVenue")
    project_name: Optional[str] = Field(None, alias="projectName")
    project_guest_count: Optional[int] = Field(None, alias="projectGuestCount")
    selected_vendor: Optional[VendorResponse] = Field(None, alias="selectedVendor")
    menu_items_count: int = Field(0, alias="menuItemsCount")
    quotations_count: int = Field(0, alias="quotationsCount")


class CateringPlanDetailResponse(CateringPlanResponse):
    menu_items: List[CateringMenuItemResponse] = Field(default_factory=list, alias="menuItems")


# =====================================================================
# Catering Quotations & Costing Engine
# =====================================================================

QuotationStatusType = Literal[
    "Received",
    "Under Review",
    "Accepted",
    "Rejected"
]


class CateringQuotationBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    vendor_id: str = Field(..., alias="vendorId", description="Vendor registering the quotation")
    quotation_reference: Optional[str] = Field(None, alias="quotationReference", max_length=100, description="Vendor reference code (e.g. QUO-MEWAR-2027-01)")
    per_person_rate: Decimal = Field(..., alias="perPersonRate", ge=0, description="Rate per guest in INR")
    total_guest_count: Optional[int] = Field(None, alias="totalGuestCount", ge=1, description="Guest count; defaults to catering plan guest count if omitted")
    equipment_charges: Decimal = Field(Decimal("0.00"), alias="equipmentCharges", ge=0, description="Additional charges for kitchen setup, crockery, live counters, etc.")
    gst_rate_percent: Decimal = Field(Decimal("18.00"), alias="gstRatePercent", ge=0, description="Configurable GST rate percentage (e.g. 0%, 5%, 12%, 18%, or custom)")
    validity_date: Optional[date] = Field(None, alias="validityDate", description="Quotation validity deadline")
    notes: Optional[str] = Field(None, description="Inclusions, payment terms, or setup specifications")

    @field_validator("per_person_rate", "equipment_charges", "gst_rate_percent", mode="before")
    def parse_quotation_decimals(cls, v):
        if v is None or v == "":
            return Decimal("0.00")
        return Decimal(str(v))


class CateringQuotationCreate(CateringQuotationBase):
    pass


class CateringQuotationUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    per_person_rate: Optional[Decimal] = Field(None, alias="perPersonRate", ge=0)
    total_guest_count: Optional[int] = Field(None, alias="totalGuestCount", ge=1)
    equipment_charges: Optional[Decimal] = Field(None, alias="equipmentCharges", ge=0)
    gst_rate_percent: Optional[Decimal] = Field(None, alias="gstRatePercent", ge=0)
    validity_date: Optional[date] = Field(None, alias="validityDate")
    notes: Optional[str] = None
    status: Optional[QuotationStatusType] = None

    @field_validator("per_person_rate", "equipment_charges", "gst_rate_percent", mode="before")
    def parse_quotation_decimals(cls, v):
        if v is None or v == "":
            return None
        return Decimal(str(v))


class CateringQuotationResponse(CateringQuotationBase):
    id: str
    catering_plan_id: str = Field(..., alias="cateringPlanId")
    food_subtotal: Decimal = Field(..., alias="foodSubtotal", description="Calculated as perPersonRate * totalGuestCount")
    gst_amount: Decimal = Field(..., alias="gstAmount", description="Calculated as (foodSubtotal + equipmentCharges) * (gstRatePercent / 100)")
    total_amount: Decimal = Field(..., alias="totalAmount", description="Calculated as foodSubtotal + equipmentCharges + gstAmount")
    status: QuotationStatusType
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    # Joined vendor details
    vendor_name: Optional[str] = Field(None, alias="vendorName")
    vendor_phone: Optional[str] = Field(None, alias="vendorPhone")
    vendor_contact_person: Optional[str] = Field(None, alias="vendorContactPerson")
    vendor_city: Optional[str] = Field(None, alias="vendorCity")
    vendor_rating: Optional[Decimal] = Field(None, alias="vendorRating")


class CateringQuotationSelectResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool = True
    message: str
    catering_plan_id: str = Field(..., alias="cateringPlanId")
    selected_vendor_id: str = Field(..., alias="selectedVendorId")
    agreed_cost: Decimal = Field(..., alias="agreedCost")
    selected_quotation_id: str = Field(..., alias="selectedQuotationId")
    selected_quotation: CateringQuotationResponse = Field(..., alias="selectedQuotation")


class CateringWhatsAppShareRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    vendor_id: Optional[str] = Field(None, alias="vendorId")
    quotation_id: Optional[str] = Field(None, alias="quotationId")
    recipient_phone: Optional[str] = Field(None, alias="recipientPhone")
    custom_message: Optional[str] = Field(None, alias="customMessage")


class CateringWhatsAppShareResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    mode: str = "manual_whatsapp_link"
    share_url: str = Field(..., alias="shareUrl")
    recipient_phone: str = Field(..., alias="recipientPhone")
    message_text: str = Field(..., alias="messageText")
    communication_id: str = Field(..., alias="communicationId")



