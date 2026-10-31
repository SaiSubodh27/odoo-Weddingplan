import time
import json
import logging
import uuid
import hmac
import hashlib
from typing import Dict, Any, Optional, List
import httpx

from app.core.config import settings
from app.services.signature_provider import BaseSignatureProvider

logger = logging.getLogger("royal_knot.zoho_sign")


class ZohoSignClient(BaseSignatureProvider):
    """
    Official Zoho Sign API Client implementing OAuth 2.0 and API v1.
    Official Documentation: https://www.zoho.com/sign/api/

    Supports:
    - OAuth 2.0 access-token refresh and caching
    - Multi-region Data Centers (India .in, US .com, EU .eu, AU .com.au, etc.)
    - Multipart PDF upload and document submission
    - Embedded client signing URLs (embedtoken)
    - Status polling and webhook verification
    - Executed PDF and Completion Certificate (audit trail) retrieval
    - Simulation Mock mode for local testing without chargeable/live credentials
    """

    def __init__(
        self,
        env: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        accounts_base_url: Optional[str] = None,
        api_base_url: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        timeout: int = 30
    ):
        self.env = env or settings.ZOHO_SIGN_ENV
        self.client_id = client_id or settings.ZOHO_SIGN_CLIENT_ID
        self.client_secret = client_secret or settings.ZOHO_SIGN_CLIENT_SECRET
        self.refresh_token = refresh_token or settings.ZOHO_SIGN_REFRESH_TOKEN
        self.accounts_base_url = (accounts_base_url or settings.ZOHO_SIGN_ACCOUNTS_BASE_URL).rstrip("/")
        self.api_base_url = (api_base_url or settings.ZOHO_SIGN_API_BASE_URL).rstrip("/")
        self.webhook_secret = webhook_secret or settings.ZOHO_SIGN_WEBHOOK_SECRET
        self.timeout = timeout or settings.ZOHO_SIGN_TIMEOUT_SECONDS

        # Token caching
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    @property
    def provider_name(self) -> str:
        return "Zoho Sign"

    @property
    def environment(self) -> str:
        return self.env

    def is_live_configured(self) -> bool:
        """Checks if required OAuth 2.0 credentials are present."""
        return bool(
            self.client_id and self.client_id.strip()
            and self.client_secret and self.client_secret.strip()
            and self.refresh_token and self.refresh_token.strip()
        )

    def get_access_token(self) -> str:
        """
        Retrieves a valid OAuth 2.0 access token, automatically refreshing
        via the refresh_token if expired or missing.
        """
        # Return cached token if valid (with 5-minute safety margin)
        if self._access_token and time.time() < (self._token_expires_at - 300):
            return self._access_token

        if not self.is_live_configured():
            raise RuntimeError(
                f"Zoho Sign {self.env.upper()} mode requires ZOHO_SIGN_CLIENT_ID, "
                "ZOHO_SIGN_CLIENT_SECRET, and ZOHO_SIGN_REFRESH_TOKEN to be configured in backend/.env."
            )

        token_url = f"{self.accounts_base_url}/oauth/v2/token"
        params = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token"
        }

        logger.info(f"Refreshing Zoho Sign OAuth 2.0 access token via: {token_url}")
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(token_url, params=params)
            if resp.status_code != 200:
                logger.error(f"Zoho Sign OAuth token refresh failed ({resp.status_code}): {resp.text}")
                raise RuntimeError(f"Zoho Sign OAuth token refresh failed: {resp.text}")

            data = resp.json()
            if "error" in data:
                logger.error(f"Zoho Sign OAuth token refresh returned error: {data['error']}")
                raise RuntimeError(f"Zoho Sign OAuth error: {data.get('error_description', data['error'])}")

            self._access_token = data["access_token"]
            expires_in = data.get("expires_in", 3600)
            self._token_expires_at = time.time() + expires_in

            # Dynamically align API domain with user's actual Zoho region
            if data.get("api_domain"):
                self.api_base_url = f"{data['api_domain']}/api/v1".rstrip("/")

            logger.info("Successfully refreshed Zoho Sign OAuth 2.0 access token.")
            return self._access_token

    def _get_auth_headers(self) -> Dict[str, str]:
        token = self.get_access_token()
        return {
            "Authorization": f"Zoho-oauthtoken {token}"
        }

    def create_signing_request(
        self,
        document_bytes: bytes,
        document_filename: str,
        signer_name: str,
        signer_email: str,
        signer_phone: Optional[str] = None,
        notes: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Creates and submits an agreement signing request via Zoho Sign API v1.
        """
        # If in mock mode, return a deterministic simulation response
        if self.env == "mock":
            logger.info("Operating in Zoho Sign Simulation Mock mode (ZOHO_SIGN_ENV=mock).")
            simulated_req_id = f"zs_mock_{uuid.uuid4().hex[:12]}"
            simulated_doc_id = f"zs_doc_{uuid.uuid4().hex[:8]}"
            simulated_act_id = f"zs_act_{uuid.uuid4().hex[:8]}"
            simulated_signing_url = f"https://sign.zoho.in/signpage?embedtoken={simulated_req_id}"

            return {
                "status": "success",
                "provider": "Zoho Sign",
                "environment": "mock",
                "provider_request_id": simulated_req_id,
                "provider_document_id": simulated_doc_id,
                "provider_action_id": simulated_act_id,
                "signing_url": simulated_signing_url,
                "signer_name": signer_name,
                "signer_email": signer_email,
                "message": "Signing request created successfully in Zoho Sign Simulation Mock mode.",
                "raw_response": {
                    "requests": {
                        "request_id": simulated_req_id,
                        "request_name": document_filename,
                        "request_status": "inprogress",
                        "document_ids": [{"document_id": simulated_doc_id, "document_name": document_filename}],
                        "actions": [{
                            "action_id": simulated_act_id,
                            "recipient_name": signer_name,
                            "recipient_email": signer_email,
                            "action_status": "UNOPENED"
                        }]
                    }
                }
            }

        # Sandbox or Production mode: require live credentials
        if not self.is_live_configured():
            raise RuntimeError(
                f"Zoho Sign {self.env.upper()} mode is enabled, but OAuth credentials are not configured in backend/.env. "
                "Please configure ZOHO_SIGN_CLIENT_ID, ZOHO_SIGN_CLIENT_SECRET, and ZOHO_SIGN_REFRESH_TOKEN, "
                "or set ZOHO_SIGN_ENV=mock for simulation mode."
            )

        # 1. Create document in Zoho Sign via multipart POST /requests
        request_data = {
            "requests": {
                "request_name": document_filename,
                "is_sequential": True,
                "actions": [
                    {
                        "recipient_name": signer_name,
                        "recipient_email": signer_email,
                        "recipient_phonenumber": signer_phone or "",
                        "action_type": "SIGN",
                        "signing_order": 1,
                        "verify_recipient": False
                    }
                ],
                "notes": notes or "Please review and electronically sign The Royal Knot Service Agreement."
            }
        }

        endpoint = f"{self.api_base_url}/requests"
        logger.info(f"Uploading agreement PDF to Zoho Sign: {endpoint}")

        files = {
            "file": (document_filename, document_bytes, "application/pdf")
        }
        data = {
            "data": json.dumps(request_data)
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(endpoint, files=files, data=data, headers=self._get_auth_headers())
            if resp.status_code not in (200, 201):
                logger.error(f"Zoho Sign create request failed ({resp.status_code}): {resp.text}")
                raise RuntimeError(f"Zoho Sign API error ({resp.status_code}): {resp.text}")

            result = resp.json()
            if result.get("status") != "success":
                err = result.get("message") or "Unknown Zoho Sign error"
                logger.error(f"Zoho Sign returned failure: {err}")
                raise RuntimeError(f"Zoho Sign API rejected request: {err}")

            req_obj = result.get("requests", {})
            request_id = str(req_obj.get("request_id"))
            doc_ids = req_obj.get("document_ids", [])
            document_id = str(doc_ids[0].get("document_id")) if doc_ids else None
            actions = req_obj.get("actions", [])
            action_id = str(actions[0].get("action_id")) if actions else None

            # 2. Submit the request if created as draft
            if req_obj.get("request_status") == "draft":
                submit_url = f"{self.api_base_url}/requests/{request_id}/submit"
                client.post(submit_url, headers=self._get_auth_headers())

            # 3. Obtain embed signing URL if action_id is available
            signing_url = None
            if action_id:
                try:
                    embed_url = f"{self.api_base_url}/requests/{request_id}/actions/{action_id}/embedtoken"
                    embed_resp = client.post(embed_url, headers=self._get_auth_headers())
                    if embed_resp.status_code == 200:
                        embed_data = embed_resp.json()
                        signing_url = embed_data.get("sign_url")
                except Exception as e:
                    logger.warning(f"Could not retrieve Zoho Sign embed token URL: {e}")

            return {
                "status": "success",
                "provider": "Zoho Sign",
                "environment": self.env,
                "provider_request_id": request_id,
                "provider_document_id": document_id,
                "provider_action_id": action_id,
                "signing_url": signing_url,
                "signer_name": signer_name,
                "signer_email": signer_email,
                "message": f"Service Agreement successfully dispatched via Zoho Sign {self.env.upper()}.",
                "raw_response": result
            }

    def get_signing_status(self, provider_request_id: str) -> Dict[str, Any]:
        """
        Retrieves current signing status from Zoho Sign API v1.
        GET /requests/{request_id}
        """
        if self.env == "mock" or provider_request_id.startswith("zs_mock_"):
            return {
                "status": "COMPLETED",
                "is_completed": True,
                "completed_at": "2026-10-31T20:00:00Z",
                "signers": [{
                    "name": "The Royal Knot Client",
                    "status": "SIGNED",
                    "action_type": "SIGN"
                }],
                "raw_response": {"mock": True, "request_id": provider_request_id}
            }

        endpoint = f"{self.api_base_url}/requests/{provider_request_id}"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(endpoint, headers=self._get_auth_headers())
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to fetch Zoho Sign request {provider_request_id}: {resp.text}")

            data = resp.json()
            req_obj = data.get("requests", {})
            zs_status = str(req_obj.get("request_status", "")).lower()

            # Map Zoho status to application standard
            status_map = {
                "completed": "COMPLETED",
                "inprogress": "SENT",
                "recalled": "CANCELLED",
                "declined": "DECLINED",
                "expired": "EXPIRED",
                "draft": "DRAFT"
            }
            app_status = status_map.get(zs_status, "SENT")

            return {
                "status": app_status,
                "is_completed": app_status == "COMPLETED",
                "completed_at": req_obj.get("completed_time"),
                "signers": req_obj.get("actions", []),
                "raw_response": data
            }

    def retrieve_signed_document(self, provider_request_id: str) -> bytes:
        """
        Retrieves binary PDF bytes of the completed signed document.
        GET /requests/{request_id}/pdf
        """
        if self.env == "mock" or provider_request_id.startswith("zs_mock_"):
            return b"%PDF-1.4\n%-- Simulated Official Zoho Sign Executed Agreement --\n%%EOF"

        endpoint = f"{self.api_base_url}/requests/{provider_request_id}/pdf"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(endpoint, headers=self._get_auth_headers())
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to download executed PDF from Zoho Sign: {resp.text}")
            return resp.content

    def retrieve_audit_trail(self, provider_request_id: str) -> Optional[bytes]:
        """
        Retrieves completion certificate / audit trail from Zoho Sign.
        GET /requests/{request_id}/completioncertificate
        """
        if self.env == "mock" or provider_request_id.startswith("zs_mock_"):
            return b"%PDF-1.4\n%-- Simulated Official Zoho Sign Completion Certificate --\n%%EOF"

        endpoint = f"{self.api_base_url}/requests/{provider_request_id}/completioncertificate"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(endpoint, headers=self._get_auth_headers())
                if resp.status_code == 200:
                    return resp.content
        except Exception as e:
            logger.warning(f"Could not retrieve Zoho Sign completion certificate: {e}")
        return None

    def verify_webhook(
        self,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Validates the authenticity of an incoming Zoho Sign webhook.
        If a webhook secret or token is configured, verifies it.
        """
        secret = (self.webhook_secret or "").strip()
        if not secret:
            if self.env == "mock":
                return True
            # In live mode without secret, log warning but permit valid Zoho payload structure
            logger.warning("ZOHO_SIGN_WEBHOOK_SECRET is not configured. Webhook token validation bypassed.")
            return True

        headers = headers or {}
        # Check custom header or payload token
        received_token = (
            headers.get("x-zoho-webhook-secret")
            or headers.get("token")
            or headers.get("x-auth-token")
            or payload.get("token")
            or payload.get("secret")
            or ""
        )

        return hmac.compare_digest(secret.lower(), str(received_token).strip().lower())


# Primary Zoho Sign client singleton
zoho_sign_client = ZohoSignClient()
