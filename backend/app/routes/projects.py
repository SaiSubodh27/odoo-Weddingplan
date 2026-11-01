from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.project_service import project_service
from decimal import Decimal
from app.schemas.project import (
    WeddingProjectCreate,
    WeddingProjectUpdate,
    ProjectStatusUpdate,
    WeddingFunctionCreate,
    WeddingFunctionUpdate,
    WeddingFunctionResponse,
    ProjectMilestoneCreate,
    ProjectMilestoneUpdate,
    ProjectMilestoneResponse,
    WeddingProjectResponse,
    WeddingProjectListItem,
    EligibleBookingResponse,
    PlanningTaskCreate,
    PlanningTaskUpdate,
    PlanningTaskResponse,
    PaymentStageCreate,
    PaymentStageUpdate,
    PaymentStageResponse,
    TeamTimeEntryCreate,
    TeamTimeEntryResponse,
    FounderProfitabilityResponse,
    DepositPaidResponse,
    BigDayScheduleEventCreate,
    BigDayScheduleEventUpdate,
    BigDayScheduleEventResponse,
    BigDayScheduleOverviewResponse,
    WeddingExtraCreate,
    WeddingExtraResponse,
    VendorPayoutCreate,
    VendorPayoutResponse,
    FinalSettlementResponse,
    ClientWeddingOverviewResponse,
)

router = APIRouter()


def _serialize_project_response(project) -> WeddingProjectResponse:
    """Helper to transform ORM WeddingProject with joined client into WeddingProjectResponse."""
    couple_name = f"{project.client.partner1_name} & {project.client.partner2_name}" if project.client else "Palace Couple"

    client_summary = None
    if project.client:
        client_summary = {
            "id": project.client.id,
            "partner1Name": project.client.partner1_name,
            "partner2Name": project.client.partner2_name,
            "email": project.client.email,
            "phone": project.client.phone,
            "status": project.client.status,
            "weddingLocation": project.client.wedding_location,
            "weddingDate": project.client.wedding_date,
            "expectedGuestCount": project.client.expected_guest_count,
            "estimatedBudget": project.client.estimated_budget,
            "servicePackage": project.client.service_package,
            "weddingTheme": project.client.wedding_theme,
        }

    return WeddingProjectResponse(
        id=project.id,
        project_code=project.project_code,
        client_id=project.client_id,
        booking_id=project.booking_id,
        project_name=project.project_name,
        wedding_date=project.wedding_date,
        location=project.location,
        guest_count=project.guest_count,
        estimated_budget=project.estimated_budget,
        package_tier=project.package_tier,
        project_manager_name=project.project_manager_name,
        status=project.status,
        notes=project.notes,
        created_at=project.created_at,
        updated_at=project.updated_at,
        couple_name=couple_name,
        client=client_summary,
        functions=[WeddingFunctionResponse.model_validate(f) for f in project.functions],
        milestones=[ProjectMilestoneResponse.model_validate(m) for m in project.milestones],
        status_history=project.status_history,
    )


@router.get(
    "/eligible-bookings",
    response_model=List[EligibleBookingResponse],
    summary="List confirmed bookings eligible for project creation",
    tags=["Wedding Projects"]
)
def get_eligible_bookings(db: Session = Depends(get_db)):
    """
    Returns confirmed client dossiers that do not yet have an active wedding project.
    """
    return project_service.get_eligible_confirmed_bookings(db)


@router.post(
    "",
    response_model=WeddingProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new wedding project from a confirmed booking",
    tags=["Wedding Projects"]
)
def create_project(
    project_in: WeddingProjectCreate,
    db: Session = Depends(get_db)
):
    """
    Sets up a wedding project from an eligible confirmed client booking dossier.
    Generates a unique project code (e.g. PRJ-2026-001) and sets up initial milestones.
    """
    try:
        project = project_service.create_project(db=db, project_in=project_in)
        # Fetch with relationships for complete response
        full_project = project_service.get_project(db=db, project_id=project.id)
        return _serialize_project_response(full_project)
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create wedding project: {str(e)}"
        )


