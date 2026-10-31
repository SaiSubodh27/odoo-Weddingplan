from typing import Dict, Any
from fastapi import APIRouter, Depends, Request, status, HTTPException
from sqlalchemy.orm import Session
import logging

from app.database.session import get_db
from app.services.agreement_service import agreement_service

logger = logging.getLogger("royal_knot.webhooks")
router = APIRouter()


@router.post(
    "/leegality/success",
    status_code=status.HTTP_200_OK,
    summary="Official Leegality Webhook Callback (Signing Completed)",
    tags=["Leegality Webhook"]
)
async def leegality_webhook_success(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receives official Leegality electronic signing success notification.
    Verifies HMAC-SHA1 MAC signature with private salt, retrieves executed PDF,
    and updates internal agreement state safely and idempotently.
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
    summary="Official Leegality Webhook Callback (Signing Expired/Declined/Failed)",
    tags=["Leegality Webhook"]
)
async def leegality_webhook_failure(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receives Leegality electronic signing failure, rejection, or expiry notification.
    """
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Malformed JSON in Leegality failure webhook: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload.")

    logger.warning(f"Received Leegality failure webhook: {payload}")
    result = agreement_service.process_leegality_webhook(db=db, payload=payload, is_success=False)
    return result

