from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List
import uuid
from ..models import Assets,User,AssetDisposals,AssetStatus,DisposalStatus
from ..utilities import get_current_user
from ..database import get_db
from ..schemas.maintain_dispose import DisposalApproveReq,DisposalExecuteReq,DisposalInitiateReq,DisposalResp,DisposalScheduleReq ,DisposalUndoReq,DisposalHistResp

router = APIRouter(
    prefix="/api/v1/assets",
    tags=["Assets Disposal"]
    )
@router.post("/{asset_id}/disposal/initiate", status_code=201, response_model=DisposalResp)
async def init_disposal(asset_id: str, req: DisposalInitiateReq, curr_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    asset = db.query(Assets).filter(Assets.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="asset not found")
    
    disposal = AssetDisposals(
        id=str(uuid.uuid4()),
        asset_id=asset_id,
        disposal_method="collected by garbage collection services",
        remarks=req.reason,
        status="initiated"
    )
    
    db.add(disposal)
    db.commit()
    db.refresh(disposal)
    
    return {"msg": "disposal initiated"}

@router.post("/{asset_id}/disposal/schedule", status_code=200, response_model=DisposalResp)
async def schedule_disposal(asset_id: str, req: DisposalScheduleReq, curr_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    disposal = db.query(AssetDisposals).filter(AssetDisposals.asset_id == asset_id, AssetDisposals.status == "initiated").first()
    if not disposal:
        raise HTTPException(status_code=404, detail="disposal request not found")
    
    disposal.disposal_date = req.disposal_date
    disposal.status = "scheduled"
    if req.disposal_method:
        disposal.disposal_method = req.disposal_method
    
    db.commit()
    db.refresh(disposal)
    
    return {"msg": "disposal scheduled"}

@router.post("/{asset_id}/disposal/approve", status_code=200, response_model=DisposalResp)
async def approve_disposal(asset_id: str, req: DisposalApproveReq, curr_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    disposal = db.query(AssetDisposals).filter(AssetDisposals.asset_id == asset_id, AssetDisposals.status == "scheduled").first()
    if not disposal:
        raise HTTPException(status_code=404, detail="scheduled disposal not found")
    
    disposal.status = "approved"
    disposal.approved_by = curr_user.id
    
    db.commit()
    db.refresh(disposal)
    
    return {"msg": "disposal approved"}

@router.post("/{asset_id}/disposal/execute", status_code=200, response_model=DisposalResp)
async def execute_disposal(asset_id: str, req: DisposalExecuteReq, curr_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    disposal = db.query(AssetDisposals).filter(AssetDisposals.asset_id == asset_id, AssetDisposals.status == "approved").first()
    if not disposal:
        raise HTTPException(status_code=404, detail="approved disposal not found")
    
    disposal.status = "executed"
    if req.proceeds_amount:
        disposal.proceeds_amount = req.proceeds_amount
    if req.disposal_cost:
        disposal.disposal_cost = req.disposal_cost
    if req.disposal_method:
        disposal.disposal_method = req.disposal_method
    if req.remarks:
        disposal.remarks = req.remarks
    
    asset = db.query(Assets).filter(Assets.id == asset_id).first()
    if asset:
        asset.status = AssetStatus.DISPOSED
        asset.disposal_date = disposal.disposal_date
        asset.disposal_value = disposal.proceeds_amount
        asset.disposal_method = disposal.disposal_method
    
    db.commit()
    db.refresh(disposal)
    
    return {"msg": "disposal executed"}

@router.post("/{asset_id}/disposal/undo", status_code=200, response_model=DisposalResp)
async def undo_disposal(asset_id: str, req: DisposalUndoReq, curr_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    disposal = db.query(AssetDisposals).filter(AssetDisposals.asset_id == asset_id, AssetDisposals.status == "executed").first()
    if not disposal:
        raise HTTPException(status_code=404, detail="executed disposal not found")
    
    disposal.status = "undone"
    disposal.remarks = f"{disposal.remarks or ''} | UNDONE: {req.justification}"
    
    asset = db.query(Assets).filter(Assets.id == asset_id).first()
    if asset:
        asset.status = AssetStatus.OPERATIONAL
        asset.disposal_date = None
        asset.disposal_value = None
        asset.disposal_method = None
    
    db.commit()
    db.refresh(disposal)
    
    return {"msg": "disposal undone"}

@router.get("/disposals", status_code=200, response_model=List[DisposalHistResp])
async def get_all_disposals(dept_id: str = None, stat: str = None, start_date: date = None, end_date: date = None, curr_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(AssetDisposals)
    
    if dept_id:
        q = q.join(Assets).filter(Assets.department_id == dept_id)
    if stat:
        q = q.filter(AssetDisposals.status == stat)
    if start_date:
        q = q.filter(AssetDisposals.disposal_date >= start_date)
    if end_date:
        q = q.filter(AssetDisposals.disposal_date <= end_date)
    
    disposals = q.all()
    return disposals

@router.get("/{asset_id}/disposal/history", status_code=200, response_model=List[DisposalHistResp])
async def get_disposal_hist(asset_id: str, curr_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    hist = db.query(AssetDisposals).filter(AssetDisposals.asset_id == asset_id).all()
    return hist