import os
from pathlib import Path
from typing import Literal, Optional, Tuple
from pydantic import BaseModel
from PIL import Image, UnidentifiedImageError

class MediaTypeDetectionResult(BaseModel):
    asset_id: str
    media_type: Optional[str] = None
    status: Literal["completed", "failed"]
    error_message: Optional[str] = None

# Magic byte signatures
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
WEBM_MAGIC = b"\x1a\x45\xdf\xa3"

def is_webp(header: bytes) -> bool:
    return len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WEBP"

def is_isobmff_video(header: bytes) -> bool:
    """Check for MP4 / MOV / QuickTime container (ftyp box)."""
    if len(header) < 12:
        return False
    # Standard MP4/MOV has 'ftyp' at offset 4
    if header[4:8] == b"ftyp":
        return True
    # QuickTime movies may start with 'moov' or 'wide' or 'mdat'
    if header[4:8] in (b"moov", b"wide", b"mdat"):
        return True
    return False

def is_webm_video(header: bytes) -> bool:
    return header.startswith(WEBM_MAGIC)

def inspect_file_signatures(header: bytes) -> Tuple[Optional[str], Optional[str]]:
    """
    Inspect magic bytes.
    Returns (detected_category, detected_format) where category is 'image' or 'video'.
    """
    if header.startswith(PNG_MAGIC):
        return "image", "png"
    if header.startswith(JPEG_MAGIC):
        return "image", "jpeg"
    if is_webp(header):
        return "image", "webp"
    if is_isobmff_video(header):
        return "video", "mp4"
    if is_webm_video(header):
        return "video", "webm"
    return None, None

def detect_media_type(asset_id: str, file_path: Path) -> MediaTypeDetectionResult:
    """
    Inspects and validates an asset file on disk:
    1. Verifies the file exists and is readable
    2. Reads initial bytes to inspect magic signatures
    3. For images, verifies integrity using Pillow
    4. Returns normalized detection result without throwing unhandled exceptions
    """
    if not file_path.is_file():
        return MediaTypeDetectionResult(
            asset_id=asset_id,
            status="failed",
            error_message=f"File not found or unreadable: {file_path}",
        )

    file_size = file_path.stat().st_size
    if file_size == 0:
        return MediaTypeDetectionResult(
            asset_id=asset_id,
            status="failed",
            error_message="File is empty (0 bytes)",
        )

    try:
        with open(file_path, "rb") as f:
            header = f.read(64)
    except Exception as e:
        return MediaTypeDetectionResult(
            asset_id=asset_id,
            status="failed",
            error_message=f"Failed to read file: {str(e)}",
        )

    category, fmt = inspect_file_signatures(header)

    if category == "image":
        # Deep inspection using Pillow to verify the image is not truncated/corrupt
        try:
            with Image.open(file_path) as img:
                img.verify()
            return MediaTypeDetectionResult(
                asset_id=asset_id,
                media_type="image",
                status="completed",
            )
        except (UnidentifiedImageError, SyntaxError, ValueError, OSError) as e:
            return MediaTypeDetectionResult(
                asset_id=asset_id,
                media_type="image",
                status="failed",
                error_message=f"Corrupt or invalid image: {str(e)}",
            )

    if category == "video":
        return MediaTypeDetectionResult(
            asset_id=asset_id,
            media_type="video",
            status="completed",
        )

    return MediaTypeDetectionResult(
        asset_id=asset_id,
        status="failed",
        error_message="Unsupported or unrecognized media format",
    )

def detect_asset_media(asset) -> MediaTypeDetectionResult:
    from app.services import storage_service
    disk_path = storage_service.get_asset_disk_path(asset.file_path)
    return detect_media_type(asset.id, disk_path)

