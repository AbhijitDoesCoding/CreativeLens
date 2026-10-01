import io
import pytest
from PIL import Image
from app.services.ffmpeg_service import is_ffmpeg_available
from tests.test_video_processor import generate_synthetic_video

def test_get_processing_unprocessed_asset(client):
    camp_res = client.post("/campaigns", json={"name": "API Test Campaign"})
    campaign_id = camp_res.json()["id"]

    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    up_res = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("blue.png", buf, "image/png")},
    )
    asset_id = up_res.json()["id"]

    # Before processing, GET /assets/{asset_id}/processing should return 404
    proc_res = client.get(f"/assets/{asset_id}/processing")
    assert proc_res.status_code == 404
    assert "processing record" in proc_res.json()["detail"].lower()

def test_get_processing_missing_asset(client):
    res = client.get("/assets/00000000-0000-0000-0000-000000000000/processing")
    assert res.status_code == 404
    assert "asset with id" in res.json()["detail"].lower()

def test_process_image_and_get_processing(client):
    camp_res = client.post("/campaigns", json={"name": "Image Flow Campaign"})
    campaign_id = camp_res.json()["id"]

    img = Image.new("RGB", (640, 480), color="green")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    up_res = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("green.png", buf, "image/png")},
    )
    asset_id = up_res.json()["id"]

    # Process image
    post_res = client.post(f"/assets/{asset_id}/process")
    assert post_res.status_code == 200
    post_data = post_res.json()
    assert post_data["status"] == "completed"
    assert post_data["width"] == 640
    assert post_data["height"] == 480

    # Retrieve status via GET /assets/{asset_id}/processing
    get_res = client.get(f"/assets/{asset_id}/processing")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["id"] == post_data["id"]
    assert get_data["status"] == "completed"
    assert get_data["width"] == 640
    assert get_data["height"] == 480
    assert get_data["format"] == "PNG"

def test_process_idempotency(client):
    camp_res = client.post("/campaigns", json={"name": "Idempotency Campaign"})
    campaign_id = camp_res.json()["id"]

    img = Image.new("RGB", (200, 200), color="purple")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    up_res = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("purple.png", buf, "image/png")},
    )
    asset_id = up_res.json()["id"]

    first_res = client.post(f"/assets/{asset_id}/process")
    assert first_res.status_code == 200
    first_data = first_res.json()
    assert first_data["status"] == "completed"

    # Second call without force should return the existing record
    second_res = client.post(f"/assets/{asset_id}/process", json={"force": False})
    assert second_res.status_code == 200
    second_data = second_res.json()
    assert second_data["id"] == first_data["id"]
    assert second_data["processed_at"] == first_data["processed_at"]

@pytest.mark.skipif(not is_ffmpeg_available(), reason="FFmpeg/ffprobe not installed")
def test_process_video_and_get_frames(client, tmp_path, monkeypatch):
    test_upload_dir = tmp_path / "campaigns"
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.services.storage_service.settings.UPLOAD_DIR", test_upload_dir)
    monkeypatch.setattr("app.services.media_processing_service.settings.UPLOAD_DIR", test_upload_dir)

    camp_res = client.post("/campaigns", json={"name": "Video API Test"})
    campaign_id = camp_res.json()["id"]

    video_path = tmp_path / "demo_video.mp4"
    generate_synthetic_video(video_path, duration_sec=2, width=320, height=240, fps=10)

    with open(video_path, "rb") as f:
        up_res = client.post(
            f"/campaigns/{campaign_id}/assets",
            files={"file": ("demo_video.mp4", f, "video/mp4")},
        )
    assert up_res.status_code == 201
    asset_id = up_res.json()["id"]

    # Process video
    proc_res = client.post(f"/assets/{asset_id}/process", json={"sample_fps": 1})
    assert proc_res.status_code == 200
    proc_data = proc_res.json()
    assert proc_data["status"] == "completed"
    assert proc_data["frames_extracted"] >= 2

    # Query frames endpoint
    frames_res = client.get(f"/assets/{asset_id}/frames")
    assert frames_res.status_code == 200
    frames_data = frames_res.json()
    assert frames_data["asset_id"] == asset_id
    assert frames_data["total_frames"] == proc_data["frames_extracted"]
    assert len(frames_data["frames"]) == proc_data["frames_extracted"]

    first_frame = frames_data["frames"][0]
    assert first_frame["filename"] == "frame_000001.jpg"
    assert first_frame["url"] == f"/assets/{asset_id}/frames/frame_000001.jpg"

    # Fetch frame image file
    file_res = client.get(f"/assets/{asset_id}/frames/{first_frame['filename']}")
    assert file_res.status_code == 200
    assert file_res.headers["content-type"].startswith("image/jpeg")
    assert len(file_res.content) > 0

def test_get_frames_image_asset(client):
    camp_res = client.post("/campaigns", json={"name": "Frames for Image"})
    campaign_id = camp_res.json()["id"]

    img = Image.new("RGB", (50, 50), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    up_res = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("white.png", buf, "image/png")},
    )
    asset_id = up_res.json()["id"]

    client.post(f"/assets/{asset_id}/process")

    frames_res = client.get(f"/assets/{asset_id}/frames")
    assert frames_res.status_code == 200
    data = frames_res.json()
    assert data["total_frames"] == 0
    assert data["frames"] == []

def test_get_frames_missing_asset(client):
    res = client.get("/assets/00000000-0000-0000-0000-000000000000/frames")
    assert res.status_code == 404
