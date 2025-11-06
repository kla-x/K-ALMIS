from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
from datetime import datetime, date, timedelta
from collections import defaultdict

from ...database import get_db
from ...models import (Assets, User, Departments, MaintenanceRequests, AssetLifecycleEvents, AssetStatus)
from ...utilities import get_current_user
from ...system_vars import sys_logger
from ...services.logger_queue import enqueue_log
from ...schemas.main import ActionType, LogLevel

router = APIRouter(prefix="/api/v1/r/reports", tags=["Asset  Reports Utils"])

@router.get("/asset-age-analysis")
async def get_asset_age_analysis_report(
    department_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Asset Age Analysis - Distribution of assets by age"""
    
    query = db.query(Assets).filter(
        Assets.is_deleted == False,
        Assets.acquisition_date.isnot(None)
    )
    
    if department_id:
        query = query.filter(Assets.department_id == department_id)
    
    assets = query.all()
    
    age_brackets = {
        "0-1 years": {"count": 0, "value": Decimal(0), "assets": []},
        "1-3 years": {"count": 0, "value": Decimal(0), "assets": []},
        "3-5 years": {"count": 0, "value": Decimal(0), "assets": []},
        "5-10 years": {"count": 0, "value": Decimal(0), "assets": []},
        "10+ years": {"count": 0, "value": Decimal(0), "assets": []}
    }
    
    for asset in assets:
        years_old = (datetime.now().date() - asset.acquisition_date).days / 365.25
        value = asset.current_value or asset.acquisition_cost or Decimal(0)
        
        asset_info = {
            "id": asset.id,
            "tag_number": asset.tag_number,
            "description": asset.description,
            "age_years": round(years_old, 1),
            "value": float(value)
        }
        
        if years_old < 1:
            age_brackets["0-1 years"]["count"] += 1
            age_brackets["0-1 years"]["value"] += value
            if len(age_brackets["0-1 years"]["assets"]) < 5:
                age_brackets["0-1 years"]["assets"].append(asset_info)
        elif years_old < 3:
            age_brackets["1-3 years"]["count"] += 1
            age_brackets["1-3 years"]["value"] += value
            if len(age_brackets["1-3 years"]["assets"]) < 5:
                age_brackets["1-3 years"]["assets"].append(asset_info)
        elif years_old < 5:
            age_brackets["3-5 years"]["count"] += 1
            age_brackets["3-5 years"]["value"] += value
            if len(age_brackets["3-5 years"]["assets"]) < 5:
                age_brackets["3-5 years"]["assets"].append(asset_info)
        elif years_old < 10:
            age_brackets["5-10 years"]["count"] += 1
            age_brackets["5-10 years"]["value"] += value
            if len(age_brackets["5-10 years"]["assets"]) < 5:
                age_brackets["5-10 years"]["assets"].append(asset_info)
        else:
            age_brackets["10+ years"]["count"] += 1
            age_brackets["10+ years"]["value"] += value
            if len(age_brackets["10+ years"]["assets"]) < 5:
                age_brackets["10+ years"]["assets"].append(asset_info)
    
    approaching_eol = []
    for asset in assets:
        if asset.useful_life_years:
            years_old = (datetime.now().date() - asset.acquisition_date).days / 365.25
            remaining = asset.useful_life_years - years_old
            if 0 < remaining <= 2:
                approaching_eol.append({
                    "id": asset.id,
                    "tag_number": asset.tag_number,
                    "description": asset.description,
                    "age_years": round(years_old, 1),
                    "useful_life_years": asset.useful_life_years,
                    "remaining_years": round(remaining, 1)
                })
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="asset_age_analysis",
            details={"filters": {"department_id": department_id}},
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "total_assets": len(assets),
            "approaching_end_of_life": len(approaching_eol)
        },
        "by_age_bracket": {
            bracket: {
                "count": data["count"],
                "value": float(data["value"]),
                "sample_assets": data["assets"]
            }
            for bracket, data in age_brackets.items()
        },
        "approaching_end_of_life": approaching_eol,
        "generated_at": datetime.now()
    }


@router.get("/department-comparison")
async def get_department_comparison_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Department Comparison - Compare asset metrics across departments"""
    
    departments = db.query(Departments).filter(
        Departments.status == "active"
    ).all()
    
    dept_metrics = []
    
    for dept in departments:
        assets = db.query(Assets).filter(
            Assets.department_id == dept.dept_id,
            Assets.is_deleted == False
        ).all()
        
        total_value = sum(a.current_value or a.acquisition_cost or Decimal(0) for a in assets)
        operational = len([a for a in assets if a.status == AssetStatus.OPERATIONAL])
        
        thirty_days_ago = datetime.now() - timedelta(days=30)
        maintenance_count = db.query(MaintenanceRequests).join(Assets).filter(
            Assets.department_id == dept.dept_id,
            MaintenanceRequests.request_date >= thirty_days_ago
        ).count()
        
        unassigned = len([a for a in assets if not a.responsible_officer_id])
        
        dept_metrics.append({
            "department_id": dept.dept_id,
            "department_name": dept.name,
            "asset_count": len(assets),
            "total_value": float(total_value),
            "operational_count": operational,
            "operational_percentage": round((operational / len(assets) * 100) if assets else 0, 2),
            "maintenance_requests_30d": maintenance_count,
            "unassigned_assets": unassigned,
            "avg_asset_value": float(total_value / len(assets)) if assets else 0
        })
    
    dept_metrics.sort(key=lambda x: x["total_value"], reverse=True)
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="department_comparison",
            details=None,
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "total_departments": len(dept_metrics),
            "total_assets": sum(d["asset_count"] for d in dept_metrics),
            "total_value": sum(d["total_value"] for d in dept_metrics)
        },
        "departments": dept_metrics,
        "generated_at": datetime.now()
    }


