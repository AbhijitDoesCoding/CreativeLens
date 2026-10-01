from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.campaign import CampaignCreate, CampaignResponse
from app.schemas.asset import AssetResponse
from app.schemas.pipeline import CampaignRunRequest, CampaignRunResponse
from app.services import campaign_service, asset_service, pipeline_service

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign_endpoint(
    campaign_in: CampaignCreate,
    db: Session = Depends(get_db),
):
    return campaign_service.create_campaign(db, campaign_in)

@router.get("", response_model=List[CampaignResponse], status_code=status.HTTP_200_OK)
def list_campaigns_endpoint(
    db: Session = Depends(get_db),
):
    return campaign_service.get_campaigns(db)

@router.get("/{campaign_id}", response_model=CampaignResponse, status_code=status.HTTP_200_OK)
def get_campaign_endpoint(
    campaign_id: str,
    db: Session = Depends(get_db),
):
    campaign = campaign_service.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with id '{campaign_id}' not found",
        )
    return campaign

@router.get("/{campaign_id}/assets", response_model=List[AssetResponse], status_code=status.HTTP_200_OK)
def list_campaign_assets_endpoint(
    campaign_id: str,
    db: Session = Depends(get_db),
):
    campaign = campaign_service.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with id '{campaign_id}' not found",
        )
    return asset_service.get_assets_by_campaign(db, campaign_id)

@router.post("/{campaign_id}/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def upload_campaign_asset_endpoint(
    campaign_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    campaign = campaign_service.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with id '{campaign_id}' not found",
        )
    return asset_service.save_and_create_asset(db, campaign_id, file)

@router.post("/{campaign_id}/run", response_model=CampaignRunResponse, status_code=status.HTTP_200_OK)
def run_campaign_pipeline_endpoint(
    campaign_id: str,
    payload: Optional[CampaignRunRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Execute all enabled models against all processable assets in a campaign.
    """
    return pipeline_service.run_campaign_pipeline(db=db, campaign_id=campaign_id, request=payload)



