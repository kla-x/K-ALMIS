from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session,joinedload
from ..models import Assets,User
from ..database import get_db
from ..schemas.assets import QRCodeResponse,AssetResponse,AssetLocationUpdate
from ..utilities import get_current_user
from datetime import datetime
import base64
import io
import qrcode
from .a_crude import create_lifecycle_event
from ..asset_utils import add_namedep_asset


router = APIRouter(
    prefix="/api/v1/assets",
    tags=["Assets Tracking"]
    )

@router.post("/{asset_id}/generate-qr", response_model=QRCodeResponse)
async def generate_asset_qr_code(asset_id: str,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    asset = db.query(Assets).filter( Assets.id == asset_id, Assets.is_deleted == False).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    qr_data = {"asset_id": asset.id,"tag_number": asset.tag_number,"description": asset.description,"category": asset.category,"generated_at": datetime.now().isoformat()}
    
    qr_code_text = f"ASSET:{asset.id}|TAG:{asset.tag_number}|DESC:{asset.description}"

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_code_text)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    asset.qr_code = qr_code_text
    
    create_lifecycle_event( db, asset.id, "qr_generated", current_user.id, details={"qr_data": qr_code_text}, remarks="QR code generated for asset")
    
    db.commit()  
    return QRCodeResponse(qr_code_data=qr_code_text, qr_code_image_url=f"data:image/png;base64,{qr_code_base64}")

@router.put("/{asset_id}/location", response_model=AssetResponse)
async def update_asset_location(asset_id: str, location_data: AssetLocationUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    
    
    asset = db.query(Assets).filter(Assets.id == asset_id,Assets.is_deleted == False).first() 
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    old_location = asset.location
    asset.location = location_data.location
    
    create_lifecycle_event(db, asset.id, "location_changed", current_user.id,
        details={
            "old_location": old_location,
            "new_location": location_data.location
        },remarks=location_data.remarks or "Asset location updated" # remak
    )
    
    db.commit()
    db.refresh(asset)
    
    return AssetResponse(**add_namedep_asset(asset))

# lookup 
@router.get("/by-tag/{tag_number}", response_model=AssetResponse)
async def get_asset_by_tag_no(tag_number: str,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):

    asset = db.query(Assets).options(joinedload(Assets.department),joinedload(Assets.responsible_officer)
    ).filter(
        Assets.tag_number == tag_number,
        Assets.is_deleted == False
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return AssetResponse(**add_namedep_asset(asset))

@router.get("/by-barcode/{barcode}", response_model=AssetResponse)
async def get_asset_by_barcode(barcode: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    
    asset = db.query(Assets).options( joinedload(Assets.department), joinedload(Assets.responsible_officer)
    ).filter(
        Assets.barcode == barcode,
        Assets.is_deleted == False
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return AssetResponse(**add_namedep_asset(asset))

@router.get("/by-serial/{serial_number}", response_model=AssetResponse)
async def get_asset_by_serial_no(
    serial_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    asset = db.query(Assets).options(joinedload(Assets.department),joinedload(Assets.responsible_officer)
    ).filter(
        Assets.serial_number == serial_number,
        Assets.is_deleted == False
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return AssetResponse(**add_namedep_asset(asset))