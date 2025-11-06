from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
from datetime import datetime, date
from collections import defaultdict

from ...database import get_db
from ...models import Assets, User
from ...utilities import get_current_user
from ...asset_utils import format_attributes_for_display, get_category_specific_reports_fields
from ...system_vars import sys_logger
from ...services.logger_queue import enqueue_log
from ...schemas.main import ActionType, LogLevel
from sqlalchemy import  or_

router = APIRouter(prefix="/api/v1/r/reports", tags=["Asset Basic Reports"])

@router.get("/asset-summary-dashboard")
async def get_asset_summary_dashboard(
    department_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """1. Asset Summary Dashboard - Overview of all assets"""
    
    query = db.query(Assets).filter(Assets.is_deleted == False)
    
    if department_id:
        query = query.filter(Assets.department_id == department_id)
    if date_from:
        query = query.filter(Assets.acquisition_date >= date_from)
    if date_to:
        query = query.filter(Assets.acquisition_date <= date_to)
    
    assets = query.all()
    
    total_assets = len(assets)
    total_value = sum(asset.current_value or asset.acquisition_cost or Decimal(0) for asset in assets)
    
    by_category = defaultdict(lambda: {"count": 0, "value": Decimal(0)})
    for asset in assets:
        by_category[asset.category]["count"] += 1
        by_category[asset.category]["value"] += asset.current_value or asset.acquisition_cost or Decimal(0)
    
    by_status = defaultdict(lambda: {"count": 0, "value": Decimal(0)})
    for asset in assets:
        by_status[asset.status.value]["count"] += 1
        by_status[asset.status.value]["value"] += asset.current_value or asset.acquisition_cost or Decimal(0)
    
    by_condition = defaultdict(lambda: {"count": 0, "value": Decimal(0)})
    for asset in assets:
        condition = asset.condition.value if asset.condition else "unknown"
        by_condition[condition]["count"] += 1
        by_condition[condition]["value"] += asset.current_value or asset.acquisition_cost or Decimal(0)
    
    dept_breakdown = defaultdict(lambda: {"count": 0, "value": Decimal(0)})
    for asset in assets:
        if asset.department:
            dept_breakdown[asset.department.name]["count"] += 1
            dept_breakdown[asset.department.name]["value"] += asset.current_value or asset.acquisition_cost or Decimal(0)
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="asset_summary_dashboard",
            details={"filters": {"department_id": department_id, "date_from": str(date_from), "date_to": str(date_to)}},
            level=LogLevel.INFO
        )
    
    return {
        "total_assets": total_assets,
        "total_value": float(total_value),
        "by_category": {k: {"count": v["count"], "value": float(v["value"])} for k, v in by_category.items()},
        "by_status": {k: {"count": v["count"], "value": float(v["value"])} for k, v in by_status.items()},
        "by_condition": {k: {"count": v["count"], "value": float(v["value"])} for k, v in by_condition.items()},
        "by_department": {k: {"count": v["count"], "value": float(v["value"])} for k, v in dept_breakdown.items()},
        "generated_at": datetime.now(),
        "filters_applied": {
            "department_id": department_id,
            "date_from": date_from,
            "date_to": date_to
        }
    }


