from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import  Optional
from decimal import Decimal
from datetime import datetime, date

from ...database import get_db
from ...models import Assets,User,Departments
from ...schemas.assets import AssetSummaryReport, DepartmentAssetReport
from ...utilities import get_current_user
from ...asset_utils import get_category_specific_reports_fields, format_attributes_for_display

router = APIRouter(prefix="/api/v1/reports", tags=["Asset Reports general"])

@router.get("/assets-summary", response_model=AssetSummaryReport)
async def get_assets_summary_report(
    department_id: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """a comprehensive assets summary report"""

    query = db.query(Assets).filter(Assets.is_deleted == False)
    
    if department_id:
        query = query.filter(Assets.department_id == department_id)
    if category:
        query = query.filter(Assets.category == category)
    if date_from:
        query = query.filter(Assets.acquisition_date >= date_from)
    if date_to:
        query = query.filter(Assets.acquisition_date <= date_to)
    
    assets = query.all()

    total_assets = len(assets)
    total_value = sum(asset.current_value or asset.acquisition_cost or Decimal(0) for asset in assets)
    
    by_category = {}
    for asset in assets:
        category_name = asset.category
        if category_name not in by_category:
            by_category[category_name] = {
                "count": 0,
                "total_value": Decimal(0),
                "avg_value": Decimal(0),
                "operational_count": 0,
                "impaired_count": 0
            }
        
        by_category[category_name]["count"] += 1
        asset_value = asset.current_value or asset.acquisition_cost or Decimal(0)
        by_category[category_name]["total_value"] += asset_value
        
        if asset.status == "Operational":
            by_category[category_name]["operational_count"] += 1
        elif asset.status in ["Impaired", "Under Maintenance"]:
            by_category[category_name]["impaired_count"] += 1

    for category_data in by_category.values():
        if category_data["count"] > 0:
            category_data["avg_value"] = category_data["total_value"] / category_data["count"]

    by_status = {}
    for asset in assets:
        status = asset.status
        if status not in by_status:
            by_status[status] = {"count": 0, "total_value": Decimal(0)}
        
        by_status[status]["count"] += 1
        asset_value = asset.current_value or asset.acquisition_cost or Decimal(0)
        by_status[status]["total_value"] += asset_value

    by_condition = {}
    for asset in assets:
        condition = asset.condition or "unknown"
        if condition not in by_condition:
            by_condition[condition] = {"count": 0, "total_value": Decimal(0)}
        
        by_condition[condition]["count"] += 1
        asset_value = asset.current_value or asset.acquisition_cost or Decimal(0)
        by_condition[condition]["total_value"] += asset_value
    
    return AssetSummaryReport(
        total_assets=total_assets,
        total_value=total_value,
        by_category=by_category,
        by_status=by_status,
        by_condition=by_condition
    )

@router.get("/department-assets/{dept_id}", response_model=DepartmentAssetReport)
async def get_department_asset_report(dept_id: str,
    include_top_assets: bool = Query(True),
    top_assets_limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),current_user: User = Depends(get_current_user)
):
    """Get detailed asset report for a specific department"""

    department = db.query(Departments).filter(Departments.dept_id == dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    
    assets = db.query(Assets).filter( Assets.department_id == dept_id, Assets.is_deleted == False).all()
    
    total_assets = len(assets)
    total_value = sum(asset.current_value or asset.acquisition_cost or Decimal(0) for asset in assets)
    
    assets_by_category = {}
    for asset in assets:
        category = asset.category
        assets_by_category[category] = assets_by_category.get(category, 0) + 1
    
    assets_by_status = {}
    for asset in assets:
        status = asset.status
        assets_by_status[status] = assets_by_status.get(status, 0) + 1

    top_assets = []
    if include_top_assets:
        top_assets_query = sorted(
            assets,
            key=lambda x: x.current_value or x.acquisition_cost or Decimal(0),
            reverse=True
        )[:top_assets_limit]
        top_assets = top_assets_query
    
    return DepartmentAssetReport(
        department_id=dept_id,
        department_name=department.name,
        total_assets=total_assets,
        total_value=total_value,
        assets_by_category=assets_by_category,
        assets_by_status=assets_by_status,
        top_assets=top_assets
    )

@router.get("/assets-by-condition")
async def get_assets_by_condition_report(
    department_id: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Assets).filter(Assets.is_deleted == False)
    
    if department_id:
        query = query.filter(Assets.department_id == department_id)
    if category:
        query = query.filter(Assets.category == category)
    
    assets = query.all()
    
    assets_by_condition = {
        "new": [],
        "excellent": [],
        "good": [],
        "fair": [],
        "poor": [],
        "unknown": []
    }
    
    condition_stats = {
        "new": {"count": 0, "total_value": Decimal(0)},
        "excellent": {"count": 0, "total_value": Decimal(0)},
        "good": {"count": 0, "total_value": Decimal(0)},
        "fair": {"count": 0, "total_value": Decimal(0)},
        "poor": {"count": 0, "total_value": Decimal(0)},
        "unknown": {"count": 0, "total_value": Decimal(0)}
    }
    
    for asset in assets:
        condition = asset.condition or "unknown"
        
        asset_info = {
            "id": asset.id,
            "description": asset.description,
            "tag_number": asset.tag_number,
            "category": asset.category,
            "current_value": asset.current_value or asset.acquisition_cost,
            "acquisition_date": asset.acquisition_date,
            "location": asset.location
        }
        
        assets_by_condition[condition].append(asset_info)
        condition_stats[condition]["count"] += 1
        condition_stats[condition]["total_value"] += asset.current_value or asset.acquisition_cost or Decimal(0)
    
    return {
        "summary": condition_stats,
        "assets_by_condition": assets_by_condition,
        "generated_at": datetime.now(),
        "filters_applied": {
            "department_id": department_id,
            "category": category
        }
    }

@router.get("/depreciation-report")
async def get_depreciation_report(
    department_id: Optional[str] = None,
    category: Optional[str] = None,
    min_depreciation_rate: Optional[float] = None,
    db: Session = Depends(get_db),current_user: User = Depends(get_current_user)
):
    """Get depreciation report showing assets with depreciation details"""
    
    query = db.query(Assets).filter(Assets.is_deleted == False, Assets.depreciation_rate.isnot(None), Assets.acquisition_date.isnot(None))
    
    if department_id:
        query = query.filter(Assets.department_id == department_id)
    if category:
        query = query.filter(Assets.category == category)
    if min_depreciation_rate:
        query = query.filter(Assets.depreciation_rate >= min_depreciation_rate)
    
    assets = query.all()
    
    depreciation_report = []
    total_original_value = Decimal(0)
    total_current_value = Decimal(0)
    total_depreciated_amount = Decimal(0)
    
    for asset in assets:
        if asset.acquisition_cost and asset.depreciation_rate and asset.acquisition_date:
            original_value = asset.acquisition_cost
            current_value = asset.current_value or original_value
            depreciated_amount = original_value - current_value
            depreciation_percentage = (depreciated_amount / original_value * 100) if original_value > 0 else 0
            
            years_owned = (datetime.now().date() - asset.acquisition_date).days / 365.25
            
            asset_report = {
                "asset_id": asset.id,
                "description": asset.description,
                "tag_number": asset.tag_number,
                "category": asset.category,
                "acquisition_date": asset.acquisition_date,
                "years_owned": round(years_owned, 2),
                "original_value": original_value,
                "current_value": current_value,
                "depreciation_rate": asset.depreciation_rate,
                "depreciated_amount": depreciated_amount,
                "depreciation_percentage": round(depreciation_percentage, 2),
                "useful_life_years": asset.useful_life_years,
                "remaining_life_years": max(0, (asset.useful_life_years or 0) - years_owned) if asset.useful_life_years else None
            }
            
            depreciation_report.append(asset_report)
            total_original_value += original_value
            total_current_value += current_value
            total_depreciated_amount += depreciated_amount

    depreciation_report.sort(key=lambda x: x["depreciation_percentage"], reverse=True)
    
    summary = {
        "total_assets": len(depreciation_report),
        "total_original_value": total_original_value,
        "total_current_value": total_current_value,
        "total_depreciated_amount": total_depreciated_amount,
        "overall_depreciation_percentage": round(
            (total_depreciated_amount / total_original_value * 100) if total_original_value > 0 else 0, 2
        )
    }
    
    return {
        "summary": summary,
        "assets": depreciation_report,
        "generated_at": datetime.now(),
        "filters_applied": {
            "department_id": department_id,
            "category": category,
            "min_depreciation_rate": min_depreciation_rate
        }
    }

@router.get("/category-specific-report/{category}")
async def get_category_specific_report(
    category: str,
    department_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Assets).filter( Assets.category == category, Assets.is_deleted == False)
    
    if department_id:
        query = query.filter(Assets.department_id == department_id)
    
    assets = query.all()
    
    if not assets:
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
            "description": asset.description,
            "tag_number": asset.tag_number,
            "status": asset.status,
            "condition": asset.condition,
            "location": asset.location,
            "acquisition_date": asset.acquisition_date,
            "current_value": asset.current_value or asset.acquisition_cost,
        }
        
        if asset.specific_attributes:
            formatted_specific = format_attributes_for_display(category, asset.specific_attributes)
            asset_data["specific_attributes"] = formatted_specific

            for field_info in category_fields:
                field_name = field_info["field"]
                if field_name in asset.specific_attributes:
                    asset_data[field_info["label"]] = asset.specific_attributes[field_name]
        
        formatted_assets.append(asset_data)
    
    total_value = sum(asset.current_value or asset.acquisition_cost or Decimal(0) for asset in assets)
    avg_value = total_value / len(assets) if assets else Decimal(0)
    
    status_distribution = {}
    for asset in assets:
        status = asset.status
        status_distribution[status] = status_distribution.get(status, 0) + 1
    
    return {
        "category": category,
        "total_count": len(assets),
        "total_value": total_value,
        "average_value": avg_value,
        "status_distribution": status_distribution,
        "category_specific_fields": category_fields,
        "assets": formatted_assets,
        "generated_at": datetime.now(),
        "filters_applied": {
            "department_id": department_id
        }
    }