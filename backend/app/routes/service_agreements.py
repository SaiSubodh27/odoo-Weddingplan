from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.session import get_db
from app.models.agreement import (
    ServiceAgreement,
    AgreementDocument,
    AgreementSignatureRequest,
    AgreementReview,
    WeddingBooking,
)
from app.models.client import Client
from app.schemas.agreement import (
    ServiceAgreementCreate,
    ServiceAgreementUpdate,
    ServiceAgreementResponse,
    ServiceAgreementListResponse,
    ServiceAgreementMetricsResponse,
    AgreementApproveRequest,
    AgreementReviewRequest,
    SendForSignatureRequest,
    SendForSignatureResponse,
    SigningStatusResponse,
    BookingConfirmRequest,
    BookingConfirmResponse,
)
from app.services.agreement_service import agreement_service
from app.services.zoho_polling_service import zoho_polling_service

router = APIRouter()


def _format_agreement_response(a: ServiceAgreement) -> ServiceAgreementResponse:
    client = a.client
    return ServiceAgreementResponse(
        id=a.id,
        agreement_number=a.agreement_number,
        client_id=a.client_id,
        status=a.status,
        signing_status=a.signing_status,
        wedding_date=a.wedding_date,
        wedding_location=a.wedding_location,
        venue=a.venue,
        guest_count=a.guest_count,
        wedding_functions=a.wedding_functions,
        service_package=a.service_package,
        included_services=a.included_services,
        excluded_services=a.excluded_services,
        deliverables=a.deliverables,
        additional_terms=a.additional_terms,
        package_price=a.package_price,
        tax_percentage=a.tax_percentage,
        tax_amount=a.tax_amount,
        discount_amount=a.discount_amount,
        total_amount=a.total_amount,
        currency=a.currency,
        current_version_number=a.current_version_number,
        is_internally_approved=a.is_internally_approved,
        approved_by=a.approved_by,
        approved_at=a.approved_at,
        is_verified=a.is_verified,
        verified_by=a.verified_by,
        verified_at=a.verified_at,
        verification_notes=a.verification_notes,
        agreement_version=getattr(a, 'agreement_version', 'v1.0') or 'v1.0',
        signing_otp_verified=getattr(a, 'signing_otp_verified', False) or False,
        consent_confirmed=getattr(a, 'consent_confirmed', False) or False,
        created_by=a.created_by,
        created_at=a.created_at,
        updated_at=a.updated_at,
        last_status_checked_at=a.last_status_checked_at,
        milestones=a.milestones,
        client_partner1_name=client.partner1_name if client else None,
        client_partner2_name=client.partner2_name if client else None,
        client_email=client.email if client else None,
        client_phone=client.phone if client else None,
    )


@router.get(
    "/metrics",
    response_model=ServiceAgreementMetricsResponse,
    summary="Get operational metrics for Service Agreements dashboard",
    tags=["Service Agreements"]
)
def get_agreement_metrics(db: Session = Depends(get_db)):
    total = db.query(ServiceAgreement).filter(ServiceAgreement.is_deleted == False).count()
    drafts = db.query(ServiceAgreement).filter(ServiceAgreement.is_deleted == False, ServiceAgreement.status == "DRAFT").count()
    pending_approval = db.query(ServiceAgreement).filter(ServiceAgreement.is_deleted == False, ServiceAgreement.is_internally_approved == False).count()
    signing_pending = db.query(ServiceAgreement).filter(ServiceAgreement.is_deleted == False, ServiceAgreement.status == "SIGNING_PENDING").count()
    signed = db.query(ServiceAgreement).filter(ServiceAgreement.is_deleted == False, ServiceAgreement.signing_status == "COMPLETED").count()
    awaiting_verification = db.query(ServiceAgreement).filter(ServiceAgreement.is_deleted == False, ServiceAgreement.status == "UNDER_VERIFICATION").count()
    verified = db.query(ServiceAgreement).filter(ServiceAgreement.is_deleted == False, ServiceAgreement.is_verified == True).count()
    confirmed = db.query(WeddingBooking).count()

    return ServiceAgreementMetricsResponse(
        total_agreements=total,
        draft_agreements=drafts,
        pending_approval=pending_approval,
        signing_pending=signing_pending,
        signed_agreements=signed,
        awaiting_verification=awaiting_verification,
        verified_agreements=verified,
        confirmed_bookings=confirmed
    )


