from pathlib import Path
from PIL import Image
from app.services.media_detector import detect_media_type, detect_asset_media
from app.models.asset import Asset

def test_image_detection(tmp_path):
    # Test PNG
    png_path = tmp_path / "valid.png"
    img = Image.new("RGBA", (200, 100), color=(255, 0, 0, 255))
    img.save(png_path, format="PNG")

    res = detect_media_type("asset-png-1", png_path)
    assert res.status == "completed"
    assert res.media_type == "image"
    assert res.error_message is None

    # Test JPEG
    jpg_path = tmp_path / "valid.jpg"
    img_rgb = Image.new("RGB", (150, 150), color="blue")
    img_rgb.save(jpg_path, format="JPEG")

    res_jpg = detect_media_type("asset-jpg-1", jpg_path)
    assert res_jpg.status == "completed"
    assert res_jpg.media_type == "image"

    # Test WebP
    webp_path = tmp_path / "valid.webp"
    img_rgb.save(webp_path, format="WEBP")

    res_webp = detect_media_type("asset-webp-1", webp_path)
    assert res_webp.status == "completed"
    assert res_webp.media_type == "image"

def test_video_detection(tmp_path):
    # Test MP4 (ISO BMFF with ftyp)
    mp4_path = tmp_path / "clip.mp4"
    mp4_path.write_bytes(b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2mp41")

    res_mp4 = detect_media_type("asset-mp4-1", mp4_path)
    assert res_mp4.status == "completed"
    assert res_mp4.media_type == "video"

    # Test WebM (EBML header)
    webm_path = tmp_path / "clip.webm"
    webm_path.write_bytes(b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01")

    res_webm = detect_media_type("asset-webm-1", webm_path)
    assert res_webm.status == "completed"
    assert res_webm.media_type == "video"

def test_unsupported_file(tmp_path):
    txt_path = tmp_path / "document.txt"
    txt_path.write_text("This is an unsupported plain text document.")

    res = detect_media_type("asset-txt-1", txt_path)
    assert res.status == "failed"
    assert "unsupported" in res.error_message.lower() or "unrecognized" in res.error_message.lower()

def test_corrupt_unreadable_file(tmp_path):
    # Corrupt PNG header with garbage data
    corrupt_png = tmp_path / "corrupt.png"
    corrupt_png.write_bytes(b"\x89PNG\r\n\x1a\n_TRUNCATED_GARBAGE_PAYLOAD")

    res = detect_media_type("asset-corrupt-1", corrupt_png)
    assert res.status == "failed"
    assert "corrupt" in res.error_message.lower() or "invalid" in res.error_message.lower()

    # Empty 0-byte file
    empty_file = tmp_path / "empty.png"
    empty_file.write_bytes(b"")

    res_empty = detect_media_type("asset-empty-1", empty_file)
    assert res_empty.status == "failed"
    assert "empty" in res_empty.error_message.lower()

    # Nonexistent file
    missing_file = tmp_path / "does_not_exist.mp4"
    res_missing = detect_media_type("asset-missing-1", missing_file)
    assert res_missing.status == "failed"
    assert "not found" in res_missing.error_message.lower()
