import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

class InferenceRun(Base):
    __tablename__ = "inference_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(
        String(36),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_id = Column(
        String(36),
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'running', 'completed', 'failed'

    # Standardized outputs
    response_text = Column(Text, nullable=True)
    context_json = Column(JSON, nullable=True)  # brand, product, offer, cta, summary

    # Execution telemetry & usage
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    ttft_ms = Column(Integer, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    estimated_cost_usd = Column(Float, nullable=True)

    # Raw model output & failure reasons
    raw_output = Column(JSON, nullable=True)
    error_message = Column(String(1024), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    asset = relationship("Asset", back_populates="inference_runs")
    model = relationship("Model", back_populates="inference_runs")
