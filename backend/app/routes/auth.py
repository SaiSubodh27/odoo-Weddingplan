from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.user import (
    TokenVerifyResponse,
    AccountActivateRequest,
    AccountActivateResponse,
    UserLoginRequest,
    UserLoginResponse,
    WebsiteClientRegisterRequest,
)
from app.services.auth_service import auth_service

router = APIRouter()


@router.get(
    "/verify-token",
    response_model=TokenVerifyResponse,
    summary="Validate client activation token",
    tags=["Account Activation"]
)
def verify_activation_token(
    token: str = Query(..., description="Activation token from email link"),
    db: Session = Depends(get_db)
):
    """
    Checks if an activation link is valid, unexpired, and unused before rendering password setup.
    """
    return auth_service.verify_activation_token(db=db, raw_token=token)


@router.post(
    "/activate",
    response_model=AccountActivateResponse,
    status_code=status.HTTP_200_OK,
    summary="Set password and activate client account",
    tags=["Account Activation"]
)
def activate_account(
    req: AccountActivateRequest,
    db: Session = Depends(get_db)
):
    """
    Validates token, securely hashes the password with Argon2, activates the account,
    and invalidates the one-time token.
    """
    return auth_service.activate_account(db=db, req=req)


@router.post(
    "/login",
    response_model=UserLoginResponse,
    summary="User login for agency staff and activated clients",
    tags=["Authentication"]
)
def login_user(
    req: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Verifies user credentials against Argon2 password hash.
    Rejects pending or inactive accounts with clear status messages.
    """
    return auth_service.login_user(db=db, req=req)


@router.post(
    "/register-website",
    status_code=status.HTTP_201_CREATED,
    summary="Public client website registration & account creation",
    tags=["Website Registration"]
)
def register_website_client(
    req: WebsiteClientRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Client-side public registration:
    Creates an Enquiry (source='Website'), ClientRegistration dossier, and active UserAccount,
    then automatically dispatches a luxury confirmation email to the client.
    """
    return auth_service.website_register_client(db=db, req=req)


@router.get(
    "/client-dossier",
    summary="Get authenticated client's registered celebration dossier",
    tags=["Client Portal"]
)
def get_client_dossier(
    email: str = Query(..., description="Client email address"),
    db: Session = Depends(get_db)
):
    """
    Returns the client's celebration dossier, wedding parameters, events, and review status.
    """
    return auth_service.get_client_dossier(db=db, email=email)
