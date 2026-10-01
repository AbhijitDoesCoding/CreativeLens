from app.models.campaign import Campaign
from app.models.asset import Asset

def test_get_assets_empty_campaign(client):
    create_res = client.post("/campaigns", json={"name": "Empty Campaign"})
    campaign_id = create_res.json()["id"]

    res = client.get(f"/campaigns/{campaign_id}/assets")
    assert res.status_code == 200
    assert res.json() == []

def test_get_assets_missing_campaign(client):
    res = client.get("/campaigns/00000000-0000-0000-0000-000000000000/assets")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

def test_get_assets_and_single_asset(client, db_session):
    # Create campaign
    campaign = Campaign(name="Holiday 2026")
    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)

    # Create image asset
    image_asset = Asset(
        campaign_id=campaign.id,
        filename="banner.png",
        file_path="data/campaigns/c1/assets/banner.png",
        media_type="image",
        mime_type="image/png",
        file_size=102400,
    )
    # Create video asset
    video_asset = Asset(
        campaign_id=campaign.id,
        filename="promo.mp4",
        file_path="data/campaigns/c1/assets/promo.mp4",
        media_type="video",
        mime_type="video/mp4",
        file_size=5242880,
    )
    db_session.add_all([image_asset, video_asset])
    db_session.commit()
    db_session.refresh(image_asset)
    db_session.refresh(video_asset)

    # Test list assets for campaign
    res = client.get(f"/campaigns/{campaign.id}/assets")
    assert res.status_code == 200
    assets = res.json()
    assert len(assets) == 2
    filenames = [a["filename"] for a in assets]
    assert "banner.png" in filenames
    assert "promo.mp4" in filenames

    # Test get asset by id for image
    img_res = client.get(f"/assets/{image_asset.id}")
    assert img_res.status_code == 200
    img_data = img_res.json()
    assert img_data["id"] == image_asset.id
    assert img_data["campaign_id"] == campaign.id
    assert img_data["filename"] == "banner.png"
    assert img_data["file_path"] == "data/campaigns/c1/assets/banner.png"
    assert img_data["media_type"] == "image"
    assert img_data["mime_type"] == "image/png"
    assert img_data["file_size"] == 102400
    assert "created_at" in img_data

    # Test get asset by id for video
    vid_res = client.get(f"/assets/{video_asset.id}")
    assert vid_res.status_code == 200
    vid_data = vid_res.json()
    assert vid_data["id"] == video_asset.id
    assert vid_data["media_type"] == "video"
    assert vid_data["mime_type"] == "video/mp4"

def test_get_nonexistent_asset(client):
    res = client.get("/assets/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

def test_get_asset_file_content(client):
    import io
    # Create campaign and upload image
    camp_res = client.post("/campaigns", json={"name": "Preview Test Campaign"})
    campaign_id = camp_res.json()["id"]

    img_bytes = b"\x89PNG\r\n\x1a\npreview_test_content"
    up_res = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("test_preview.png", io.BytesIO(img_bytes), "image/png")},
    )
    assert up_res.status_code == 201
    asset_id = up_res.json()["id"]

    # Retrieve file
    file_res = client.get(f"/assets/{asset_id}/file")
    assert file_res.status_code == 200
    assert file_res.headers["content-type"].startswith("image/png")
    assert file_res.content == img_bytes

def test_get_asset_file_nonexistent_asset(client):
    res = client.get("/assets/00000000-0000-0000-0000-000000000000/file")
    assert res.status_code == 404

def test_get_asset_file_missing_on_disk(client, db_session):
    # Campaign exists and DB record exists, but file on disk is missing
    camp = Campaign(name="Missing Disk File Campaign")
    db_session.add(camp)
    db_session.commit()
    db_session.refresh(camp)

    missing_asset = Asset(
        campaign_id=camp.id,
        filename="ghost.png",
        file_path="data/campaigns/ghost/assets/nonexistent_ghost.png",
        media_type="image",
        mime_type="image/png",
        file_size=100,
    )
    db_session.add(missing_asset)
    db_session.commit()
    db_session.refresh(missing_asset)

    res = client.get(f"/assets/{missing_asset.id}/file")
    assert res.status_code == 404
    assert "not found on disk" in res.json()["detail"].lower()

