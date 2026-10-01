import pytest
from pydantic import ValidationError
from app.models.model import Model
from app.schemas.model import ModelCreate, ModelUpdate, ModelResponse

def test_create_model_db_record(db_session):
    """Test creating a model record in the database."""
    model = Model(
        name="Example Vision Model",
        provider="example_provider",
        model_key="example-model-v1",
        model_type="multimodal",
        enabled=True,
        configuration_json={"temperature": 0.2, "max_tokens": 1024},
        pricing_json={"input_per_million": 0.15, "output_per_million": 0.60},
    )
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)

    assert model.id is not None
    assert len(model.id) == 36
    assert model.name == "Example Vision Model"
    assert model.provider == "example_provider"
    assert model.model_key == "example-model-v1"
    assert model.model_type == "multimodal"
    assert model.enabled is True
    assert model.configuration_json == {"temperature": 0.2, "max_tokens": 1024}
    assert model.pricing_json == {"input_per_million": 0.15, "output_per_million": 0.60}
    assert model.created_at is not None
    assert model.updated_at is not None

def test_model_defaults_in_db(db_session):
    """Test default values for enabled and model_type."""
    model = Model(
        name="Default Test Model",
        provider="test_provider",
        model_key="test-key",
    )
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)

    assert model.enabled is False
    assert model.model_type == "multimodal"
    assert model.configuration_json is None
    assert model.pricing_json is None

def test_model_create_schema_valid():
    """Test ModelCreate validation with valid data."""
    data = {
        "name": "Gemini 1.5 Flash",
        "provider": "google",
        "model_key": "gemini-1.5-flash",
        "configuration_json": {"safety": "standard"},
    }
    schema = ModelCreate(**data)
    assert schema.name == "Gemini 1.5 Flash"
    assert schema.provider == "google"
    assert schema.model_key == "gemini-1.5-flash"
    assert schema.enabled is False
    assert schema.model_type == "multimodal"
    assert schema.configuration_json == {"safety": "standard"}

def test_model_create_validation_errors():
    """Test validation errors for required/blank fields."""
    # Blank name
    with pytest.raises(ValidationError) as exc:
        ModelCreate(name="   ", provider="google", model_key="gemini")
    assert "Model name cannot be blank" in str(exc.value)

    # Blank provider
    with pytest.raises(ValidationError) as exc:
        ModelCreate(name="Gemini", provider="", model_key="gemini")
    assert "Provider cannot be blank" in str(exc.value)

    # Blank model_key
    with pytest.raises(ValidationError) as exc:
        ModelCreate(name="Gemini", provider="google", model_key="   ")
    assert "Model key cannot be blank" in str(exc.value)

def test_model_update_schema():
    """Test ModelUpdate allows partial updates and validates blank fields."""
    update = ModelUpdate(enabled=True, name="Updated Name")
    assert update.enabled is True
    assert update.name == "Updated Name"
    assert update.provider is None

    # Blank name in update
    with pytest.raises(ValidationError):
        ModelUpdate(name="  ")