@router.get(
    "",
    summary="List all wedding projects with filtering and summary progress",
    tags=["Wedding Projects"]
)
def list_projects(
    search: Optional[str] = Query(None, description="Search project code, name, palace venue, or couple name"),
    status: Optional[str] = Query(None, description="Filter by status: Planning, In Progress, On Hold, Completed, Cancelled"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Returns list of wedding projects with milestone progress metrics.
    """
    clean_search = search if isinstance(search, str) else None
    clean_status = status if isinstance(status, str) else None
    clean_page = page if isinstance(page, int) else 1
    clean_page_size = page_size if isinstance(page_size, int) else 50
    projects, total = project_service.list_projects(
        db=db,
        search=clean_search,
        status=clean_status,
        page=clean_page,
        page_size=clean_page_size
    )

    items = []
    for p in projects:
        couple = f"{p.client.partner1_name} & {p.client.partner2_name}" if p.client else "Palace Couple"
        total_ms = len(p.milestones)
        completed_ms = sum(1 for m in p.milestones if m.status == "Completed")
        items.append(
            WeddingProjectListItem(
                id=p.id,
                project_code=p.project_code,
                client_id=p.client_id,
                project_name=p.project_name,
                couple_name=couple,
                wedding_date=p.wedding_date,
                location=p.location,
                guest_count=p.guest_count,
                estimated_budget=p.estimated_budget,
                package_tier=p.package_tier,
                project_manager_name=p.project_manager_name,
                status=p.status,
                created_at=p.created_at,
                functions_count=len(p.functions),
                completed_milestones_count=completed_ms,
                total_milestones_count=total_ms
            )
        )

    return {
        "total": total,
        "page": page,
        "pageSize": page_size,
        "items": items
    }


@router.get(
    "/{project_id}",
    response_model=WeddingProjectResponse,
    summary="Get full wedding project dossier details",
    tags=["Wedding Projects"]
)
def get_project_details(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves complete project dossier including functions, milestones, and status audit log.
    """
    project = project_service.get_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wedding project '{project_id}' not found."
        )
    return _serialize_project_response(project)


@router.put(
    "/{project_id}",
    response_model=WeddingProjectResponse,
    summary="Update wedding project metadata",
    tags=["Wedding Projects"]
)
def update_project(
    project_id: str,
    project_in: WeddingProjectUpdate,
    db: Session = Depends(get_db)
):
    project = project_service.update_project(db=db, project_id=project_id, project_in=project_in)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wedding project '{project_id}' not found."
        )
    full = project_service.get_project(db=db, project_id=project.id)
    return _serialize_project_response(full)


@router.patch(
    "/{project_id}/status",
    response_model=WeddingProjectResponse,
    summary="Update wedding project status & record history audit log",
    tags=["Wedding Projects"]
)
@router.post(
    "/{project_id}/status",
    response_model=WeddingProjectResponse,
    summary="Update wedding project status & record history audit log (POST alias)",
    tags=["Wedding Projects"],
    include_in_schema=False
)
def update_project_status(
    project_id: str,
    status_in: ProjectStatusUpdate,
    db: Session = Depends(get_db)
):
    project = project_service.update_project_status(db=db, project_id=project_id, status_in=status_in)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wedding project '{project_id}' not found."
        )
    full = project_service.get_project(db=db, project_id=project.id)
    return _serialize_project_response(full)


# =====================================================================
# Wedding Functions Endpoints
# =====================================================================

@router.get(
    "/{project_id}/functions",
    response_model=List[WeddingFunctionResponse],
    summary="List all wedding functions for a project",
    tags=["Wedding Functions"]
)
def list_wedding_functions(
    project_id: str,
    db: Session = Depends(get_db)
):
    project = project_service.get_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found.")
    return project.functions


@router.post(
    "/{project_id}/functions",
    response_model=WeddingFunctionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a wedding function to the project",
    tags=["Wedding Functions"]
)
def add_wedding_function(
    project_id: str,
    func_in: WeddingFunctionCreate,
    db: Session = Depends(get_db)
):
    try:
        func_item = project_service.add_function(db=db, project_id=project_id, func_in=func_in)
        return func_item
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{project_id}/functions/{func_id}",
    response_model=WeddingFunctionResponse,
    summary="Update a wedding function",
    tags=["Wedding Functions"]
)
@router.patch(
    "/{project_id}/functions/{func_id}",
    response_model=WeddingFunctionResponse,
    summary="Update a wedding function (partial)",
    tags=["Wedding Functions"],
    include_in_schema=False
)
def update_wedding_function(
    project_id: str,
    func_id: str,
    func_in: WeddingFunctionUpdate,
    db: Session = Depends(get_db)
):
    func_item = project_service.update_function(db=db, project_id=project_id, func_id=func_id, func_in=func_in)
    if not func_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Function '{func_id}' not found.")
    return func_item


