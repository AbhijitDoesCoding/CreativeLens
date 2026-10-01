import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, JSON, String
from sqlalchemy.orm import relationship
from app.db.session import Base

class Model(Base):
    __tablename__ = "models"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    provider = Column(String(100), nullable=False)
    model_key = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False, default="multimodal")
    enabled = Column(Boolean, nullable=False, default=False)
    configuration_json = Column(JSON, nullable=True)
    pricing_json = Column(JSON, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    inference_runs = relationship(
        "InferenceRun",
        back_populates="model",
        cascade="all, delete-orphan",
        order_by="InferenceRun.created_at.desc()",
    )

