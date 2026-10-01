import pytest
from pathlib import Path
from app.core.config import settings
from app.services import ffmpeg_service
from app.services.ffmpeg_service import is_ffmpeg_available
from tests.test_video_processor import generate_synthetic_video

@pytest.mark.skipif(not is_ffmpeg_available(), reason="FFmpeg/ffprobe not installed")
def test_frame_extraction_default_rate(client, tmp_path, monkeypatch):
    test_upload_dir = tmp_path / "campaigns"
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.services.storage_service.settings.UPLOAD_DIR", test_upload_dir)
    monkeypatch.setattr("app.services.media_processing_service.settings.UPLOAD_DIR", test_upload_dir)

    camp_res = client.post("/campaigns", json={"name": "Frame Extraction Campaign"})
    campaign_id = camp_res.json()["id"]

    video_path = tmp_path / "test_video.mp4"
    generate_synthetic_video(video_path, duration_sec=3, width=320, height=240, fps=10)

    with open(video_path, "rb") as f:
        up_res = client.post(
            f"/campaigns/{campaign_id}/assets",
            files={"file": ("test_video.mp4", f, "video/mp4")},
        )
    assert up_res.status_code == 201
    asset_id = up_res.json()["id"]

    # Process with default sample_fps = 1
    proc_res = client.post(f"/assets/{asset_id}/process")
    assert proc_res.status_code == 200
    data = proc_res.json()
    assert data["status"] == "completed"
    assert data["media_type"] == "video"
    assert data["frames_extracted"] >= 3
    assert f"data/campaigns/{campaign_id}/processed/{asset_id}/frames" in data["frame_directory"]

    # Verify generated files on disk
    frames_dir = test_upload_dir / campaign_id / "processed" / asset_id / "frames"
    assert frames_dir.is_dir()
    frame_files = sorted(list(frames_dir.glob("frame_*.jpg")))
    assert len(frame_files) == data["frames_extracted"]
    for f in frame_files:
        assert f.stat().st_size > 0

@pytest.mark.skipif(not is_ffmpeg_available(), reason="FFmpeg/ffprobe not installed")
def test_frame_extraction_custom_sample_rate(client, tmp_path, monkeypatch):
    test_upload_dir = tmp_path / "campaigns"
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.services.storage_service.settings.UPLOAD_DIR", test_upload_dir)
    monkeypatch.setattr("app.services.media_processing_service.settings.UPLOAD_DIR", test_upload_dir)

    camp_res = client.post("/campaigns", json={"name": "Sample Rate Campaign"})
    campaign_id = camp_res.json()["id"]

    video_path = tmp_path / "short_clip.mp4"
    generate_synthetic_video(video_path, duration_sec=2, width=320, height=240, fps=10)

    with open(video_path, "rb") as f:
        up_res = client.post(
            f"/campaigns/{campaign_id}/assets",
            files={"file": ("short_clip.mp4", f, "video/mp4")},
        )
    assert up_res.status_code == 201
    asset_id = up_res.json()["id"]

    # Process with sample_fps = 2 (approx 4 frames for 2s)
    proc_res = client.post(f"/assets/{asset_id}/process", json={"sample_fps": 2})
    assert proc_res.status_code == 200
    data = proc_res.json()
    assert data["status"] == "completed"
    assert data["frames_extracted"] >= 4

    frames_dir = test_upload_dir / campaign_id / "processed" / asset_id / "frames"
    frame_files = sorted(list(frames_dir.glob("frame_*.jpg")))
    assert len(frame_files) >= 4

def test_invalid_sample_rate(client):
    camp_res = client.post("/campaigns", json={"name": "Invalid Rate Campaign"})
    campaign_id = camp_res.json()["id"]

    # Upload empty dummy file with .mp4 to get an asset_id
    up_res = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("test.mp4", b"\x00\x00\x00\x18ftypisom", "video/mp4")},
    )
    asset_id = up_res.json()["id"]

    # Test sample_fps <= 0
    res_zero = client.post(f"/assets/{asset_id}/process", json={"sample_fps": 0})
    assert res_zero.status_code in (400, 422)

    res_negative = client.post(f"/assets/{asset_id}/process", json={"sample_fps": -5})
    assert res_negative.status_code in (400, 422)

    # Test excessive sample_fps > 60
    res_huge = client.post(f"/assets/{asset_id}/process", json={"sample_fps": 1000})
    assert res_huge.status_code in (400, 422)

def test_failed_ffmpeg_processing(client):
    camp_res = client.post("/campaigns", json={"name": "Failed Video Campaign"})
    campaign_id = camp_res.json()["id"]

    # Corrupt video file
    corrupt_bytes = b"\x00\x00\x00\x18ftypisomGARBAGE_PAYLOAD"
    up_res = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("corrupt.mp4", corrupt_bytes, "video/mp4")},
    )
    assert up_res.status_code == 201
    asset_id = up_res.json()["id"]

    proc_res = client.post(f"/assets/{asset_id}/process")
    assert proc_res.status_code == 200
    data = proc_res.json()
    assert data["status"] == "failed"
    assert data["error_message"] is not None
