from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
from datetime import datetime
from collections import defaultdict

from ...database import get_db
from ...models import Assets, User
from ...utilities import get_current_user
from ...system_vars import sys_logger
from ...services.logger_queue import enqueue_log
from ...schemas.main import ActionType, LogLevel


router = APIRouter(prefix="/api/v1/r/reports", tags=["Asset Complience Reports"])

@router.get("/missing-data")
async def get_missing_data_report(
    department_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """16. Missing Data Report - Assets with incomplete information"""
    
    query = db.query(Assets).filter(Assets.is_deleted == False)
    
    if department_id:
        query = query.filter(Assets.department_id == department_id)
    
    assets = query.all()
    
    issues = []
    for asset in assets:
        missing_fields = []
        
        if not asset.acquisition_cost:
            missing_fields.append("acquisition_cost")
        if not asset.acquisition_date:
            missing_fields.append("acquisition_date")
        if not asset.responsible_officer_id:
            missing_fields.append("responsible_officer")
        if not asset.department_id:
            missing_fields.append("department")
        if not asset.location:
            missing_fields.append("location")
        if not asset.serial_number and asset.category.value not in ["Land", "Buildings and building improvements"]:
            missing_fields.append("serial_number")
        
        if missing_fields:
            issues.append({
                "asset_id": asset.id,
                "tag_number": asset.tag_number,
                "description": asset.description,
                "category": asset.category.value,
                "department": asset.department.name if asset.department else None,
                "missing_fields": missing_fields,
                "completeness_score": round((1 - len(missing_fields) / 6) * 100, 2)
            })
    
    if assets:
        avg_completeness = sum(i["completeness_score"] for i in issues) / len(issues) if issues else 100
        overall_score = round(((len(assets) - len(issues)) / len(assets) * 100 + avg_completeness) / 2, 2)
    else:
        overall_score = 100
    
    by_field = defaultdict(int)
    for issue in issues:
        for field in issue["missing_fields"]:
            by_field[field] += 1
    
    issues.sort(key=lambda x: len(x["missing_fields"]), reverse=True)
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="missing_data",
            details={"filters": {"department_id": department_id}},
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "total_assets": len(assets),
            "assets_with_issues": len(issues),
            "overall_data_quality_score": overall_score,
            "by_missing_field": dict(by_field)
        },
        "assets_with_missing_data": issues,
        "generated_at": datetime.now()
    }


@router.get("/geographic-distribution")
async def get_geographic_distribution_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """17. Geographic Distribution Report"""
    
    assets = db.query(Assets).filter(Assets.is_deleted == False).all()
    
    by_county = defaultdict(lambda: {"count": 0, "value": Decimal(0)})
    by_entity = defaultdict(lambda: {"count": 0, "value": Decimal(0)})
    
    for asset in assets:
        county = "Unknown"
        if asset.location and isinstance(asset.location, dict):
            county = asset.location.get("county", "Unknown")
        
        value = asset.current_value or asset.acquisition_cost or Decimal(0)
        by_county[county]["count"] += 1
        by_county[county]["value"] += value
        
        if asset.department and asset.department.entity_type:
            entity = asset.department.entity_type.value
            by_entity[entity]["count"] += 1
            by_entity[entity]["value"] += value
    
    county_list = [
        {
            "county": county,
            "asset_count": data["count"],
            "total_value": float(data["value"])
        }
        for county, data in by_county.items()
    ]
    county_list.sort(key=lambda x: x["total_value"], reverse=True)
    
    entity_list = [
        {
            "entity_type": entity,
            "asset_count": data["count"],
            "total_value": float(data["value"])
        }
        for entity, data in by_entity.items()
    ]
    entity_list.sort(key=lambda x: x["total_value"], reverse=True)
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="geographic_distribution",
            details=None,
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "total_assets": len(assets),
            "counties_covered": len(by_county),
            "entity_types": len(by_entity)
        },
        "by_county": county_list,
        "by_entity_type": entity_list,
        "generated_at": datetime.now()
    }
