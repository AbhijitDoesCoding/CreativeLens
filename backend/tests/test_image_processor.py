import io
from PIL import Image
from app.models.campaign import Campaign
from app.models.asset import Asset

def test_process_image_endpoint(client):
    camp_res = client.post("/campaigns", json={"name": "Image Process Campaign"})
    campaign_id = camp_res.json()["id"]

    # Generate 1200x628 PNG image
    img = Image.new("RGB", (1200, 628), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    up_res = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("banner.png", buf, "image/png")},
    )
    assert up_res.status_code == 201
    asset_id = up_res.json()["id"]

    # Process asset
    process_res = client.post(f"/assets/{asset_id}/process")
    assert process_res.status_code == 200
    data = process_res.json()
    assert data["asset_id"] == asset_id
    assert data["media_type"] == "image"
    assert data["status"] == "completed"
    assert data["width"] == 1200
    assert data["height"] == 628
    assert data["format"] == "PNG"
    assert data["color_mode"] == "RGB"
    assert data["processed_at"] is not None

def test_process_jpeg_image(client):
    camp_res = client.post("/campaigns", json={"name": "JPEG Process Campaign"})
    campaign_id = camp_res.json()["id"]

    img = Image.new("RGB", (800, 600), color=(255, 128, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    up_res = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("photo.jpg", buf, "image/jpeg")},
    )
    assert up_res.status_code == 201
    asset_id = up_res.json()["id"]

    process_res = client.post(f"/assets/{asset_id}/process")
    assert process_res.status_code == 200
    data = process_res.json()
    assert data["status"] == "completed"
    assert data["width"] == 800
    assert data["height"] == 600
    assert data["format"] == "JPEG"

def test_process_corrupt_image(client):
    camp_res = client.post("/campaigns", json={"name": "Corrupt Image Campaign"})
    campaign_id = camp_res.json()["id"]

    corrupt_bytes = b"\x89PNG\r\n\x1a\nNotAValidPngDataStructure"
    up_res = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("corrupt.png", io.BytesIO(corrupt_bytes), "image/png")},
    )
    assert up_res.status_code == 201
    asset_id = up_res.json()["id"]

    process_res = client.post(f"/assets/{asset_id}/process")
    assert process_res.status_code == 200
    data = process_res.json()
    assert data["status"] == "failed"
    assert data["error_message"] is not None
    assert "corrupt" in data["error_message"].lower() or "invalid" in data["error_message"].lower()

def test_process_missing_asset(client):
    res = client.post("/assets/00000000-0000-0000-0000-000000000000/process")
    assert res.status_code == 404

def test_process_missing_disk_file(client, db_session):
    camp = Campaign(name="Missing Disk File")
    db_session.add(camp)
    db_session.commit()

    asset = Asset(
        campaign_id=camp.id,
        filename="missing.png",
        file_path="data/campaigns/c/assets/nonexistent_file.png",
        media_type="image",
        mime_type="image/png",
        file_size=100,
    )
    db_session.add(asset)
    db_session.commit()

    res = client.post(f"/assets/{asset.id}/process")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "failed"
    assert "not found" in data["error_message"].lower()
