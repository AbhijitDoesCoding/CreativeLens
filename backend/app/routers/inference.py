from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.asset import Asset
from app.schemas.inference_run import InferAssetRequest, InferenceRunResponse
from app.services import inference_service

router = APIRouter(tags=["inference"])

@router.post(
    "/assets/{asset_id}/infer/{model_id}",
    response_model=InferenceRunResponse,
    status_code=status.HTTP_200_OK,
)
def infer_asset_endpoint(
    asset_id: str,
    model_id: str,
    payload: Optional[InferAssetRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Executes model inference for an asset using an enabled model.
    Accepts optional prompt instructions in the request body.
    """
    prompt = payload.prompt if payload else None
    run = inference_service.run_asset_inference(
        db=db,
        asset_id=asset_id,
        model_id=model_id,
        prompt=prompt,
    )
    return inference_service.serialize_inference_run(run)

@router.get(
    "/assets/{asset_id}/inference-runs",
    response_model=List[InferenceRunResponse],
    status_code=status.HTTP_200_OK,
)
def get_asset_inference_runs_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve all inference runs performed for a specific asset.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with id '{asset_id}' not found",
        )

    runs = inference_service.get_inference_runs_for_asset(db=db, asset_id=asset_id)
    return [inference_service.serialize_inference_run(r) for r in runs]

@router.get(
    "/inference-runs/{run_id}",
    response_model=InferenceRunResponse,
    status_code=status.HTTP_200_OK,
)
def get_inference_run_endpoint(
    run_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve execution telemetry and outputs of a single inference run by its ID.
    """
    run = inference_service.get_inference_run_by_id(db=db, run_id=run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inference run with id '{run_id}' not found",
        )
    return inference_service.serialize_inference_run(run)
