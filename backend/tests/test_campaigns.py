def test_create_campaign(client):
    response = client.post("/campaigns", json={"name": "AO Gold Colgate SBW"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "AO Gold Colgate SBW"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_list_campaigns(client):
    # Empty list initially
    response = client.get("/campaigns")
    assert response.status_code == 200
    assert response.json() == []

    # Create campaigns
    client.post("/campaigns", json={"name": "Campaign Alpha"})
    client.post("/campaigns", json={"name": "Campaign Beta"})

    response = client.get("/campaigns")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = [c["name"] for c in data]
    assert "Campaign Alpha" in names
    assert "Campaign Beta" in names

def test_get_campaign(client):
    create_res = client.post("/campaigns", json={"name": "Nike Summer Campaign"})
    assert create_res.status_code == 201
    campaign_id = create_res.json()["id"]

    get_res = client.get(f"/campaigns/{campaign_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == campaign_id
    assert data["name"] == "Nike Summer Campaign"

def test_invalid_campaign_name_empty(client):
    response = client.post("/campaigns", json={"name": ""})
    assert response.status_code == 422

def test_invalid_campaign_name_whitespace(client):
    response = client.post("/campaigns", json={"name": "   "})
    assert response.status_code == 422

def test_invalid_campaign_missing_name_field(client):
    response = client.post("/campaigns", json={})
    assert response.status_code == 422

def test_missing_campaign_returns_404(client):
    response = client.get("/campaigns/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
