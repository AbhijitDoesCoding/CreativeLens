from datetime import datetime
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

InferenceRunStatus = Literal["pending", "running", "completed", "failed"]

class InferAssetRequest(BaseModel):
    prompt: Optional[str] = None

class InferenceRunBase(BaseModel):
    asset_id: str
    model_id: str
    status: InferenceRunStatus = "pending"
    text: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
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

    @model_validator(mode="after")
    def sync_text_and_context(self) -> "InferenceRunBase":
        if not self.text and self.response_text:
            self.text = self.response_text
        elif not self.response_text and self.text:
            self.response_text = self.text

        if not self.context and self.context_json:
            self.context = self.context_json
        elif not self.context_json and self.context:
            self.context_json = self.context
        return self

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
