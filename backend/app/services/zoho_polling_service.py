import os
import time
import logging
import uuid
import hashlib
import threading
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Set
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import SessionLocal
from app.models.agreement import (
    ServiceAgreement,
    AgreementSignatureRequest,
    AgreementDocument,
)
from app.services.agreement_service import agreement_service
from app.services.zoho_sign_service import (
    zoho_sign_client,
    ZohoRateLimitError,
    ZohoNotFoundError,
    ZohoAuthenticationError,
)

logger = logging.getLogger("royal_knot.zoho_polling")


class ZohoSignPollingService:
    """
    Automatic and on-demand polling manager for Zoho Sign requests.
    Enables local development, status synchronization, signed document retrieval,
    and completion certificate management without requiring public HTTPS webhooks or ngrok.
    """

    def __init__(self):
        self._active_polls: Set[str] = set()
        self._lock = threading.Lock()
        self._is_running = False

    def is_polling_active(self, request_id: str) -> bool:
        with self._lock:
            return request_id in self._active_polls

    def poll_agreement_status(
        self,
        db: Session,
        agreement_id: str,
        is_manual: bool = False
    ) -> Dict[str, Any]:
        """
        Polls the official Zoho Sign API for a specific agreement's latest electronic signature status.
        Transitions the agreement upon confirmed completion, retrieves executed PDF and audit certificate,
        and records timestamps and telemetry.
        """
        agreement = db.query(ServiceAgreement).filter(ServiceAgreement.id == agreement_id).first()
        if not agreement:
            raise ValueError(f"Service agreement '{agreement_id}' not found.")

        sig_req = (
            db.query(AgreementSignatureRequest)
            .filter(AgreementSignatureRequest.agreement_id == agreement.id)
            .order_by(AgreementSignatureRequest.created_at.desc())
            .first()
        )
        if not sig_req:
            return {
                "agreement_id": agreement.id,
                "status": agreement.signing_status,
                "message": "No signature request found for this agreement."
            }

        req_id = sig_req.provider_request_id or sig_req.leegality_document_id
        if not req_id:
            return {
                "agreement_id": agreement.id,
                "status": agreement.signing_status,
                "message": "No provider request identifier registered."
            }

        # Concurrency protection: prevent overlapping checks for the same request
        with self._lock:
            if req_id in self._active_polls:
                logger.info(f"Polling already in progress for request {req_id}. Skipping overlapping poll.")
                return {
                    "agreement_id": agreement.id,
                    "status": agreement.signing_status,
                    "message": "Status check is currently in progress."
                }
            self._active_polls.add(req_id)

        # Terminal state protection: avoid polling finalized requests
        if agreement.status in ("UNDER_VERIFICATION", "VERIFIED", "BOOKING_CONFIRMED") and sig_req.status == "SIGNED":
            if not is_manual:
                with self._lock:
                    self._active_polls.discard(req_id)
                return {
                    "agreement_id": agreement.id,
                    "status": "COMPLETED",
                    "message": "Agreement signing is already verified and completed."
                }

        now = datetime.now(timezone.utc)
        try:
            # Query official Zoho Sign API v1
            status_info = zoho_sign_client.get_signing_status(req_id)
            provider_status = status_info.get("status", "SENT").upper()
            is_completed = status_info.get("is_completed", False)

            sig_req.last_status_checked_at = now
            agreement.last_status_checked_at = now
            sig_req.last_polling_error = None

            if is_completed:
                logger.info(f"Zoho Sign confirmed completion for request {req_id}. Transitioning agreement {agreement.agreement_number}...")
                sig_req.status = "SIGNED"
                sig_req.completed_at = now
                sig_req.provider_completed_at = now
                sig_req.next_status_check_at = None
                agreement.signing_status = "COMPLETED"

                # 1. Download and store executed signed PDF if not already present
                existing_signed_pdf = db.query(AgreementDocument).filter(
                    AgreementDocument.agreement_id == agreement.id,
                    AgreementDocument.document_type == "signed_agreement_pdf"
                ).first()

                if not existing_signed_pdf:
                    try:
                        signed_bytes = zoho_sign_client.retrieve_signed_document(req_id)
                        signed_dir = os.path.join(settings.UPLOAD_DIR, "agreements")
                        os.makedirs(signed_dir, exist_ok=True)
                        signed_filename = f"{agreement.agreement_number}_v{sig_req.version_number}_ZOHO_SIGNED.pdf"
                        signed_path = os.path.join(signed_dir, signed_filename)
                        with open(signed_path, "wb") as f:
                            f.write(signed_bytes)

                        doc_record = AgreementDocument(
                            id=f"DOC-{uuid.uuid4().hex[:10].upper()}",
                            agreement_id=agreement.id,
                            version_number=sig_req.version_number,
                            document_type="signed_agreement_pdf",
                            original_filename=signed_filename,
                            stored_filename=signed_filename,
                            file_path=signed_path,
                            file_size=len(signed_bytes),
                            file_hash_sha256=hashlib.sha256(signed_bytes).hexdigest(),
                            mime_type="application/pdf",
                            source="Zoho Sign Polling"
                        )
                        db.add(doc_record)
                        logger.info(f"Stored executed signed PDF for agreement {agreement.agreement_number}.")
                    except Exception as e:
                        logger.error(f"Failed to retrieve/store executed PDF from Zoho Sign: {e}")
                        sig_req.last_polling_error = f"Executed PDF download deferred: {e}"

                # 2. Download and store completion certificate / audit trail if not already present
                existing_cert = db.query(AgreementDocument).filter(
                    AgreementDocument.agreement_id == agreement.id,
                    AgreementDocument.document_type == "signature_audit_trail"
                ).first()

                if not existing_cert:
                    try:
                        cert_bytes = zoho_sign_client.retrieve_audit_trail(req_id)
                        if cert_bytes:
                            signed_dir = os.path.join(settings.UPLOAD_DIR, "agreements")
                            os.makedirs(signed_dir, exist_ok=True)
                            cert_filename = f"{agreement.agreement_number}_v{sig_req.version_number}_ZOHO_AUDIT_TRAIL.pdf"
                            cert_path = os.path.join(signed_dir, cert_filename)
                            with open(cert_path, "wb") as f:
                                f.write(cert_bytes)

                            cert_doc = AgreementDocument(
                                id=f"DOC-{uuid.uuid4().hex[:10].upper()}",
                                agreement_id=agreement.id,
                                version_number=sig_req.version_number,
                                document_type="signature_audit_trail",
                                original_filename=cert_filename,
                                stored_filename=cert_filename,
                                file_path=cert_path,
                                file_size=len(cert_bytes),
                                file_hash_sha256=hashlib.sha256(cert_bytes).hexdigest(),
                                mime_type="application/pdf",
                                source="Zoho Sign Audit Trail Polling"
                            )
                            db.add(cert_doc)
                            logger.info(f"Stored completion certificate for agreement {agreement.agreement_number}.")
                    except Exception as e:
                        logger.warning(f"Failed to retrieve completion certificate: {e}")

                # Transition to UNDER_VERIFICATION only when signing is confirmed
                if agreement.status != "UNDER_VERIFICATION" and agreement.status != "BOOKING_CONFIRMED":
                    agreement_service._record_status_history(
                        db, agreement, "UNDER_VERIFICATION", "Zoho Sign Polling",
                        "Client electronic signature confirmed completed via Zoho Sign API."
                    )

            elif provider_status in ("DECLINED", "REJECTED"):
                sig_req.status = "DECLINED"
                sig_req.next_status_check_at = None
                agreement.signing_status = "DECLINED"
                agreement_service._record_status_history(
                    db, agreement, "NEEDS_CORRECTION", "Zoho Sign Polling",
                    "Client declined the electronic signature invitation."
                )

            elif provider_status in ("EXPIRED", "CANCELLED", "RECALLED"):
                sig_req.status = provider_status
                sig_req.next_status_check_at = None
                agreement.signing_status = provider_status
                agreement_service._record_status_history(
                    db, agreement, "EXPIRED" if provider_status == "EXPIRED" else "CANCELLED", "Zoho Sign Polling",
                    f"Signature request {provider_status.lower()} on Zoho Sign."
                )

            else:
                # Active in-flight state (SENT, VIEWED, IN_PROGRESS)
                agreement.signing_status = provider_status
                sig_req.status = "SENT"
                sig_req.polling_attempt_count += 1
                sig_req.next_status_check_at = now + timedelta(seconds=settings.ZOHO_SIGN_POLLING_INTERVAL_SECONDS)

            db.commit()
            return {
                "agreement_id": agreement.id,
                "provider_request_id": req_id,
                "signing_status": agreement.signing_status,
                "agreement_status": agreement.status,
                "is_completed": is_completed,
                "last_status_checked_at": now.isoformat(),
                "next_status_check_at": sig_req.next_status_check_at.isoformat() if sig_req.next_status_check_at else None
            }

        except ZohoRateLimitError as e:
            logger.warning(f"Rate limited while polling request {req_id}: {e}")
            sig_req.last_status_checked_at = now
            sig_req.last_polling_error = f"Rate limited. Retry after {e.retry_after}s."
            sig_req.next_status_check_at = now + timedelta(seconds=e.retry_after)
            db.commit()
            return {
                "agreement_id": agreement.id,
                "signing_status": agreement.signing_status,
                "error": "rate_limited",
                "retry_after": e.retry_after
            }

        except Exception as e:
            logger.error(f"Error while polling request {req_id}: {e}")
            sig_req.last_status_checked_at = now
            sig_req.polling_attempt_count += 1
            # Exponential backoff calculation
            backoff_sec = min(settings.ZOHO_SIGN_POLLING_INTERVAL_SECONDS * (2 ** min(sig_req.polling_attempt_count, 5)), 3600)
            sig_req.next_status_check_at = now + timedelta(seconds=backoff_sec)
            sig_req.last_polling_error = str(e)
            db.commit()
            return {
                "agreement_id": agreement.id,
                "signing_status": agreement.signing_status,
                "error": "polling_failed",
                "details": str(e)
            }

        finally:
            with self._lock:
                self._active_polls.discard(req_id)

    def poll_all_pending_agreements(self, db: Session) -> Dict[str, Any]:
        """
        Scans and polls all active agreements currently awaiting signature.
        Respects next_status_check_at and stops polling terminated agreements.
        """
        now = datetime.now(timezone.utc)
        pending_agreements = (
            db.query(ServiceAgreement)
            .join(AgreementSignatureRequest, AgreementSignatureRequest.agreement_id == ServiceAgreement.id)
            .filter(
                ServiceAgreement.status == "SIGNING_PENDING",
                ServiceAgreement.signing_status.in_(["SENT", "IN_PROGRESS", "VIEWED", "NOT_CREATED"]),
                AgreementSignatureRequest.provider == "Zoho Sign",
                AgreementSignatureRequest.status.notin_(["SIGNED", "COMPLETED", "DECLINED", "EXPIRED", "CANCELLED"]),
                (AgreementSignatureRequest.next_status_check_at.is_(None) | (AgreementSignatureRequest.next_status_check_at <= now))
            )
            .all()
        )

        checked = 0
        completed = 0
        errors = 0

        for ag in pending_agreements:
            try:
                res = self.poll_agreement_status(db, ag.id, is_manual=False)
                checked += 1
                if res.get("is_completed"):
                    completed += 1
                elif "error" in res:
                    errors += 1
            except Exception as e:
                logger.error(f"Failed to poll agreement {ag.id}: {e}")
                errors += 1

        return {
            "pending_count": len(pending_agreements),
            "checked": checked,
            "completed": completed,
            "errors": errors
        }

    async def run_polling_background_loop(self):
        """
        Non-blocking async background task integrated into the FastAPI application lifespan.
        Executes periodic polling checks across all active signing agreements.
        """
        logger.info("Initializing Zoho Sign background polling loop...")
        while True:
            try:
                await asyncio.sleep(settings.ZOHO_SIGN_POLLING_INTERVAL_SECONDS)
                if settings.ZOHO_SIGN_POLLING_ENABLED:
                    db = SessionLocal()
                    try:
                        self.poll_all_pending_agreements(db)
                    except Exception as e:
                        logger.error(f"Error in Zoho Sign polling background loop: {e}")
                    finally:
                        db.close()
            except asyncio.CancelledError:
                logger.info("Zoho Sign background polling loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Unexpected error in Zoho Sign polling runner: {e}")


# Singleton instance
zoho_polling_service = ZohoSignPollingService()
