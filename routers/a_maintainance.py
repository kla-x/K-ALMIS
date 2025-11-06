from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List
import uuid
from ..models import MaintenanceRequests,Assets,User,AssetStatus, MaintenanceStatus, MaintenanceType,PriorityLevel, SeverityLevel,IssueCategory
from..schemas.maintain_dispose import MaintenanceApproveReq,MaintenanceCompleteReq,MaintenanceCompleteResp,MaintenanceHistResp,MaintenanceInitiateReq,MaintenanceResp,MaintenanceScheduleReq,MaintenanceStartReq
from ..utilities import get_current_user
from ..services.policy_eval import check_simple_permission,require_specific_role
from ..schemas.main import LogLevel, ActionType
from ..services.logger_queue import enqueue_log
from ..system_vars import sys_logger

from ..database import get_db

router = APIRouter(
    prefix="/api/v1/assets",
    tags=["Assets Maintainance"]
    )


@router.post("/{asset_id}/maintenance/initiate", status_code=201, response_model=MaintenanceResp)
async def init_maint_req(asset_id: str, req: MaintenanceInitiateReq, curr_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not check_simple_permission(curr_user, "maintenance", "create"):
        if sys_logger:
            await enqueue_log(
                user_id=curr_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="maintenance_requests",
                target_id=None,
                details=f"Unauthorized attempt to initiate maintenance for asset {asset_id}",
                level=LogLevel.WARNING
            )
        raise HTTPException(status_code=403, detail="Not enough permissions")

    asset = db.query(Assets).filter(Assets.id == asset_id).first()
    if not asset:
        if sys_logger:
            await enqueue_log(
                user_id=curr_user.id,
                action=ActionType.VIEW,
                target_table="assets",
                target_id=asset_id,
                details="Asset not found when initiating maintenance",
                level=LogLevel.INFO
            )
        raise HTTPException(status_code=404, detail="asset not found")
    
    asset.status = AssetStatus.UNDER_MAINTENANCE

    maint_req = MaintenanceRequests(
        id=str(uuid.uuid4()),
        asset_id=asset_id,
        requested_by=curr_user.id,
        issue_type=req.issue_type,
        description=req.description,
        status="initiated",
        maintenance_type=req.maintenance_type or MaintenanceType.CORRECTIVE,
        issue_category=req.issue_category or IssueCategory.OTHER,
        priority=req.priority or PriorityLevel.MEDIUM,
        severity=req.severity or SeverityLevel.MINOR
    )

    db.add(maint_req)
    db.commit()
    db.refresh(asset)
    db.refresh(maint_req)

    if sys_logger:
        await enqueue_log(
            user_id=curr_user.id,
            action=ActionType.CREATE,
            target_table="maintenance_requests",
            target_id=maint_req.id,
            details={"route": "initiate", "asset_id": asset_id, "payload": req.dict(exclude_unset=True)},
            level=LogLevel.INFO
        )

    return {"msg": "maintenance initiated"}

@router.post("/{asset_id}/maintenance/schedule", status_code=200, response_model=MaintenanceResp)
async def schedule_maint(asset_id: str, req: MaintenanceScheduleReq, curr_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not check_simple_permission(curr_user, "maintenance", "update"):
        if sys_logger:
            await enqueue_log(
                user_id=curr_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="maintenance_requests",
                target_id=None,
                details=f"Unauthorized attempt to schedule maintenance for asset {asset_id}",
                level=LogLevel.WARNING
            )
        raise HTTPException(status_code=403, detail="Not enough permissions")

    asset = db.query(Assets).filter(Assets.id == asset_id).first()
    if not asset:
        if sys_logger:
            await enqueue_log(
                user_id=curr_user.id,
                action=ActionType.VIEW,
                target_table="assets",
                target_id=asset_id,
                details="Asset not found when scheduling maintenance",
                level=LogLevel.INFO
            )
        raise HTTPException(status_code=404, detail="asset not found")
    
    asset.status = AssetStatus.SCHEDULED_MAINTENANCE

    maint_req = MaintenanceRequests(
        id=str(uuid.uuid4()),
        asset_id=asset_id,
        requested_by=curr_user.id,
        issue_type=req.issue_type,
        description=req.description,
        status="scheduled",
        maintenance_type=req.maintenance_type or MaintenanceType.PREVENTIVE,
        issue_category=req.issue_category or IssueCategory.OTHER,
        priority=req.priority or PriorityLevel.MEDIUM,
        severity=req.severity or SeverityLevel.MINOR,
        maintenance_date=req.maintenance_date
    )

    db.add(maint_req)
    db.commit()
    db.refresh(asset)
    db.refresh(maint_req)

    if sys_logger:
        await enqueue_log(
            user_id=curr_user.id,
            action=ActionType.CREATE,
            target_table="maintenance_requests",
            target_id=maint_req.id,
            details={"route": "schedule", "asset_id": asset_id, "payload": req.dict(exclude_unset=True)},
            level=LogLevel.INFO
        )

    return {"msg": "maintenance scheduled"}


@router.post("/{asset_id}/maintenance/approve", status_code=200, response_model=MaintenanceResp)
async def approve_maint(asset_id: str, req: MaintenanceApproveReq, curr_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    state, det = require_specific_role(curr_user, ["maintenance_manager"])
    if not state:
        if sys_logger:
            await enqueue_log(
                user_id=curr_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="maintenance_requests",
                target_id=None,
                details=f"Unauthorized attempt to approve maintenance for asset {asset_id}: {det}",
                level=LogLevel.CRITICAL
            )
        raise HTTPException(status_code=403, detail=det)

    maint_req = db.query(MaintenanceRequests).filter(MaintenanceRequests.asset_id == asset_id, MaintenanceRequests.status == "scheduled").first()
    if not maint_req:
        raise HTTPException(status_code=404, detail="scheduled maintenance not found")
    
    maint_req.status = "approved"
    db.commit()
    db.refresh(maint_req)

    if sys_logger:
        await enqueue_log(
            user_id=curr_user.id,
            action=ActionType.UPDATE,
            target_table="maintenance_requests",
            target_id=maint_req.id,
            details={"route": "approve"},
            level=LogLevel.INFO
        )
    
    return {"msg": "maintenance approved"}


@router.post("/{asset_id}/maintenance/start", status_code=200, response_model=MaintenanceResp)
async def start_maint(asset_id: str, req: MaintenanceStartReq, curr_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    allowed = curr_user.id == db.query(Assets).filter(Assets.id == asset_id).first().owner_id or check_simple_permission(curr_user, "asset", "maintain")
    if not allowed:
        if sys_logger:
            await enqueue_log(
                user_id=curr_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="maintenance_requests",
                target_id=None,
                details=f"Unauthorized attempt to start maintenance for asset {asset_id}",
                level=LogLevel.WARNING
            )
        raise HTTPException(status_code=403, detail="Not enough permissions")

    maint_req = db.query(MaintenanceRequests).filter(MaintenanceRequests.asset_id == asset_id, MaintenanceRequests.status == "approved").first()
    if not maint_req:
        raise HTTPException(status_code=404, detail="approved maintenance not found")
    
    maint_req.status = "in_progress"
    db.commit()
    db.refresh(maint_req)

    if sys_logger:
        await enqueue_log(
            user_id=curr_user.id,
            action=ActionType.UPDATE,
            target_table="maintenance_requests",
            target_id=maint_req.id,
            details={"route": "start"},
            level=LogLevel.INFO
        )
    
    return {"msg": "maintenance started"}


@router.post("/{asset_id}/maintenance/complete", status_code=200, response_model=MaintenanceCompleteResp)
async def complete_maint(asset_id: str, req: MaintenanceCompleteReq, curr_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    allowed = curr_user.id == db.query(Assets).filter(Assets.id == asset_id).first().owner_id or check_simple_permission(curr_user, "asset", "maintain")
    if not allowed:
        if sys_logger:
            await enqueue_log(user_id=curr_user.id, action=ActionType.SUSPICIOUS_ACTIVITY, target_table="maintenance_requests", target_id=None, details=f"Unauthorized attempt to complete maintenance for asset {asset_id}", level=LogLevel.WARNING)
        raise HTTPException(status_code=403, detail="Not enough permissions")

    maint_req = db.query(MaintenanceRequests).filter(MaintenanceRequests.asset_id == asset_id, MaintenanceRequests.status == "in_progress").first()
    if not maint_req:
        raise HTTPException(status_code=404, detail="active maintenance not found")

    maint_req.status = "completed"
    maint_req.completed_at = datetime.now()
    if maint_req.started_at:
        maint_req.duration = maint_req.completed_at - maint_req.started_at
    maint_req.cost = req.cost

    maint_req.outcome = req.outcome
    maint_req.notes = req.notes

    asset = db.query(Assets).filter(Assets.id == asset_id).first()
    if asset and req.outcome == "fixed":
        asset.status = AssetStatus.OPERATIONAL

    db.commit()
    db.refresh(maint_req)

    if sys_logger:
        await enqueue_log(user_id=curr_user.id, action=ActionType.UPDATE, target_table="maintenance_requests", target_id=maint_req.id, details={"route": "complete", "payload": req.dict(exclude_unset=True)}, level=LogLevel.INFO)

    return {
        "id": maint_req.id,
        "asset_id": maint_req.asset_id,
        "status": maint_req.status,
        "started_at": maint_req.started_at,
        "completed_at": maint_req.completed_at,
        "duration": str(maint_req.duration) if maint_req.duration else None,
        "cost": float(maint_req.cost) if maint_req.cost else None,
        "paid_by": maint_req.paid_by,
        "outcome": maint_req.outcome,
        "notes": maint_req.notes
    }
@router.post("/{asset_id}/maintenance/complete", status_code=200, response_model=MaintenanceCompleteResp)
async def complete_maint(asset_id: str, req: MaintenanceCompleteReq, curr_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    allowed = curr_user.id == db.query(Assets).filter(Assets.id == asset_id).first().owner_id or check_simple_permission(curr_user, "asset", "maintain")
    if not allowed:
        if sys_logger:
            await enqueue_log(user_id=curr_user.id, action=ActionType.SUSPICIOUS_ACTIVITY, target_table="maintenance_requests", target_id=None, details=f"Unauthorized attempt to complete maintenance for asset {asset_id}", level=LogLevel.WARNING)
        raise HTTPException(status_code=403, detail="Not enough permissions")

    maint_req = db.query(MaintenanceRequests).filter(MaintenanceRequests.asset_id == asset_id, MaintenanceRequests.status == "in_progress").first()
    if not maint_req:
        raise HTTPException(status_code=404, detail="active maintenance not found")

    maint_req.status = "completed"
    maint_req.completed_at = datetime.now()
    if maint_req.started_at:
        maint_req.duration = maint_req.completed_at - maint_req.started_at
    maint_req.cost = req.cost
    maint_req.paid_by = req.paid_by
    maint_req.outcome = req.outcome
    maint_req.notes = req.notes

    asset = db.query(Assets).filter(Assets.id == asset_id).first()
    if asset and req.outcome == "fixed":
        asset.status = AssetStatus.OPERATIONAL

    db.commit()
    db.refresh(maint_req)

    if sys_logger:
        await enqueue_log(user_id=curr_user.id, action=ActionType.UPDATE, target_table="maintenance_requests", target_id=maint_req.id, details={"route": "complete", "payload": req.dict(exclude_unset=True)}, level=LogLevel.INFO)

    return {
        "id": maint_req.id,
        "asset_id": maint_req.asset_id,
        "status": maint_req.status,
        "started_at": maint_req.started_at,
        "completed_at": maint_req.completed_at,
        "duration": str(maint_req.duration) if maint_req.duration else None,
        "cost": float(maint_req.cost) if maint_req.cost else None,
        "paid_by": maint_req.paid_by,
        "outcome": maint_req.outcome,
        "notes": maint_req.notes
    }

@router.get("/{asset_id}/maintenance/history", status_code=200, response_model=List[MaintenanceHistResp])
async def get_maint_hist(asset_id: str, curr_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not check_simple_permission(curr_user, "maintenance", "read"):
        if sys_logger:
            await enqueue_log(
                user_id=curr_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="maintenance_requests",
                target_id=None,
                details=f"Unauthorized attempt to fetch maintenance history for asset {asset_id}",
                level=LogLevel.WARNING
            )
        raise HTTPException(status_code=403, detail="Not enough permissions")

    hist = db.query(MaintenanceRequests).filter(MaintenanceRequests.asset_id == asset_id).all()

    if sys_logger:
        await enqueue_log(
            user_id=curr_user.id,
            action=ActionType.VIEW,
            target_table="maintenance_requests",
            target_id=None,
            details={"route": "history", "asset_id": asset_id},
            level=LogLevel.INFO
        )
    return hist


@router.get("/maintenance/upcoming", status_code=200, response_model=List[MaintenanceHistResp])
async def get_upcoming_maint(dept_id: str = None, start_date: date = None, end_date: date = None, curr_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not check_simple_permission(curr_user, "maintenance", "read"):
        if sys_logger:
            await enqueue_log(
                user_id=curr_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="maintenance_requests",
                target_id=None,
                details="Unauthorized attempt to fetch upcoming maintenance",
                level=LogLevel.WARNING
            )
        raise HTTPException(status_code=403, detail="Not enough permissions")

    q = db.query(MaintenanceRequests).filter(MaintenanceRequests.status.in_(["scheduled", "approved"]))
    if dept_id:
        q = q.join(Assets).filter(Assets.department_id == dept_id)
    if start_date:
        q = q.filter(MaintenanceRequests.maintenance_date >= start_date)
    if end_date:
        q = q.filter(MaintenanceRequests.maintenance_date <= end_date)
    
    upcoming = q.all()

    if sys_logger:
        await enqueue_log(
            user_id=curr_user.id,
            action=ActionType.VIEW,
            target_table="maintenance_requests",
            target_id=None,
            details={"route": "upcoming", "dept_id": dept_id, "range": [start_date, end_date]},
            level=LogLevel.INFO
        )
    return upcoming
