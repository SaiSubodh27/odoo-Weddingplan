from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.project_service import project_service
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
    projects, total = project_service.list_projects(
        db=db,
        search=search,
        status=status,
        page=page,
        page_size=page_size
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

