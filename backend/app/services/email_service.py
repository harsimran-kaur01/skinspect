import smtplib
import secrets
import logging
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..config import settings

logger = logging.getLogger(__name__)


def generate_verification_token() -> tuple[str, datetime]:
    """Generate a random verification token and its expiry timestamp."""
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(
        hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS
    )
    return token, expires


def send_verification_email(to_email: str, token: str) -> None:
    """
    Sends the verification email, or in dev mode (no SMTP configured),
    logs the verification link to the console instead so the flow can
    be tested end-to-end without a real email provider.
    """
    verify_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    if not settings.email_configured:
        # Dev-mode fallback — no SMTP credentials set.
        logger.info(
            "=" * 70
            + f"\n📧 DEV MODE — no SMTP configured, not actually sending email.\n"
            + f"   Verification link for {to_email}:\n"
            + f"   {verify_link}\n"
            + "=" * 70
        )
        return

    subject = "Verify your SkinSpect account"
    body = (
        f"Welcome to SkinSpect!\n\n"
        f"Please verify your email by clicking the link below:\n"
        f"{verify_link}\n\n"
        f"This link expires in {settings.VERIFICATION_TOKEN_EXPIRE_HOURS} hours.\n"
        f"If you didn't create this account, you can ignore this email."
    )

    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info(f"✅ Verification email sent to {to_email}")
    except Exception as e:
        # Don't let email failure block registration — log it and move
        # on. The user can request a resend later.
        logger.error(f"Failed to send verification email to {to_email}: {e}")
