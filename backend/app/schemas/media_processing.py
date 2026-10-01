from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

ProcessingStatus = Literal["pending", "processing", "completed", "failed"]

class ProcessAssetRequest(BaseModel):
    sample_fps: Optional[float] = Field(default=1.0, gt=0, le=60)
    force: Optional[bool] = False

class MediaProcessingBase(BaseModel):
    media_type: str
    status: ProcessingStatus = "pending"
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    color_mode: Optional[str] = None
    duration_ms: Optional[int] = None
    frame_rate: Optional[float] = None
    total_frames: Optional[int] = None
    frames_extracted: Optional[int] = None
    frame_directory: Optional[str] = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class MediaProcessingCreate(MediaProcessingBase):
    asset_id: str

class MediaProcessingUpdate(BaseModel):
    status: Optional[ProcessingStatus] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    color_mode: Optional[str] = None
    duration_ms: Optional[int] = None
    frame_rate: Optional[float] = None
    total_frames: Optional[int] = None
    frames_extracted: Optional[int] = None
    frame_directory: Optional[str] = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class MediaProcessingResponse(MediaProcessingBase):
    id: str
    asset_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FrameInfo(BaseModel):
    frame_number: int
    filename: str
    url: str

class AssetFramesResponse(BaseModel):
    asset_id: str
    total_frames: int
    frame_directory: Optional[str] = None
    frames: List[FrameInfo] = []