@router.put(
    "/functions/{func_id}",
    response_model=WeddingFunctionResponse,
    summary="Update a wedding function directly by ID",
    tags=["Wedding Functions"],
    include_in_schema=False
)
@router.patch(
    "/functions/{func_id}",
    response_model=WeddingFunctionResponse,
    summary="Update a wedding function directly by ID (partial)",
    tags=["Wedding Functions"],
    include_in_schema=False
)
def update_wedding_function_direct(
    func_id: str,
    func_in: WeddingFunctionUpdate,
    db: Session = Depends(get_db)
):
    func_item = project_service.update_function(db=db, project_id="", func_id=func_id, func_in=func_in)
    if not func_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Function '{func_id}' not found.")
    return func_item


@router.delete(
    "/{project_id}/functions/{func_id}",
    summary="Delete a wedding function",
    tags=["Wedding Functions"]
)
def delete_wedding_function(
    project_id: str,
    func_id: str,
    db: Session = Depends(get_db)
):
    success = project_service.delete_function(db=db, project_id=project_id, func_id=func_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Function '{func_id}' not found.")
    return {"success": True, "message": f"Wedding function '{func_id}' deleted."}


# =====================================================================
# Project Milestones Endpoints
# =====================================================================

@router.post(
    "/{project_id}/milestones",
    response_model=ProjectMilestoneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a project milestone checkpoint",
    tags=["Project Milestones"]
)
def add_project_milestone(
    project_id: str,
    ms_in: ProjectMilestoneCreate,
    db: Session = Depends(get_db)
):
    try:
        ms = project_service.add_milestone(db=db, project_id=project_id, ms_in=ms_in)
        return ms
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{project_id}/milestones/{ms_id}",
    response_model=ProjectMilestoneResponse,
    summary="Update a project milestone status or details",
    tags=["Project Milestones"]
)
@router.patch(
    "/{project_id}/milestones/{ms_id}",
    response_model=ProjectMilestoneResponse,
    summary="Update a project milestone status or details (partial)",
    tags=["Project Milestones"],
    include_in_schema=False
)
def update_project_milestone(
    project_id: str,
    ms_id: str,
    ms_in: ProjectMilestoneUpdate,
    db: Session = Depends(get_db)
):
    ms = project_service.update_milestone(db=db, project_id=project_id, ms_id=ms_id, ms_in=ms_in)
    if not ms:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Milestone '{ms_id}' not found.")
    return ms


