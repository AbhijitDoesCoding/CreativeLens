import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.adapters import AdapterNotFoundError, ModelRequest, get_adapter
from app.models.asset import Asset
from app.models.inference_run import InferenceRun
from app.models.model import Model
from app.schemas.inference_run import InferenceRunResponse
from app.services import media_processing_service, storage_service

def serialize_inference_run(run: InferenceRun) -> InferenceRunResponse:
    """Format an InferenceRun ORM model into InferenceRunResponse with model metadata."""
    return InferenceRunResponse(
        id=run.id,
        asset_id=run.asset_id,
        model_id=run.model_id,
        status=run.status,
        response_text=run.response_text,
        context_json=run.context_json,
        started_at=run.started_at,
        completed_at=run.completed_at,
        latency_ms=run.latency_ms,
        ttft_ms=run.ttft_ms,
        input_tokens=run.input_tokens,
        output_tokens=run.output_tokens,
        estimated_cost_usd=run.estimated_cost_usd,
        raw_output=run.raw_output,
        error_message=run.error_message,
        created_at=run.created_at,
        model_name=run.model.name if run.model else None,
        model_key=run.model.model_key if run.model else None,
        provider=run.model.provider if run.model else None,
    )

def get_inference_run_by_id(db: Session, run_id: str) -> Optional[InferenceRun]:
    """Retrieve an InferenceRun record by its ID."""
    return db.query(InferenceRun).filter(InferenceRun.id == run_id).first()

def get_inference_runs_for_asset(db: Session, asset_id: str) -> List[InferenceRun]:
    """Retrieve all inference runs for a specific asset ordered newest first."""
    return (
        db.query(InferenceRun)
        .filter(InferenceRun.asset_id == asset_id)
        .order_by(InferenceRun.created_at.desc())
        .all()
    )

def run_asset_inference(
    db: Session,
    asset_id: str,
    model_id: str,
    prompt: Optional[str] = None,
) -> InferenceRun:
    """
    Executes inference for an asset using the specified model adapter.
    Handles images directly and videos via pre-extracted sampled frames.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with id '{asset_id}' not found",
        )

    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id '{model_id}' not found",
        )

    if not model.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model '{model.name}' is disabled. Enable the model before running inference.",
        )

    # Resolve adapter from registry
    try:
        adapter = get_adapter(
            provider=model.provider,
            model_key=model.model_key,
            configuration=model.configuration_json,
        )
    except AdapterNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Validate media requirements based on asset type
    model_request: ModelRequest
    if asset.media_type == "image":
        disk_path = storage_service.get_asset_disk_path(asset.file_path)
        if not disk_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Asset image file not found on disk: {disk_path.name}",
            )
        model_request = ModelRequest(
            image_path=str(disk_path),
            prompt=prompt,
            configuration=model.configuration_json,
        )
    elif asset.media_type == "video":
        processing = media_processing_service.get_processing_by_asset_id(db, asset_id)
        if not processing or processing.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video asset must be processed before running inference. Please process the video asset first.",
            )

        frames_resp = media_processing_service.get_asset_frames(db, asset_id)
        if not frames_resp.frames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No extracted frames found for video asset. Re-process the video to extract frames.",
            )

        frame_disk_paths: List[str] = []
        for frame_info in frames_resp.frames:
            f_path = media_processing_service.get_asset_frame_disk_path(
                db=db,
                asset_id=asset_id,
                frame_filename=frame_info.filename,
            )
            frame_disk_paths.append(str(f_path))

        model_request = ModelRequest(
            frame_paths=frame_disk_paths,
            prompt=prompt,
            configuration=model.configuration_json,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported media type '{asset.media_type}' for model inference",
        )

    # Create initial running record
    started_at = datetime.now(timezone.utc)
    inference_run = InferenceRun(
        id=str(uuid.uuid4()),
        asset_id=asset.id,
        model_id=model.id,
        status="running",
        started_at=started_at,
    )
    db.add(inference_run)
    db.commit()
    db.refresh(inference_run)

    wall_start = time.perf_counter()
    try:
        adapter_response = adapter.run(model_request)
        wall_elapsed_ms = int((time.perf_counter() - wall_start) * 1000)

        # Calculate or adopt latency & costs
        latency_ms = adapter_response.latency_ms or wall_elapsed_ms
        ttft_ms = adapter_response.ttft_ms
        input_tokens = adapter_response.input_tokens
        output_tokens = adapter_response.output_tokens

        estimated_cost = adapter_response.estimated_cost_usd
        if estimated_cost is None and model.pricing_json and input_tokens and output_tokens:
            in_rate = (
                model.pricing_json.get("input_per_million", 0) / 1_000_000
                or model.pricing_json.get("input_cost", 0)
            )
            out_rate = (
                model.pricing_json.get("output_per_million", 0) / 1_000_000
                or model.pricing_json.get("output_cost", 0)
            )
            estimated_cost = round((input_tokens * in_rate) + (output_tokens * out_rate), 6)

        inference_run.status = "completed"
        inference_run.response_text = adapter_response.text
        inference_run.context_json = adapter_response.context.model_dump()
        inference_run.completed_at = datetime.now(timezone.utc)
        inference_run.latency_ms = latency_ms
        inference_run.ttft_ms = ttft_ms
        inference_run.input_tokens = input_tokens
        inference_run.output_tokens = output_tokens
        inference_run.estimated_cost_usd = estimated_cost
        inference_run.raw_output = adapter_response.raw_output
        inference_run.error_message = None

    except Exception as e:
        wall_elapsed_ms = int((time.perf_counter() - wall_start) * 1000)
        inference_run.status = "failed"
        inference_run.completed_at = datetime.now(timezone.utc)
        inference_run.latency_ms = wall_elapsed_ms
        inference_run.error_message = str(e)

    db.commit()
    db.refresh(inference_run)
    return inference_run
