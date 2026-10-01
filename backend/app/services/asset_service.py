from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.schemas.asset import AssetCreate

def create_asset(db: Session, asset_in: AssetCreate) -> Asset:
    asset = Asset(
        campaign_id=asset_in.campaign_id,
        filename=asset_in.filename,
        file_path=asset_in.file_path,
        media_type=asset_in.media_type,
        mime_type=asset_in.mime_type,
        file_size=asset_in.file_size,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset

def get_assets_by_campaign(db: Session, campaign_id: str) -> List[Asset]:
    return (
        db.query(Asset)
        .filter(Asset.campaign_id == campaign_id)
        .order_by(Asset.created_at.desc())
        .all()
    )

def get_asset_by_id(db: Session, asset_id: str) -> Optional[Asset]:
    return db.query(Asset).filter(Asset.id == asset_id).first()