@router.get("/asset-utilization")
async def get_asset_utilization_report(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Asset Utilization Report - Track asset usage and idle assets"""
    
    query = db.query(Assets).filter(Assets.is_deleted == False)
    
    if category:
        query = query.filter(Assets.category == category)
    
    assets = query.all()
    
    assigned = [a for a in assets if a.responsible_officer_id]
    unassigned = [a for a in assets if not a.responsible_officer_id]
    operational = [a for a in assets if a.status == AssetStatus.OPERATIONAL]
    
    idle_assets = []
    for asset in assets:
        if asset.status == AssetStatus.OPERATIONAL and not asset.responsible_officer_id:
            recent_events = db.query(AssetLifecycleEvents).filter(
                AssetLifecycleEvents.asset_id == asset.id,
                AssetLifecycleEvents.event_date >= datetime.now() - timedelta(days=90)
            ).count()
            
            if recent_events == 0:
                idle_assets.append({
                    "id": asset.id,
                    "tag_number": asset.tag_number,
                    "description": asset.description,
                    "category": asset.category.value,
                    "value": float(asset.current_value or asset.acquisition_cost or 0),
                    "last_activity": asset.updated_at or asset.created_at
                })
    
    location_usage = defaultdict(lambda: {"assigned": 0, "unassigned": 0})
    for asset in assets:
        location = "Unknown"
        if asset.location and isinstance(asset.location, dict):
            location = asset.location.get("county", "Unknown")
        
        if asset.responsible_officer_id:
            location_usage[location]["assigned"] += 1
        else:
            location_usage[location]["unassigned"] += 1
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="asset_utilization",
            details={"filters": {"category": category}},
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "total_assets": len(assets),
            "assigned": len(assigned),
            "unassigned": len(unassigned),
            "operational": len(operational),
            "idle_assets": len(idle_assets),
            "utilization_rate": round((len(assigned) / len(assets) * 100) if assets else 0, 2)
        },
        "idle_assets": idle_assets,
        "by_location": {
            loc: {
                "assigned": data["assigned"],
                "unassigned": data["unassigned"],
                "utilization_rate": round((data["assigned"] / (data["assigned"] + data["unassigned"]) * 100) if (data["assigned"] + data["unassigned"]) > 0 else 0, 2)
            }
            for loc, data in location_usage.items()
        },
        "generated_at": datetime.now()
    }


@router.get("/maintenance-cost-analysis")
async def get_maintenance_cost_analysis_report(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    department_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Maintenance Cost Analysis - Detailed cost breakdown"""
    
    query = db.query(MaintenanceRequests).filter(
        MaintenanceRequests.cost.isnot(None)
    )
    
    if date_from:
        query = query.filter(MaintenanceRequests.request_date >= date_from)
    if date_to:
        query = query.filter(MaintenanceRequests.request_date <= date_to)
    if department_id:
        query = query.join(Assets).filter(Assets.department_id == department_id)
    
    requests = query.all()
    
    total_cost = sum(r.cost for r in requests)
    
    by_type = defaultdict(lambda: {"count": 0, "total_cost": Decimal(0)})
    for req in requests:
        by_type[req.maintenance_type.value]["count"] += 1
        by_type[req.maintenance_type.value]["total_cost"] += req.cost
    
    by_category = defaultdict(lambda: {"count": 0, "total_cost": Decimal(0)})
    for req in requests:
        if req.asset:
            category = req.asset.category.value
            by_category[category]["count"] += 1
            by_category[category]["total_cost"] += req.cost
    
    expensive_requests = sorted(requests, key=lambda x: x.cost, reverse=True)[:10]
    expensive_list = [
        {
            "id": r.id,
            "asset_id": r.asset_id,
            "asset_description": r.asset.description if r.asset else None,
            "cost": float(r.cost),
            "maintenance_type": r.maintenance_type.value,
            "request_date": r.request_date,
            "completed_at": r.completed_at
        }
        for r in expensive_requests
    ]
    
    asset_costs = defaultdict(lambda: {"cost": Decimal(0), "count": 0, "asset": None})
    for req in requests:
        if req.asset:
            asset_costs[req.asset_id]["cost"] += req.cost
            asset_costs[req.asset_id]["count"] += 1
            asset_costs[req.asset_id]["asset"] = req.asset
    
    high_cost_assets = sorted(
        [
            {
                "asset_id": asset_id,
                "asset_description": data["asset"].description,
                "asset_tag": data["asset"].tag_number,
                "total_maintenance_cost": float(data["cost"]),
                "maintenance_count": data["count"],
                "avg_cost_per_maintenance": float(data["cost"] / data["count"])
            }
            for asset_id, data in asset_costs.items() if data["asset"]
        ],
        key=lambda x: x["total_maintenance_cost"],
        reverse=True
    )[:10]
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="maintenance_cost_analysis",
            details={"filters": {"department_id": department_id, "date_from": str(date_from), "date_to": str(date_to)}},
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "total_requests": len(requests),
            "total_cost": float(total_cost),
            "average_cost": float(total_cost / len(requests)) if requests else 0
        },
        "by_maintenance_type": {
            mtype: {
                "count": data["count"],
                "total_cost": float(data["total_cost"]),
                "avg_cost": float(data["total_cost"] / data["count"]) if data["count"] > 0 else 0
            }
            for mtype, data in by_type.items()
        },
        "by_category": {
            cat: {
                "count": data["count"],
                "total_cost": float(data["total_cost"]),
                "avg_cost": float(data["total_cost"] / data["count"]) if data["count"] > 0 else 0
            }
            for cat, data in by_category.items()
        },
        "most_expensive_requests": expensive_list,
        "high_cost_assets": high_cost_assets,
        "generated_at": datetime.now()
    }


