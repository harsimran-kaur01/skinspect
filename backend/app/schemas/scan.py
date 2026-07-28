from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, UUID4, ConfigDict


# ============ REQUEST ============
class ScanUploadRequest(BaseModel):
    skin_type: Optional[str] = Field(None, description="Skin type from questionnaire")
    # In future, we can add more fields like age, concerns, etc.


# ============ RESPONSE (sub‑models) ============
class SkinConditionResponse(BaseModel):
    condition: str
    confidence: float
    severity: Optional[str]
    affected_area_percentage: Optional[int]
    description: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class RecommendationResponse(BaseModel):
    type: str
    title: str
    description: str
    priority: Optional[str]
    category: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class SkinScanResponse(BaseModel):
    id: UUID4
    user_id: UUID4
    image_url: str
    thumbnail_url: Optional[str]
    skin_type: Optional[str]
    overall_health_score: Optional[int]
    quality_score: Optional[int]
    ai_model_name: Optional[str]
    ai_model_version: Optional[str]
    processing_time_ms: Optional[int]
    follow_up_needed: bool
    has_changes: bool
    previous_scan_id: Optional[UUID4]
    created_at: datetime
    updated_at: Optional[datetime]
    conditions: List[SkinConditionResponse] = []
    recommendations: List[RecommendationResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ProgressSummaryResponse(BaseModel):
    score_change: int
    trend: str
    previous_score: int
    current_score: int
    message: str


class ScanAnalyzeResponse(BaseModel):
    scan: SkinScanResponse
    progress_summary: Optional[ProgressSummaryResponse] = None
    message: str = "Analysis complete"


# ============ ERROR ============
class ScanErrorResponse(BaseModel):
    detail: str
    status_code: int
