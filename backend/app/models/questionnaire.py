from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from ..database import Base, GUID
import uuid
from sqlalchemy.orm import relationship


class UserQuestionnaire(Base):
    __tablename__ = "user_questionnaires"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    responses = Column(JSON, nullable=False)
    version = Column(String(10), default="1.0")
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="questionnaire")
