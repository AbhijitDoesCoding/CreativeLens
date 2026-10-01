import io
from pathlib import Path
from app.core.config import settings

def test_image_upload(client):
    campaign_res = client.post("/campaigns", json={"name": "Image Campaign"})
    campaign_id = campaign_res.json()["id"]

    file_content = b"\x89PNG\r\n\x1a\nfake_image_binary_data"
    response = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("hero_banner.png", io.BytesIO(file_content), "image/png")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["campaign_id"] == campaign_id
    assert data["filename"] == "hero_banner.png"
    assert data["media_type"] == "image"
    assert data["mime_type"] == "image/png"
    assert data["file_size"] == len(file_content)
    assert f"data/campaigns/{campaign_id}/assets/" in data["file_path"]

def test_video_upload(client):
    campaign_res = client.post("/campaigns", json={"name": "Video Campaign"})
    campaign_id = campaign_res.json()["id"]

    file_content = b"\x00\x00\x00 ftypisomfake_video_bytes"
    response = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("commercial.mp4", io.BytesIO(file_content), "video/mp4")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["campaign_id"] == campaign_id
    assert data["filename"] == "commercial.mp4"
    assert data["media_type"] == "video"
    assert data["mime_type"] == "video/mp4"
    assert data["file_size"] == len(file_content)

def test_unsupported_file_extension(client):
    campaign_res = client.post("/campaigns", json={"name": "Invalid File Campaign"})
    campaign_id = campaign_res.json()["id"]

    file_content = b"echo 'bad script'"
    response = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("bad_script.sh", io.BytesIO(file_content), "text/x-shellscript")},
    )
    assert response.status_code == 400
    assert "unsupported file type" in response.json()["detail"].lower()

def test_upload_missing_campaign(client):
    file_content = b"fake image"
    response = client.post(
        "/campaigns/00000000-0000-0000-0000-000000000000/assets",
        files={"file": ("photo.jpg", io.BytesIO(file_content), "image/jpeg")},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_file_persistence_and_sanitization(client, tmp_path, monkeypatch):
    test_upload_dir = tmp_path / "campaigns"
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.services.storage_service.settings.UPLOAD_DIR", test_upload_dir)

    campaign_res = client.post("/campaigns", json={"name": "Persistence Campaign"})
    campaign_id = campaign_res.json()["id"]

    file_content = b"persisted image bytes"
    # Filename with path traversal attempts
    traversal_filename = "../../../etc/passwd.png"

    response = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": (traversal_filename, io.BytesIO(file_content), "image/png")},
    )
    assert response.status_code == 201
    data = response.json()
    asset_id = data["id"]
    sanitized_name = data["filename"]

    # Verify no path traversal in sanitized filename
    assert "/" not in sanitized_name
    assert ".." not in sanitized_name

    # Check file exists on filesystem under test_upload_dir
    expected_path = test_upload_dir / campaign_id / "assets" / f"{asset_id}_{sanitized_name}"
    assert expected_path.exists()
    assert expected_path.read_bytes() == file_content
