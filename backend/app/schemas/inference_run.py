from datetime import datetime
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

InferenceRunStatus = Literal["pending", "running", "completed", "failed"]

class InferenceRunBase(BaseModel):
    asset_id: str
    model_id: str
    status: InferenceRunStatus = "pending"
    response_text: Optional[str] = None
    context_json: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    latency_ms: Optional[int] = None
    ttft_ms: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    raw_output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class InferenceRunCreate(InferenceRunBase):
    pass

class InferenceRunUpdate(BaseModel):
    status: Optional[InferenceRunStatus] = None
    response_text: Optional[str] = None
    context_json: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    latency_ms: Optional[int] = None
    ttft_ms: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    raw_output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class InferenceRunResponse(InferenceRunBase):
    id: str
    created_at: datetime
    model_name: Optional[str] = None
    model_key: Optional[str] = None
    provider: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
