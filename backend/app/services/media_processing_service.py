import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.models.media_processing import MediaProcessing
from app.schemas.media_processing import MediaProcessingUpdate

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
