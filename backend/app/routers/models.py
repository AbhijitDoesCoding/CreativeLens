from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.model import ModelCreate, ModelResponse, ModelUpdate
from app.services import model_service

router = APIRouter(prefix="/models", tags=["models"])

@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
def create_model_endpoint(
    model_in: ModelCreate,
    db: Session = Depends(get_db),
):
    """Register a new model."""
    return model_service.create_model(db=db, model_in=model_in)

@router.get("", response_model=List[ModelResponse], status_code=status.HTTP_200_OK)
def list_models_endpoint(
    enabled_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    """List all registered models, optionally filtering by enabled status."""
    return model_service.get_models(db=db, enabled_only=enabled_only)

@router.get("/{model_id}", response_model=ModelResponse, status_code=status.HTTP_200_OK)
def get_model_endpoint(
    model_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve details for a single model."""
    model = model_service.get_model_by_id(db=db, model_id=model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id '{model_id}' not found",
        )
    return model

@router.patch("/{model_id}", response_model=ModelResponse, status_code=status.HTTP_200_OK)
def update_model_endpoint(
    model_id: str,
    update_data: ModelUpdate,
    db: Session = Depends(get_db),
):
    """Update fields or configuration of an existing model."""
    model = model_service.get_model_by_id(db=db, model_id=model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id '{model_id}' not found",
        )
    return model_service.update_model(db=db, model=model, update_data=update_data)

@router.post("/{model_id}/enable", response_model=ModelResponse, status_code=status.HTTP_200_OK)
def enable_model_endpoint(
    model_id: str,
    db: Session = Depends(get_db),
):
    """Enable a model for inference execution."""
    model = model_service.get_model_by_id(db=db, model_id=model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id '{model_id}' not found",
        )
    return model_service.set_model_enabled(db=db, model=model, enabled=True)

@router.post("/{model_id}/disable", response_model=ModelResponse, status_code=status.HTTP_200_OK)
def disable_model_endpoint(
    model_id: str,
    db: Session = Depends(get_db),
):
    """Disable a model so it is not eligible for inference pipeline execution."""
    model = model_service.get_model_by_id(db=db, model_id=model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id '{model_id}' not found",
        )
    return model_service.set_model_enabled(db=db, model=model, enabled=False)
