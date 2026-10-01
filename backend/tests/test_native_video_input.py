from pathlib import Path
import pytest
from app.adapters.base import ModelAdapter, ModelRequest, ModelResponse
from app.adapters.mock_adapter import MockModelAdapter
from app.adapters.registry import register_adapter
from app.models.campaign import Campaign
from app.models.asset import Asset
from app.models.model import Model
from app.models.media_processing import MediaProcessing
from app.services import inference_service
from app.core.config import settings

def test_image_request_has_image_path():
    """Verify image request specifies image_path and identifies as image media type."""
    req = ModelRequest(image_path="/path/to/creative.png")
    assert req.image_path == "/path/to/creative.png"
    assert req.video_path is None
    assert req.frame_paths is None
    assert req.media_type == "image"

def test_video_request_has_native_video_path():
    """Verify native video request specifies video_path and identifies as video media type."""
    req = ModelRequest(video_path="/path/to/commercial.mp4")
    assert req.video_path == "/path/to/commercial.mp4"
    assert req.image_path is None
    assert req.frame_paths is None
    assert req.media_type == "video"

def test_processed_video_request_has_frame_paths():
    """Verify processed video request specifies frame_paths and identifies as video media type."""
    frames = ["/path/to/frame_000001.jpg", "/path/to/frame_000002.jpg"]
    req = ModelRequest(frame_paths=frames)
    assert req.frame_paths == frames
    assert req.image_path is None
    assert req.video_path is None
    assert req.media_type == "video"

def test_video_request_contains_both_video_path_and_frame_paths():
    """Verify a video request can supply BOTH native video_path and processed frame_paths."""
    frames = ["/path/to/frame_000001.jpg", "/path/to/frame_000002.jpg", "/path/to/frame_000003.jpg"]
    req = ModelRequest(
        video_path="/path/to/source_video.mp4",
        frame_paths=frames,
        metadata={"filename": "source_video.mp4"},
    )
    assert req.video_path == "/path/to/source_video.mp4"
    assert req.frame_paths == frames
    assert len(req.frame_paths) == 3
    assert req.media_type == "video"

def test_mock_adapter_handles_native_video_input():
    """Verify MockModelAdapter produces structured output from native video_path."""
    adapter = MockModelAdapter(model_key="mock-vision-v1")
    req = ModelRequest(
        video_path="/media/nike_tv_spot.mp4",
        metadata={"filename": "nike_tv_spot.mp4"},
    )
    resp = adapter.run(req)
    assert isinstance(resp, ModelResponse)
    assert resp.raw_output["input_type"] == "video"
    assert resp.context.brand == "Nike"
    assert "Nike" in resp.text
    assert resp.context.summary is not None
    assert len(resp.context.summary) > 0

def test_mock_adapter_existing_frame_based_behavior_preserved():
    """Verify existing frame-based video behavior continues working identically."""
    adapter = MockModelAdapter(model_key="mock-vision-v1")
    frames = ["/media/frame_000001.jpg", "/media/frame_000002.jpg"]
    req = ModelRequest(
        video_path="/media/source_video.mp4",
        frame_paths=frames,
    )
    resp = adapter.run(req)
    assert isinstance(resp, ModelResponse)
    assert resp.raw_output["input_type"] == "video"
    # When frames are provided, frame-based count is rendered
    assert "2 frames" in resp.text
    assert "2 keyframes" in resp.context.summary

def test_inference_service_provides_both_video_path_and_frame_paths(db_session, tmp_path):
    """
    Verify run_asset_inference supplies BOTH source video_path and processed frame_paths
    to the adapter for video assets.
    """
    campaign = Campaign(name="Dual Video Input Campaign")
    db_session.add(campaign)
    db_session.commit()

    # Create real source video file on disk
    assets_dir = settings.UPLOAD_DIR / campaign.id / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    video_disk_file = assets_dir / "campaign_commercial.mp4"
    video_disk_file.write_bytes(b"dummy mp4 source video content")

    asset = Asset(
        campaign_id=campaign.id,
        filename="campaign_commercial.mp4",
        file_path=f"data/campaigns/{campaign.id}/assets/campaign_commercial.mp4",
        media_type="video",
        mime_type="video/mp4",
        file_size=video_disk_file.stat().st_size,
    )
    db_session.add(asset)
    db_session.commit()

    # Create processed keyframes on disk
    frames_dir = settings.UPLOAD_DIR / campaign.id / "processed" / asset.id / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    f1 = frames_dir / "frame_000001.jpg"
    f2 = frames_dir / "frame_000002.jpg"
    f1.write_bytes(b"frame 1 jpeg")
    f2.write_bytes(b"frame 2 jpeg")

    processing = MediaProcessing(
        asset_id=asset.id,
        media_type="video",
        status="completed",
        frames_extracted=2,
        frame_directory=f"data/campaigns/{campaign.id}/processed/{asset.id}/frames",
    )
    db_session.add(processing)

    # Register an intercepting adapter that verifies the request fields
    captured_requests = []

    class InspectingAdapter(ModelAdapter):
        def run(self, request: ModelRequest) -> ModelResponse:
            captured_requests.append(request)
            return ModelResponse(
                text="Inspecting adapter response",
                raw_output={"captured_video_path": request.video_path},
            )

    register_adapter("inspecting_provider", lambda key, cfg: InspectingAdapter())

    model = Model(
        name="Inspecting Multimodal Model",
        provider="inspecting_provider",
        model_key="inspector-v1",
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
    assert len(captured_requests) == 1
    req = captured_requests[0]

    # Verify BOTH video_path and frame_paths are provided
    assert req.video_path is not None
    assert req.video_path.endswith("campaign_commercial.mp4")
    assert Path(req.video_path).is_file()

    assert req.frame_paths is not None
    assert len(req.frame_paths) == 2
    for fp in req.frame_paths:
        assert Path(fp).is_file()

    assert req.media_type == "video"
