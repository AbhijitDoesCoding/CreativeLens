import io
from PIL import Image
import pytest
from fastapi.testclient import TestClient
from app.models.campaign import Campaign
from app.models.asset import Asset
from app.models.model import Model
from app.models.inference_run import InferenceRun
from app.services import inference_service
from app.core.config import settings

def test_robustness_adapter_unavailable(client: TestClient, db_session):
    """When an adapter is unavailable, record status 'failed' with reason in InferenceRun."""
    camp_res = client.post("/campaigns", json={"name": "Unavailable Adapter Campaign"})
    campaign_id = camp_res.json()["id"]

    img_buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="pink").save(img_buf, format="PNG")
    up_res = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("pink.png", img_buf.getvalue(), "image/png")},
    )
    asset_id = up_res.json()["id"]

    model_res = client.post(
        "/models",
        json={
            "name": "Unavailable Model",
            "provider": "mock",
            "model_key": "mock-unavail",
            "enabled": True,
            "configuration_json": {"available": False},
        },
    )
    model_id = model_res.json()["id"]

    infer_res = client.post(f"/assets/{asset_id}/infer/{model_id}")
    assert infer_res.status_code == 200
    data = infer_res.json()

    assert data["status"] == "failed"
    assert "currently unavailable" in data["error_message"].lower()

    # Verify inspectable via GET /inference-runs/{run_id}
    run_res = client.get(f"/inference-runs/{data['id']}")
    assert run_res.status_code == 200
    assert run_res.json()["status"] == "failed"

def test_robustness_timeout_handling(client: TestClient, db_session):
    """Model execution exceeding timeout records 'failed' with timeout error."""
    camp_res = client.post("/campaigns", json={"name": "Timeout Campaign"})
    campaign_id = camp_res.json()["id"]

    img_buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="orange").save(img_buf, format="PNG")
    up_res = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("orange.png", img_buf.getvalue(), "image/png")},
    )
    asset_id = up_res.json()["id"]

    model_res = client.post(
        "/models",
        json={
            "name": "Slow Model",
            "provider": "mock",
            "model_key": "mock-slow",
            "enabled": True,
            "configuration_json": {"should_timeout": True, "timeout_seconds": 0.05},
        },
    )
    model_id = model_res.json()["id"]

    infer_res = client.post(f"/assets/{asset_id}/infer/{model_id}")
    assert infer_res.status_code == 200
    data = infer_res.json()

    assert data["status"] == "failed"
    assert "timed out" in data["error_message"].lower()

def test_robustness_malformed_model_response(client: TestClient, db_session):
    """When adapter returns malformed response, record status 'failed' cleanly."""
    camp_res = client.post("/campaigns", json={"name": "Malformed Response Campaign"})
    campaign_id = camp_res.json()["id"]

    img_buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="purple").save(img_buf, format="PNG")
    up_res = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("purple.png", img_buf.getvalue(), "image/png")},
    )
    asset_id = up_res.json()["id"]

    model_res = client.post(
        "/models",
        json={
            "name": "Malformed Model",
            "provider": "mock",
            "model_key": "mock-malformed",
            "enabled": True,
            "configuration_json": {"malformed_response": True},
        },
    )
    model_id = model_res.json()["id"]

    infer_res = client.post(f"/assets/{asset_id}/infer/{model_id}")
    assert infer_res.status_code == 200
    data = infer_res.json()

    assert data["status"] == "failed"
    assert "malformed model response" in data["error_message"].lower()

def test_robustness_missing_configuration_handled_gracefully(client: TestClient, db_session):
    """Models with null/missing configuration run safely with default fallbacks."""
    camp_res = client.post("/campaigns", json={"name": "No Config Campaign"})
    campaign_id = camp_res.json()["id"]

    img_buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="gray").save(img_buf, format="PNG")
    up_res = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("gray.png", img_buf.getvalue(), "image/png")},
    )
    asset_id = up_res.json()["id"]

    model_res = client.post(
        "/models",
        json={
            "name": "No Config Model",
            "provider": "mock",
            "model_key": "mock-noconfig",
            "enabled": True,
            "configuration_json": None,
        },
    )
    model_id = model_res.json()["id"]

    infer_res = client.post(f"/assets/{asset_id}/infer/{model_id}")
    assert infer_res.status_code == 200
    data = infer_res.json()
    assert data["status"] == "completed"
    assert data["error_message"] is None

