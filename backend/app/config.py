from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # App
    APP_NAME: str = "SkinSpect"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False  # Default to False for production

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:8000"

    # --- Email verification ---
    # Base URL used to build the verification link sent to users, e.g.
    # "http://localhost:5173" in dev, your real domain in production.
    FRONTEND_URL: str = "http://localhost:5173"
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24

    # SMTP is OPTIONAL. If left blank, the app runs in "dev mode" for
    # email: instead of actually sending anything, it logs the
    # verification link to the backend console so you can test the full
    # flow locally without signing up for an email provider first.
    # Fill these in (e.g. with Resend/SendGrid/Mailgun SMTP credentials)
    # to send real emails.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@skinspect.local"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [
            origin.strip()
            for origin in self.ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def email_configured(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_USERNAME and self.SMTP_PASSWORD)

    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
