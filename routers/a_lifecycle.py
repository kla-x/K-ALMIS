from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Assets,AssetStatus,User,AssetLifecycleEvents
from ..schemas.assets import AssetResponse
from sqlalchemy import desc
from .a_crude import create_lifecycle_event
from ..utilities import get_current_user
from typing import List
from ..schemas.assets import AssetLifecycleEventResponse
from ..asset_utils import add_namedep_asset

from ..asset_utils import add_namedep_asset
router = APIRouter(
    prefix="/api/v1/assets/life",
    tags=["Assets Lifecycle"]
    )

@router.post("/{asset_id}/activate")
async def activate_asset(asset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    asset = db.query(Assets).filter(Assets.id == asset_id, Assets.is_deleted == False).first()
    
    if not asset:
     
        raise HTTPException(status_code=404, detail="Asset not found")
    
    if asset.status == AssetStatus.OPERATIONAL:
        raise HTTPException(status_code=400, detail="Asset is already operational")
    
    asset.status = AssetStatus.OPERATIONAL
    
    # create_lifecycle_event(db, asset.id, "activated", current_user.id,remarks="Asset activated for operational use")
    
    db.commit()
    db.refresh(asset)
    
    return {"msg" : f"Asset {asset.id} : Activated" }

@router.post("/{asset_id}/deactivate")  
async def deactivate_asset(asset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    asset = db.query(Assets).filter(Assets.id == asset_id, Assets.is_deleted == False).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    if asset.status in [AssetStatus.DISPOSED, AssetStatus.RETIRED]:
        raise HTTPException(status_code=400, detail="Cannot deactivate disposed or retired asset")
    
    asset.status = AssetStatus.IMPAIRED
    
    # create_lifecycle_event(db, asset.id, "deactivated", current_user.id,remarks="Asset deactivated from operational use")
    
    db.commit()
    db.refresh(asset)
    
    return {"msg" : f"Asset {asset.id} : Dectivated" }

@router.post("/{asset_id}/mark-disposal")
async def mark_asset_for_disposal( asset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    asset = db.query(Assets).filter(Assets.id == asset_id,Assets.is_deleted == False).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    if asset.status in [AssetStatus.DISPOSED, AssetStatus.HELD_FOR_SALE]:
        raise HTTPException(status_code=400, detail="Asset already marked for disposal")
    
    asset.status = AssetStatus.HELD_FOR_SALE
    
    # create_lifecycle_event(db, asset.id, "marked_for_disposal", current_user.id,remarks="Asset marked for disposal")
    
    db.commit()
    db.refresh(asset)
    
    return AssetResponse(**add_namedep_asset(asset))


@router.get("/{asset_id}/lifecycle", response_model=List[AssetLifecycleEventResponse])
async def get_asset_lifecycle_adm(asset_id: str,db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get complete asset lifecycle history"""
    
    asset = db.query(Assets).filter(Assets.id == asset_id,Assets.is_deleted == False).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    events = db.query(AssetLifecycleEvents).filter(AssetLifecycleEvents.asset_id == asset_id).order_by(desc(AssetLifecycleEvents.event_date)).all()
    
    return events