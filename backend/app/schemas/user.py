from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
import re


class TokenVerifyResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    valid: bool
    email: Optional[str] = None
    client_name: Optional[str] = Field(None, alias="clientName")
    message: str


class AccountActivateRequest(BaseModel):
    token: str = Field(..., description="Secret activation token")
    password: str = Field(..., min_length=8, description="New secure password")
    confirm_password: str = Field(..., alias="confirmPassword", min_length=8, description="Password confirmation")

    @field_validator("confirm_password")
    def passwords_match(cls, v: str, info):
        password = info.data.get("password")
        if password and v != password:
            raise ValueError("Passwords do not match.")
        return v


class AccountActivateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    message: str
    email: str
    activated_at: datetime = Field(..., alias="activatedAt")


class UserLoginRequest(BaseModel):
    email: str = Field(..., description="User Email")
    password: str = Field(..., description="User Password")


class UserSignupRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    full_name: str = Field(..., min_length=2, max_length=150, alias="fullName")
    email: str = Field(..., min_length=5, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field("RoyalKnot2026!", min_length=6, description="Password")
    role: str = Field("client", description="client | staff | vendor")

    @field_validator("email")
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean):
            raise ValueError("Invalid email format.")
        return clean


class UserLoginResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    message: str
    user_id: str = Field(..., alias="userId")
    email: str
    role: str
    client_id: Optional[str] = Field(None, alias="clientId")
    client_name: Optional[str] = Field(None, alias="clientName")
    access_token: Optional[str] = Field(None, alias="accessToken")
    has_completed_details: bool = Field(True, alias="hasCompletedDetails")
    has_signed_agreement: bool = Field(True, alias="hasSignedAgreement")
    agreement_id: Optional[str] = Field(None, alias="agreementId")
    agreement_status: Optional[str] = Field(None, alias="agreementStatus")


class WebsiteClientRegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    full_name: str = Field(..., min_length=2, max_length=150, alias="fullName")
    partner_name: Optional[str] = Field(None, max_length=150, alias="partnerName")
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8)
    phone: str = Field(..., min_length=7, max_length=50)

    # Wedding Parameters
    wedding_date: Optional[date] = Field(None, alias="weddingDate")
    wedding_location: Optional[str] = Field(None, max_length=255, alias="weddingLocation")
    expected_guest_count: Optional[int] = Field(None, ge=1, alias="expectedGuestCount")
    estimated_budget: Optional[Decimal] = Field(None, ge=0, alias="estimatedBudget")
    wedding_events: Optional[List[str]] = Field(default_factory=list, alias="weddingEvents")
    preferred_theme: Optional[str] = Field(None, max_length=255, alias="preferredTheme")
    service_package: Optional[str] = Field("Full-Service", alias="servicePackage")
    preferences: Optional[str] = Field(None, max_length=3000)

    @field_validator("email")
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean):
            raise ValueError("Invalid email format.")
        return clean
