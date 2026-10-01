import io
import pytest
from fastapi import HTTPException
from PIL import Image
from app.models.campaign import Campaign
from app.models.asset import Asset
from app.models.model import Model
from app.models.media_processing import MediaProcessing
from app.services import inference_service, media_processing_service
from app.core.config import settings

def test_inference_service_image_success(db_session, tmp_path):
    """Test successful image inference via inference service."""
    campaign = Campaign(name="Image Infer Campaign")
    db_session.add(campaign)
    db_session.commit()

    # Create real image on disk
    assets_dir = settings.UPLOAD_DIR / campaign.id / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    img_path = assets_dir / "test_banner.png"

    img = Image.new("RGB", (200, 100), color="blue")
    img.save(img_path, format="PNG")

    asset = Asset(
        campaign_id=campaign.id,
        filename="test_banner.png",
        file_path=f"data/campaigns/{campaign.id}/assets/test_banner.png",
        media_type="image",
        mime_type="image/png",
        file_size=img_path.stat().st_size,
    )
    db_session.add(asset)

    model = Model(
        name="Mock Vision Model",
        provider="mock",
        model_key="mock-vision-v1",
        enabled=True,
    )
    db_session.add(model)
    db_session.commit()

    run = inference_service.run_asset_inference(
        db=db_session,
        asset_id=asset.id,
        model_id=model.id,
    )

    assert run.status == "completed"
    assert "Colgate" in run.response_text
    assert run.context_json["brand"] == "Colgate"
    assert run.latency_ms is not None
    assert run.input_tokens > 0
    assert run.output_tokens > 0
    assert run.estimated_cost_usd > 0
    assert run.error_message is None

    # Test serialization
    serialized = inference_service.serialize_inference_run(run)
    assert serialized.model_name == "Mock Vision Model"
    assert serialized.provider == "mock"

def test_inference_service_video_success(db_session, tmp_path):
    """Test successful video inference using pre-extracted sampled frames."""
    campaign = Campaign(name="Video Infer Campaign")
    db_session.add(campaign)
    db_session.commit()

    asset = Asset(
        campaign_id=campaign.id,
        filename="promo.mp4",
        file_path=f"data/campaigns/{campaign.id}/assets/promo.mp4",
        media_type="video",
        mime_type="video/mp4",
        file_size=1024,
    )
    db_session.add(asset)
    db_session.commit()

    # Create processed frames directory
    frames_dir = settings.UPLOAD_DIR / campaign.id / "processed" / asset.id / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    (frames_dir / "frame_000001.jpg").write_bytes(b"frame 1")
    (frames_dir / "frame_000002.jpg").write_bytes(b"frame 2")

    processing = MediaProcessing(
        asset_id=asset.id,
        media_type="video",
        status="completed",
        frames_extracted=2,
        frame_directory=f"data/campaigns/{campaign.id}/processed/{asset.id}/frames",
    )
    db_session.add(processing)

    model = Model(
        name="Mock Vision Video",
        provider="mock",
        model_key="mock-vision-v1",
        enabled=True,
    )
    db_session.add(model)
    db_session.commit()

    run = inference_service.run_asset_inference(
        db=db_session,
        asset_id=asset.id,
        model_id=model.id,
    )

    assert run.status == "completed"
    assert "2 frames" in run.response_text
    assert "2 keyframes" in run.context_json["summary"]

def test_inference_service_unprocessed_video_fails(db_session):
    """Running inference on an unprocessed video must raise HTTPException."""
    campaign = Campaign(name="Unprocessed Video Campaign")
    db_session.add(campaign)
    db_session.commit()

    asset = Asset(
        campaign_id=campaign.id,
        filename="raw.mp4",
        file_path="data/raw.mp4",
        media_type="video",
        mime_type="video/mp4",
        file_size=1024,
    )
    model = Model(name="Mock", provider="mock", model_key="mock-v1", enabled=True)
    db_session.add_all([asset, model])
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        inference_service.run_asset_inference(
            db=db_session,
            asset_id=asset.id,
            model_id=model.id,
        )
    assert exc.value.status_code == 400
    assert "Video asset must be processed" in exc.value.detail

def test_inference_service_disabled_model_rejected(db_session):
    """Running inference with a disabled model must raise HTTPException 400."""
    campaign = Campaign(name="Disabled Model Campaign")
    db_session.add(campaign)
    db_session.commit()

    asset = Asset(
        campaign_id=campaign.id,
        filename="img.png",
        file_path="data/img.png",
        media_type="image",
        mime_type="image/png",
        file_size=1024,
    )
    model = Model(
        name="Disabled Model",
        provider="mock",
        model_key="mock-v1",
        enabled=False,
    )
    db_session.add_all([asset, model])
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        inference_service.run_asset_inference(
            db=db_session,
            asset_id=asset.id,
            model_id=model.id,
        )
    assert exc.value.status_code == 400
    assert "is disabled" in exc.value.detail

def test_inference_service_adapter_failure_handling(db_session, tmp_path):
    """When an adapter fails during execution, status is marked 'failed' and error stored."""
    campaign = Campaign(name="Failing Adapter Campaign")
    db_session.add(campaign)
    db_session.commit()

    assets_dir = settings.UPLOAD_DIR / campaign.id / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    img_path = assets_dir / "crash.png"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path, format="PNG")

    asset = Asset(
        campaign_id=campaign.id,
        filename="crash.png",
        file_path=f"data/campaigns/{campaign.id}/assets/crash.png",
        media_type="image",
        mime_type="image/png",
        file_size=img_path.stat().st_size,
    )
    # Configure mock adapter to fail
    model = Model(
        name="Crashing Model",
        provider="mock",
        model_key="mock-crash",
        enabled=True,
        configuration_json={"should_fail": True},
    )
    db_session.add_all([asset, model])
    db_session.commit()

    run = inference_service.run_asset_inference(
        db=db_session,
        asset_id=asset.id,
        model_id=model.id,
    )

    assert run.status == "failed"
    assert "simulated provider failure" in run.error_message
    assert run.completed_at is not None
