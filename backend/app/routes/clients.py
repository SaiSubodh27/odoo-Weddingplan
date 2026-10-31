from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.session import get_db
from app.schemas.client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientListResponse,
    HealthResponse,
)
from app.services.client_service import client_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System Health"])
def health_check(db: Session = Depends(get_db)):
    """Verifies API status and live PostgreSQL connectivity."""
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception as e:
        db_connected = False

    return HealthResponse(
        service="The Royal Knot — Backend API Service",
        status="operational" if db_connected else "degraded",
        database_connected=db_connected,
        operating_regions=["Jaipur", "Udaipur"],
        version="1.0.0"
    )


@router.post(
    "/clients",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new wedding client dossier",
    tags=["Client Registration"]
)
def register_client(
    client_in: ClientCreate,
    db: Session = Depends(get_db)
):
    """
    Creates a new client dossier in the PostgreSQL database.
    Validates couple details, destination wedding parameters, and contact info.
    """
    try:
        new_client = client_service.create_client(db=db, client_in=client_in)
        return new_client
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to complete client registration: {str(e)}"
        )


@router.get(
    "/clients",
    response_model=ClientListResponse,
    summary="List client dossiers with filtering & search",
    tags=["Client Directory"]
)
def list_clients(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search couple name, email, phone, venue, or reference ID"),
    status: Optional[str] = Query(None, description="Filter by registration status"),
    enquiry_source: Optional[str] = Query(None, description="Filter by enquiry source (Email/Phone/Website)"),
    db: Session = Depends(get_db)
):
    """
    Returns registered client dossiers with pagination, searching, and filtering.
    """
    items, total = client_service.list_clients(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        enquiry_source=enquiry_source
    )

    return ClientListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.get(
    "/clients/{client_id}",
    response_model=ClientResponse,
    summary="Retrieve a specific client dossier",
    tags=["Client Details"]
)
def get_client(
    client_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves full client registration dossier by unique reference ID.
    """
    client = client_service.get_client(db=db, client_id=client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client dossier '{client_id}' not found."
        )
    return client


@router.put(
    "/clients/{client_id}",
    response_model=ClientResponse,
    summary="Update client dossier information",
    tags=["Client Management"]
)
def update_client(
    client_id: str,
    client_in: ClientUpdate,
    db: Session = Depends(get_db)
):
    """
    Updates client details or registration status.
    """
    updated_client = client_service.update_client(
        db=db,
        client_id=client_id,
        client_in=client_in
    )
    if not updated_client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client dossier '{client_id}' not found."
        )
    return updated_client


@router.delete(
    "/clients/{client_id}",
    status_code=status.HTTP_200_OK,
    summary="Soft-delete a client dossier",
    tags=["Client Management"]
)
def soft_delete_client(
    client_id: str,
    db: Session = Depends(get_db)
):
    """
    Performs a safe soft-delete of the client record by setting is_deleted=True.
    Physical records remain in the database for audit integrity.
    """
    success = client_service.soft_delete_client(db=db, client_id=client_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client dossier '{client_id}' not found."
        )
    return {
        "message": f"Client dossier '{client_id}' has been archived (soft-deleted).",
        "client_id": client_id,
        "is_deleted": True
    }

