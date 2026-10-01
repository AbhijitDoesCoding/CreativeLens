from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.model import Model
from app.schemas.model import ModelCreate, ModelUpdate

def create_model(db: Session, model_in: ModelCreate) -> Model:
    """Create a new model record."""
    model = Model(
        name=model_in.name,
        provider=model_in.provider,
        model_key=model_in.model_key,
        model_type=model_in.model_type or "multimodal",
        enabled=model_in.enabled or False,
        configuration_json=model_in.configuration_json,
        pricing_json=model_in.pricing_json,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model

def get_models(db: Session, enabled_only: bool = False) -> List[Model]:
    """Retrieve all models or only enabled models."""
    query = db.query(Model)
    if enabled_only:
        query = query.filter(Model.enabled.is_(True))
    return query.order_by(Model.created_at.desc()).all()

def get_model_by_id(db: Session, model_id: str) -> Optional[Model]:
    """Retrieve a single model by ID."""
    return db.query(Model).filter(Model.id == model_id).first()

def update_model(db: Session, model: Model, update_data: ModelUpdate) -> Model:
    """Update fields of an existing model."""
    data = update_data.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(model, field, value)
    db.commit()
    db.refresh(model)
    return model

def set_model_enabled(db: Session, model: Model, enabled: bool) -> Model:
    """Enable or disable a model."""
    model.enabled = enabled
    db.commit()
    db.refresh(model)
    return model
