import json
from typing import Dict, Any
from fastapi import APIRouter, Depends, Request, status, HTTPException
from sqlalchemy.orm import Session
import logging

from app.database.session import get_db
from app.services.agreement_service import agreement_service

logger = logging.getLogger("royal_knot.webhooks")
router = APIRouter()


@router.post(
    "/zoho/callback",
    status_code=status.HTTP_200_OK,
    summary="Official Zoho Sign Webhook Callback",
    tags=["Zoho Sign Webhook"]
)
@router.post(
    "/zoho/success",
    status_code=status.HTTP_200_OK,
    summary="Official Zoho Sign Webhook Callback (Alias)",
    tags=["Zoho Sign Webhook"]
)
async def zoho_webhook_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receives official Zoho Sign electronic signing webhook notifications.
    Supports request_status updates: RequestCompleted, RequestSent, RequestViewed, RequestDeclined, RequestExpired.
    Safely extracts payload, validates request authenticity, and updates agreement status idempotently.
    """
    payload: Dict[str, Any] = {}
    content_type = request.headers.get("content-type", "")

    try:
        if "application/json" in content_type:
            payload = await request.json()
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form_data = await request.form()
            if "notifications" in form_data:
                raw_notif = form_data["notifications"]
                payload = {"notifications": json.loads(raw_notif) if isinstance(raw_notif, str) else raw_notif}
            else:
                payload = dict(form_data)
        else:
            # Fallback to try json parsing then text
            body = await request.body()
            if body:
                try:
                    payload = json.loads(body.decode("utf-8"))
                except Exception:
                    payload = {}
    except Exception as e:
        logger.error(f"Malformed payload in Zoho Sign webhook: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook payload format.")

    headers = dict(request.headers)
    logger.info(f"Received Zoho Sign webhook. Processing payload keys: {list(payload.keys())}")
    result = agreement_service.process_zoho_webhook(db=db, payload=payload, headers=headers)
    return result


@router.post(
    "/leegality/success",
    status_code=status.HTTP_200_OK,
    summary="Historical Leegality Webhook Callback (Signing Completed)",
    tags=["Historical Leegality Webhook"]
)
async def leegality_webhook_success(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receives historical Leegality electronic signing success notification.
    Preserved for backward compatibility and historical webhook replays.
    """
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Malformed JSON in Leegality success webhook: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload.")

    logger.info(f"Received Leegality success webhook for document: {payload.get('documentId')}")
    result = agreement_service.process_leegality_webhook(db=db, payload=payload, is_success=True)
    return result


@router.post(
    "/leegality/failure",
    status_code=status.HTTP_200_OK,
    summary="Historical Leegality Webhook Callback (Signing Expired/Declined/Failed)",
    tags=["Historical Leegality Webhook"]
)
async def leegality_webhook_failure(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receives historical Leegality electronic signing failure, rejection, or expiry notification.
    Preserved for backward compatibility.
    """
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Malformed JSON in Leegality failure webhook: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload.")

    logger.warning(f"Received Leegality failure webhook: {payload}")
    result = agreement_service.process_leegality_webhook(db=db, payload=payload, is_success=False)
    return result


