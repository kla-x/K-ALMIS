from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date


from ...database import get_db
from ...models import Assets, User,AssetTransfers, AssetDisposals
from ...utilities import get_current_user
from ...system_vars import sys_logger
from ...services.logger_queue import enqueue_log
from ...schemas.main import ActionType, LogLevel
from sqlalchemy import  or_
router = APIRouter(prefix="/api/v1/r/reports", tags=["Asset Transfers n Disposals Reports"])

@router.get("/pending-transfers-disposals")
async def get_pending_transfers_disposals_report(
    department_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """11. Pending Transfers & Disposals Report"""
    
    transfer_query = db.query(AssetTransfers).filter(
        AssetTransfers.status.in_(["initiated", "pending", "approved"])
    )
    if department_id:
        transfer_query = transfer_query.filter(
            or_(
                AssetTransfers.from_dept_id == department_id,
                AssetTransfers.to_dept_id == department_id
            )
        )
    
    pending_transfers = transfer_query.all()
    
    transfer_list = [
        {
            "id": t.id,
            "asset_id": t.asset_id,
            "asset_description": t.asset.description if t.asset else None,
            "asset_tag": t.asset.tag_number if t.asset else None,
            "from_department": t.from_dept_id,
            "to_department": t.to_dept_id,
            "initiated_by": f"{t.initiated_by_user.first_name} {t.initiated_by_user.last_name}" if t.initiated_by_user else None,
            "initiated_date": t.initiated_date,
            "status": t.status.value,
            "transfer_reason": t.transfer_reason,
            "value": float(t.asset.current_value or t.asset.acquisition_cost or 0) if t.asset else 0
        }
        for t in pending_transfers
    ]
    
    disposal_query = db.query(AssetDisposals).filter(
        AssetDisposals.status.in_(["initiated", "scheduled", "approved"])
    )
    if department_id:
        disposal_query = disposal_query.join(Assets).filter(Assets.department_id == department_id)
    
    pending_disposals = disposal_query.all()
    
    disposal_list = [
        {
            "id": d.id,
            "asset_id": d.asset_id,
            "asset_description": d.asset.description if d.asset else None,
            "asset_tag": d.asset.tag_number if d.asset else None,
            "department": d.asset.department.name if d.asset and d.asset.department else None,
            "disposal_method": d.disposal_method,
            "disposal_date": d.disposal_date,
            "status": d.status.value,
            "value": float(d.asset.current_value or d.asset.acquisition_cost or 0) if d.asset else 0
        }
        for d in pending_disposals
    ]
    
    total_transfer_value = sum(t["value"] for t in transfer_list)
    total_disposal_value = sum(d["value"] for d in disposal_list)
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="pending_transfers_disposals",
            details={"filters": {"department_id": department_id}},
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "pending_transfers": len(transfer_list),
            "pending_disposals": len(disposal_list),
            "total_transfer_value": total_transfer_value,
            "total_disposal_value": total_disposal_value
        },
        "pending_transfers": transfer_list,
        "pending_disposals": disposal_list,
        "generated_at": datetime.now()
    }


@router.get("/transfer-disposal-history")
async def get_transfer_disposal_history_report(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    department_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """12. Transfer & Disposal History Report"""
    
    transfer_query = db.query(AssetTransfers).filter(
        AssetTransfers.status == "completed"
    )
    if date_from:
        transfer_query = transfer_query.filter(AssetTransfers.completed_date >= date_from)
    if date_to:
        transfer_query = transfer_query.filter(AssetTransfers.completed_date <= date_to)
    if department_id:
        transfer_query = transfer_query.filter(
            or_(
                AssetTransfers.from_dept_id == department_id,
                AssetTransfers.to_dept_id == department_id
            )
        )
    
    completed_transfers = transfer_query.all()
    
    transfer_list = [
        {
            "id": t.id,
            "asset_id": t.asset_id,
            "asset_description": t.asset.description if t.asset else None,
            "from_department": t.from_dept_id,
            "to_department": t.to_dept_id,
            "completed_date": t.completed_date,
            "value": float(t.asset.current_value or t.asset.acquisition_cost or 0) if t.asset else 0
        }
        for t in completed_transfers
    ]
    
    disposal_query = db.query(AssetDisposals).filter(
        AssetDisposals.status == "executed"
    )
    if date_from:
        disposal_query = disposal_query.filter(AssetDisposals.disposal_date >= date_from)
    if date_to:
        disposal_query = disposal_query.filter(AssetDisposals.disposal_date <= date_to)
    if department_id:
        disposal_query = disposal_query.join(Assets).filter(Assets.department_id == department_id)
    
    executed_disposals = disposal_query.all()
    
    disposal_list = [
        {
            "id": d.id,
            "asset_id": d.asset_id,
            "asset_description": d.asset.description if d.asset else None,
            "disposal_method": d.disposal_method,
            "disposal_date": d.disposal_date,
            "proceeds_amount": float(d.proceeds_amount or 0),
            "disposal_cost": float(d.disposal_cost or 0),
            "net_proceeds": float((d.proceeds_amount or 0) - (d.disposal_cost or 0))
        }
        for d in executed_disposals
    ]
    
    total_proceeds = sum(d["proceeds_amount"] for d in disposal_list)
    total_disposal_costs = sum(d["disposal_cost"] for d in disposal_list)
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="transfer_disposal_history",
            details={"filters": {"department_id": department_id, "date_from": str(date_from), "date_to": str(date_to)}},
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "completed_transfers": len(transfer_list),
            "executed_disposals": len(disposal_list),
            "total_proceeds": total_proceeds,
            "total_disposal_costs": total_disposal_costs,
            "net_proceeds": total_proceeds - total_disposal_costs
        },
        "completed_transfers": transfer_list,
        "executed_disposals": disposal_list,
        "generated_at": datetime.now()
    }
