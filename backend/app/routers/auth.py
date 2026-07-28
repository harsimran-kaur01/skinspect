from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timezone

from ..database import get_db
from ..models.user import User
from ..schemas.user import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    AuthResponse,
    UserUpdate,
    VerifyEmailRequest,
    MessageResponse,
    ErrorResponse,
)
from ..auth.jwt_handler import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from ..auth.dependencies import get_current_user, get_current_active_user
from ..services.email_service import (
    generate_verification_token,
    send_verification_email,
)
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ============ HELPER FUNCTIONS ============


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def _apply_user_update(
    update_data: UserUpdate, current_user: User, db: Session
) -> User:
    """Shared logic for PUT/PATCH /me — previously duplicated verbatim
    across both handlers."""
    if update_data.email:
        email = update_data.email.lower()
        existing = (
            db.query(User)
            .filter(User.email == email, User.id != current_user.id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use"
            )
        current_user.email = email

    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name.strip()

    db.commit()
    db.refresh(current_user)

    logger.info(f"User updated: {current_user.email}")
    return current_user


# ============ PUBLIC ENDPOINTS ============


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Email already registered or invalid input",
        },
        422: {"description": "Validation error"},
    },
)
async def register(
    user_data: UserRegister,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Register a new user. Sends a verification email (or logs the link
    to the console in dev mode — see services/email_service.py)."""
    email = user_data.email.lower()

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    hashed_password = hash_password(user_data.password)
    token, expires = generate_verification_token()

    db_user = User(
        email=email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        is_verified=False,
        verification_token=token,
        verification_token_expires=expires,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    logger.info(f"User registered: {email}")

    # Sending email shouldn't block the registration response — run it
    # in the background. If it fails, the user can request a resend.
    background_tasks.add_task(send_verification_email, email, token)

    access_token = create_access_token(db_user.id)

    return AuthResponse(
        user=UserResponse.model_validate(db_user),
        token=TokenResponse(
            access_token=access_token, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        ),
        verification_required=True,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Incorrect email or password"},
    },
)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login user with email and password (JSON format). Verification is
    NOT required to log in — only to access gated features (see
    get_current_verified_user) — so a user can still explore the app and
    resend their verification email if needed."""
    user = authenticate_user(db, login_data.email.lower(), login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"User logged in: {user.email}")

    access_token = create_access_token(user.id)

    return AuthResponse(
        user=UserResponse.model_validate(user),
        token=TokenResponse(
            access_token=access_token, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        ),
        verification_required=not user.is_verified,
    )


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """OAuth2 compatible token login (used by Swagger UI's authorize button)."""
    user = authenticate_user(db, form_data.username.lower(), form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user.id)
    logger.info(f"OAuth2 token login: {user.email}")

    return TokenResponse(
        access_token=access_token, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or expired token"},
    },
)
async def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify a user's email using the token sent to them at registration."""
    user = db.query(User).filter(User.verification_token == payload.token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    if user.is_verified:
        return MessageResponse(message="Email already verified.")

    if (
        user.verification_token_expires is None
        or user.verification_token_expires < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired. Please request a new one.",
        )

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()

    logger.info(f"Email verified: {user.email}")
    return MessageResponse(message="Email verified successfully.")


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
)
async def resend_verification(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Request a new verification email (invalidates the previous token)."""
    if current_user.is_verified:
        return MessageResponse(message="Email already verified.")

    token, expires = generate_verification_token()
    current_user.verification_token = token
    current_user.verification_token_expires = expires
    db.commit()

    background_tasks.add_task(send_verification_email, current_user.email, token)

    return MessageResponse(message="Verification email sent.")


# ============ PROTECTED ENDPOINTS ============


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update current user profile (full replace semantics at the API level)."""
    updated = _apply_user_update(update_data, current_user, db)
    return UserResponse.model_validate(updated)


@router.patch("/me", response_model=UserResponse)
async def patch_me(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Partially update current user profile."""
    updated = _apply_user_update(update_data, current_user, db)
    return UserResponse.model_validate(updated)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client side token invalidation)."""
    return {"message": "Logged out successfully"}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Delete user account."""
    email = current_user.email
    db.delete(current_user)
    db.commit()
    logger.info(f"User deleted: {email}")
