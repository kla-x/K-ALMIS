from fastapi import status, Depends,HTTPException,APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..database import get_db
from ..utilities import generate_id,get_current_user

from ..schemas.assets import AssetTransfereInitiate,TransferStatusEnum,TransSearchParams
from ..models import User, AssetTransfers,Assets
from datetime import timezone, datetime

router = APIRouter(
    prefix="/api/v1/transfers",
    tags=["Assets Transfers"]
    )

@router.post("/initiate", status_code=status.HTTP_200_OK)
async def transfer_an_asset(det: AssetTransfereInitiate,curr_user : User = Depends(get_current_user),db: Session = Depends(get_db)):
    
    asset = db.query(Assets).filter(Assets.id == det.asset_id).first()
    transfa = AssetTransfers(
        id = generate_id(40),
        asset_id = det.asset_id,
        from_user_id = asset.responsible_officer_id,
        to_user_id = det.to_user_id,
        from_dept_id = asset.department_id,
        to_dept_id = det.to_dept_id,

        initiated_by = curr_user.id,
        initiated_date = datetime.now(timezone.utc),
        approved_by = None,
        approval_date = None,
        completed_date = None,

        status = TransferStatusEnum.INITIATED,
        transfer_reason = det.transfer_reason,
        remarks = det.remarks,
        )
    db.add(transfa)
    db.commit()
    db.refresh(transfa)

    return transfa


@router.get("/",status_code=200)
async def list_transfers_param( p : TransSearchParams = Depends() ,curr_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    """_summary_

    Args:
        u_from : from user id.
        d_from : from department id.
        u_to : to user id
        d_to : department id destination
        init_by : id of initializer
        f_init_date : initialized from date 
        t_init_date : initialized upto date
        approv_by : who approved  id
        f_approv_date : transferes aproved from date
        t_approv_date : approved upto date
        status : status of approval, [initiated,apptoved,rejected,completed,cancelled]

    Returns:
        List : of all transfers matching filter
    """
    
    
    res = db.query(AssetTransfers)
    if p.u_from:
        res = res.filter(AssetTransfers.from_user_id == p.u_from)
    if p.d_from:
        res = res.filter(AssetTransfers.from_dept_id == p.d_from)
    if p.u_to: 
        res = res.filter(AssetTransfers.to_user_id == p.u_to)
    if p.d_to:
        res = res.filter(AssetTransfers.to_dept_id == p.d_to)
    if p.init_by:
        res = res.filter(AssetTransfers.initiated_by == p.init_by)
    if p.approv_by: 
        res = res.filter(AssetTransfers.approved_by == p.approv_by)
    if p.status:
        res = res.filter(AssetTransfers.status == status)

    if p.f_init_date and not p.t_init_date:
        res = res.filter(AssetTransfers.initiated_date >= p.f_init_date)
    elif p.t_init_date and not p.f_init_date:
        res = res.filter(AssetTransfers.initiated_date <= p.t_init_date)
    elif p.t_init_date and p.f_init_date:
        res = res.filter(AssetTransfers.initiated_date.between(p.f_init_date,p.t_init_date))


    if p.f_approv_date and not p.t_approv_date:
        res = res.filter(AssetTransfers.approval_date >= p.f_approv_date)
    elif p.t_approv_date and not p.f_approv_date:
        res = res.filter(AssetTransfers.approval_date <= p.f_approv_date)
    elif  p.t_approv_date and p.f_approv_date:
        res = res.filter(AssetTransfers.approval_date.between(p.f_approv_date,p.f_approv_date))
    return res

@router.get("/{trans_id}",status_code=200)
async def get_transfer_by_id(trans_id, curr: User = Depends(get_current_user), db: Session = Depends(get_db)):
    transf = db.query(AssetTransfers).filter(AssetTransfers.id == trans_id).first()
    if not transf:
        raise HTTPException(status_code=404, detail="transfer record not found")
    return transf

@router.post("/{trans_id}/approve",status_code=200)
async def approve_a_transfer(trans_id,curr_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    transf = db.query(AssetTransfers).filter(AssetTransfers.id == trans_id).first()
    if not transf:
        raise HTTPException(status_code=404, detail="transfer record not found")
    transf.status = TransferStatusEnum.APPROVED
    db.commit()
    db.refresh(transf)
    return {"msg":"transfer approved"}


@router.post("/{trans_id}/complete",status_code=200)
async def approve_a_transfer(trans_id,curr_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    transf = db.query(AssetTransfers).filter(AssetTransfers.id == trans_id).first()
    if not transf:
        raise HTTPException(status_code=404, detail="transfer record not found")
    transf.status = TransferStatusEnum.COMPLETED
    db.commit()
    db.refresh(transf)
    return {"msg":"transfer completed"}


@router.post("/{asset_id}/history",status_code=200)
async def get_asset_transfer_hist(asset_id,curr_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    hist = db.query(AssetTransfers).filter(AssetTransfers.asset_id == asset_id).all()
    return hist

@router.post("/{trans_id}/reject")
async def reject_transfer_request(trans_id,curr_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    transf = db.query(AssetTransfers).filter(AssetTransfers.id == trans_id).first()
    if not transf:
        raise HTTPException(status_code=404, detail="transfer record not found")
    transf.status = TransferStatusEnum.REJECTED
    db.commit()
    db.refresh(transf)
    return {"msg":"transfer rejected"}

    
@router.post("/{trans_id}/cancel")
async def cancel_a_transfer_request(trans_id,curr_user: User = Depends(get_current_user),db: Session = Depends(get_db)) :
    transf = db.query(AssetTransfers).filter(AssetTransfers.id == trans_id).first()
    if not transf:
        raise HTTPException(status_code=404, detail="transfer record not found")
    transf.status = TransferStatusEnum.CANCELLED
    db.commit()
    db.refresh(transf)
    return {"msg":"transfer cancelled"}  
  
@router.get("/pending")
async def list_all_pending_transfers(curr_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    p = db.query(AssetTransfers).filter(AssetTransfers.status == TransferStatusEnum.PENDING).all()

    return p

@router.get("/by-user/{user_id}")
async def show_all_user_transers(user_id,curr_user: User = Depends(get_current_user),db: Session = Depends(get_db)):

    p = db.query(AssetTransfers).filter(or_( AssetTransfers.to_user_id == user_id,AssetTransfers.from_user_id == user_id)).all()


    return p
