from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
from datetime import datetime, date, timedelta
from collections import defaultdict

from ...database import get_db
from ...models import  Assets, User, MaintenanceRequests
from ...utilities import get_current_user
from ...system_vars import sys_logger
from ...services.logger_queue import enqueue_log
from ...schemas.main import ActionType, LogLevel

router = APIRouter(prefix="/api/v1/r/reports", tags=["Asset Maintainance Reports"])

@router.get("/maintenance-summary")
async def get_maintenance_summary_report(
    department_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """8. Maintenance Summary Report"""
    
    query = db.query(MaintenanceRequests)
    
    if department_id:
        query = query.join(Assets).filter(Assets.department_id == department_id)
    if date_from:
        query = query.filter(MaintenanceRequests.request_date >= date_from)
    if date_to:
        query = query.filter(MaintenanceRequests.request_date <= date_to)
    
    requests = query.all()
    
    by_status = defaultdict(int)
    for req in requests:
        by_status[req.status.value] += 1
    
    by_priority = defaultdict(int)
    for req in requests:
        by_priority[req.priority.value] += 1
    
    by_type = defaultdict(int)
    for req in requests:
        by_type[req.maintenance_type.value] += 1
    
    total_cost = sum(req.cost or Decimal(0) for req in requests)
    completed_requests = [r for r in requests if r.status.value == "completed"]
    avg_cost = total_cost / len(completed_requests) if completed_requests else Decimal(0)
    
    asset_request_count = defaultdict(int)
    for req in requests:
        asset_request_count[req.asset_id] += 1
    
    high_maintenance = [
        {
            "asset_id": asset_id,
            "request_count": count,
            "asset": db.query(Assets).filter(Assets.id == asset_id).first().description
        }
        for asset_id, count in asset_request_count.items() if count >= 3
    ]
    high_maintenance.sort(key=lambda x: x["request_count"], reverse=True)
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="maintenance_summary",
            details={"filters": {"department_id": department_id, "date_from": str(date_from), "date_to": str(date_to)}},
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "total_requests": len(requests),
            "total_cost": float(total_cost),
            "average_cost": float(avg_cost),
            "completed": by_status.get("completed", 0),
            "pending": by_status.get("initiated", 0) + by_status.get("scheduled", 0),
            "in_progress": by_status.get("in_progress", 0)
        },
        "by_status": dict(by_status),
        "by_priority": dict(by_priority),
        "by_type": dict(by_type),
        "high_maintenance_assets": high_maintenance[:10],
        "generated_at": datetime.now()
    }


@router.get("/upcoming-maintenance")
async def get_upcoming_maintenance_report(
    days_ahead: int = Query(30, ge=1, le=365),
    department_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """9. Upcoming Maintenance Schedule"""
    
    end_date = datetime.now().date() + timedelta(days=days_ahead)
    
    query = db.query(MaintenanceRequests).filter(
        MaintenanceRequests.status.in_(["scheduled", "approved"]),
        MaintenanceRequests.maintenance_date.isnot(None),
        MaintenanceRequests.maintenance_date <= end_date
    )
    
    if department_id:
        query = query.join(Assets).filter(Assets.department_id == department_id)
    
    scheduled = query.order_by(MaintenanceRequests.maintenance_date).all()
    
    scheduled_list = [
        {
            "id": req.id,
            "asset_id": req.asset_id,
            "asset_description": req.asset.description if req.asset else None,
            "asset_tag": req.asset.tag_number if req.asset else None,
            "department": req.asset.department.name if req.asset and req.asset.department else None,
            "maintenance_date": req.maintenance_date,
            "priority": req.priority.value,
            "type": req.maintenance_type.value,
            "status": req.status.value,
            "assigned_to": f"{req.assignee.first_name} {req.assignee.last_name}" if req.assignee else None
        }
        for req in scheduled
    ]
    
    by_date = defaultdict(list)
    for item in scheduled_list:
        by_date[str(item["maintenance_date"])].append(item)
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="upcoming_maintenance",
            details={"filters": {"department_id": department_id, "days_ahead": days_ahead}},
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "total_scheduled": len(scheduled),
            "days_ahead": days_ahead,
            "date_range": {
                "from": datetime.now().date(),
                "to": end_date
            }
        },
        "scheduled_maintenance": scheduled_list,
        "by_date": dict(by_date),
        "generated_at": datetime.now()
    }


@router.get("/maintenance-backlog")
async def get_maintenance_backlog_report(
    department_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """10. Maintenance Backlog - Overdue and aging requests"""
    
    query = db.query(MaintenanceRequests).filter(
        MaintenanceRequests.status.in_(["initiated", "scheduled", "approved"])
    )
    
    if department_id:
        query = query.join(Assets).filter(Assets.department_id == department_id)
    
    pending = query.all()
    
    now = datetime.now()
    overdue = []
    aging = []
    
    for req in pending:
        days_pending = (now - req.request_date).days if req.request_date else 0
        
        item = {
            "id": req.id,
            "asset_id": req.asset_id,
            "asset_description": req.asset.description if req.asset else None,
            "asset_tag": req.asset.tag_number if req.asset else None,
            "department": req.asset.department.name if req.asset and req.asset.department else None,
            "request_date": req.request_date,
            "days_pending": days_pending,
            "priority": req.priority.value,
            "status": req.status.value,
            "maintenance_type": req.maintenance_type.value
        }
        
        if req.maintenance_date and req.maintenance_date < now.date():
            item["days_overdue"] = (now.date() - req.maintenance_date).days
            overdue.append(item)
        elif days_pending > 14:
            aging.append(item)
    
    overdue.sort(key=lambda x: x.get("days_overdue", 0), reverse=True)
    aging.sort(key=lambda x: x["days_pending"], reverse=True)
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="maintenance_backlog",
            details={"filters": {"department_id": department_id}},
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "total_pending": len(pending),
            "overdue_count": len(overdue),
            "aging_count": len(aging)
        },
        "overdue_maintenance": overdue,
        "aging_maintenance": aging,
        "generated_at": datetime.now()
    }

