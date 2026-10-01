import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.db.session import Base

class MediaProcessing(Base):
    __tablename__ = "media_processing"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(
        String(36),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    media_type = Column(String(50), nullable=False)  # 'image' or 'video'
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'processing', 'completed', 'failed'
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    frame_rate = Column(Float, nullable=True)
    total_frames = Column(Integer, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String(1024), nullable=True)
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

    asset = relationship("Asset", back_populates="media_processing")
