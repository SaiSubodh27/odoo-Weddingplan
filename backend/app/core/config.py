from typing import List, Union, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from pathlib import Path


class Settings(BaseSettings):
    PROJECT_NAME: str = "The Royal Knot — Wedding Planning Management System"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "postgresql+psycopg://postgres@localhost:5432/royal_knot_db"
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"]
    SECRET_KEY: str = "theroyalknot-luxury-wedding-management-secret-key-2026"

    # File uploads for registration documents & email attachments
    UPLOAD_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "uploads")

    # Agency Primary Email
    AGENCY_EMAIL: str = "saisubodh6@gmail.com"

    # SMTP Configuration (Outgoing Email)
    SMTP_HOST: Optional[str] = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = "saisubodh6@gmail.com"
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "saisubodh6@gmail.com"
    SMTP_FROM_NAME: str = "The Royal Knot Concierge"
    SMTP_USE_TLS: bool = True

    # IMAP Configuration (Incoming Email Retrieval)
    IMAP_HOST: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    IMAP_USERNAME: Optional[str] = "saisubodh6@gmail.com"
    IMAP_PASSWORD: Optional[str] = None
    IMAP_USE_SSL: bool = True
    EMAIL_POLL_INTERVAL_SECONDS: int = 60

    # Application URLs
    FRONTEND_BASE_URL: str = "http://localhost:5173"
    BACKEND_BASE_URL: str = "http://localhost:8000"

    # Token Lifespans (in minutes: 72 hours = 4320 mins)
    ACTIVATION_TOKEN_EXPIRY_MINUTES: int = 4320

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
