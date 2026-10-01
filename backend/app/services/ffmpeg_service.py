import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

class FFmpegNotFoundError(RuntimeError):
    """Raised when ffmpeg or ffprobe executable is not available on the system."""
    pass

class VideoProcessingError(ValueError):
    """Raised when video analysis or frame extraction fails due to invalid/corrupt input."""
    pass

def get_binary_path(name: str) -> Optional[str]:
    """Find the path of a binary looking in PATH and standard locations."""
    # 1. System PATH
    found = shutil.which(name)
    if found:
        return found

    # 2. Common Homebrew and standard locations on macOS/Linux
    common_paths = [
        Path(f"/opt/homebrew/bin/{name}"),
        Path(f"/usr/local/bin/{name}"),
        Path(f"/usr/bin/{name}"),
    ]
    for p in common_paths:
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)

    return None

def is_ffmpeg_available() -> bool:
    """Check if both ffmpeg and ffprobe are installed and executable."""
    return bool(get_binary_path("ffmpeg") and get_binary_path("ffprobe"))

def parse_frame_rate(fps_str: Optional[str]) -> Optional[float]:
    """Parse ffprobe r_frame_rate strings like '30/1' or '30000/1001' into float."""
    if not fps_str or fps_str == "0/0":
        return None
    try:
        if "/" in fps_str:
            num, den = fps_str.split("/", 1)
            den_val = float(den)
            if den_val == 0:
                return None
            return round(float(num) / den_val, 2)
        return round(float(fps_str), 2)
    except (ValueError, ZeroDivisionError):
        return None

def probe_video(file_path: Path) -> Dict[str, Any]:
    """
    Extracts metadata from a video file using ffprobe.
    Returns:
        dict with:
        - width: int
        - height: int
        - duration_ms: int
        - frame_rate: float
        - total_frames: int
        - codec: str
    Raises:
        FileNotFoundError: if video file does not exist
        FFmpegNotFoundError: if ffprobe is not installed
        VideoProcessingError: if file is malformed or not a valid video
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Video file not found: {file_path}")

    ffprobe_bin = get_binary_path("ffprobe")
    if not ffprobe_bin:
        raise FFmpegNotFoundError(
            "ffprobe is not installed or not found on system PATH. Please install FFmpeg."
        )

    cmd = [
        ffprobe_bin,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,nb_frames,codec_name,duration:format=duration",
        "-of", "json",
        str(file_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise VideoProcessingError("Video metadata extraction timed out")
    except Exception as e:
        raise VideoProcessingError(f"Failed to execute ffprobe: {str(e)}")

    if result.returncode != 0:
        raise VideoProcessingError(
            "Failed to probe video: malformed, invalid, or unsupported video file"
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise VideoProcessingError("Failed to parse video metadata output")

    streams = data.get("streams", [])
    if not streams:
        raise VideoProcessingError("No valid video stream found in file")

    video_stream = streams[0]
    width = video_stream.get("width")
    height = video_stream.get("height")
    codec = video_stream.get("codec_name") or "unknown"

    if not width or not height:
        raise VideoProcessingError("Invalid video stream dimensions")

    # Frame rate
    fps = parse_frame_rate(video_stream.get("r_frame_rate")) or 30.0

    # Duration: prefer stream duration, fallback to container format duration
    duration_str = video_stream.get("duration") or data.get("format", {}).get("duration")
    duration_sec = 0.0
    if duration_str:
        try:
            duration_sec = float(duration_str)
        except ValueError:
            duration_sec = 0.0

    duration_ms = int(duration_sec * 1000)

    # Total frames: prefer nb_frames, fallback to duration * fps
    total_frames = None
    nb_frames_str = video_stream.get("nb_frames")
    if nb_frames_str and nb_frames_str.isdigit():
        total_frames = int(nb_frames_str)
    elif duration_sec > 0 and fps:
        total_frames = max(1, int(round(duration_sec * fps)))

    return {
        "width": int(width),
        "height": int(height),
        "duration_ms": duration_ms,
        "frame_rate": float(fps),
        "total_frames": total_frames,
        "codec": str(codec),
    }
