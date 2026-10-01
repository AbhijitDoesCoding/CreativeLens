from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict

MediaType = Literal["image", "video"]

class AssetBase(BaseModel):
    filename: str
    media_type: MediaType
    mime_type: str
    file_size: int

class AssetCreate(AssetBase):
    campaign_id: str
    file_path: str

class AssetResponse(AssetBase):
    id: str
    campaign_id: str
    file_path: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