@router.delete(
    "/{project_id}/milestones/{ms_id}",
    summary="Delete a project milestone",
    tags=["Project Milestones"]
)
def delete_project_milestone(
    project_id: str,
    ms_id: str,
    db: Session = Depends(get_db)
):
    success = project_service.delete_milestone(db=db, project_id=project_id, ms_id=ms_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Milestone '{ms_id}' not found.")
    return {"success": True, "message": f"Milestone '{ms_id}' deleted."}



# =====================================================================
# Deposit & Planning Tasks (P0 Item 3)
# =====================================================================

@router.post(
    "/{project_id}/deposit-paid",
    response_model=DepositPaidResponse,
    summary="Mark booking deposit paid and generate template planning tasks and payment stages",
    tags=["Wedding Plans"]
)
def mark_deposit_paid(
    project_id: str,
    db: Session = Depends(get_db)
):
    try:
        res = project_service.mark_deposit_paid(db=db, project_id=project_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{project_id}/tasks",
    response_model=List[PlanningTaskResponse],
    summary="List all planning tasks for a wedding project",
    tags=["Wedding Plans"]
)
def list_tasks(
    project_id: str,
    stage: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        tasks = project_service.list_tasks(
            db=db,
            project_id=project_id,
            stage=stage,
            category=category,
            assigned_to=assigned_to
        )
        return [PlanningTaskResponse.model_validate(t) for t in tasks]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{project_id}/tasks/{task_id}",
    response_model=PlanningTaskResponse,
    summary="Update task stage, owner, due date, or notes",
    tags=["Wedding Plans"]
)
def update_task(
    project_id: str,
    task_id: str,
    task_in: PlanningTaskUpdate,
    db: Session = Depends(get_db)
):
    task = project_service.update_task(db=db, project_id=project_id, task_id=task_id, task_in=task_in)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found.")
    return PlanningTaskResponse.model_validate(task)


@router.get(
    "/{project_id}/payment-stages",
    response_model=List[PaymentStageResponse],
    summary="List 3-stage payment milestones for the wedding",
    tags=["Wedding Plans"]
)
def list_payment_stages(
    project_id: str,
    db: Session = Depends(get_db)
):
    try:
        stages = project_service.list_payment_stages(db=db, project_id=project_id)
        return [PaymentStageResponse.model_validate(s) for s in stages]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{project_id}/payment-stages/{stage_id}",
    response_model=PaymentStageResponse,
    summary="Update payment milestone status or details",
    tags=["Wedding Plans"]
)
def update_payment_stage(
    project_id: str,
    stage_id: str,
    stage_in: PaymentStageUpdate,
    db: Session = Depends(get_db)
):
    stage = project_service.update_payment_stage(db=db, project_id=project_id, stage_id=stage_id, stage_in=stage_in)
    if not stage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Payment stage '{stage_id}' not found.")
    return PaymentStageResponse.model_validate(stage)


# =====================================================================
# Time Tracking & Profitability (P0 Item 4)
# =====================================================================

@router.post(
    "/{project_id}/time-entries",
    response_model=TeamTimeEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log employee working hours against wedding project",
    tags=["Team Time Tracking"]
)
def add_time_entry(
    project_id: str,
    entry_in: TeamTimeEntryCreate,
    db: Session = Depends(get_db)
):
    try:
        entry = project_service.add_time_entry(db=db, project_id=project_id, entry_in=entry_in)
        total_cost = Decimal(str(entry.hours)) * Decimal(str(entry.hourly_rate)) * Decimal("1.00")
        return TeamTimeEntryResponse(
            id=entry.id,
            project_id=entry.project_id,
            employee_name=entry.employee_name,
            role=entry.role,
            hours=entry.hours,
            hourly_rate=entry.hourly_rate,
            total_cost=total_cost,
            task_description=entry.task_description,
            entry_date=entry.entry_date,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{project_id}/time-entries",
    response_model=List[TeamTimeEntryResponse],
    summary="List team time tracking entries for project",
    tags=["Team Time Tracking"]
)
def list_time_entries(
    project_id: str,
    db: Session = Depends(get_db)
):
    try:
        entries = project_service.list_time_entries(db=db, project_id=project_id)
        res = []
        for entry in entries:
            total_cost = Decimal(str(entry.hours)) * Decimal(str(entry.hourly_rate)) * Decimal("1.00")
            res.append(TeamTimeEntryResponse(
                id=entry.id,
                project_id=entry.project_id,
                employee_name=entry.employee_name,
                role=entry.role,
                hours=entry.hours,
                hourly_rate=entry.hourly_rate,
                total_cost=total_cost,
                task_description=entry.task_description,
                entry_date=entry.entry_date,
                created_at=entry.created_at,
                updated_at=entry.updated_at,
            ))
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{project_id}/profitability",
    response_model=FounderProfitabilityResponse,
    summary="Founder gross profit analysis (client payments - vendor costs - team costs)",
    tags=["Founder Financials"]
)
def get_project_profitability(
    project_id: str,
    db: Session = Depends(get_db)
):
    try:
        prof = project_service.get_profitability(db=db, project_id=project_id)
        return FounderProfitabilityResponse.model_validate(prof)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =====================================================================
# P1 Item 5: Big Day Live Schedule & Check-in
# =====================================================================

