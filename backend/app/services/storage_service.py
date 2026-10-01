import os
import re
from pathlib import Path
from typing import Optional, Tuple
from fastapi import HTTPException, UploadFile, status
from app.core.config import settings

ALLOWED_EXTENSIONS = {
    ".jpg": ("image", "image/jpeg"),
    ".jpeg": ("image", "image/jpeg"),
    ".png": ("image", "image/png"),
    ".webp": ("image", "image/webp"),
    ".mp4": ("video", "video/mp4"),
    ".mov": ("video", "video/quicktime"),
    ".webm": ("video", "video/webm"),
}

def sanitize_filename(filename: str) -> str:
    """Sanitize the original filename to prevent directory traversal or invalid characters."""
    base_name = os.path.basename(filename)
    clean_name = base_name.replace("\x00", "").replace("/", "").replace("\\", "")
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", clean_name)
    if not safe_name or safe_name.startswith("."):
        safe_name = f"upload{safe_name}"
    return safe_name

def validate_and_classify_file(filename: str, content_type: Optional[str] = None) -> Tuple[str, str, str]:
    """Validate extension and determine media_type and mime_type."""
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS.keys()))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Supported file types: {allowed}",
        )

    media_type, default_mime = ALLOWED_EXTENSIONS[ext]
    mime_type = content_type if (content_type and "/" in content_type) else default_mime
    return ext, media_type, mime_type

def save_uploaded_file(
    upload_file: UploadFile,
    campaign_id: str,
    asset_id: str,
) -> Tuple[str, str, str, str, int]:
    """
    Saves an uploaded file to the local filesystem.
    Returns: (safe_filename, relative_file_path, media_type, mime_type, file_size)
    """
    original_filename = upload_file.filename or "file"
    _, media_type, mime_type = validate_and_classify_file(
        original_filename, upload_file.content_type
    )
    safe_filename = sanitize_filename(original_filename)

    campaign_assets_dir = settings.UPLOAD_DIR / campaign_id / "assets"
    campaign_assets_dir.mkdir(parents=True, exist_ok=True)

    dest_filename = f"{asset_id}_{safe_filename}"
    dest_path = campaign_assets_dir / dest_filename

    file_size = 0
    with open(dest_path, "wb") as f:
        while chunk := upload_file.file.read(1024 * 1024):  # 1MB buffer
            f.write(chunk)
            file_size += len(chunk)

    rel_path = f"data/campaigns/{campaign_id}/assets/{dest_filename}"
    return safe_filename, rel_path, media_type, mime_type, file_size
