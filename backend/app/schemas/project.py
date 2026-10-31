from typing import Optional, List, Literal, Any
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator

ProjectStatusType = Literal[
    "Planning",
    "In Progress",
    "On Hold",
    "Completed",
    "Cancelled"
]

FunctionStatusType = Literal[
    "Scheduled",
    "In Progress",
    "Completed",
    "Cancelled"
]

MilestoneStatusType = Literal[
    "Pending",
    "In Progress",
    "Completed"
]


# =====================================================================
# Wedding Functions
# =====================================================================

class WeddingFunctionBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    function_name: str = Field(..., alias="functionName", min_length=2, max_length=100)
    function_date: date = Field(..., alias="functionDate")
    start_time: Optional[str] = Field(None, alias="startTime", max_length=20)
    end_time: Optional[str] = Field(None, alias="endTime", max_length=20)
    venue: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    guest_count_override: Optional[int] = Field(None, alias="guestCountOverride", ge=1)
    event_notes: Optional[str] = Field(None, alias="eventNotes")
    status: FunctionStatusType = Field("Scheduled")
    estimated_cost: Optional[Decimal] = Field(None, alias="estimatedCost", ge=0)

    @field_validator("estimated_cost", mode="before")
    def parse_cost(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, (int, float, Decimal)):
            return Decimal(str(v))
        try:
            return Decimal(str(v))
        except Exception:
            return None


class WeddingFunctionCreate(WeddingFunctionBase):
    pass


class WeddingFunctionUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    function_name: Optional[str] = Field(None, alias="functionName", min_length=2, max_length=100)
    function_date: Optional[date] = Field(None, alias="functionDate")
    start_time: Optional[str] = Field(None, alias="startTime", max_length=20)
    end_time: Optional[str] = Field(None, alias="endTime", max_length=20)
    venue: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    guest_count_override: Optional[int] = Field(None, alias="guestCountOverride", ge=1)
    event_notes: Optional[str] = Field(None, alias="eventNotes")
    status: Optional[FunctionStatusType] = None
    estimated_cost: Optional[Decimal] = Field(None, alias="estimatedCost", ge=0)

    @field_validator("estimated_cost", mode="before")
    def parse_cost(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, (int, float, Decimal)):
            return Decimal(str(v))
        try:
            return Decimal(str(v))
        except Exception:
            return None


class WeddingFunctionResponse(WeddingFunctionBase):
    id: str
    project_id: str = Field(..., alias="projectId")
    estimated_cost: Decimal = Field(Decimal("0.00"), alias="estimatedCost")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


# =====================================================================
# Project Milestones
# =====================================================================

class ProjectMilestoneBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    milestone_name: str = Field(..., alias="milestoneName", min_length=2, max_length=255)
    assigned_to: Optional[str] = Field(None, alias="assignedTo")
    function_id: Optional[str] = Field(None, alias="functionId")
    category: str = "General"
    description: Optional[str] = None
    due_date: date = Field(..., alias="dueDate")
    status: MilestoneStatusType = Field("Pending")


class ProjectMilestoneCreate(ProjectMilestoneBase):
    pass


class ProjectMilestoneUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    milestone_name: Optional[str] = Field(None, alias="milestoneName", min_length=2, max_length=255)
    assigned_to: Optional[str] = Field(None, alias="assignedTo")
    function_id: Optional[str] = Field(None, alias="functionId")
    category: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = Field(None, alias="dueDate")
    status: Optional[MilestoneStatusType] = None


class ProjectMilestoneResponse(ProjectMilestoneBase):
    id: str
    project_id: str = Field(..., alias="projectId")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


# =====================================================================
# Project Status History
# =====================================================================

class ProjectStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: int
    project_id: str = Field(..., alias="projectId")
    old_status: Optional[str] = Field(None, alias="oldStatus")
    new_status: str = Field(..., alias="newStatus")
    changed_by: str = Field(..., alias="changedBy")
    notes: Optional[str] = None
    changed_at: datetime = Field(..., alias="changedAt")


class ProjectStatusUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    status: ProjectStatusType
    changed_by: Optional[str] = Field("Agency Staff", alias="changedBy")
    notes: Optional[str] = None


# =====================================================================
# Wedding Project
# =====================================================================

class WeddingProjectCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    client_id: str = Field(..., alias="clientId", description="Confirmed client reference ID (e.g. TRK-2026-081)")
    project_name: Optional[str] = Field(None, alias="projectName", max_length=255)
    wedding_date: Optional[date] = Field(None, alias="weddingDate")
    location: Optional[str] = Field(None, max_length=255)
    guest_count: Optional[int] = Field(None, alias="guestCount", ge=1)
    estimated_budget: Optional[Decimal] = Field(None, alias="estimatedBudget", ge=0)
    package_tier: Optional[str] = Field(None, alias="packageTier", max_length=50)
    project_manager_name: Optional[str] = Field("Maharani Gayatri Singh", alias="projectManagerName", max_length=100)
    notes: Optional[str] = None

    @field_validator("estimated_budget", mode="before")
    def parse_budget_input(cls, v):
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
            try:
                return Decimal(clean)
            except Exception:
                return Decimal("0.00")
        return v


class WeddingProjectUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    project_name: Optional[str] = Field(None, alias="projectName", max_length=255)
    wedding_date: Optional[date] = Field(None, alias="weddingDate")
    location: Optional[str] = Field(None, max_length=255)
    guest_count: Optional[int] = Field(None, alias="guestCount", ge=1)
    estimated_budget: Optional[Decimal] = Field(None, alias="estimatedBudget", ge=0)
    package_tier: Optional[str] = Field(None, alias="packageTier", max_length=50)
    project_manager_name: Optional[str] = Field(None, alias="projectManagerName", max_length=100)
    notes: Optional[str] = None

    @field_validator("estimated_budget", mode="before")
    def parse_budget_update(cls, v):
        if v is None:
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
            try:
                return Decimal(clean)
            except Exception:
                return None
        return v


class ClientDossierSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    partner1_name: str = Field(..., alias="partner1Name")
    partner2_name: str = Field(..., alias="partner2Name")
    email: str
    phone: str
    status: str
    wedding_location: str = Field(..., alias="weddingLocation")
    wedding_date: date = Field(..., alias="weddingDate")
    expected_guest_count: int = Field(..., alias="expectedGuestCount")
    estimated_budget: Decimal = Field(..., alias="estimatedBudget")
    service_package: str = Field(..., alias="servicePackage")
    wedding_theme: Optional[str] = Field(None, alias="weddingTheme")


class WeddingProjectResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    project_code: str = Field(..., alias="projectCode")
    client_id: str = Field(..., alias="clientId")
    booking_id: Optional[str] = Field(None, alias="bookingId")
    project_name: str = Field(..., alias="projectName")
    wedding_date: date = Field(..., alias="weddingDate")
    location: str
    guest_count: int = Field(..., alias="guestCount")
    estimated_budget: Decimal = Field(..., alias="estimatedBudget")
    package_tier: str = Field(..., alias="packageTier")
    project_manager_name: str = Field(..., alias="projectManagerName")
    status: ProjectStatusType
    notes: Optional[str] = None
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    couple_name: Optional[str] = Field(None, alias="coupleName")
    client: Optional[ClientDossierSummary] = None
    functions: List[WeddingFunctionResponse] = []
    milestones: List[ProjectMilestoneResponse] = []
    status_history: List[ProjectStatusHistoryResponse] = Field([], alias="statusHistory")


class WeddingProjectListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    project_code: str = Field(..., alias="projectCode")
    client_id: str = Field(..., alias="clientId")
    project_name: str = Field(..., alias="projectName")
    couple_name: str = Field(..., alias="coupleName")
    wedding_date: date = Field(..., alias="weddingDate")
    location: str
    guest_count: int = Field(..., alias="guestCount")
    estimated_budget: Decimal = Field(..., alias="estimatedBudget")
    package_tier: str = Field(..., alias="packageTier")
    project_manager_name: str = Field(..., alias="projectManagerName")
    status: ProjectStatusType
    created_at: datetime = Field(..., alias="createdAt")
    functions_count: int = Field(0, alias="functionsCount")
    completed_milestones_count: int = Field(0, alias="completedMilestonesCount")
    total_milestones_count: int = Field(0, alias="totalMilestonesCount")


class EligibleBookingResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    client_id: str = Field(..., alias="clientId")
    partner1_name: str = Field(..., alias="partner1Name")
    partner2_name: str = Field(..., alias="partner2Name")
    couple_name: str = Field(..., alias="coupleName")
    wedding_date: date = Field(..., alias="weddingDate")
    wedding_location: str = Field(..., alias="weddingLocation")
    expected_guest_count: int = Field(..., alias="expectedGuestCount")
    estimated_budget: Decimal = Field(..., alias="estimatedBudget")
    service_package: str = Field(..., alias="servicePackage")
    status: str
    created_at: datetime = Field(..., alias="createdAt")

