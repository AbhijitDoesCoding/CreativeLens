import os
import shutil
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.models.asset import Asset
from app.models.media_processing import MediaProcessing
from app.services import ffmpeg_service, media_processing_service

def test_process_zero_byte_image(client: TestClient, db_session, tmp_path):
    """Zero-byte image should fail processing and record clear error without crashing."""
    camp_resp = client.post("/campaigns", json={"name": "Zero Byte Image Test"})
    campaign_id = camp_resp.json()["id"]

    # Upload empty file pretending to be png
    upload_resp = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert upload_resp.status_code == 201
    asset_id = upload_resp.json()["id"]

    # Trigger processing
    proc_resp = client.post(f"/assets/{asset_id}/process")
    assert proc_resp.status_code == 200
    data = proc_resp.json()
    assert data["status"] == "failed"
    assert "empty (0 bytes)" in data["error_message"]

def test_process_corrupt_or_unsupported_image(client: TestClient, db_session):
    """Text file pretending to be an image should fail processing with clear error."""
    camp_resp = client.post("/campaigns", json={"name": "Corrupt Image Test"})
    campaign_id = camp_resp.json()["id"]

    fake_png = b"This is not a PNG file header, just text content pretending to be image."
    upload_resp = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("fake_image.png", fake_png, "image/png")},
    )
    assert upload_resp.status_code == 201
    asset_id = upload_resp.json()["id"]

    proc_resp = client.post(f"/assets/{asset_id}/process")
    assert proc_resp.status_code == 200
    data = proc_resp.json()
    assert data["status"] == "failed"
    assert "Corrupt or invalid image file" in data["error_message"]

def test_process_zero_byte_video(client: TestClient, db_session):
    """Zero-byte video should fail processing and record clear error."""
    camp_resp = client.post("/campaigns", json={"name": "Zero Byte Video Test"})
    campaign_id = camp_resp.json()["id"]

    upload_resp = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("empty.mp4", b"", "video/mp4")},
    )
    assert upload_resp.status_code == 201
    asset_id = upload_resp.json()["id"]

    proc_resp = client.post(f"/assets/{asset_id}/process")
    assert proc_resp.status_code == 200
    data = proc_resp.json()
    assert data["status"] == "failed"
    assert "empty (0 bytes)" in data["error_message"]

def test_process_corrupt_or_unsupported_video(client: TestClient, db_session):
    """Text file pretending to be a video should fail processing gracefully."""
    camp_resp = client.post("/campaigns", json={"name": "Fake Video Test"})
    campaign_id = camp_resp.json()["id"]

    fake_video = b"Not an mp4 container, just garbage bytes."
    upload_resp = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("corrupt.mp4", fake_video, "video/mp4")},
    )
    assert upload_resp.status_code == 201
    asset_id = upload_resp.json()["id"]

    proc_resp = client.post(f"/assets/{asset_id}/process")
    assert proc_resp.status_code == 200
    data = proc_resp.json()
    assert data["status"] == "failed"
    assert data["error_message"] is not None

def test_process_missing_source_file_on_disk(client: TestClient, db_session):
    """If asset file is deleted from disk, processing marks failed and records error."""
    camp_resp = client.post("/campaigns", json={"name": "Missing File Test"})
    campaign_id = camp_resp.json()["id"]

    fake_png = b"some content"
    upload_resp = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("temp.png", fake_png, "image/png")},
    )
    asset_id = upload_resp.json()["id"]
    file_path = upload_resp.json()["file_path"]

    # Delete the underlying file
    from app.services.storage_service import get_asset_disk_path
    disk_path = get_asset_disk_path(file_path)
    if disk_path.is_file():
        disk_path.unlink()

    proc_resp = client.post(f"/assets/{asset_id}/process")
    assert proc_resp.status_code == 200
    data = proc_resp.json()
    assert data["status"] == "failed"
    assert "Media file not found on disk" in data["error_message"]

