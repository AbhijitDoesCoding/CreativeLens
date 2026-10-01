import subprocess
import pytest
from pathlib import Path
from app.services import ffmpeg_service
from app.services.ffmpeg_service import (
    FFmpegNotFoundError,
    VideoProcessingError,
    get_binary_path,
    is_ffmpeg_available,
    parse_frame_rate,
    probe_video,
)

def test_parse_frame_rate():
    assert parse_frame_rate("30/1") == 30.0
    assert parse_frame_rate("24000/1001") == 23.98
    assert parse_frame_rate("25") == 25.0
    assert parse_frame_rate("0/0") is None
    assert parse_frame_rate(None) is None
    assert parse_frame_rate("invalid") is None

def test_ffmpeg_available_returns_bool():
    available = is_ffmpeg_available()
    assert isinstance(available, bool)

def generate_synthetic_video(output_path: Path, duration_sec: int = 1, width: int = 320, height: int = 240, fps: int = 10):
    ffmpeg_bin = get_binary_path("ffmpeg")
    assert ffmpeg_bin is not None, "ffmpeg must be available to generate synthetic video"
    cmd = [
        ffmpeg_bin,
        "-y",
        "-f", "lavfi",
        "-i", f"testsrc=duration={duration_sec}:size={width}x{height}:rate={fps}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0, f"ffmpeg failed: {res.stderr}"

@pytest.mark.skipif(not is_ffmpeg_available(), reason="FFmpeg/ffprobe not installed")
def test_probe_valid_video(tmp_path):
    video_path = tmp_path / "synthetic_test.mp4"
    generate_synthetic_video(video_path, duration_sec=1, width=320, height=240, fps=10)

    meta = probe_video(video_path)
    assert meta["width"] == 320
    assert meta["height"] == 240
    assert meta["frame_rate"] == 10.0
    assert meta["duration_ms"] >= 900
    assert meta["codec"] == "h264"
    assert meta["total_frames"] in (10, None) or meta["total_frames"] >= 9

@pytest.mark.skipif(not is_ffmpeg_available(), reason="FFmpeg/ffprobe not installed")
def test_process_video_endpoint(client, tmp_path):
    camp_res = client.post("/campaigns", json={"name": "Video Processing Test"})
    campaign_id = camp_res.json()["id"]

    video_path = tmp_path / "sample_promo.mp4"
    generate_synthetic_video(video_path, duration_sec=2, width=640, height=360, fps=15)

    with open(video_path, "rb") as f:
        up_res = client.post(
            f"/campaigns/{campaign_id}/assets",
            files={"file": ("sample_promo.mp4", f, "video/mp4")},
        )
    assert up_res.status_code == 201
    asset_id = up_res.json()["id"]

    # Process the video
    proc_res = client.post(f"/assets/{asset_id}/process")
    assert proc_res.status_code == 200
    data = proc_res.json()
    assert data["asset_id"] == asset_id
    assert data["media_type"] == "video"
    assert data["status"] == "completed"
    assert data["width"] == 640
    assert data["height"] == 360
    assert data["frame_rate"] == 15.0
    assert data["duration_ms"] >= 1900
    assert data["format"] == "h264"
    assert data["processed_at"] is not None

def test_probe_malformed_video(tmp_path):
    corrupt_video = tmp_path / "corrupt_video.mp4"
    corrupt_video.write_bytes(b"\x00\x00\x00\x18ftypisomNOT_A_VALID_VIDEO_BODY")

    if is_ffmpeg_available():
        with pytest.raises(VideoProcessingError):
            probe_video(corrupt_video)

def test_probe_missing_video():
    with pytest.raises(FileNotFoundError):
        probe_video(Path("/tmp/this_file_definitely_does_not_exist_12345.mp4"))

def test_ffmpeg_missing_error(monkeypatch, tmp_path):
    monkeypatch.setattr(ffmpeg_service, "get_binary_path", lambda name: None)
    dummy_video = tmp_path / "dummy.mp4"
    dummy_video.write_bytes(b"content")

    with pytest.raises(FFmpegNotFoundError):
        probe_video(dummy_video)
