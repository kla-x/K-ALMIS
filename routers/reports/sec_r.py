from fastapi import APIRouter, Depends,Query
from sqlalchemy.orm import Session
from typing import Optional

from datetime import datetime
from collections import defaultdict

from ...database import get_db
from ...models import (
     User, ActivityLog
)
from ...utilities import get_current_user
from ...system_vars import sys_logger
from ...services.logger_queue import enqueue_log
from ...schemas.main import ActionType, LogLevel
from sqlalchemy import desc

router = APIRouter(prefix="/api/v1/r/reports", tags=["Asset Security Reports"])

@router.get("/activity-log")
async def get_activity_log_report(
    user_id: Optional[str] = None,
    action_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """13. Activity Log Report"""
    
    query = db.query(ActivityLog)
    
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    if action_type:
        query = query.filter(ActivityLog.action == action_type)
    if date_from:
        query = query.filter(ActivityLog.created_at >= date_from)
    if date_to:
        query = query.filter(ActivityLog.created_at <= date_to)
    
    logs = query.order_by(desc(ActivityLog.created_at)).limit(limit).all()
    
    action_summary = defaultdict(int)
    for log in logs:
        action_summary[log.action] += 1
    
    user_summary = defaultdict(int)
    for log in logs:
        if log.user:
            user_name = f"{log.user.first_name} {log.user.last_name}"
            user_summary[user_name] += 1
    
    critical = [log for log in logs if log.logg_level == "CRITICAL"]
    
    log_list = [
        {
            "id": str(log.id),
            "user": f"{log.user.first_name} {log.user.last_name}" if log.user else None,
            "action": log.action,
            "target_table": log.target_table,
            "target_id": log.target_id,
            "level": log.logg_level,
            "details": log.details,
            "created_at": log.created_at
        }
        for log in logs
    ]
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="activity_log",
            details={"filters": {"user_id": user_id, "action_type": action_type}},
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "total_activities": len(logs),
            "critical_count": len(critical),
            "by_action": dict(action_summary),
            "by_user": dict(user_summary)
        },
        "activities": log_list,
        "generated_at": datetime.now()
    }


@router.get("/failed-login-attempts")
async def get_failed_login_report(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """14. Failed Login Attempts Report"""
    
    query = db.query(ActivityLog).filter(
        ActivityLog.action == "LOGIN_FAILED"
    )
    
    if date_from:
        query = query.filter(ActivityLog.created_at >= date_from)
    if date_to:
        query = query.filter(ActivityLog.created_at <= date_to)
    
    failed_logins = query.order_by(desc(ActivityLog.created_at)).all()
    
    user_failures = defaultdict(lambda: {"count": 0, "attempts": []})
    for log in failed_logins:
        user_email = log.details.get("email") if log.details else "Unknown"
        user_failures[user_email]["count"] += 1
        user_failures[user_email]["attempts"].append({
            "timestamp": log.created_at,
            "details": log.details
        })
    
    excessive_failures = [
        {"email": email, "count": data["count"], "latest_attempts": data["attempts"][:5]}
        for email, data in user_failures.items() if data["count"] > 5
    ]
    excessive_failures.sort(key=lambda x: x["count"], reverse=True)
    
    suspicious = []
    for email, data in user_failures.items():
        if data["count"] >= 3:
            attempts = sorted(data["attempts"], key=lambda x: x["timestamp"], reverse=True)
            if len(attempts) >= 3:
                time_diff = (attempts[0]["timestamp"] - attempts[2]["timestamp"]).total_seconds() / 60
                if time_diff <= 10:
                    suspicious.append({
                        "email": email,
                        "count": data["count"],
                        "time_window_minutes": round(time_diff, 2)
                    })
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="failed_login_attempts",
            details={"filters": {"date_from": str(date_from), "date_to": str(date_to)}},
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "total_failed_attempts": len(failed_logins),
            "unique_users": len(user_failures),
            "users_with_excessive_failures": len(excessive_failures),
            "suspicious_patterns": len(suspicious)
        },
        "by_user": [
            {"email": email, "failure_count": data["count"]}
            for email, data in sorted(user_failures.items(), key=lambda x: x[1]["count"], reverse=True)
        ],
        "excessive_failures": excessive_failures,
        "suspicious_patterns": suspicious,
        "generated_at": datetime.now()
    }


@router.get("/data-modifications")
async def get_data_modification_audit_report(
    target_table: Optional[str] = None,
    user_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """15. Data Modification Audit Report"""
    
    query = db.query(ActivityLog).filter(
        ActivityLog.action.in_(["CREATE", "UPDATE", "DELETE"])
    )
    
    if target_table:
        query = query.filter(ActivityLog.target_table == target_table)
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    if date_from:
        query = query.filter(ActivityLog.created_at >= date_from)
    if date_to:
        query = query.filter(ActivityLog.created_at <= date_to)
    
    modifications = query.order_by(desc(ActivityLog.created_at)).limit(limit).all()
    
    by_action = defaultdict(int)
    for mod in modifications:
        by_action[mod.action] += 1
    
    by_table = defaultdict(int)
    for mod in modifications:
        by_table[mod.target_table or "unknown"] += 1
    
    by_user = defaultdict(int)
    for mod in modifications:
        if mod.user:
            user_name = f"{mod.user.first_name} {mod.user.last_name}"
            by_user[user_name] += 1
    
    high_frequency = []
    for user_name, count in by_user.items():
        if count > 20:
            high_frequency.append({"user": user_name, "modification_count": count})
    high_frequency.sort(key=lambda x: x["modification_count"], reverse=True)
    
    modification_list = [
        {
            "id": str(mod.id),
            "user": f"{mod.user.first_name} {mod.user.last_name}" if mod.user else None,
            "action": mod.action,
            "target_table": mod.target_table,
            "target_id": mod.target_id,
            "details": mod.details,
            "created_at": mod.created_at
        }
        for mod in modifications
    ]
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="reports",
            target_id="data_modifications",
            details={"filters": {"target_table": target_table, "user_id": user_id}},
            level=LogLevel.INFO
        )
    
    return {
        "summary": {
            "total_modifications": len(modifications),
            "by_action": dict(by_action),
            "by_table": dict(by_table),
            "high_frequency_users": len(high_frequency)
        },
        "modifications": modification_list,
        "high_frequency_users": high_frequency,
        "generated_at": datetime.now()
    }

