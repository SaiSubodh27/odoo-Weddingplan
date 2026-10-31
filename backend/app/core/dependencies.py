from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import UserAccount
from app.models.agreement import ServiceAgreement


def require_signed_agreement(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """
    Backend Authorization Gate:
    Enforces that authenticated client users must have a legally executed,
    SIGNED Service Agreement before accessing protected client resources.
    Agency planners, employees, and administrators are exempt from this restriction.
    """
    if not authorization:
        return None

    token = authorization.replace("Bearer ", "").strip()

    # Agency staff tokens are exempt
    if "staff" in token or token == "trk_staff_session_token_2026":
        return {"role": "staff", "exempt": True}

    if token.startswith("trk_token_"):
        user_id = token.replace("trk_token_", "")
        user = db.query(UserAccount).filter(UserAccount.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user session."
            )

        if user.role != "client":
            return {"role": user.role, "exempt": True}

        if not user.client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Client profile is not associated with this account."
            )

        agreement = db.query(ServiceAgreement).filter(
            ServiceAgreement.client_id == user.client_id,
            ServiceAgreement.is_deleted == False
        ).order_by(ServiceAgreement.created_at.desc()).first()

        if not agreement or (agreement.status != "SIGNED" and not agreement.is_verified):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Digital execution of the Service Agreement is required before accessing client portal resources.",
                headers={"X-Agreement-Required": "true", "X-Agreement-Id": agreement.id if agreement else ""}
            )

        return {"role": "client", "user": user, "agreement": agreement}

    return None

