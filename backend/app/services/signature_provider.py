from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseSignatureProvider(ABC):
    """
    Abstract Signature Provider Interface.
    Enables pluggable e-signature backends (Zoho Sign, Mock, or future providers)
    without coupling agreement lifecycle business logic to a single vendor.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'Zoho Sign', 'Mock', 'Leegality')."""
        pass

    @property
    @abstractmethod
    def environment(self) -> str:
        """Current operating environment ('sandbox', 'production', 'mock')."""
        pass

    @abstractmethod
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
        Submits the document to the e-signature provider and creates a signing invitation.
        Returns a standardized dictionary:
        {
            "status": "success",
            "provider": str,
            "environment": str,
            "provider_request_id": str,
            "provider_document_id": Optional[str],
            "signing_url": Optional[str],
            "signer_name": str,
            "signer_email": str,
            "raw_response": Dict[str, Any]
        }
        """
        pass

    @abstractmethod
    def get_signing_status(self, provider_request_id: str) -> Dict[str, Any]:
        """
        Fetches the latest execution status for the given request ID.
        Standardized return:
        {
            "status": str,  # 'NOT_CREATED', 'SENT', 'VIEWED', 'COMPLETED', 'DECLINED', 'EXPIRED'
            "is_completed": bool,
            "completed_at": Optional[str],
            "signers": List[Dict[str, Any]],
            "raw_response": Dict[str, Any]
        }
        """
        pass

    @abstractmethod
    def retrieve_signed_document(self, provider_request_id: str) -> bytes:
        """Retrieves binary PDF bytes of the completed signed document."""
        pass

    @abstractmethod
    def retrieve_audit_trail(self, provider_request_id: str) -> Optional[bytes]:
        """Retrieves binary PDF bytes of the completion certificate / audit trail."""
        pass

    @abstractmethod
    def verify_webhook(
        self,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """Validates the authenticity of an incoming webhook callback."""
        pass