@router.get("/depreciation")
async def get_depreciation_report(
    department_id: Optional[str] = None,
    category: Optional[str] = None,
    min_depreciation_rate: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """2. Depreciation Report - Asset values and depreciation analysis"""
    
    query = db.query(Assets).filter(
        Assets.is_deleted == False,
        Assets.depreciation_rate.isnot(None),
        Assets.acquisition_date.isnot(None)
    )
    
    if department_id:
        query = query.filter(Assets.department_id == department_id)
    if category:
        query = query.filter(Assets.category == category)
    if min_depreciation_rate:
        query = query.filter(Assets.depreciation_rate >= min_depreciation_rate)
    
    assets = query.all()
    
    depreciation_details = []
    total_original_value = Decimal(0)
    total_current_value = Decimal(0)
    total_depreciated = Decimal(0)
    
    for asset in assets:
        if asset.acquisition_cost:
            original_value = asset.acquisition_cost
            current_value = asset.current_value or original_value
            depreciated_amount = original_value - current_value
            depreciation_pct = (depreciated_amount / original_value * 100) if original_value > 0 else 0
            
            years_owned = (datetime.now().date() - asset.acquisition_date).days / 365.25 if asset.acquisition_date else 0
            
            depreciation_details.append({
                "asset_id": asset.id,
                "tag_number": asset.tag_number,
                "description": asset.description,
                "category": asset.category.value,
                "department": asset.department.name if asset.department else None,
                "acquisition_date": asset.acquisition_date,
                "years_owned": round(years_owned, 2),
                "original_value": float(original_value),
                "current_value": float(current_value),
                "depreciation_rate": float(asset.depreciation_rate),
                "depreciated_amount": float(depreciated_amount),
                "depreciation_percentage": round(float(depreciation_pct), 2),
                "useful_life_years": asset.useful_life_years,
                "remaining_life_years": max(0, (asset.useful_life_years or 0) - years_owned) if asset.useful_life_years else None
            })
            
            total_original_value += original_value
            total_current_value += current_value
            total_depreciated += depreciated_amount
    
    depreciation_details.sort(key=lambda x: x["depreciation_percentage"], reverse=True)
    
    nearly_depreciated = [a for a in depreciation_details if a["depreciation_percentage"] > 80]
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="depreciation_report",
            details={"filters": {"department_id": department_id, "category": category}},
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "total_assets": len(depreciation_details),
            "total_original_value": float(total_original_value),
            "total_current_value": float(total_current_value),
            "total_depreciated_amount": float(total_depreciated),
            "overall_depreciation_percentage": round(
                float((total_depreciated / total_original_value * 100) if total_original_value > 0 else 0), 2
            ),
            "assets_near_full_depreciation": len(nearly_depreciated)
        },
        "assets": depreciation_details,
        "assets_near_full_depreciation": nearly_depreciated[:10],
        "generated_at": datetime.now()
    }


@router.get("/asset-status-condition")
async def get_asset_status_condition_report(
    department_id: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """3. Asset Status & Condition Report"""
    
    query = db.query(Assets).filter(Assets.is_deleted == False)
    
    if department_id:
        query = query.filter(Assets.department_id == department_id)
    if category:
        query = query.filter(Assets.category == category)
    
    assets = query.all()
    
    status_breakdown = defaultdict(lambda: {"count": 0, "value": Decimal(0), "assets": []})
    for asset in assets:
        status = asset.status.value
        value = asset.current_value or asset.acquisition_cost or Decimal(0)
        status_breakdown[status]["count"] += 1
        status_breakdown[status]["value"] += value
        if len(status_breakdown[status]["assets"]) < 5:
            status_breakdown[status]["assets"].append({
                "id": asset.id,
                "tag_number": asset.tag_number,
                "description": asset.description
            })
    
    condition_breakdown = defaultdict(lambda: {"count": 0, "value": Decimal(0), "assets": []})
    for asset in assets:
        condition = asset.condition.value if asset.condition else "unknown"
        value = asset.current_value or asset.acquisition_cost or Decimal(0)
        condition_breakdown[condition]["count"] += 1
        condition_breakdown[condition]["value"] += value
        if len(condition_breakdown[condition]["assets"]) < 5:
            condition_breakdown[condition]["assets"].append({
                "id": asset.id,
                "tag_number": asset.tag_number,
                "description": asset.description
            })
    
    requiring_attention = [
        {
            "id": a.id,
            "tag_number": a.tag_number,
            "description": a.description,
            "status": a.status.value,
            "condition": a.condition.value if a.condition else None,
            "department": a.department.name if a.department else None
        }
        for a in assets
        if (a.condition and a.condition.value in ["poor", "fair"]) or 
           a.status.value in ["Under Maintenance", "Impaired", "Lost/Stolen"]
    ]
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="asset_status_condition",
            details={"filters": {"department_id": department_id, "category": category}},
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "total_assets": len(assets),
            "requiring_attention": len(requiring_attention)
        },
        "by_status": {k: {"count": v["count"], "value": float(v["value"]), "sample_assets": v["assets"]} 
                      for k, v in status_breakdown.items()},
        "by_condition": {k: {"count": v["count"], "value": float(v["value"]), "sample_assets": v["assets"]} 
                         for k, v in condition_breakdown.items()},
        "assets_requiring_attention": requiring_attention,
        "generated_at": datetime.now()
    }


