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


class WebsiteClientRegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    full_name: str = Field(..., min_length=1, max_length=150, alias="fullName")
    partner_name: Optional[str] = Field(None, max_length=150, alias="partnerName")
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6)
    phone: str = Field(..., min_length=3, max_length=50)

    # Wedding Parameters
    wedding_date: Optional[date] = Field(None, alias="weddingDate")
    wedding_location: Optional[str] = Field(None, max_length=255, alias="weddingLocation")
    expected_guest_count: Optional[int] = Field(None, ge=1, alias="expectedGuestCount")
    estimated_budget: Optional[Decimal] = Field(None, ge=0, alias="estimatedBudget")
    wedding_events: Optional[List[str]] = Field(default_factory=list, alias="weddingEvents")
    preferred_theme: Optional[str] = Field(None, max_length=255, alias="preferredTheme")
    service_package: Optional[str] = Field("Full-Service", alias="servicePackage")
    preferences: Optional[str] = Field(None, max_length=3000)

    @field_validator("wedding_date", mode="before")
    def validate_wedding_date(cls, v):
        if not v:
            return None
        if isinstance(v, (date, datetime)):
            return v if isinstance(v, date) else v.date()
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return None
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%m/%d/%Y"):
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    pass
        return None

    @field_validator("estimated_budget", mode="before")
    def validate_budget(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, (int, float, Decimal)):
            return Decimal(str(v))
        if isinstance(v, str):
            clean = v.replace("₹", "").replace(",", "").strip()
            # check for "crore" or "lakh"
            lower = clean.lower()
            if "crore" in lower or "cr" in lower:
                nums = re.findall(r"[\d\.]+", lower)
                if nums:
                    return Decimal(str(float(nums[0]) * 10000000))
            if "lakh" in lower or "lac" in lower:
                nums = re.findall(r"[\d\.]+", lower)
                if nums:
                    return Decimal(str(float(nums[0]) * 100000))
            nums = re.findall(r"[\d\.]+", clean)
            if nums:
                try:
                    return Decimal(nums[0])
                except Exception:
                    return None
            return None
        return None

    @field_validator("email")
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean):
            raise ValueError("Invalid email format.")
        return clean
