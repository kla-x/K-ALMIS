from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, date, timedelta
from collections import defaultdict

from ...database import get_db
from ...models import (
    Assets, User, MaintenanceRequests, AssetTransfers, 
    AssetDisposals,AssetStatus
)
from ...utilities import get_current_user
from ...system_vars import sys_logger
from ...services.logger_queue import enqueue_log
from ...schemas.main import ActionType, LogLevel

router = APIRouter(prefix="/api/v1/r/reports", tags=["Asset Executive Reports"])

@router.get("/executive-summary")
async def get_executive_summary_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """18. Executive Summary - High-level overview for decision makers"""
    
    assets = db.query(Assets).filter(Assets.is_deleted == False).all()
    
    total_assets = len(assets)
    total_value = sum(a.current_value or a.acquisition_cost or Decimal(0) for a in assets)
    
    operational_count = len([a for a in assets if a.status == AssetStatus.OPERATIONAL])
    operational_pct = (operational_count / total_assets * 100) if total_assets > 0 else 0
    
    under_maintenance = len([a for a in assets if a.status == AssetStatus.UNDER_MAINTENANCE])
    
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_maintenance = db.query(MaintenanceRequests).filter(
        MaintenanceRequests.request_date >= thirty_days_ago
    ).all()
    maintenance_rate = len(recent_maintenance)
    
    recent_disposals = db.query(AssetDisposals).filter(
        AssetDisposals.disposal_date >= thirty_days_ago.date()
    ).count()
    
    last_month_start = (datetime.now() - timedelta(days=60)).date()
    last_month_end = (datetime.now() - timedelta(days=30)).date()
    this_month_start = (datetime.now() - timedelta(days=30)).date()
    
    last_month_assets = db.query(Assets).filter(
        Assets.acquisition_date.between(last_month_start, last_month_end),
        Assets.is_deleted == False
    ).count()
    
    this_month_assets = db.query(Assets).filter(
        Assets.acquisition_date >= this_month_start,
        Assets.is_deleted == False
    ).count()
    
    mom_change = this_month_assets - last_month_assets
    
    category_values = defaultdict(Decimal)
    for asset in assets:
        category_values[asset.category.value] += asset.current_value or asset.acquisition_cost or Decimal(0)
    
    top_categories = sorted(
        [{"category": cat, "value": float(val)} for cat, val in category_values.items()],
        key=lambda x: x["value"],
        reverse=True
    )[:5]
    
    alerts = []
    
    attention_needed = [
        a for a in assets 
        if (a.condition and a.condition.value in ["poor", "fair"]) or 
           a.status.value in ["Impaired", "Lost/Stolen"]
    ]
    if attention_needed:
        alerts.append({
            "type": "warning",
            "message": f"{len(attention_needed)} assets require immediate attention",
            "count": len(attention_needed)
        })
    
    pending_transfers = db.query(AssetTransfers).filter(
        AssetTransfers.status.in_(["initiated", "pending"])
    ).count()
    if pending_transfers > 0:
        alerts.append({
            "type": "info",
            "message": f"{pending_transfers} transfers pending approval",
            "count": pending_transfers
        })
    
    overdue_maintenance = db.query(MaintenanceRequests).filter(
        MaintenanceRequests.status.in_(["scheduled", "approved"]),
        MaintenanceRequests.maintenance_date < datetime.now().date()
    ).count()
    if overdue_maintenance > 0:
        alerts.append({
            "type": "critical",
            "message": f"{overdue_maintenance} maintenance requests overdue",
            "count": overdue_maintenance
        })
    
    unassigned = len([a for a in assets if not a.responsible_officer_id])
    if unassigned > 10:
        alerts.append({
            "type": "warning",
            "message": f"{unassigned} assets without responsible officers",
            "count": unassigned
        })
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="executive_summary",
            details=None,
            level=LogLevel.INFO
        )
    
    return {
        "overview": {
            "total_assets": total_assets,
            "total_value": float(total_value),
            "operational_percentage": round(operational_pct, 2),
            "under_maintenance": under_maintenance
        },
        "key_metrics": {
            "operational_count": operational_count,
            "maintenance_rate_30d": maintenance_rate,
            "disposal_rate_30d": recent_disposals,
            "month_over_month_change": mom_change
        },
        "top_5_categories": top_categories,
        "critical_alerts": alerts,
        "generated_at": datetime.now()
    }

