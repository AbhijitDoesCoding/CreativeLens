import io
from PIL import Image
from fastapi.testclient import TestClient
from app.models.inference_run import InferenceRun

def test_run_campaign_pipeline_success(client: TestClient, db_session):
    """Test running all enabled models across processable assets in a campaign."""
    # 1. Create Campaign
    camp_resp = client.post("/campaigns", json={"name": "Pipeline Run Campaign"})
    campaign_id = camp_resp.json()["id"]

    # 2. Upload two image assets
    buf1 = io.BytesIO()
    Image.new("RGB", (150, 150), color="blue").save(buf1, format="PNG")
    client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("asset_one.png", buf1.getvalue(), "image/png")},
    )

    buf2 = io.BytesIO()
    Image.new("RGB", (150, 150), color="red").save(buf2, format="PNG")
    client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("asset_two.png", buf2.getvalue(), "image/png")},
    )

    # 3. Create two enabled models and one disabled model
    client.post(
        "/models",
        json={"name": "Enabled Model 1", "provider": "mock", "model_key": "m1", "enabled": True},
    )
    client.post(
        "/models",
        json={"name": "Enabled Model 2", "provider": "mock", "model_key": "m2", "enabled": True},
    )
    client.post(
        "/models",
        json={"name": "Disabled Model", "provider": "mock", "model_key": "m3", "enabled": False},
    )

    # 4. Trigger pipeline run: POST /campaigns/{campaign_id}/run
    run_resp = client.post(
        f"/campaigns/{campaign_id}/run",
        json={"prompt": "Analyze creative text and context", "max_workers": 2},
    )
    assert run_resp.status_code == 200
    summary = run_resp.json()

    assert summary["campaign_id"] == campaign_id
    assert summary["assets"] == 2
    assert summary["enabled_models"] >= 2
    expected_runs = 2 * summary["enabled_models"]
    assert summary["runs_created"] == expected_runs
    assert summary["successful_runs"] == expected_runs

    # Verify runs were actually persisted in database
    db_runs = db_session.query(InferenceRun).all()
    assert len(db_runs) >= expected_runs

def test_run_campaign_pipeline_no_enabled_models(client: TestClient, db_session):
    """Pipeline run fails with 400 if no models are enabled."""
    camp_resp = client.post("/campaigns", json={"name": "No Models Campaign"})
    campaign_id = camp_resp.json()["id"]

    # Disable all models
    from app.models.model import Model
    db_session.query(Model).update({Model.enabled: False})
    db_session.commit()

    run_resp = client.post(f"/campaigns/{campaign_id}/run")
    assert run_resp.status_code == 400
    assert "No enabled models found" in run_resp.json()["detail"]

def test_run_campaign_pipeline_missing_campaign(client: TestClient):
    """Missing campaign returns 404."""
    run_resp = client.post("/campaigns/nonexistent-campaign-id-999/run")
    assert run_resp.status_code == 404
