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
    description: Optional[str] = None
    due_date: date = Field(..., alias="dueDate")
    status: MilestoneStatusType = Field("Pending")


class ProjectMilestoneCreate(ProjectMilestoneBase):
    pass


class ProjectMilestoneUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    milestone_name: Optional[str] = Field(None, alias="milestoneName", min_length=2, max_length=255)
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



# =====================================================================
# Planning Tasks
# =====================================================================

class PlanningTaskBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    title: str = Field(..., min_length=2, max_length=255)
    category: str = Field(..., max_length=100)
    stage: str = Field("To Plan")  # To Plan, In Progress, Review, Done
    assigned_to: str = Field("Maharani Gayatri Singh", alias="assignedTo", max_length=150)
    priority: str = Field("Medium")
    due_date: date = Field(..., alias="dueDate")
    notes: Optional[str] = None
    is_completed: bool = Field(False, alias="isCompleted")
    function_id: Optional[str] = Field(None, alias="functionId")


class PlanningTaskCreate(PlanningTaskBase):
    pass


class PlanningTaskUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    title: Optional[str] = None
    category: Optional[str] = None
    stage: Optional[str] = None
    assigned_to: Optional[str] = Field(None, alias="assignedTo")
    priority: Optional[str] = None
    due_date: Optional[date] = Field(None, alias="dueDate")
    notes: Optional[str] = None
    is_completed: Optional[bool] = Field(None, alias="isCompleted")
    function_id: Optional[str] = Field(None, alias="functionId")


class PlanningTaskResponse(PlanningTaskBase):
    id: str
    project_id: str = Field(..., alias="projectId")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


# =====================================================================
# Payment Stages
# =====================================================================

class PaymentStageBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    stage_name: str = Field(..., alias="stageName", max_length=150)
    percentage: Decimal = Field(..., ge=0, le=100)
    amount: Decimal = Field(Decimal("0.00"), ge=0)
    due_date: date = Field(..., alias="dueDate")
    due_description: Optional[str] = Field(None, alias="dueDescription")
    status: str = Field("Pending")
    paid_at: Optional[datetime] = Field(None, alias="paidAt")


class PaymentStageCreate(PaymentStageBase):
    pass


class PaymentStageUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    stage_name: Optional[str] = Field(None, alias="stageName")
    percentage: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    due_date: Optional[date] = Field(None, alias="dueDate")
    due_description: Optional[str] = Field(None, alias="dueDescription")
    status: Optional[str] = None
    paid_at: Optional[datetime] = Field(None, alias="paidAt")


