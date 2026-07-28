from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from typing import Optional, List
from pathlib import Path
import shutil
import uuid
import time
import sys
import threading
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..models.user import User
from ..models.scan import SkinScan, SkinCondition, Recommendation
from ..models.questionnaire import UserQuestionnaire
from ..schemas.scan import (
    ScanAnalyzeResponse,
    SkinScanResponse,
    SkinConditionResponse,
    RecommendationResponse,
    ProgressSummaryResponse,
    ScanErrorResponse,
)
from ..auth.dependencies import get_current_active_user, get_current_verified_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scans", tags=["scans"])

# --- Paths -----------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ML_PIPELINE = PROJECT_ROOT / "ml" / "pipeline"
UPLOAD_DIR = PROJECT_ROOT / "backend" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# --- Upload constraints ------------------------------------------------
MAX_UPLOAD_SIZE_BYTES = 8 * 1024 * 1024  # 8 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Add pipeline to sys.path
if str(ML_PIPELINE) not in sys.path:
    sys.path.insert(0, str(ML_PIPELINE))

# Add engine to sys.path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- Imports from external modules ------------------------------------
from run_inference import SkinSpectPipeline
from ml.engine.recommendation_engine import generate_recommendations

_pipeline = None
_pipeline_lock = threading.Lock()


def get_pipeline():
    """Thread-safe lazy singleton — avoids double-initialization if two
    requests hit this concurrently before the pipeline has been created."""
    global _pipeline
    if _pipeline is None:
        with _pipeline_lock:
            if _pipeline is None:  # re-check inside the lock
                config_path = ML_PIPELINE / "config.yaml"
                _pipeline = SkinSpectPipeline(str(config_path))
                logger.info("✅ SkinSpect pipeline initialized")
    return _pipeline


