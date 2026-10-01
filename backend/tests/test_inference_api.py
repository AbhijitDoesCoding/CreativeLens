import io
from PIL import Image
from fastapi.testclient import TestClient
from app.core.config import settings
from app.models.media_processing import MediaProcessing

def test_infer_image_api_success(client: TestClient, db_session):
    """Test successful image inference via POST /assets/{asset_id}/infer/{model_id}."""
    # 1. Create campaign
    camp_resp = client.post("/campaigns", json={"name": "Inference API Campaign"})
    campaign_id = camp_resp.json()["id"]

    # 2. Upload image asset
    img_buf = io.BytesIO()
    Image.new("RGB", (300, 200), color="green").save(img_buf, format="PNG")
    upload_resp = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("creative.png", img_buf.getvalue(), "image/png")},
    )
    asset_id = upload_resp.json()["id"]

    # 3. Create enabled model
    model_resp = client.post(
        "/models",
        json={
            "name": "Mock Multimodal Model",
            "provider": "mock",
            "model_key": "mock-vision-v1",
            "enabled": True,
            "pricing_json": {"input_per_million": 0.50, "output_per_million": 1.50},
        },
    )
    model_id = model_resp.json()["id"]

    # 4. Execute inference
    infer_resp = client.post(
        f"/assets/{asset_id}/infer/{model_id}",
        json={"prompt": "Extract all text and brand context"},
    )
    assert infer_resp.status_code == 200
    data = infer_resp.json()

    assert data["status"] == "completed"
    assert "text" in data
    assert "context" in data
    assert data["context"]["brand"] == "Colgate"
    assert data["latency_ms"] is not None
    assert data["input_tokens"] > 0
    assert data["output_tokens"] > 0
    assert data["estimated_cost_usd"] is not None
    assert data["model_name"] == "Mock Multimodal Model"
    assert data["model_key"] == "mock-vision-v1"

    run_id = data["id"]

    # 5. Fetch single run via GET /inference-runs/{run_id}
    get_run_resp = client.get(f"/inference-runs/{run_id}")
    assert get_run_resp.status_code == 200
    assert get_run_resp.json()["id"] == run_id
    assert get_run_resp.json()["status"] == "completed"

    # 6. Fetch asset runs via GET /assets/{asset_id}/inference-runs
    asset_runs_resp = client.get(f"/assets/{asset_id}/inference-runs")
    assert asset_runs_resp.status_code == 200
    runs = asset_runs_resp.json()
    assert len(runs) >= 1
    assert runs[0]["id"] == run_id

def test_infer_video_api_success(client: TestClient, db_session):
    """Test successful video inference using pre-extracted frames."""
    camp_resp = client.post("/campaigns", json={"name": "Video API Campaign"})
    campaign_id = camp_resp.json()["id"]

    upload_resp = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("video_ad.mp4", b"dummy video bytes", "video/mp4")},
    )
    asset_id = upload_resp.json()["id"]

    # Create processed frames
    frames_dir = settings.UPLOAD_DIR / campaign_id / "processed" / asset_id / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    (frames_dir / "frame_000001.jpg").write_bytes(b"frame 1")
    (frames_dir / "frame_000002.jpg").write_bytes(b"frame 2")

    processing = MediaProcessing(
        asset_id=asset_id,
        media_type="video",
        status="completed",
        frames_extracted=2,
        frame_directory=f"data/campaigns/{campaign_id}/processed/{asset_id}/frames",
    )
    db_session.add(processing)
    db_session.commit()

    model_resp = client.post(
        "/models",
        json={"name": "Mock Video Model", "provider": "mock", "model_key": "mock-v1", "enabled": True},
    )
    model_id = model_resp.json()["id"]

    infer_resp = client.post(f"/assets/{asset_id}/infer/{model_id}")
    assert infer_resp.status_code == 200
    data = infer_resp.json()
    assert data["status"] == "completed"
    assert "2 frames" in data["text"]

def test_infer_disabled_model_rejected(client: TestClient):
    """Attempting inference with disabled model returns 400 Bad Request."""
    camp_resp = client.post("/campaigns", json={"name": "Disabled Test"})
    campaign_id = camp_resp.json()["id"]

    upload_resp = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("test.png", b"dummy image bytes", "image/png")},
    )
    asset_id = upload_resp.json()["id"]

    model_resp = client.post(
        "/models",
        json={"name": "Disabled Model", "provider": "mock", "model_key": "m1", "enabled": False},
    )
    model_id = model_resp.json()["id"]

    infer_resp = client.post(f"/assets/{asset_id}/infer/{model_id}")
    assert infer_resp.status_code == 400
    assert "is disabled" in infer_resp.json()["detail"]

def test_infer_missing_resources_404(client: TestClient):
    """Missing asset or missing model returns 404."""
    # Missing asset
    res1 = client.post("/assets/nonexistent-asset/infer/some-model")
    assert res1.status_code == 404

    # Valid asset, missing model
    camp_resp = client.post("/campaigns", json={"name": "Missing Model Test"})
    campaign_id = camp_resp.json()["id"]
    upload_resp = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("test.png", b"dummy image bytes", "image/png")},
    )
    asset_id = upload_resp.json()["id"]

    res2 = client.post(f"/assets/{asset_id}/infer/nonexistent-model")
    assert res2.status_code == 404

def test_infer_unprocessed_video_rejected(client: TestClient):
    """Attempting inference on unprocessed video returns 400."""
    camp_resp = client.post("/campaigns", json={"name": "Unprocessed Video"})
    campaign_id = camp_resp.json()["id"]
    upload_resp = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("raw.mp4", b"dummy video bytes", "video/mp4")},
    )
    asset_id = upload_resp.json()["id"]

    model_resp = client.post(
        "/models",
        json={"name": "Enabled Model", "provider": "mock", "model_key": "m2", "enabled": True},
    )
    model_id = model_resp.json()["id"]

    infer_resp = client.post(f"/assets/{asset_id}/infer/{model_id}")
    assert infer_resp.status_code == 400
    assert "Video asset must be processed" in infer_resp.json()["detail"]

def test_infer_adapter_failure_persists_failed_status(client: TestClient):
    """Adapter failure is recorded as status 'failed' and error stored cleanly."""
    camp_resp = client.post("/campaigns", json={"name": "Crash Campaign"})
    campaign_id = camp_resp.json()["id"]

    img_buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="yellow").save(img_buf, format="PNG")
    upload_resp = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("crash.png", img_buf.getvalue(), "image/png")},
    )
    asset_id = upload_resp.json()["id"]

    model_resp = client.post(
        "/models",
        json={
            "name": "Crashing Model",
            "provider": "mock",
            "model_key": "mock-crash",
            "enabled": True,
            "configuration_json": {"should_fail": True},
        },
    )
    model_id = model_resp.json()["id"]

    infer_resp = client.post(f"/assets/{asset_id}/infer/{model_id}")
    assert infer_resp.status_code == 200
    data = infer_resp.json()
    assert data["status"] == "failed"
    assert "simulated provider failure" in data["error_message"]
    assert data["latency_ms"] is not None

def test_get_nonexistent_inference_run(client: TestClient):
    """GET /inference-runs/{run_id} returns 404 for unknown ID."""
    res = client.get("/inference-runs/unknown-run-id-999")
    assert res.status_code == 404