def test_process_missing_ffmpeg_handling(client: TestClient, db_session):
    """When FFmpeg is missing, processing fails with user-friendly FFmpeg message."""
    camp_resp = client.post("/campaigns", json={"name": "Missing FFmpeg Test"})
    campaign_id = camp_resp.json()["id"]

    upload_resp = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("dummy.mp4", b"dummy video content", "video/mp4")},
    )
    asset_id = upload_resp.json()["id"]

    with patch("app.services.ffmpeg_service.get_binary_path", return_value=None):
        proc_resp = client.post(f"/assets/{asset_id}/process")
        assert proc_resp.status_code == 200
        data = proc_resp.json()
        assert data["status"] == "failed"
        assert "not installed or not found on system PATH" in data["error_message"]

def test_invalid_sample_fps_ranges(client: TestClient, db_session):
    """Negative, 0, or excessive sample_fps values are rejected."""
    camp_resp = client.post("/campaigns", json={"name": "Invalid FPS Test"})
    campaign_id = camp_resp.json()["id"]

    upload_resp = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("test.mp4", b"dummy content", "video/mp4")},
    )
    asset_id = upload_resp.json()["id"]

    # Negative FPS
    res1 = client.post(f"/assets/{asset_id}/process", json={"sample_fps": -1.0})
    assert res1.status_code == 422

    # Zero FPS
    res2 = client.post(f"/assets/{asset_id}/process", json={"sample_fps": 0})
    assert res2.status_code == 422

    # Absurdly high FPS (> 60)
    res3 = client.post(f"/assets/{asset_id}/process", json={"sample_fps": 120})
    assert res3.status_code == 422

def test_video_partial_artifact_cleanup_on_failure(client: TestClient, db_session, tmp_path):
    """When frame extraction encounters an error, partial frame files are deleted."""
    camp_resp = client.post("/campaigns", json={"name": "Cleanup Test"})
    campaign_id = camp_resp.json()["id"]

    upload_resp = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("test_clean.mp4", b"dummy video bytes", "video/mp4")},
    )
    asset_id = upload_resp.json()["id"]

    # Mock probe_video to succeed, but extract_video_frames to simulate failure after creating a partial file
    def fail_with_partial_frames(video_path, output_dir, sample_fps=1.0):
        output_dir.mkdir(parents=True, exist_ok=True)
        # Create a partial dummy frame
        (output_dir / "frame_000001.jpg").write_bytes(b"partial image data")
        raise ffmpeg_service.VideoProcessingError("Simulated frame extraction crash")

    with patch("app.services.ffmpeg_service.probe_video", return_value={
        "width": 1920,
        "height": 1080,
        "duration_ms": 5000,
        "frame_rate": 30.0,
        "total_frames": 150,
        "codec": "h264",
    }):
        with patch("app.services.ffmpeg_service.extract_video_frames", side_effect=fail_with_partial_frames):
            proc_resp = client.post(f"/assets/{asset_id}/process")
            assert proc_resp.status_code == 200
            data = proc_resp.json()
            assert data["status"] == "failed"
            assert "Simulated frame extraction crash" in data["error_message"]

    # Verify that the frames directory and partial files were cleaned up
    from app.core.config import settings
    frames_dir = settings.UPLOAD_DIR / campaign_id / "processed" / asset_id / "frames"
    assert not frames_dir.exists()

def test_duplicate_processing_idempotency(client: TestClient, db_session):
    """Re-requesting processing on an already-completed asset is idempotent unless force=True."""
    camp_resp = client.post("/campaigns", json={"name": "Duplicate Test"})
    campaign_id = camp_resp.json()["id"]

    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="blue").save(buf, format="PNG")
    buf.seek(0)

    upload_resp = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("box.png", buf.getvalue(), "image/png")},
    )
    asset_id = upload_resp.json()["id"]

    # First process call
    res1 = client.post(f"/assets/{asset_id}/process")
    assert res1.status_code == 200
    assert res1.json()["status"] == "completed"
    processed_at_1 = res1.json()["processed_at"]

    # Second call without force -> returns existing record without re-processing
    res2 = client.post(f"/assets/{asset_id}/process", json={"force": False})
    assert res2.status_code == 200
    assert res2.json()["processed_at"] == processed_at_1

    # Third call with force=True -> re-processes
    res3 = client.post(f"/assets/{asset_id}/process", json={"force": True})
    assert res3.status_code == 200
    assert res3.json()["status"] == "completed"
