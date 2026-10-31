import hmac
import hashlib
import base64
import logging
import uuid
from typing import Dict, Any, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger("royal_knot.leegality")


class LeegalityClient:
    """
    Official API Client for Leegality v2.1 eSigning Workflow.
    Documentation: https://leegality.apidocumentation.com/
    Sandbox Base URL: https://sandbox.leegality.com/api/v2.1
    Production Base URL: https://app1.leegality.com/api/v2.1
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        private_salt: Optional[str] = None,
        timeout: int = 30,
        env: Optional[str] = None
    ):
        self.base_url = (base_url or settings.LEEGALITY_BASE_URL).rstrip("/")
        self.auth_token = auth_token or settings.LEEGALITY_AUTH_TOKEN
        self.private_salt = private_salt or settings.LEEGALITY_PRIVATE_SALT
        self.timeout = timeout or settings.LEEGALITY_TIMEOUT_SECONDS
        self.env = env or settings.LEEGALITY_ENV

    def is_live_configured(self) -> bool:
        """Checks if real Leegality credentials are provided."""
        return bool(self.auth_token and self.auth_token.strip())

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.auth_token:
            headers["X-Auth-Token"] = self.auth_token
        return headers

    def create_signing_request(
        self,
        document_base64: str,
        document_filename: str,
        signer_name: str,
        signer_email: str,
        signer_phone: Optional[str] = None,
        webhook_success_url: Optional[str] = None,
        webhook_failure_url: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Creates an eSigning invitation request via official endpoint:
        POST /sign/request (or /v2.1/sign/request)
        """
        success_url = webhook_success_url or settings.LEEGALITY_WEBHOOK_SUCCESS_URL
        failure_url = webhook_failure_url or settings.LEEGALITY_WEBHOOK_FAILURE_URL

        payload = {
            "file": document_base64,
            "filename": document_filename,
            "profileId": "",  # Optional configured Leegality workflow profile
            "invitees": [
                {
                    "name": signer_name,
                    "email": signer_email,
                    "phone": signer_phone or "",
                    "signType": "electronic",  # Electronic / Virtual / Aadhaar
                    "mandatory": True
                }
            ],
            "webhook": {
                "successUrl": success_url,
                "failureUrl": failure_url
            }
        }

        # If live credentials are not yet configured in development, provide safe deterministic mock response
        if not self.is_live_configured() or self.env == "mock":
            logger.info("Operating in Leegality Sandbox Mock mode (no live token provided in .env).")
            simulated_doc_id = f"mock_leegality_{uuid.uuid4().hex[:12]}"
            simulated_signing_url = f"https://sandbox.leegality.com/sign/{simulated_doc_id}?invitee={signer_email}"
            return {
                "status": 1,
                "response": {
                    "documentId": simulated_doc_id,
                    "irn": f"IRN-{uuid.uuid4().hex[:8].upper()}",
                    "invitations": [
                        {
                            "name": signer_name,
                            "email": signer_email,
                            "active": True,
                            "signUrl": simulated_signing_url
                        }
                    ]
                },
                "message": "Signing request created successfully (Sandbox Simulation)."
            }

        endpoint = f"{self.base_url}/sign/request"
        logger.info(f"Submitting signing request to Leegality: {endpoint}")
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(endpoint, json=payload, headers=self._get_headers())
            if resp.status_code not in (200, 201):
                logger.error(f"Leegality API error ({resp.status_code}): {resp.text}")
                raise RuntimeError(f"Leegality API request failed with status {resp.status_code}: {resp.text}")
            return resp.json()

    def get_signing_status(self, document_id: str) -> Dict[str, Any]:
        """
        Retrieves current signing status and completion details:
        GET /sign/request?documentId={document_id}
        """
        if not self.is_live_configured() or self.env == "mock" or document_id.startswith("mock_"):
            return {
                "status": 1,
                "response": {
                    "documentId": document_id,
                    "status": "COMPLETED",
                    "signed": True,
                    "completedAt": "2026-10-31T18:30:00Z",
                    "invitees": [
                        {
                            "name": "The Royal Knot Client",
                            "status": "SIGNED",
                            "signedAt": "2026-10-31T18:30:00Z"
                        }
                    ]
                }
            }

        endpoint = f"{self.base_url}/sign/request"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(endpoint, params={"documentId": document_id}, headers=self._get_headers())
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to fetch Leegality status for {document_id}: {resp.text}")
            return resp.json()

    def retrieve_signed_document(self, document_id: str) -> bytes:
        """
        Retrieves the final executed PDF file from Leegality.
        In sandbox mock, returns a stamped copy or raw binary.
        """
        if not self.is_live_configured() or self.env == "mock" or document_id.startswith("mock_"):
            # Return placeholder simulated signed PDF content
            return b"%PDF-1.4\n%-- Simulated Official Leegality Executed Agreement --\n%%EOF"

        endpoint = f"{self.base_url}/document/download"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(endpoint, params={"documentId": document_id}, headers=self._get_headers())
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to download executed document from Leegality: {resp.text}")
            return resp.content

    def retrieve_audit_trail(self, document_id: str) -> Optional[bytes]:
        """
        Retrieves the official completion / audit trail certificate.
        """
        if not self.is_live_configured() or self.env == "mock" or document_id.startswith("mock_"):
            return b"%PDF-1.4\n%-- Simulated Official Leegality Audit Certificate --\n%%EOF"

        endpoint = f"{self.base_url}/document/audit-trail"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(endpoint, params={"documentId": document_id}, headers=self._get_headers())
                if resp.status_code == 200:
                    return resp.content
        except Exception as e:
            logger.warning(f"Could not retrieve audit trail: {e}")
        return None

    def verify_webhook_mac(self, document_id: str, received_mac: str) -> bool:
        """
        Validates Leegality Webhook Authenticity using HMAC-SHA1 and Private Salt.
        Documented algorithm: HMAC-SHA1(key=private_salt, message=document_id)
        Constant-time comparison prevents timing attacks.
        """
        salt = (self.private_salt or "").strip()
        if not salt:
            # In development/mock without configured salt, accept mock signatures
            if not self.is_live_configured() or self.env == "mock":
                return True
            logger.warning("LEEGALITY_PRIVATE_SALT is not configured. Webhook validation cannot proceed securely.")
            return False

        computed_mac = hmac.new(
            salt.encode("utf-8"),
            document_id.encode("utf-8"),
            hashlib.sha1
        ).hexdigest()

        return hmac.compare_digest(computed_mac.lower(), received_mac.strip().lower())

    def compute_webhook_mac(self, document_id: str) -> str:
        """Helper for test suites and sandbox mock generators to calculate matching MAC."""
        salt = (self.private_salt or "test_secret_salt_2026").strip()
        return hmac.new(
            salt.encode("utf-8"),
            document_id.encode("utf-8"),
            hashlib.sha1
        ).hexdigest()


leegality_client = LeegalityClient()
