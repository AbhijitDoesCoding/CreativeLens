from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, sessionmaker
from app.db.session import SessionLocal
from app.models.campaign import Campaign
from app.models.model import Model
from app.schemas.pipeline import CampaignRunRequest, CampaignRunResponse
from app.services import inference_service

def is_asset_processable(asset) -> bool:
    """Determine if an asset is processable for inference."""
    if asset.media_type == "image":
        return True
    if asset.media_type == "video":
        return bool(asset.media_processing and asset.media_processing.status == "completed")
    return False

def run_campaign_pipeline(
    db: Session,
    campaign_id: str,
    request: Optional[CampaignRunRequest] = None,
) -> CampaignRunResponse:
    """
    Executes all enabled models across all processable assets in a campaign.
    Uses bounded thread-pool concurrency to avoid overwhelming providers.
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with id '{campaign_id}' not found",
        )

    # Find enabled models
    enabled_models = (
        db.query(Model)
        .filter(Model.enabled.is_(True))
        .all()
    )
    if not enabled_models:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No enabled models found for pipeline execution. Please enable at least one model in Model Registry.",
        )

    # Filter processable assets
    processable_assets = [a for a in campaign.assets if is_asset_processable(a)]
    if not processable_assets:
        return CampaignRunResponse(
            campaign_id=campaign_id,
            assets=len(campaign.assets),
            enabled_models=len(enabled_models),
            runs_created=0,
            successful_runs=0,
            failed_runs=0,
        )

    prompt = request.prompt if request else None
    max_workers = request.max_workers if (request and request.max_workers) else 3

    # Build combination tasks: (asset_id, model_id)
    tasks = [
        (asset.id, model.id)
        for asset in processable_assets
        for model in enabled_models
    ]

    successful = 0
    failed = 0

    import threading
    _db_lock = threading.Lock()
    SessionMaker = sessionmaker(bind=db.get_bind(), autocommit=False, autoflush=False)

    def _execute_task(task_pair):
        a_id, m_id = task_pair
        with _db_lock:
            session = SessionMaker()
        try:
            with _db_lock:
                run = inference_service.run_asset_inference(
                    db=session,
                    asset_id=a_id,
                    model_id=m_id,
                    prompt=prompt,
                )
                return run.status == "completed"
        except Exception:
            return False
        finally:
            with _db_lock:
                session.close()



    with ThreadPoolExecutor(max_workers=min(max_workers, len(tasks) or 1)) as executor:
        futures = [executor.submit(_execute_task, task) for task in tasks]
        for future in as_completed(futures):
            try:
                if future.result():
                    successful += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

    return CampaignRunResponse(
        campaign_id=campaign_id,
        assets=len(processable_assets),
        enabled_models=len(enabled_models),
        runs_created=len(tasks),
        successful_runs=successful,
        failed_runs=failed,
    )
