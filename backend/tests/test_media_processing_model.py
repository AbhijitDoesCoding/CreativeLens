import pytest
from fastapi import HTTPException
from app.models.campaign import Campaign
from app.models.asset import Asset
from app.models.media_processing import MediaProcessing
from app.schemas.media_processing import MediaProcessingUpdate
from app.services import media_processing_service

def test_create_processing_record(db_session):
    campaign = Campaign(name="Processing Test Campaign")
    db_session.add(campaign)
    db_session.commit()

    asset = Asset(
        campaign_id=campaign.id,
        filename="test.png",
        file_path="data/campaigns/c/assets/test.png",
        media_type="image",
        mime_type="image/png",
        file_size=1234,
    )
    db_session.add(asset)
    db_session.commit()

    record = media_processing_service.create_or_get_processing_record(
        db=db_session,
        asset_id=asset.id,
        media_type="image",
    )
    assert record.id is not None
    assert record.asset_id == asset.id
    assert record.media_type == "image"
    assert record.status == "pending"
    assert record.created_at is not None
    assert record.updated_at is not None

def test_relationship_with_asset(db_session):
    campaign = Campaign(name="Relationship Test Campaign")
    db_session.add(campaign)
    db_session.commit()

    asset = Asset(
        campaign_id=campaign.id,
        filename="video.mp4",
        file_path="data/campaigns/c/assets/video.mp4",
        media_type="video",
        mime_type="video/mp4",
        file_size=50000,
    )
    db_session.add(asset)
    db_session.commit()

    record = media_processing_service.create_or_get_processing_record(
        db=db_session,
        asset_id=asset.id,
        media_type="video",
    )

    db_session.refresh(asset)
    assert asset.media_processing is not None
    assert asset.media_processing.id == record.id
    assert record.asset.id == asset.id

    # Verify cascade delete
    db_session.delete(asset)
    db_session.commit()

    deleted_record = (
        db_session.query(MediaProcessing)
        .filter(MediaProcessing.id == record.id)
        .first()
    )
    assert deleted_record is None

def test_status_transitions(db_session):
    campaign = Campaign(name="Transitions Campaign")
    db_session.add(campaign)
    db_session.commit()

    asset = Asset(
        campaign_id=campaign.id,
        filename="clip.mp4",
        file_path="data/campaigns/c/assets/clip.mp4",
        media_type="video",
        mime_type="video/mp4",
        file_size=10000,
    )
    db_session.add(asset)
    db_session.commit()

    record = media_processing_service.create_or_get_processing_record(
        db=db_session,
        asset_id=asset.id,
        media_type="video",
    )
    assert record.status == "pending"

    # Transition: pending -> processing
    media_processing_service.update_processing_record(
        db=db_session,
        processing=record,
        update_data=MediaProcessingUpdate(status="processing"),
    )
    assert record.status == "processing"

    # Transition: processing -> completed
    media_processing_service.update_processing_record(
        db=db_session,
        processing=record,
        update_data=MediaProcessingUpdate(
            status="completed",
            width=1920,
            height=1080,
            duration_ms=6000,
            frame_rate=30.0,
            total_frames=180,
        ),
    )
    assert record.status == "completed"
    assert record.width == 1920
    assert record.height == 1080
    assert record.duration_ms == 6000
    assert record.frame_rate == 30.0
    assert record.total_frames == 180
    assert record.processed_at is not None

    # Transition: completed -> failed
    media_processing_service.update_processing_record(
        db=db_session,
        processing=record,
        update_data=MediaProcessingUpdate(
            status="failed",
            error_message="Corrupted file format",
        ),
    )
    assert record.status == "failed"
    assert record.error_message == "Corrupted file format"

def test_invalid_asset_handling(db_session):
    with pytest.raises(HTTPException) as exc_info:
        media_processing_service.create_or_get_processing_record(
            db=db_session,
            asset_id="00000000-0000-0000-0000-000000000000",
            media_type="image",
        )
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()