@router.post(
    "/upload",
    response_model=ScanAnalyzeResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            "model": ScanErrorResponse,
            "description": "Invalid image or no face detected",
        },
        401: {"model": ScanErrorResponse, "description": "Unauthorized"},
        413: {"model": ScanErrorResponse, "description": "File too large"},
        500: {"model": ScanErrorResponse, "description": "Internal error"},
    },
)
async def upload_scan(
    file: UploadFile = File(...),
    # Optional overrides from frontend (kept for compatibility)
    skin_type: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    concerns: Optional[str] = Form(None),
    sensitivity: Optional[bool] = Form(None),
    routine: Optional[str] = Form(None),
    lifestyle: Optional[str] = Form(None),
    current_user: User = Depends(
        get_current_verified_user
    ),  # requires email verification
    db: Session = Depends(get_db),
):
    # ---- 1. Validate content type --------------------------------------
    # file.content_type can be None depending on the client, so guard
    # against that before calling .startswith() on it. We also restrict
    # to a known allow-list instead of any "image/*", since content_type
    # is client-supplied and not proof the bytes are actually an image.
    if not file.content_type or file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a JPEG, PNG, or WEBP image",
        )

    # ---- 2. Read + size-check before touching disk ---------------------
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB limit",
        )
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file"
        )

    # ---- 3. Verify it's actually a decodable image ----------------------
    try:
        from PIL import Image
        import io

        Image.open(io.BytesIO(contents)).verify()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not a valid image",
        )

    # ---- 4. Save image ---------------------------------------------------
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    file_ext = Path(file.filename).suffix or ".jpg"
    filename = f"{current_user.id}_{timestamp}_{unique_id}{file_ext}"
    file_path = UPLOAD_DIR / filename

    try:
        with file_path.open("wb") as buffer:
            buffer.write(contents)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image",
        )

    # ---- 5. Run inference --------------------------------------------
    try:
        pipeline = get_pipeline()
        pipeline_questionnaire = {"skin_type": skin_type} if skin_type else {}
        result = await run_in_threadpool(
            pipeline.run,
            str(file_path),
            questionnaire=pipeline_questionnaire,
            save_crop=False,
        )
    except Exception as e:
        logger.error(f"Inference error: {e}")
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {str(e)}",
        )

    if isinstance(result, dict) and "error" in result:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Image quality insufficient"),
        )

    # ---- 6. Fetch stored questionnaire (if any) ----------------------
    user_q = (
        db.query(UserQuestionnaire)
        .filter(UserQuestionnaire.user_id == current_user.id)
        .first()
    )

    # Build base questionnaire from stored data. Copy it so we don't
    # mutate the ORM-tracked dict in place.
    questionnaire = dict(user_q.responses) if user_q else {}

    # ---- 7. Override with form-provided fields (if given) ------------
    if skin_type is not None:
        questionnaire["skin_type"] = skin_type
    if age is not None:
        questionnaire["age"] = age
    if concerns is not None:
        questionnaire["concerns"] = [
            c.strip() for c in concerns.split(",") if c.strip()
        ]
    if sensitivity is not None:
        questionnaire["sensitivity"] = sensitivity
    if routine is not None:
        questionnaire["routine"] = routine
    if lifestyle is not None:
        questionnaire["lifestyle"] = lifestyle

    if "skin_type" not in questionnaire:
        questionnaire["skin_type"] = result.get("skin_type", "combination")

    # ---- 8. Add previous scan for progress tracking -------------------
    previous_scan = (
        db.query(SkinScan)
        .filter(SkinScan.user_id == current_user.id)
        .order_by(SkinScan.created_at.desc())
        .first()
    )
    if previous_scan:
        questionnaire["previous_scan"] = {
            "overall_health_score": previous_scan.overall_health_score,
        }

    # ---- 9. Generate recommendations ----------------------------------
    progress_summary = None
    try:
        engine_output = generate_recommendations(result, questionnaire)
        recommendations = engine_output.get("recommendations", [])
        progress_summary = engine_output.get("progress_summary")
    except Exception as e:
        logger.error(f"Recommendation engine error: {e}")
        recommendations = result.get("recommendations", [])

    # ---- 10. Save to database ------------------------------------------
    try:
        scan = SkinScan(
            user_id=current_user.id,
            image_url=str(file_path.relative_to(PROJECT_ROOT)),
            thumbnail_url=None,
            skin_type=result.get("skin_type"),
            overall_health_score=result.get("overall_health_score"),
            quality_score=result.get("quality_score"),
            ai_model_name=result.get("ai_model", {}).get("model_name"),
            ai_model_version=result.get("ai_model", {}).get("model_version"),
            processing_time_ms=result.get("ai_model", {}).get("processing_time_ms"),
            follow_up_needed=result.get("follow_up_needed", False),
            has_changes=result.get("has_changes", False),
            previous_scan_id=previous_scan.id if previous_scan else None,
        )
        db.add(scan)
        db.flush()

        for cond in result.get("skin_conditions", []):
            condition = SkinCondition(
                scan_id=scan.id,
                condition=cond["condition"],
                confidence=cond["confidence"],
                severity=cond.get("severity"),
                affected_area_percentage=cond.get("affected_area_percentage"),
                description=cond.get("description"),
            )
            db.add(condition)

        for rec in recommendations:
            recommendation = Recommendation(
                scan_id=scan.id,
                type=rec.get("type"),
                title=rec["title"],
                description=rec["description"],
                priority=rec.get("priority"),
                category=rec.get("category"),
            )
            db.add(recommendation)

        db.commit()
        db.refresh(scan)

    except Exception as e:
        db.rollback()
        file_path.unlink(missing_ok=True)
        logger.error(f"Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save analysis results",
        )

    # ---- 11. Build response -------------------------------------------
    scan_response = SkinScanResponse(
        id=scan.id,
        user_id=scan.user_id,
        image_url=scan.image_url,
        thumbnail_url=scan.thumbnail_url,
        skin_type=scan.skin_type,
        overall_health_score=scan.overall_health_score,
        quality_score=scan.quality_score,
        ai_model_name=scan.ai_model_name,
        ai_model_version=scan.ai_model_version,
        processing_time_ms=scan.processing_time_ms,
        follow_up_needed=scan.follow_up_needed,
        has_changes=scan.has_changes,
        previous_scan_id=scan.previous_scan_id,
        created_at=scan.created_at,
        updated_at=scan.updated_at,
        conditions=[
            SkinConditionResponse(
                condition=c.condition,
                confidence=c.confidence,
                severity=c.severity,
                affected_area_percentage=c.affected_area_percentage,
                description=c.description,
            )
            for c in scan.conditions
        ],
        recommendations=[
            RecommendationResponse(
                type=r.type,
                title=r.title,
                description=r.description,
                priority=r.priority,
                category=r.category,
            )
            for r in scan.recommendations
        ],
    )

    progress_response = (
        ProgressSummaryResponse(**progress_summary) if progress_summary else None
    )

    return ScanAnalyzeResponse(scan=scan_response, progress_summary=progress_response)


@router.get("/history", response_model=List[SkinScanResponse])
async def get_scan_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 10,
    offset: int = 0,
):
    limit = max(1, min(limit, 50))  # cap to avoid unbounded queries
    scans = (
        db.query(SkinScan)
        .filter(SkinScan.user_id == current_user.id)
        .order_by(SkinScan.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        SkinScanResponse.model_validate(scan, from_attributes=True) for scan in scans
    ]


@router.get(
    "/{scan_id}",
    response_model=SkinScanResponse,
    responses={
        404: {"model": ScanErrorResponse, "description": "Scan not found"},
        401: {"model": ScanErrorResponse, "description": "Unauthorized"},
    },
)
async def get_scan(
    scan_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Fetch a single scan by ID. This endpoint was missing before —
    the frontend's ScanDetail page called it but it always 404'd."""
    scan = (
        db.query(SkinScan)
        .filter(SkinScan.id == scan_id, SkinScan.user_id == current_user.id)
        .first()
    )
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found"
        )
    return SkinScanResponse.model_validate(scan, from_attributes=True)