class PaymentStageResponse(PaymentStageBase):
    id: str
    project_id: str = Field(..., alias="projectId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


# =====================================================================
# Team Time Entries & Profitability (P0 Item 4)
# =====================================================================

class TeamTimeEntryBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    employee_name: str = Field(..., alias="employeeName", max_length=150)
    role: str = Field("Wedding Planner")
    hours: Decimal = Field(..., ge=0)
    hourly_rate: Decimal = Field(..., alias="hourlyRate", ge=0)
    task_description: Optional[str] = Field(None, alias="taskDescription")
    entry_date: date = Field(..., alias="entryDate")


class TeamTimeEntryCreate(TeamTimeEntryBase):
    pass


class TeamTimeEntryResponse(TeamTimeEntryBase):
    id: str
    project_id: str = Field(..., alias="projectId")
    total_cost: Decimal = Field(Decimal("0.00"), alias="totalCost")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class FounderProfitabilityResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    project_id: str = Field(..., alias="projectId")
    project_code: str = Field(..., alias="projectCode")
    project_name: str = Field(..., alias="projectName")
    client_payments_received: Decimal = Field(Decimal("0.00"), alias="clientPaymentsReceived")
    vendor_contracted_costs: Decimal = Field(Decimal("0.00"), alias="vendorContractedCosts")
    team_labor_costs: Decimal = Field(Decimal("0.00"), alias="teamLaborCosts")
    founder_gross_profit: Decimal = Field(Decimal("0.00"), alias="founderGrossProfit")
    profit_margin_percentage: Decimal = Field(Decimal("0.00"), alias="profitMarginPercentage")
    time_entries_count: int = Field(0, alias="timeEntriesCount")
    total_team_hours: Decimal = Field(Decimal("0.00"), alias="totalTeamHours")


class DepositPaidResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    project_id: str = Field(..., alias="projectId")
    project_code: str = Field(..., alias="projectCode")
    deposit_paid: bool = Field(..., alias="depositPaid")
    deposit_paid_at: datetime = Field(..., alias="depositPaidAt")
    tasks_count: int = Field(..., alias="tasksCount")
    payment_stages_count: int = Field(..., alias="paymentStagesCount")
    package_tier: str = Field(..., alias="packageTier")
    message: str


# =====================================================================
# P1 Item 5: Big Day Live Schedule & Check-in
# =====================================================================

class BigDayScheduleEventBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    title: str = Field(..., min_length=2, max_length=255)
    event_time: str = Field(..., alias="eventTime", max_length=20)
    expected_arrival_time: Optional[datetime] = Field(None, alias="expectedArrivalTime")
    owner_name: str = Field("Maharani Gayatri Singh", alias="ownerName", max_length=150)
    vendor_id: Optional[str] = Field(None, alias="vendorId")
    vendor_name: Optional[str] = Field(None, alias="vendorName")
    grace_period_minutes: int = Field(15, alias="gracePeriodMinutes", ge=0)
    status: str = Field("Scheduled")
    notes: Optional[str] = None


class BigDayScheduleEventCreate(BigDayScheduleEventBase):
    pass


class BigDayScheduleEventUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    title: Optional[str] = None
    event_time: Optional[str] = Field(None, alias="eventTime")
    expected_arrival_time: Optional[datetime] = Field(None, alias="expectedArrivalTime")
    owner_name: Optional[str] = Field(None, alias="ownerName")
    vendor_id: Optional[str] = Field(None, alias="vendorId")
    vendor_name: Optional[str] = Field(None, alias="vendorName")
    grace_period_minutes: Optional[int] = Field(None, alias="gracePeriodMinutes")
    status: Optional[str] = None
    notes: Optional[str] = None


class BigDayScheduleEventResponse(BigDayScheduleEventBase):
    id: str
    project_id: str = Field(..., alias="projectId")
    arrived_at: Optional[datetime] = Field(None, alias="arrivedAt")
    is_late: bool = Field(False, alias="isLate")
    minutes_late: int = Field(0, alias="minutesLate")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class BigDayScheduleOverviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    project_id: str = Field(..., alias="projectId")
    total_events: int = Field(0, alias="totalEvents")
    arrived_count: int = Field(0, alias="arrivedCount")
    late_count: int = Field(0, alias="lateCount")
    pending_count: int = Field(0, alias="pendingCount")
    server_time: datetime = Field(..., alias="serverTime")
    events: List[BigDayScheduleEventResponse] = []


# =====================================================================
# P1 Item 6: Extras & Final Settlement
# =====================================================================

class WeddingExtraBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    description: str = Field(..., min_length=2, max_length=255)
    category: str = Field("Catering")
    quantity: Decimal = Field(Decimal("1.00"), ge=0)
    unit_price: Decimal = Field(Decimal("0.00"), alias="unitPrice", ge=0)
    client_amount: Decimal = Field(Decimal("0.00"), alias="clientAmount", ge=0)
    vendor_amount: Decimal = Field(Decimal("0.00"), alias="vendorAmount", ge=0)
    is_approved: bool = Field(True, alias="isApproved")
    approved_by: str = Field("Maharani Gayatri Singh", alias="approvedBy")
    vendor_id: Optional[str] = Field(None, alias="vendorId")


class WeddingExtraCreate(WeddingExtraBase):
    pass


class WeddingExtraResponse(WeddingExtraBase):
    id: str
    project_id: str = Field(..., alias="projectId")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class VendorPayoutCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    vendor_id: str = Field(..., alias="vendorId")
    agreed_amount: Decimal = Field(..., alias="agreedAmount", ge=0)
    approved_extras: Decimal = Field(Decimal("0.00"), alias="approvedExtras", ge=0)
    advance_paid: Decimal = Field(Decimal("0.00"), alias="advancePaid", ge=0)
    notes: Optional[str] = None


class VendorPayoutResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    project_id: str = Field(..., alias="projectId")
    vendor_id: str = Field(..., alias="vendorId")
    vendor_name: Optional[str] = Field(None, alias="vendorName")
    idempotency_key: str = Field(..., alias="idempotencyKey")
    agreed_amount: Decimal = Field(..., alias="agreedAmount")
    approved_extras: Decimal = Field(..., alias="approvedExtras")
    advance_paid: Decimal = Field(..., alias="advancePaid")
    final_payout_amount: Decimal = Field(..., alias="finalPayoutAmount")
    status: str
    notes: Optional[str] = None
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class ClientInvoiceSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    package_budget: Decimal = Field(..., alias="packageBudget")
    approved_extras: Decimal = Field(..., alias="approvedExtras")
    total_invoice: Decimal = Field(..., alias="totalInvoice")
    payments_received: Decimal = Field(..., alias="paymentsReceived")
    balance_due: Decimal = Field(..., alias="balanceDue")


class FinalSettlementResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    project_id: str = Field(..., alias="projectId")
    project_code: str = Field(..., alias="projectCode")
    project_name: str = Field(..., alias="projectName")
    client_invoice: ClientInvoiceSummary = Field(..., alias="clientInvoice")
    vendor_payouts: List[VendorPayoutResponse] = Field([], alias="vendorPayouts")
    total_vendor_payouts: Decimal = Field(Decimal("0.00"), alias="totalVendorPayouts")
    agency_gross_retainage: Decimal = Field(Decimal("0.00"), alias="agencyGrossRetainage")
    is_settled: bool = Field(False, alias="isSettled")


# =====================================================================
# P1 Item 7: Client Wedding Overview (Read-Only)
# =====================================================================

class ConfirmedVendorItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    vendor_id: str = Field(..., alias="vendorId")
    name: str
    category: str
    status: str
    contact_person: Optional[str] = Field(None, alias="contactPerson")


class TaskProgressSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    total_tasks: int = Field(..., alias="totalTasks")
    completed_tasks: int = Field(..., alias="completedTasks")
    completion_percentage: Decimal = Field(..., alias="completionPercentage")


class PaymentProgressSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    deposit_paid: bool = Field(..., alias="depositPaid")
    total_budget: Decimal = Field(..., alias="totalBudget")
    total_paid: Decimal = Field(..., alias="totalPaid")
    balance_remaining: Decimal = Field(..., alias="balanceRemaining")
    stages: List[PaymentStageResponse] = []


class FinalCostsSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    base_budget: Decimal = Field(..., alias="baseBudget")
    extras_total: Decimal = Field(..., alias="extrasTotal")
    final_total_cost: Decimal = Field(..., alias="finalTotalCost")


class ClientWeddingOverviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    project_id: str = Field(..., alias="projectId")
    project_code: str = Field(..., alias="projectCode")
    project_name: str = Field(..., alias="projectName")
    wedding_date: date = Field(..., alias="weddingDate")
    location: str
    guest_count: int = Field(..., alias="guestCount")
    package_tier: str = Field(..., alias="packageTier")
    events: List[WeddingFunctionResponse] = []
    live_schedule: List[BigDayScheduleEventResponse] = Field([], alias="liveSchedule")
    task_progress: TaskProgressSummary = Field(..., alias="taskProgress")
    confirmed_vendors: List[ConfirmedVendorItem] = Field([], alias="confirmedVendors")
    payment_status: PaymentProgressSummary = Field(..., alias="paymentStatus")
    final_costs: FinalCostsSummary = Field(..., alias="finalCosts")
