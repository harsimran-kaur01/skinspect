from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class QuestionnaireSchema(BaseModel):
    # Section A
    skin_type: Optional[str] = None
    skin_tone: Optional[str] = None

    # Section B
    concerns: Optional[List[str]] = None

    # Section C
    sensitivity_level: Optional[str] = None
    reactions: Optional[List[str]] = None

    # Section D
    routine_complexity: Optional[str] = None
    active_ingredients: Optional[List[str]] = None
    exfoliation_freq: Optional[str] = None
    sunscreen_use: Optional[str] = None

    # Section E
    age_group: Optional[str] = None
    sun_exposure: Optional[str] = None
    stress_level: Optional[str] = None
    sleep_hours: Optional[str] = None
    water_intake: Optional[str] = None
    smoking: Optional[str] = None
    alcohol_freq: Optional[str] = None

    # Section F (preferences)
    price_preference: Optional[str] = None
    fragrance_preference: Optional[str] = None
    ethical_preference: Optional[str] = None


class QuestionnaireResponse(BaseModel):
    id: UUID
    user_id: UUID
    responses: QuestionnaireSchema
    submitted_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Add to existing questionnaire.py schema file


class QuestionnaireDetailResponse(BaseModel):
    id: UUID
    user_id: UUID
    responses: QuestionnaireSchema
    version: str
    submitted_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
