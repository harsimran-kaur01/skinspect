from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from typing import Optional
from uuid import UUID
from ..config import settings
import logging

logger = logging.getLogger(__name__)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def create_access_token(
    user_id: UUID, expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token for a user."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": str(user_id), "exp": expire}

    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to create token: {e}")
        raise


def decode_access_token(token: str) -> Optional[str]:
    """Decode and validate a JWT token, return user_id if valid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.JWTClaimsError:
        logger.warning("Invalid token claims")
        return None
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def get_token_expiry() -> datetime:
    """Get the expiry time for a new token."""
    return datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