@router.get(
    "",
    response_model=ServiceAgreementListResponse,
    summary="List all service agreements with search, filter, and pagination",
    tags=["Service Agreements"]
)
def list_agreements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search agreement number or client"),
    status: Optional[str] = Query(None, description="Filter by agreement status"),
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    db: Session = Depends(get_db)
):
    query = db.query(ServiceAgreement).filter(ServiceAgreement.is_deleted == False)

    clean_client_id = client_id if isinstance(client_id, str) else None
    clean_status = status if isinstance(status, str) else None
    clean_search = search if isinstance(search, str) else None
    clean_page = page if isinstance(page, int) else 1
    clean_page_size = page_size if isinstance(page_size, int) else 20

    if clean_client_id:
        query = query.filter(ServiceAgreement.client_id == clean_client_id)
    if clean_status and clean_status != "All":
        query = query.filter(ServiceAgreement.status == clean_status)
    if clean_search:
        search_filter = f"%{clean_search}%"
        query = query.join(Client).filter(
            (ServiceAgreement.agreement_number.ilike(search_filter)) |
            (Client.partner1_name.ilike(search_filter)) |
            (Client.partner2_name.ilike(search_filter)) |
            (Client.email.ilike(search_filter))
        )

    total = query.count()
    items = query.order_by(ServiceAgreement.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return ServiceAgreementListResponse(
        items=[_format_agreement_response(a) for a in items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post(
    "",
    response_model=ServiceAgreementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new service agreement for a registered client",
    tags=["Service Agreements"]
)
def create_agreement(
    req: ServiceAgreementCreate,
    db: Session = Depends(get_db)
):
    agreement = agreement_service.create_agreement(db=db, req=req)
    return _format_agreement_response(agreement)


@router.get(
    "/{id}",
    response_model=ServiceAgreementResponse,
    summary="Get detailed service agreement dossier",
    tags=["Service Agreements"]
)
def get_agreement(id: str, db: Session = Depends(get_db)):
    agreement = db.query(ServiceAgreement).filter(ServiceAgreement.id == id, ServiceAgreement.is_deleted == False).first()
    if not agreement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service Agreement '{id}' not found.")
    return _format_agreement_response(agreement)


@router.post(
    "/{id}/generate-pdf",
    summary="Generate professional, printable Service Agreement PDF",
    tags=["Service Agreements"]
)
def generate_agreement_pdf(id: str, db: Session = Depends(get_db)):
    doc = agreement_service.generate_agreement_pdf(db=db, agreement_id=id)
    return {
        "success": True,
        "message": "Service agreement PDF generated successfully.",
        "document_id": doc.id,
        "filename": doc.original_filename,
        "file_size": doc.file_size,
        "sha256": doc.file_hash_sha256
    }


@router.get(
    "/{id}/download-pdf",
    summary="Download or view generated Service Agreement PDF",
    tags=["Service Agreements"]
)
def download_agreement_pdf(
    id: str,
    inline: bool = Query(True, description="Inline browser preview or attachment download"),
    db: Session = Depends(get_db)
):
    agreement = db.query(ServiceAgreement).filter(ServiceAgreement.id == id).first()
    if not agreement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service agreement not found.")

    doc = db.query(AgreementDocument).filter(
        AgreementDocument.agreement_id == agreement.id
    ).order_by(AgreementDocument.created_at.desc()).first()

    if not doc:
        doc = agreement_service.generate_agreement_pdf(db, agreement.id)

    content_disposition = "inline" if inline else "attachment"
    return FileResponse(
        path=doc.file_path,
        filename=doc.original_filename,
        media_type=doc.mime_type,
        content_disposition_type=content_disposition
    )


@router.post(
    "/{id}/approve",
    response_model=ServiceAgreementResponse,
    summary="Internally approve service agreement before signing invitation",
    tags=["Service Agreements"]
)
def approve_agreement(
    id: str,
    req: AgreementApproveRequest,
    db: Session = Depends(get_db)
):
    agreement = agreement_service.approve_agreement(db=db, agreement_id=id, req=req)
    return _format_agreement_response(agreement)


@router.post(
    "/{id}/send-for-signature",
    response_model=SendForSignatureResponse,
    summary="Dispatch approved agreement to electronic signature provider (Zoho Sign)",
    tags=["Electronic Signature"]
)
def send_for_signature(
    id: str,
    req: Optional[SendForSignatureRequest] = None,
    db: Session = Depends(get_db)
):
    res = agreement_service.send_for_signature(db=db, agreement_id=id, req_body=req)
    return SendForSignatureResponse(**res)


@router.get(
    "/{id}/signature-status",
    response_model=SigningStatusResponse,
    summary="Retrieve current electronic signature status from backend and provider",
    tags=["Electronic Signature"]
)
def get_signature_status(id: str, db: Session = Depends(get_db)):
    agreement = db.query(ServiceAgreement).filter(ServiceAgreement.id == id).first()
    if not agreement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service agreement not found.")

    sig_req = db.query(AgreementSignatureRequest).filter(
        AgreementSignatureRequest.agreement_id == agreement.id
    ).order_by(AgreementSignatureRequest.created_at.desc()).first()

    has_signed_pdf = db.query(AgreementDocument).filter(
        AgreementDocument.agreement_id == agreement.id,
        AgreementDocument.document_type == "signed_agreement_pdf"
    ).first() is not None

    has_audit_cert = db.query(AgreementDocument).filter(
        AgreementDocument.agreement_id == agreement.id,
        AgreementDocument.document_type == "signature_audit_trail"
    ).first() is not None

    return SigningStatusResponse(
        agreement_id=agreement.id,
        agreement_number=agreement.agreement_number,
        version_number=agreement.current_version_number,
        signing_status=agreement.signing_status,
        agreement_status=agreement.status,
        provider=sig_req.provider if sig_req else "Zoho Sign",
        environment=sig_req.environment if sig_req else "sandbox",
        provider_request_id=sig_req.provider_request_id if sig_req else None,
        provider_document_id=sig_req.provider_document_id if sig_req else None,
        leegality_document_id=sig_req.leegality_document_id if sig_req else None,
        signing_url=sig_req.signing_url if sig_req else None,
        signer_name=sig_req.signer_name if sig_req else None,
        signer_email=sig_req.signer_email if sig_req else None,
        completed_at=sig_req.completed_at if sig_req else None,
        last_status_checked_at=sig_req.last_status_checked_at if sig_req else agreement.last_status_checked_at,
        next_status_check_at=sig_req.next_status_check_at if sig_req else None,
        polling_attempt_count=sig_req.polling_attempt_count if sig_req else 0,
        last_polling_error=sig_req.last_polling_error if sig_req else None,
        has_signed_pdf=has_signed_pdf,
        has_audit_certificate=has_audit_cert,
        raw_provider_status=sig_req.raw_response if sig_req else None
    )


@router.post(
    "/{id}/refresh-status",
    response_model=SigningStatusResponse,
    summary="Poll and synchronize signature status directly from Zoho Sign API",
    tags=["Electronic Signature"]
)
def refresh_signature_status(id: str, db: Session = Depends(get_db)):
    """
    Manually triggers a verified status check against Zoho Sign.
    If complete, downloads the executed PDF & audit trail certificate, and advances the agreement.
    """
    zoho_polling_service.poll_agreement_status(db=db, agreement_id=id, is_manual=True)
    return get_signature_status(id=id, db=db)


@router.post(
    "/{id}/verify",
    response_model=ServiceAgreementResponse,
    summary="Employee verification and sign-off on executed agreement",
    tags=["Verification & Booking"]
)
def verify_agreement(
    id: str,
    req: AgreementReviewRequest,
    db: Session = Depends(get_db)
):
    agreement = agreement_service.review_agreement(db=db, agreement_id=id, req=req)
    return _format_agreement_response(agreement)


@router.post(
    "/{id}/confirm-booking",
    response_model=BookingConfirmResponse,
    summary="Officially confirm wedding booking and handoff to Phase 3",
    tags=["Verification & Booking"]
)
def confirm_booking(
    id: str,
    req: BookingConfirmRequest,
    db: Session = Depends(get_db)
):
    bk = agreement_service.confirm_booking(db=db, agreement_id=id, req=req)
    return BookingConfirmResponse(
        success=True,
        message=f"Wedding booking '{bk.booking_reference}' confirmed successfully! Dossier ready for Phase 3 Project Handoff.",
        booking_id=bk.id,
        booking_reference=bk.booking_reference,
        client_id=bk.client_id,
        agreement_id=bk.agreement_id,
        confirmed_version_number=bk.confirmed_version_number,
        couple_title=bk.couple_title,
        wedding_date=bk.wedding_date,
        wedding_location=bk.wedding_location,
        venue=bk.venue,
        confirmed_total_amount=bk.confirmed_total_amount,
        advance_amount_agreed=bk.advance_amount_agreed,
        confirmed_by=bk.confirmed_by,
        confirmed_at=bk.confirmed_at,
        phase3_handoff_ready=bk.phase3_handoff_ready
    )

