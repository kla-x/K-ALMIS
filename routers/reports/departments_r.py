from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
from datetime import datetime
from collections import defaultdict

from ...database import get_db
from ...models import (
    Assets, User, Departments
)
from ...utilities import get_current_user
from ...system_vars import sys_logger
from ...services.logger_queue import enqueue_log
from ...schemas.main import ActionType, LogLevel

router = APIRouter(prefix="/api/v1/r/reports", tags=["Asset Departments Reports"])

@router.get("/department-assets/{dept_id}")
async def get_department_asset_report(
    dept_id: str,
    include_top_assets: bool = Query(True),
    top_assets_limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """6. Department Asset Report"""
    
    department = db.query(Departments).filter(Departments.dept_id == dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    assets = db.query(Assets).filter(
        Assets.department_id == dept_id,
        Assets.is_deleted == False
    ).all()
    
    total_assets = len(assets)
    total_value = sum(asset.current_value or asset.acquisition_cost or Decimal(0) for asset in assets)
    
    by_category = defaultdict(int)
    for asset in assets:
        by_category[asset.category.value] += 1
    
    by_status = defaultdict(int)
    for asset in assets:
        by_status[asset.status.value] += 1
    
    top_assets = []
    if include_top_assets:
        sorted_assets = sorted(
            assets,
            key=lambda x: x.current_value or x.acquisition_cost or Decimal(0),
            reverse=True
        )[:top_assets_limit]
        top_assets = [
            {
                "id": a.id,
                "tag_number": a.tag_number,
                "description": a.description,
                "category": a.category.value,
                "value": float(a.current_value or a.acquisition_cost or 0)
            }
            for a in sorted_assets
        ]
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id=f"department_assets_{dept_id}",
            details=None,
            level=LogLevel.INFO
        )
    
    return {
        "department_id": dept_id,
        "department_name": department.name,
        "total_assets": total_assets,
        "total_value": float(total_value),
        "by_category": dict(by_category),
        "by_status": dict(by_status),
        "top_assets": top_assets,
        "generated_at": datetime.now()
    }


@router.get("/user-responsibility")
async def get_user_responsibility_report(
    department_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """7. User Responsibility Report - Assets assigned per user"""
    
    query = db.query(Assets).filter(
        Assets.is_deleted == False,
        Assets.responsible_officer_id.isnot(None)
    )
    
    if department_id:
        query = query.filter(Assets.department_id == department_id)
    
    assets = query.all()
    
    user_assets = defaultdict(lambda: {"count": 0, "value": Decimal(0), "assets": []})
    for asset in assets:
        if asset.responsible_officer:
            user_id = asset.responsible_officer.id
            user_name = f"{asset.responsible_officer.first_name} {asset.responsible_officer.last_name}"
            user_assets[user_id]["user_name"] = user_name
            user_assets[user_id]["email"] = asset.responsible_officer.email
            user_assets[user_id]["department"] = asset.department.name if asset.department else None
            user_assets[user_id]["count"] += 1
            user_assets[user_id]["value"] += asset.current_value or asset.acquisition_cost or Decimal(0)
            user_assets[user_id]["assets"].append({
                "id": asset.id,
                "tag_number": asset.tag_number,
                "description": asset.description,
                "value": float(asset.current_value or asset.acquisition_cost or 0)
            })
    
    user_list = [
        {
            "user_id": user_id,
            "user_name": data["user_name"],
            "email": data["email"],
            "department": data["department"],
            "asset_count": data["count"],
            "total_value": float(data["value"]),
            "assets": data["assets"]
        }
        for user_id, data in user_assets.items()
    ]
    user_list.sort(key=lambda x: x["total_value"], reverse=True)
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="user_responsibility",
            details={"filters": {"department_id": department_id}},
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "total_users": len(user_list),
            "total_assets": sum(u["asset_count"] for u in user_list),
            "total_value": sum(u["total_value"] for u in user_list)
        },
        "users": user_list,
        "generated_at": datetime.now()
    }