@router.post(
    "/{project_id}/big-day/schedule",
    response_model=BigDayScheduleEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an event to the Big Day live schedule",
    tags=["Big Day Coordinator"]
)
def add_schedule_event(
    project_id: str,
    event_in: BigDayScheduleEventCreate,
    db: Session = Depends(get_db)
):
    try:
        ev = project_service.add_schedule_event(db=db, project_id=project_id, event_in=event_in)
        return BigDayScheduleEventResponse.model_validate(ev)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{project_id}/big-day/schedule",
    response_model=BigDayScheduleOverviewResponse,
    summary="Get Big Day live schedule with real-time late alerts and 30s polling support",
    tags=["Big Day Coordinator"]
)
def get_live_schedule(
    project_id: str,
    db: Session = Depends(get_db)
):
    try:
        return project_service.list_schedule_events(db=db, project_id=project_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{project_id}/big-day/events/{event_id}/check-in",
    response_model=BigDayScheduleEventResponse,
    summary="Check-in arriving vendor on the Big Day",
    tags=["Big Day Coordinator"]
)
def check_in_vendor_event(
    project_id: str,
    event_id: str,
    db: Session = Depends(get_db)
):
    try:
        ev = project_service.check_in_event(db=db, project_id=project_id, event_id=event_id)
        return BigDayScheduleEventResponse.model_validate(ev)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =====================================================================
# P1 Item 6: Extras & Final Settlement
# =====================================================================

@router.post(
    "/{project_id}/extras",
    response_model=WeddingExtraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an extra charge (extra plates, DJ overtime, etc.)",
    tags=["Settlement & Extras"]
)
def add_wedding_extra(
    project_id: str,
    extra_in: WeddingExtraCreate,
    db: Session = Depends(get_db)
):
    try:
        extra = project_service.add_extra(db=db, project_id=project_id, extra_in=extra_in)
        return WeddingExtraResponse.model_validate(extra)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{project_id}/extras",
    response_model=List[WeddingExtraResponse],
    summary="List all extras for wedding project",
    tags=["Settlement & Extras"]
)
def list_wedding_extras(
    project_id: str,
    db: Session = Depends(get_db)
):
    try:
        extras = project_service.list_extras(db=db, project_id=project_id)
        return [WeddingExtraResponse.model_validate(e) for e in extras]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{project_id}/settlement/payout",
    response_model=VendorPayoutResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create idempotent vendor settlement payout",
    tags=["Settlement & Extras"]
)
def create_vendor_payout(
    project_id: str,
    payout_in: VendorPayoutCreate,
    db: Session = Depends(get_db)
):
    try:
        payout = project_service.create_vendor_payout(db=db, project_id=project_id, payout_in=payout_in)
        v_name = payout.vendor.name if payout.vendor else "Vendor"
        return VendorPayoutResponse(
            id=payout.id,
            project_id=payout.project_id,
            vendor_id=payout.vendor_id,
            vendor_name=v_name,
            idempotency_key=payout.idempotency_key,
            agreed_amount=payout.agreed_amount,
            approved_extras=payout.approved_extras,
            advance_paid=payout.advance_paid,
            final_payout_amount=payout.final_payout_amount,
            status=payout.status,
            notes=payout.notes,
            created_at=payout.created_at,
            updated_at=payout.updated_at
        )
    except ValueError as e:
        if "Duplicate payout" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{project_id}/settlement",
    response_model=FinalSettlementResponse,
    summary="View final settlement statement (client invoice, payments, vendor payouts)",
    tags=["Settlement & Extras"]
)
def get_final_settlement(
    project_id: str,
    db: Session = Depends(get_db)
):
    try:
        settlement = project_service.get_final_settlement(db=db, project_id=project_id)
        return FinalSettlementResponse.model_validate(settlement)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =====================================================================
# P1 Item 7: Client Wedding Overview (Read-Only)
# =====================================================================

@router.get(
    "/{project_id}/client-overview",
    response_model=ClientWeddingOverviewResponse,
    summary="Client read-only portal wedding overview",
    tags=["Client Portal Overview"]
)
def get_client_wedding_overview(
    project_id: str,
    db: Session = Depends(get_db)
):
    try:
        overview = project_service.get_client_wedding_overview(db=db, project_id=project_id)
        return ClientWeddingOverviewResponse.model_validate(overview)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
