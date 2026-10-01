from fastapi.testclient import TestClient

def test_create_model_api(client: TestClient):
    """Test registering a new model via POST /models."""
    payload = {
        "name": "GPT-4o Vision",
        "provider": "openai",
        "model_key": "gpt-4o",
        "model_type": "multimodal",
        "enabled": False,
        "configuration_json": {"temperature": 0.1, "detail": "high"},
        "pricing_json": {"input_cost": 0.005, "output_cost": 0.015},
    }
    response = client.post("/models", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "GPT-4o Vision"
    assert data["provider"] == "openai"
    assert data["model_key"] == "gpt-4o"
    assert data["enabled"] is False
    assert data["configuration_json"]["detail"] == "high"
    assert "id" in data
    assert "created_at" in data

def test_create_model_validation_failure(client: TestClient):
    """Test validation errors on missing/blank fields."""
    # Missing required name
    res1 = client.post("/models", json={"provider": "google", "model_key": "gemini"})
    assert res1.status_code == 422

    # Blank model_key
    res2 = client.post(
        "/models",
        json={"name": "Test Model", "provider": "google", "model_key": "  "},
    )
    assert res2.status_code == 422

def test_list_models_and_filter_enabled(client: TestClient):
    """Test listing models and filtering by enabled_only."""
    # Create one disabled and one enabled
    m1 = client.post(
        "/models",
        json={"name": "Model Disabled", "provider": "test", "model_key": "m-dis", "enabled": False},
    ).json()

    m2 = client.post(
        "/models",
        json={"name": "Model Enabled", "provider": "test", "model_key": "m-enb", "enabled": True},
    ).json()

    # List all
    all_res = client.get("/models")
    assert all_res.status_code == 200
    all_ids = [m["id"] for m in all_res.json()]
    assert m1["id"] in all_ids
    assert m2["id"] in all_ids

    # List enabled only
    enb_res = client.get("/models?enabled_only=true")
    assert enb_res.status_code == 200
    enb_ids = [m["id"] for m in enb_res.json()]
    assert m2["id"] in enb_ids
    assert m1["id"] not in enb_ids

def test_get_model_by_id(client: TestClient):
    """Test getting single model and 404 for nonexistent."""
    create_res = client.post(
        "/models",
        json={"name": "Claude 3.5 Sonnet", "provider": "anthropic", "model_key": "claude-3-5-sonnet"},
    )
    model_id = create_res.json()["id"]

    get_res = client.get(f"/models/{model_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == model_id
    assert get_res.json()["name"] == "Claude 3.5 Sonnet"

    # 404 missing
    missing_res = client.get("/models/nonexistent-model-id-999")
    assert missing_res.status_code == 404
    assert "not found" in missing_res.json()["detail"]

def test_update_model(client: TestClient):
    """Test partial update via PATCH /models/{model_id}."""
    create_res = client.post(
        "/models",
        json={"name": "Original Name", "provider": "mock", "model_key": "mock-v1"},
    )
    model_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/models/{model_id}",
        json={"name": "Updated Name", "configuration_json": {"new_key": "val"}},
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["name"] == "Updated Name"
    assert data["provider"] == "mock"
    assert data["configuration_json"] == {"new_key": "val"}

    # 404 for updating missing model
    miss_res = client.patch("/models/missing-id", json={"name": "New"})
    assert miss_res.status_code == 404

def test_enable_and_disable_model(client: TestClient):
    """Test enabling and disabling a model."""
    create_res = client.post(
        "/models",
        json={"name": "Toggle Model", "provider": "test", "model_key": "toggle-key", "enabled": False},
    )
    model_id = create_res.json()["id"]
    assert create_res.json()["enabled"] is False

    # Enable
    enb_res = client.post(f"/models/{model_id}/enable")
    assert enb_res.status_code == 200
    assert enb_res.json()["enabled"] is True

    # Disable
    dis_res = client.post(f"/models/{model_id}/disable")
    assert dis_res.status_code == 200
    assert dis_res.json()["enabled"] is False

    # 404 for enable/disable missing model
    assert client.post("/models/missing-id/enable").status_code == 404
    assert client.post("/models/missing-id/disable").status_code == 404
