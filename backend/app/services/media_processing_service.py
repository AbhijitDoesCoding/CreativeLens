import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.asset import Asset
from app.models.media_processing import MediaProcessing
from app.schemas.media_processing import MediaProcessingUpdate
from app.services import ffmpeg_service, image_processor, storage_service


def create_or_get_processing_record(
    db: Session,
    asset_id: str,
    media_type: str,
) -> MediaProcessing:
    """Create a processing record for an asset or return existing one."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with id '{asset_id}' not found",
        )

    processing = (
        db.query(MediaProcessing)
        .filter(MediaProcessing.asset_id == asset_id)
        .first()
    )
    if processing:
        return processing

    new_record = MediaProcessing(
        id=str(uuid.uuid4()),
        asset_id=asset_id,
        media_type=media_type,
        status="pending",
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record

def get_processing_by_asset_id(db: Session, asset_id: str) -> Optional[MediaProcessing]:
    """Retrieve processing record by asset ID."""
    return (
        db.query(MediaProcessing)
        .filter(MediaProcessing.asset_id == asset_id)
        .first()
    )

def update_processing_record(
    db: Session,
    processing: MediaProcessing,
    update_data: MediaProcessingUpdate,
) -> MediaProcessing:
    """Update fields of an existing processing record."""
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(processing, field, value)

    if update_data.status == "completed" and not processing.processed_at:
        processing.processed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(processing)
    return processing

def process_asset(
    db: Session,
    asset_id: str,
    sample_fps: Optional[float] = 1.0,
) -> MediaProcessing:
    """Process asset media (image or video) and record results in MediaProcessing."""
    fps = sample_fps if sample_fps is not None else 1.0
    if fps <= 0 or fps > 60:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sample_fps {fps}. Must be greater than 0 and at most 60.",
        )

    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with id '{asset_id}' not found",
        )

    processing = create_or_get_processing_record(db, asset_id, asset.media_type)

    if asset.media_type == "image":
        update_processing_record(
            db=db,
            processing=processing,
            update_data=MediaProcessingUpdate(status="processing"),
        )
        try:
            disk_path = storage_service.get_asset_disk_path(asset.file_path)
            meta = image_processor.process_image(disk_path)
            update_processing_record(
                db=db,
                processing=processing,
                update_data=MediaProcessingUpdate(
                    status="completed",
                    width=meta["width"],
                    height=meta["height"],
                    format=meta["format"],
                    color_mode=meta["color_mode"],
                    error_message=None,
                ),
            )
        except Exception as e:
            update_processing_record(
                db=db,
                processing=processing,
                update_data=MediaProcessingUpdate(
                    status="failed",
                    error_message=str(e),
                ),
            )
    elif asset.media_type == "video":
        update_processing_record(
            db=db,
            processing=processing,
            update_data=MediaProcessingUpdate(status="processing"),
        )
        try:
            disk_path = storage_service.get_asset_disk_path(asset.file_path)
            meta = ffmpeg_service.probe_video(disk_path)

            # Extract frames
            frames_disk_dir = (
                settings.UPLOAD_DIR / asset.campaign_id / "processed" / asset.id / "frames"
            )
            rel_frames_dir = (
                f"data/campaigns/{asset.campaign_id}/processed/{asset.id}/frames"
            )
            extracted_count = ffmpeg_service.extract_video_frames(
                video_path=disk_path,
                output_dir=frames_disk_dir,
                sample_fps=fps,
            )

            update_processing_record(
                db=db,
                processing=processing,
                update_data=MediaProcessingUpdate(
                    status="completed",
                    width=meta["width"],
                    height=meta["height"],
                    duration_ms=meta["duration_ms"],
                    frame_rate=meta["frame_rate"],
                    total_frames=meta["total_frames"],
                    frames_extracted=extracted_count,
                    frame_directory=rel_frames_dir,
                    format=meta["codec"],
                    error_message=None,
                ),
            )
        except Exception as e:
            update_processing_record(
                db=db,
                processing=processing,
                update_data=MediaProcessingUpdate(
                    status="failed",
                    error_message=str(e),
                ),
            )

    return processing


