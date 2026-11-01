from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, Request, Response, status, Header
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.agreement import (
    ServiceAgreementResponse,
    ServiceAgreementListResponse,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    SignAgreementRequest,
    SignAgreementResponse
)
from app.services.agreement_service import agreement_service
from app.models.agreement import ServiceAgreement
from app.models.user import UserAccount

router = APIRouter()


def _format_agreement_response(agreement: ServiceAgreement) -> ServiceAgreementResponse:
    client = agreement.client
    client_name = f"{client.partner1_name} & {client.partner2_name}" if client else None
    client_email = client.email if client else None
    client_phone = client.phone if client else None

    return ServiceAgreementResponse(
        id=agreement.id,
        agreement_number=agreement.agreement_number,
        client_id=agreement.client_id,
        client_name=client_name,
        client_email=client_email,
        client_phone=client_phone,
        status=agreement.status,
        wedding_date=agreement.wedding_date,
        wedding_location=agreement.wedding_location,
        venue=agreement.venue,
        guest_count=agreement.guest_count,
        wedding_functions=agreement.wedding_functions,
        service_package=agreement.service_package,
        included_services=agreement.included_services,
        excluded_services=agreement.excluded_services,
        deliverables=agreement.deliverables,
        additional_terms=agreement.additional_terms,
        package_price=agreement.package_price,
        tax_percentage=agreement.tax_percentage,
        tax_amount=agreement.tax_amount,
        discount_amount=agreement.discount_amount,
        total_amount=agreement.total_amount,
        currency=agreement.currency,
        current_version_number=agreement.current_version_number,
        agreement_version=agreement.agreement_version,
        is_internally_approved=agreement.is_internally_approved,
        approved_by=agreement.approved_by,
        approved_at=agreement.approved_at,
        is_verified=agreement.is_verified,
        signed_at=agreement.signed_at,
        signed_by_name=agreement.signed_by_name,
        signed_by_email=agreement.signed_by_email,
        signed_pdf_url=f"/api/v1/agreements/{agreement.id}/pdf",
        signing_otp_verified=agreement.signing_otp_verified,
        consent_confirmed=agreement.consent_confirmed,
        created_at=agreement.created_at,
        updated_at=agreement.updated_at,
        milestones=agreement.milestones
    )


@router.get(
    "/agreements/my-agreement",
    response_model=ServiceAgreementResponse,
    summary="Get or instantiate the service agreement for currently authenticated client",
    tags=["Service Agreements"]
)
def get_my_agreement(
    client_id: Optional[str] = Query(None, description="Explicit Client ID if provided"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Returns the client's current service agreement. If one doesn't exist,
    it automatically instantiates a draft agreement populated from the client's DB profile.
    """
    # If client_id is not given, attempt lookup from token or fallback to the first active client
    target_client_id = client_id
    if not target_client_id and authorization:
        token = authorization.replace("Bearer ", "").strip()
        if token.startswith("trk_token_"):
            user_id = token.replace("trk_token_", "")
            user = db.query(UserAccount).filter(UserAccount.id == user_id).first()
            if user and user.client_id:
                target_client_id = user.client_id

    if not target_client_id:
        # Default to first client in system (e.g., TRK-2026-001)
        from app.models.client import Client
        first_client = db.query(Client).filter(Client.is_deleted == False).first()
        if first_client:
            target_client_id = first_client.id
        else:
            target_client_id = "TRK-2026-001"

    agreement = agreement_service.get_or_create_agreement_for_client(db, target_client_id)
    return _format_agreement_response(agreement)


@router.get(
    "/agreements/{agreement_id}",
    response_model=ServiceAgreementResponse,
    summary="Get service agreement by ID",
    tags=["Service Agreements"]
)
@router.get(
    "/agreements/client/{client_id}",
    response_model=ServiceAgreementResponse,
    summary="Get or instantiate service agreement for specific client ID",
    tags=["Service Agreements"]
)
def get_agreement_by_client_id(
    client_id: str = Path(..., description="Client ID"),
    db: Session = Depends(get_db)
):
    agreement = agreement_service.get_or_create_agreement_for_client(db, client_id)
    return _format_agreement_response(agreement)


def get_agreement_by_id(
    agreement_id: str = Path(..., description="Agreement ID"),
    db: Session = Depends(get_db)
):
    agreement = agreement_service.get_agreement(db, agreement_id)
    return _format_agreement_response(agreement)


@router.get(
    "/agreements/client/{client_id}",
    response_model=Optional[ServiceAgreementResponse],
    summary="Get service agreement for a specific client record (Staff view)",
    tags=["Service Agreements"]
)
def get_client_agreement(
    client_id: str = Path(..., description="Client ID"),
    db: Session = Depends(get_db)
):
    agreement = db.query(ServiceAgreement).filter(
        ServiceAgreement.client_id == client_id,
        ServiceAgreement.is_deleted == False
    ).order_by(ServiceAgreement.created_at.desc()).first()

    if not agreement:
        # Optionally create draft so staff can view/edit
        agreement = agreement_service.get_or_create_agreement_for_client(db, client_id)

    return _format_agreement_response(agreement)


@router.get(
    "/agreements",
    response_model=ServiceAgreementListResponse,
    summary="List all service agreements (Staff)",
    tags=["Service Agreements"]
)
def list_agreements(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    data = agreement_service.list_agreements(db, page, page_size, status)
    formatted_items = [_format_agreement_response(a) for a in data["items"]]
    return ServiceAgreementListResponse(
        total=data["total"],
        page=data["page"],
        page_size=data["page_size"],
        items=formatted_items
    )


@router.post(
    "/agreements/{agreement_id}/send-otp",
    response_model=SendOTPResponse,
    summary="Send signing verification code to client email",
    tags=["Service Agreements"]
)
def send_signing_otp(
    agreement_id: str = Path(...),
    db: Session = Depends(get_db)
):
    return agreement_service.send_signing_otp(db, agreement_id)


@router.post(
    "/agreements/{agreement_id}/verify-otp",
    response_model=VerifyOTPResponse,
    summary="Verify signing code",
    tags=["Service Agreements"]
)
def verify_signing_otp(
    agreement_id: str = Path(...),
    req: VerifyOTPRequest = ...,
    db: Session = Depends(get_db)
):
    return agreement_service.verify_signing_otp(db, agreement_id, req.otp)


@router.post(
    "/agreements/{agreement_id}/sign",
    response_model=SignAgreementResponse,
    summary="Digitally sign service agreement",
    tags=["Service Agreements"]
)
def sign_agreement(
    request: Request,
    agreement_id: str = Path(...),
    req: SignAgreementRequest = ...,
    db: Session = Depends(get_db)
):
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "Unknown Browser")
    return agreement_service.sign_agreement(
        db=db,
        agreement_id=agreement_id,
        req=req,
        ip_address=ip_address,
        user_agent=user_agent
    )


@router.get(
    "/agreements/{agreement_id}/pdf",
    summary="Download or view signed/draft Service Agreement PDF",
    tags=["Service Agreements"]
)
def download_agreement_pdf(
    agreement_id: str = Path(...),
    db: Session = Depends(get_db)
):
    pdf_bytes = agreement_service.get_signed_pdf_bytes(db, agreement_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=RoyalKnot_Agreement_{agreement_id}.pdf"
        }
    )

