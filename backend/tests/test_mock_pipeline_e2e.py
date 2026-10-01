import io
from pathlib import Path
from PIL import Image
import pytest
from fastapi.testclient import TestClient
from app.adapters.base import ModelRequest
from app.adapters.mock_adapter import MockModelAdapter
from app.models.inference_run import InferenceRun
from app.services.ffmpeg_service import is_ffmpeg_available
from tests.test_video_processor import generate_synthetic_video

def test_mock_adapter_deterministic_marketing_detection():
    """Verify MockModelAdapter detects marketing signals from filenames and formats outputs."""
    adapter = MockModelAdapter(model_key="mock-vision-v1", simulated_latency_ms=10)

    # 1. Nike Creative
    nike_req = ModelRequest(
        image_path="/media/nike_air_max_campaign.png",
        metadata={"filename": "nike_air_max_campaign.png"},
    )
    nike_resp = adapter.run(nike_req)
    assert nike_resp.context.brand == "Nike"
    assert nike_resp.context.product == "Air Max Pro"
    assert nike_resp.context.cta == "Just Do It"
    assert "Nike" in nike_resp.text
    assert nike_resp.latency_ms >= 10
    assert nike_resp.input_tokens > 0
    assert nike_resp.output_tokens > 0
    assert nike_resp.estimated_cost_usd > 0

    # 2. Apple Creative
    apple_req = ModelRequest(
        image_path="/media/apple_iphone_commercial.jpg",
        metadata={"filename": "apple_iphone_commercial.jpg"},
    )
    apple_resp = adapter.run(apple_req)
    assert apple_resp.context.brand == "Apple"
    assert apple_resp.context.product == "iPhone 15 Pro"
    assert apple_resp.context.offer == "Trade in and Save"

    # 3. Samsung Creative
    samsung_req = ModelRequest(
        image_path="/media/samsung_galaxy_showcase.webp",
        metadata={"filename": "samsung_galaxy_showcase.webp"},
    )
    samsung_resp = adapter.run(samsung_req)
    assert samsung_resp.context.brand == "Samsung"
    assert samsung_resp.context.cta == "Pre-Order"

    # 4. Coca-Cola Creative
    coke_req = ModelRequest(
        image_path="/media/coca_cola_summer.png",
        metadata={"filename": "coca_cola_summer.png"},
    )
    coke_resp = adapter.run(coke_req)
    assert coke_resp.context.brand == "Coca-Cola"
    assert coke_resp.context.product == "Zero Sugar"

    # 5. Video Frame Input with Colgate Default
    video_req = ModelRequest(
        frame_paths=["/media/frame_000001.jpg", "/media/frame_000002.jpg", "/media/frame_000003.jpg"],
        metadata={"filename": "colgate_sbw_commercial.mp4", "frame_count": 3},
    )
    video_resp = adapter.run(video_req)
    assert video_resp.context.brand == "Colgate"
    assert "3 frames" in video_resp.text
    assert "3 keyframes" in video_resp.context.summary

