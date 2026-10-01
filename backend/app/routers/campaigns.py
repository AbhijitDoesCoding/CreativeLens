from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.campaign import CampaignCreate, CampaignResponse
from app.schemas.asset import AssetResponse
from app.services import campaign_service, asset_service

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

