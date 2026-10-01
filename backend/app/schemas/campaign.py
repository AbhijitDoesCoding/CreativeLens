from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator

class CampaignBase(BaseModel):
    name: str

class CampaignCreate(CampaignBase):
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if v is None:
            raise ValueError("Campaign name is required")
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Campaign name cannot be blank")
        return trimmed

class CampaignResponse(CampaignBase):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
