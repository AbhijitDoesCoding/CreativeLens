from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.asset import AssetResponse
from app.services import asset_service, storage_service

router = APIRouter(prefix="/assets", tags=["assets"])

@router.get("/{asset_id}", response_model=AssetResponse, status_code=status.HTTP_200_OK)
def get_asset_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
):
    asset = asset_service.get_asset_by_id(db, asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with id '{asset_id}' not found",
        )
    return asset

@router.get("/{asset_id}/file")
def get_asset_file_endpoint(
    asset_id: str,
    db: Session = Depends(get_db),
):
    asset = asset_service.get_asset_by_id(db, asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with id '{asset_id}' not found",
        )

    disk_path = storage_service.get_asset_disk_path(asset.file_path)
    if not disk_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset file not found on disk",
        )

    return FileResponse(
        path=disk_path,
        media_type=asset.mime_type,
        filename=asset.filename,
    )

