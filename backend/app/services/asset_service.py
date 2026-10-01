import uuid
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.schemas.asset import AssetCreate
from app.services import storage_service

def create_asset(db: Session, asset_in: AssetCreate, asset_id: Optional[str] = None) -> Asset:
    asset = Asset(
        id=asset_id or str(uuid.uuid4()),
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

def save_and_create_asset(
    db: Session,
    campaign_id: str,
    upload_file: UploadFile,
) -> Asset:
    asset_id = str(uuid.uuid4())
    safe_filename, rel_path, media_type, mime_type, file_size = storage_service.save_uploaded_file(
        upload_file=upload_file,
        campaign_id=campaign_id,
        asset_id=asset_id,
    )
    asset_in = AssetCreate(
        campaign_id=campaign_id,
        filename=safe_filename,
        file_path=rel_path,
        media_type=media_type,  # type: ignore[arg-type]
        mime_type=mime_type,
        file_size=file_size,
    )
    return create_asset(db, asset_in, asset_id=asset_id)

def get_assets_by_campaign(db: Session, campaign_id: str) -> List[Asset]:
    return (
        db.query(Asset)
        .filter(Asset.campaign_id == campaign_id)
        .order_by(Asset.created_at.desc())
        .all()
    )

def get_asset_by_id(db: Session, asset_id: str) -> Optional[Asset]:
    return db.query(Asset).filter(Asset.id == asset_id).first()

