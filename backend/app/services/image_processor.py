from pathlib import Path
from typing import Any, Dict
from PIL import Image, UnidentifiedImageError

def process_image(file_path: Path) -> Dict[str, Any]:
    """
    Loads, validates, and extracts metadata from an image file using Pillow.
    Returns:
        dict containing:
        - width: int
        - height: int
        - format: str
        - color_mode: str
        - file_size: int
    Raises:
        FileNotFoundError: if the file does not exist
        ValueError: if image is invalid, corrupt, or empty
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Image file not found: {file_path}")

    file_size = file_path.stat().st_size
    if file_size == 0:
        raise ValueError("Image file is empty (0 bytes)")

    try:
        # Verify file structure and integrity
        with Image.open(file_path) as img:
            img.verify()

        # Re-open after verify() to inspect properties safely (Pillow requirement)
        with Image.open(file_path) as img:
            width, height = img.size
            img_format = img.format or "UNKNOWN"
            color_mode = img.mode

        return {
            "width": width,
            "height": height,
            "format": img_format,
            "color_mode": color_mode,
            "file_size": file_size,
        }
    except Exception as e:
        raise ValueError(f"Corrupt or invalid image file: {str(e)}")
