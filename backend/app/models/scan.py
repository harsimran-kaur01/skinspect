from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    Integer,
    Float,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base, GUID
import uuid


class SkinScan(Base):
    __tablename__ = "skin_scans"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    skin_type = Column(String(20), nullable=True)
    overall_health_score = Column(Integer, nullable=True)
    quality_score = Column(Integer, nullable=True)
    ai_model_name = Column(String(50), nullable=True)
    ai_model_version = Column(String(20), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    follow_up_needed = Column(Boolean, default=False)
    has_changes = Column(Boolean, default=False)
    previous_scan_id = Column(GUID, ForeignKey("skin_scans.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="scans")
    conditions = relationship(
        "SkinCondition", back_populates="scan", cascade="all, delete-orphan"
    )
    recommendations = relationship(
        "Recommendation", back_populates="scan", cascade="all, delete-orphan"
    )


class SkinCondition(Base):
    __tablename__ = "skin_conditions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    scan_id = Column(
        GUID,
        ForeignKey("skin_scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    condition = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    severity = Column(String(20), nullable=True)
    affected_area_percentage = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scan = relationship("SkinScan", back_populates="conditions")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    scan_id = Column(
        GUID,
        ForeignKey("skin_scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = Column(String(20), nullable=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(10), nullable=True)
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scan = relationship("SkinScan", back_populates="recommendations")
