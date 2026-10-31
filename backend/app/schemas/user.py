from typing import Optional
from datetime import datetime
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
