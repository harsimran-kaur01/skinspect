from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from uuid import UUID

from ..database import get_db
from ..models.user import User
from ..models.questionnaire import UserQuestionnaire
from ..schemas.questionnaire import (
    QuestionnaireSchema,
    QuestionnaireResponse,
    QuestionnaireDetailResponse,
)
from ..auth.dependencies import get_current_active_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/questionnaire", tags=["questionnaire"])


@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
)
async def submit_questionnaire(
    q_data: QuestionnaireSchema,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Submit or update the user's skincare questionnaire.
    If the user already has a questionnaire, it will be updated.
    """
    # Check if user already has a questionnaire
    existing = (
        db.query(UserQuestionnaire)
        .filter(UserQuestionnaire.user_id == current_user.id)
        .first()
    )

    # Convert Pydantic model to dict (exclude unset fields)
    data = q_data.model_dump(exclude_unset=True)

    if existing:
        # Update existing
        existing.responses = data
        existing.updated_at = datetime.utcnow()
        db.commit()
        logger.info(f"Updated questionnaire for user: {current_user.email}")
        return {
            "message": "Questionnaire updated successfully",
            "user_id": str(current_user.id),
        }
    else:
        # Create new
        new_q = UserQuestionnaire(
            user_id=current_user.id, responses=data, version="1.0"
        )
        db.add(new_q)
        db.commit()
        logger.info(f"Created questionnaire for user: {current_user.email}")
        return {
            "message": "Questionnaire saved successfully",
            "user_id": str(current_user.id),
        }


@router.get(
    "/",
    response_model=QuestionnaireDetailResponse,
    responses={
        404: {"description": "Questionnaire not found"},
        401: {"description": "Unauthorized"},
    },
)
async def get_questionnaire(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve the user's stored questionnaire.
    Returns 404 if no questionnaire exists.
    """
    q = (
        db.query(UserQuestionnaire)
        .filter(UserQuestionnaire.user_id == current_user.id)
        .first()
    )

    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questionnaire not found for this user",
        )

    return QuestionnaireDetailResponse(
        id=q.id,
        user_id=q.user_id,
        responses=q.responses,
        version=q.version,
        submitted_at=q.submitted_at,
        updated_at=q.updated_at,
    )


@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Questionnaire not found"},
        401: {"description": "Unauthorized"},
    },
)
async def delete_questionnaire(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Delete the user's questionnaire.
    """
    q = (
        db.query(UserQuestionnaire)
        .filter(UserQuestionnaire.user_id == current_user.id)
        .first()
    )

    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questionnaire not found for this user",
        )

    db.delete(q)
    db.commit()
    logger.info(f"Deleted questionnaire for user: {current_user.email}")
    return None  # 204 No Content


@router.get(
    "/check",
    response_model=dict,
)
async def check_questionnaire_exists(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Lightweight endpoint to check if a user has submitted a questionnaire.
    Returns a boolean flag.
    """
    exists = (
        db.query(UserQuestionnaire)
        .filter(UserQuestionnaire.user_id == current_user.id)
        .first()
        is not None
    )

    return {"has_questionnaire": exists, "user_id": str(current_user.id)}