def test_robustness_missing_usage_info(client: TestClient, db_session):
    """When model does not provide token usage info, run completes without error."""
    camp_res = client.post("/campaigns", json={"name": "No Usage Campaign"})
    campaign_id = camp_res.json()["id"]

    img_buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="teal").save(img_buf, format="PNG")
    up_res = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("teal.png", img_buf.getvalue(), "image/png")},
    )
    asset_id = up_res.json()["id"]

    model_res = client.post(
        "/models",
        json={
            "name": "No Usage Model",
            "provider": "mock",
            "model_key": "mock-nousage",
            "enabled": True,
            "configuration_json": {"missing_usage": True},
        },
    )
    model_id = model_res.json()["id"]

    infer_res = client.post(f"/assets/{asset_id}/infer/{model_id}")
    assert infer_res.status_code == 200
    data = infer_res.json()
    assert data["status"] == "completed"
    assert data["input_tokens"] is None
    assert data["output_tokens"] is None
    assert data["estimated_cost_usd"] is None
    assert data["latency_ms"] is not None

def test_robustness_empty_model_output(client: TestClient, db_session):
    """When model returns empty output string, pipeline persists without crashing."""
    camp_res = client.post("/campaigns", json={"name": "Empty Output Campaign"})
    campaign_id = camp_res.json()["id"]

    img_buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="black").save(img_buf, format="PNG")
    up_res = client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("black.png", img_buf.getvalue(), "image/png")},
    )
    asset_id = up_res.json()["id"]

    model_res = client.post(
        "/models",
        json={
            "name": "Empty Output Model",
            "provider": "mock",
            "model_key": "mock-empty",
            "enabled": True,
            "configuration_json": {"empty_output": True},
        },
    )
    model_id = model_res.json()["id"]

    infer_res = client.post(f"/assets/{asset_id}/infer/{model_id}")
    assert infer_res.status_code == 200
    data = infer_res.json()
    assert data["status"] == "completed"
    assert data["text"] == ""

def test_robustness_campaign_pipeline_fault_isolation(client: TestClient, db_session):
    """
    Campaign pipeline must isolate failures:
    A crashing or timing-out model must NOT prevent healthy models from completing.
    """
    # Disable all prior models first
    db_session.query(Model).update({Model.enabled: False})
    db_session.commit()

    # 1. Create Campaign with 2 image assets
    camp_res = client.post("/campaigns", json={"name": "Fault Isolation Campaign"})
    campaign_id = camp_res.json()["id"]

    buf1 = io.BytesIO()
    Image.new("RGB", (120, 120), color="red").save(buf1, format="PNG")
    client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("asset_a.png", buf1.getvalue(), "image/png")},
    )

    buf2 = io.BytesIO()
    Image.new("RGB", (120, 120), color="blue").save(buf2, format="PNG")
    client.post(
        f"/campaigns/{campaign_id}/assets",
        files={"file": ("asset_b.png", buf2.getvalue(), "image/png")},
    )

    # 2. Register 3 enabled models: 1 healthy, 1 crashing, 1 timing out
    client.post(
        "/models",
        json={
            "name": "Healthy Model",
            "provider": "mock",
            "model_key": "healthy-v1",
            "enabled": True,
            "configuration_json": {"simulated_latency_ms": 10},
        },
    )
    client.post(
        "/models",
        json={
            "name": "Crashing Model",
            "provider": "mock",
            "model_key": "crash-v1",
            "enabled": True,
            "configuration_json": {"should_fail": True},
        },
    )
    client.post(
        "/models",
        json={
            "name": "Timeout Model",
            "provider": "mock",
            "model_key": "timeout-v1",
            "enabled": True,
            "configuration_json": {"should_timeout": True, "timeout_seconds": 0.05},
        },
    )

    # 3. Run Campaign Pipeline
    pipe_res = client.post(
        f"/campaigns/{campaign_id}/run",
        json={"prompt": "Isolate faults across models", "max_workers": 2},
    )
    assert pipe_res.status_code == 200
    summary = pipe_res.json()

    assert summary["campaign_id"] == campaign_id
    assert summary["assets"] == 2
    assert summary["enabled_models"] == 3
    assert summary["runs_created"] == 6
    assert summary["successful_runs"] == 2  # Healthy model succeeded on both assets
    assert summary["failed_runs"] == 4      # Crashing & timeout models failed on both assets

    # 4. Check DB records
    runs = db_session.query(InferenceRun).all()
    completed_runs = [r for r in runs if r.status == "completed"]
    failed_runs = [r for r in runs if r.status == "failed"]
    assert len(completed_runs) >= 2
    assert len(failed_runs) >= 4
    for r in failed_runs:
        assert r.error_message is not None and len(r.error_message) > 0
