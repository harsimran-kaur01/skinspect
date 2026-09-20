from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class QuestionnaireSchema(BaseModel):
    # Section 1 – Basic Profile
    skin_type: Optional[str] = None
    age_group: Optional[str] = None
    biological_sex: Optional[str] = None

    # Section 2 – Skin History & Safety
    pregnant: Optional[str] = None
    under_dermatologist_care: Optional[str] = None
    allergies: Optional[List[str]] = None
    diagnosed_conditions: Optional[List[str]] = None

    # Sex-specific follow-ups (conditionally shown on the frontend)
    hormonal_pattern: Optional[str] = None
    shaving_irritation: Optional[str] = None

    # Section 3 – Current Routine
    routine_complexity: Optional[str] = None
    active_ingredients: Optional[List[str]] = None
    sunscreen_use: Optional[str] = None

    # Section 4 – Lifestyle
    sun_exposure: Optional[str] = None
    sleep_quality: Optional[str] = None
    stress_level: Optional[str] = None
    smoking: Optional[str] = None

    # Section 5 – Goals
    primary_concern: Optional[str] = None
    secondary_concern: Optional[str] = None
    budget: Optional[str] = None
    routine_complexity_preference: Optional[str] = None


class QuestionnaireResponse(BaseModel):
    id: UUID
    user_id: UUID
    responses: QuestionnaireSchema
    submitted_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class QuestionnaireDetailResponse(BaseModel):
    id: UUID
    user_id: UUID
    responses: QuestionnaireSchema
    version: str
    submitted_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