@router.get("/available-reports")
async def list_available_reports(
    current_user: User = Depends(get_current_user)
):
    """List all available reports with descriptions"""
    
    reports = [
        {
            "id": "asset-summary-dashboard",
            "name": "Asset Summary Dashboard",
            "description": "Complete overview of all assets with breakdowns by category, status, condition, and department",
            "category": "Asset Reports",
            "endpoint": "/api/v1/r/reports/asset-summary-dashboard"
        },
        {
            "id": "depreciation",
            "name": "Depreciation Report",
            "description": "Asset values and depreciation analysis with assets nearing full depreciation",
            "category": "Asset Reports",
            "endpoint": "/api/v1/r/reports/depreciation"
        },
        {
            "id": "asset-status-condition",
            "name": "Asset Status & Condition",
            "description": "Status and condition breakdowns with assets requiring attention",
            "category": "Asset Reports",
            "endpoint": "/api/v1/r/reports/asset-status-condition"
        },
        {
            "id": "category-specific",
            "name": "Category-Specific Reports",
            "description": "Detailed reports for Land, Buildings, and Standard Assets",
            "category": "Asset Reports",
            "endpoint": "/api/v1/r/reports/category-specific/{category}"
        },
        {
            "id": "unassigned-assets",
            "name": "Unassigned Assets",
            "description": "Assets without responsible officers or department assignments",
            "category": "Asset Reports",
            "endpoint": "/api/v1/r/reports/unassigned-assets"
        },
        {
            "id": "asset-age-analysis",
            "name": "Asset Age Analysis",
            "description": "Distribution of assets by age and approaching end of life",
            "category": "Asset Reports",
            "endpoint": "/api/v1/r/reports/asset-age-analysis"
        },
        {
            "id": "asset-utilization",
            "name": "Asset Utilization",
            "description": "Track asset usage, idle assets, and utilization rates",
            "category": "Asset Reports",
            "endpoint": "/api/v1/r/reports/asset-utilization"
        },
        {
            "id": "department-assets",
            "name": "Department Asset Report",
            "description": "Comprehensive per-department breakdown with top assets",
            "category": "Department Reports",
            "endpoint": "/api/v1/r/reports/department-assets/{dept_id}"
        },
        {
            "id": "user-responsibility",
            "name": "User Responsibility",
            "description": "Assets assigned per user with total values under care",
            "category": "Department Reports",
            "endpoint": "/api/v1/r/reports/user-responsibility"
        },
        {
            "id": "department-comparison",
            "name": "Department Comparison",
            "description": "Compare asset metrics across all departments",
            "category": "Department Reports",
            "endpoint": "/api/v1/r/reports/department-comparison"
        },
        {
            "id": "maintenance-summary",
            "name": "Maintenance Summary",
            "description": "Complete maintenance overview with costs and high-maintenance assets",
            "category": "Maintenance Reports",
            "endpoint": "/api/v1/r/reports/maintenance-summary"
        },
        {
            "id": "upcoming-maintenance",
            "name": "Upcoming Maintenance",
            "description": "Scheduled maintenance with date grouping",
            "category": "Maintenance Reports",
            "endpoint": "/api/v1/r/reports/upcoming-maintenance"
        },
        {
            "id": "maintenance-backlog",
            "name": "Maintenance Backlog",
            "description": "Overdue and aging maintenance requests",
            "category": "Maintenance Reports",
            "endpoint": "/api/v1/r/reports/maintenance-backlog"
        },
        {
            "id": "maintenance-cost-analysis",
            "name": "Maintenance Cost Analysis",
            "description": "Detailed cost breakdown by type, category, and asset",
            "category": "Maintenance Reports",
            "endpoint": "/api/v1/r/reports/maintenance-cost-analysis"
        },
        {
            "id": "pending-transfers-disposals",
            "name": "Pending Transfers & Disposals",
            "description": "All pending transfers and disposals awaiting approval",
            "category": "Transfer & Disposal Reports",
            "endpoint": "/api/v1/r/reports/pending-transfers-disposals"
        },
        {
            "id": "transfer-disposal-history",
            "name": "Transfer & Disposal History",
            "description": "Completed transactions with financial details",
            "category": "Transfer & Disposal Reports",
            "endpoint": "/api/v1/r/reports/transfer-disposal-history"
        },
        {
            "id": "activity-log",
            "name": "Activity Log",
            "description": "System activities with critical operation tracking",
            "category": "Security & Audit Reports",
            "endpoint": "/api/v1/r/reports/activity-log"
        },
        {
            "id": "failed-login-attempts",
            "name": "Failed Login Attempts",
            "description": "Suspicious patterns and excessive login failures",
            "category": "Security & Audit Reports",
            "endpoint": "/api/v1/r/reports/failed-login-attempts"
        },
        {
            "id": "data-modifications",
            "name": "Data Modifications",
            "description": "Audit trail with high-frequency user detection",
            "category": "Security & Audit Reports",
            "endpoint": "/api/v1/r/reports/data-modifications"
        },
        {
            "id": "missing-data",
            "name": "Missing Data",
            "description": "Assets with incomplete information and data quality scores",
            "category": "Compliance Reports",
            "endpoint": "/api/v1/r/reports/missing-data"
        },
        {
            "id": "geographic-distribution",
            "name": "Geographic Distribution",
            "description": "Assets by county and entity type",
            "category": "Compliance Reports",
            "endpoint": "/api/v1/r/reports/geographic-distribution"
        },
        {
            "id": "executive-summary",
            "name": "Executive Summary",
            "description": "High-level KPIs with critical alerts and trends",
            "category": "Executive Report",
            "endpoint": "/api/v1/r/reports/executive-summary"
        }
    ]
    
    by_category = defaultdict(list)
    for report in reports:
        by_category[report["category"]].append(report)
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="available_reports_list",
            details=None,
            level=LogLevel.INFO
        )
    
    return {
        "total_reports": len(reports),
        "categories": list(by_category.keys()),
        "reports_by_category": dict(by_category),
        "all_reports": reports
    }