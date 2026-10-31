from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.registration import (
    ClientRegistrationSubmitRequest,
    RegistrationVerifyResponse,
)
from app.services.registration_service import registration_service

router = APIRouter()


@router.get(
    "/verify",
    response_model=RegistrationVerifyResponse,
    summary="Verify registration token from client invitation email",
    tags=["Client Online Registration"]
)
def verify_registration_token(
    token: str = Query(..., description="Secure registration token"),
    db: Session = Depends(get_db)
):
    """
    Public endpoint: Validates the token and returns pre-filled enquiry parameters
    so the client can complete their registration form.
    """
    return registration_service.verify_token(db=db, token=token)


@router.post(
    "/submit",
    status_code=status.HTTP_201_CREATED,
    summary="Submit client wedding registration form online",
    tags=["Client Online Registration"]
)
def submit_registration_form(
    req: ClientRegistrationSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    Public endpoint: Receives client-submitted wedding parameters, saves them to PostgreSQL,
    associates the submission with the original enquiry, and updates status for employee review.
    """
    return registration_service.submit_registration(db=db, req=req)