@router.get("/category-specific/{category}")
async def get_category_specific_report(
    category: str,
    department_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """4. Category-Specific Reports (Land, Buildings, Standard Assets)"""
    
    query = db.query(Assets).filter(
        Assets.category == category,
        Assets.is_deleted == False
    )
    
    if department_id:
        query = query.filter(Assets.department_id == department_id)
    
    assets = query.all()
    
    if not assets:
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.VIEW,
                target_table="reports",
                target_id=f"category_specific_{category}",
                details={"message": "No assets found"},
                level=LogLevel.INFO
            )
        return {
            "category": category,
            "assets": [],
            "total_count": 0,
            "message": "No assets found for this category"
        }
    
    category_fields = get_category_specific_reports_fields(category)
    
    formatted_assets = []
    for asset in assets:
        asset_data = {
            "id": asset.id,
            "tag_number": asset.tag_number,
            "description": asset.description,
            "status": asset.status.value,
            "condition": asset.condition.value if asset.condition else None,
            "location": asset.location,
            "department": asset.department.name if asset.department else None,
            "acquisition_date": asset.acquisition_date,
            "current_value": float(asset.current_value or asset.acquisition_cost or 0),
        }
        
        if asset.specific_attributes:
            formatted_specific = format_attributes_for_display(category, asset.specific_attributes)
            asset_data["specific_attributes"] = formatted_specific
        
        formatted_assets.append(asset_data)
    
    total_value = sum(asset.current_value or asset.acquisition_cost or Decimal(0) for asset in assets)
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id=f"category_specific_{category}",
            details={"filters": {"department_id": department_id}},
            level=LogLevel.INFO
        )
    
    return {
        "category": category,
        "total_count": len(assets),
        "total_value": float(total_value),
        "category_specific_fields": category_fields,
        "assets": formatted_assets,
        "generated_at": datetime.now()
    }


@router.get("/unassigned-assets")
async def get_unassigned_assets_report(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """5. Unassigned Assets +++
    
    
    Report"""
    
    query = db.query(Assets).filter(
        Assets.is_deleted == False,
        or_(
            Assets.responsible_officer_id.is_(None),
            Assets.department_id.is_(None)
        )
    )
    
    if category:
        query = query.filter(Assets.category == category)
    
    assets = query.all()
    
    no_officer = [a for a in assets if a.responsible_officer_id is None]
    no_department = [a for a in assets if a.department_id is None]
    no_both = [a for a in assets if a.responsible_officer_id is None and a.department_id is None]
    
    total_value = sum(a.current_value or a.acquisition_cost or Decimal(0) for a in assets)
    
    asset_details = [
        {
            "id": a.id,
            "tag_number": a.tag_number,
            "description": a.description,
            "category": a.category.value,
            "status": a.status.value,
            "current_value": float(a.current_value or a.acquisition_cost or 0),
            "missing": {
                "responsible_officer": a.responsible_officer_id is None,
                "department": a.department_id is None
            }
        }
        for a in assets
    ]
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="unassigned_assets",
            details={"filters": {"category": category}},
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "total_unassigned": len(assets),
            "no_officer": len(no_officer),
            "no_department": len(no_department),
            "no_both": len(no_both),
            "total_value": float(total_value)
        },
        "assets": asset_details,
        "generated_at": datetime.now()
    }





