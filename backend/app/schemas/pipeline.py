from typing import Optional
from pydantic import BaseModel, Field

class CampaignRunRequest(BaseModel):
    prompt: Optional[str] = None
    max_workers: Optional[int] = Field(default=3, ge=1, le=10)

class CampaignRunResponse(BaseModel):
    campaign_id: str
    assets: int
    enabled_models: int
    runs_created: int
    successful_runs: Optional[int] = None
    failed_runs: Optional[int] = None