@pytest.mark.skipif(not is_ffmpeg_available(), reason="FFmpeg/ffprobe required for video frames")
def test_end_to_end_mock_inference_pipeline(client: TestClient, db_session, tmp_path, monkeypatch):
    """
    End-to-End Test for Feature 26:
    1. Create campaign
    2. Upload image asset
    3. Upload video asset
    4. Process media (image metadata & video frame extraction)
    5. Register & enable mock model
    6. Run campaign inference pipeline
    7. Retrieve inference results via API
    8. Check stored outputs & metrics in SQLite
    """
    # Isolate storage directory for testing
    test_upload_dir = tmp_path / "campaigns"
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.services.storage_service.settings.UPLOAD_DIR", test_upload_dir)
    monkeypatch.setattr("app.services.media_processing_service.settings.UPLOAD_DIR", test_upload_dir)

    # 1. Create Campaign
    camp_res = client.post("/campaigns", json={"name": "AO Gold Colgate SBW Campaign"})
    assert camp_res.status_code == 201
    campaign_id = camp_res.json()["id"]

    # 2. Upload Image Asset
    img_buf = io.BytesIO()
    Image.new("RGB", (640, 480), color="blue").save(img_buf, format="PNG")
    img_res = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("colgate_hero_banner.png", img_buf.getvalue(), "image/png")},
    )
    assert img_res.status_code == 201
    image_asset_id = img_res.json()["id"]

    # 3. Upload Video Asset
    video_file = tmp_path / "colgate_tv_commercial.mp4"
    generate_synthetic_video(video_file, duration_sec=2, width=320, height=240, fps=10)
    with open(video_file, "rb") as vf:
        vid_res = client.post(
            f"/campaigns/{campaign_id}/assets",
            files={"file": ("colgate_tv_commercial.mp4", vf, "video/mp4")},
        )
    assert vid_res.status_code == 201
    video_asset_id = vid_res.json()["id"]

    # 4. Process Media for both assets
    img_proc_res = client.post(f"/assets/{image_asset_id}/process")
    assert img_proc_res.status_code == 200
    assert img_proc_res.json()["status"] == "completed"

    vid_proc_res = client.post(f"/assets/{video_asset_id}/process", json={"sample_fps": 1})
    assert vid_proc_res.status_code == 200
    assert vid_proc_res.json()["status"] == "completed"
    assert vid_proc_res.json()["frames_extracted"] >= 2

    # 5. Register and Enable Mock Model
    model_res = client.post(
        "/models",
        json={
            "name": "Deterministic Mock Multimodal",
            "provider": "mock",
            "model_key": "mock-vision-v1",
            "model_type": "multimodal",
            "enabled": True,
            "configuration_json": {"simulated_latency_ms": 15},
            "pricing_json": {"input_per_million": 0.50, "output_per_million": 1.50},
        },
    )
    assert model_res.status_code == 201
    model_id = model_res.json()["id"]

    # 6. Run Campaign Pipeline: POST /campaigns/{campaign_id}/run
    pipeline_res = client.post(
        f"/campaigns/{campaign_id}/run",
        json={"prompt": "Extract marketing text and core messaging", "max_workers": 2},
    )
    assert pipeline_res.status_code == 200
    pipeline_summary = pipeline_res.json()

    assert pipeline_summary["campaign_id"] == campaign_id
    assert pipeline_summary["assets"] == 2
    assert pipeline_summary["runs_created"] >= 2
    assert pipeline_summary["successful_runs"] >= 2
    assert pipeline_summary["failed_runs"] == 0

    # 7. Retrieve Inference Results
    # For Image Asset
    img_runs_res = client.get(f"/assets/{image_asset_id}/inference-runs")
    assert img_runs_res.status_code == 200
    img_runs = img_runs_res.json()
    assert len(img_runs) >= 1
    latest_img_run = img_runs[0]
    assert latest_img_run["status"] == "completed"
    assert "Colgate" in latest_img_run["text"]
    assert latest_img_run["context"]["brand"] == "Colgate"
    assert latest_img_run["latency_ms"] >= 15
    assert latest_img_run["estimated_cost_usd"] > 0

    # For Video Asset
    vid_runs_res = client.get(f"/assets/{video_asset_id}/inference-runs")
    assert vid_runs_res.status_code == 200
    vid_runs = vid_runs_res.json()
    assert len(vid_runs) >= 1
    latest_vid_run = vid_runs[0]
    assert latest_vid_run["status"] == "completed"
    assert "Video Commercial" in latest_vid_run["text"]
    assert "frames" in latest_vid_run["text"]
    assert latest_vid_run["context"]["brand"] == "Colgate"
    assert latest_vid_run["latency_ms"] >= 15
    assert latest_vid_run["estimated_cost_usd"] > 0

    # Retrieve single inference run directly by ID
    run_id = latest_img_run["id"]
    single_run_res = client.get(f"/inference-runs/{run_id}")
    assert single_run_res.status_code == 200
    assert single_run_res.json()["id"] == run_id

    # 8. Check stored outputs in SQLite database
    db_runs = db_session.query(InferenceRun).filter(InferenceRun.asset_id.in_([image_asset_id, video_asset_id])).all()
    assert len(db_runs) >= 2
    for r in db_runs:
        assert r.status == "completed"
        assert r.response_text is not None and len(r.response_text) > 0
        assert r.context_json is not None
        assert "brand" in r.context_json
        assert "cta" in r.context_json
        assert r.latency_ms is not None and r.latency_ms > 0
        assert r.input_tokens is not None and r.input_tokens > 0
        assert r.output_tokens is not None and r.output_tokens > 0
        assert r.estimated_cost_usd is not None and r.estimated_cost_usd > 0
