from fastapi import APIRouter, Depends,HTTPException,status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..models import Assets,User,Departments,AssetLifecycleEvents
from ..database import get_db
from ..utilities import get_current_user,generate_id
from ..schemas.assets import AssignAssetUserDep,AssetResponse
from ..system_vars import sys_logger,debugging
from ..services.logger_queue import enqueue_log
from ..schemas.main import  ActionType, LogLevel, UserStatus
from ..services.policy_eval import check_simple_permission, check_full_permission, build_asset_resource,require_specific_role
from ..asset_utils import add_namedep_asset


router = APIRouter(
    prefix="/api/v1/assets",
    tags=["Assets Assignment"]
    )

@router.post("/{asset_id}/assign")
async def assign_user_an_asset(asset_id: str, resp: AssignAssetUserDep, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    asset = db.query(Assets).filter(Assets.id == asset_id).first()
    if not asset:
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.UPDATE,
                target_table="assets",
                target_id=asset_id,
                details="Asset not found for assignment",
                level=LogLevel.INFO
            )
        raise HTTPException(status_code=404, detail="Asset not found")
    
    try:
        resource = build_asset_resource(asset)
        # check_full_permission(current_user, "asset", "assign", db, resource=resource)

    except HTTPException as e:
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="assets",
                target_id=asset_id,
                details=f"Assignment denied: {e.detail}",
                level=LogLevel.CRITICAL
            )
        raise
    
    if not resp.user_id and not resp.dept_id:
        raise HTTPException(status_code=400, detail="User or department must be specified")
    
    if asset.department_id is not None or asset.responsible_officer_id is not None:
        raise HTTPException(
            status_code=409,
            detail="Asset already assigned to department or user"
        )
    
    usr = None
    dep = None
    assignment_details = {}
    
    if resp.user_id and resp.dept_id:
        usr = db.query(User).filter(User.id == resp.user_id).first()
            
        if not usr.status == UserStatus.active:
            raise HTTPException(status_code=400, detail="USer not active")
        

        dep = db.query(Departments).filter(Departments.dept_id == resp.dept_id).first()
        
        if not usr or not dep:
            raise HTTPException(status_code=400, detail="User or department not found")
        
        if usr.department_id != resp.dept_id:
            raise HTTPException(status_code=400, detail="User not in specified department")
        
        asset.responsible_officer_id = resp.user_id
        asset.department_id = resp.dept_id
        assignment_details = {
            "type": "user_and_department",
            "user_name": f"{usr.first_name} {usr.last_name}",
            "department_name": dep.name
        }
    
    elif resp.user_id:
        usr = db.query(User).filter(User.id == resp.user_id).first()
        if not usr:
            raise HTTPException(status_code=400, detail="User not found")
        if not usr.status == UserStatus.active:
            raise HTTPException(status_code=400, detail="USer not active")
        
        
        asset.responsible_officer_id = resp.user_id
        asset.department_id = usr.department_id
        assignment_details = {
            "type": "user_only",
            "user_name": f"{usr.first_name} {usr.last_name}",
            "department_id": usr.department_id
        }
    
    elif resp.dept_id:
        dep = db.query(Departments).filter(Departments.dept_id == resp.dept_id).first()
        if not dep:
            raise HTTPException(status_code=400, detail="Department not found")
        
        asset.department_id = resp.dept_id
        assignment_details = {
            "type": "department_only",
            "department_name": dep.name
        }
    
    try:
        db.commit()
        db.refresh(asset)
        
        lifecycle_event = AssetLifecycleEvents(
            id=generate_id(60),
            asset_id=asset_id,
            event_type="assigned",
            performed_by=current_user.id,
            details=assignment_details,
            remarks=f"Asset assigned by {current_user.first_name} {current_user.last_name}"
        )
        db.add(lifecycle_event)
        db.commit()
        
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.UPDATE,
                target_table="assets",
                target_id=asset_id,
                details=assignment_details,
                level=LogLevel.INFO
            )
        
        return {"detail": "Asset assigned successfully", "assignment": assignment_details}
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Assignment failed due to db err")

@router.delete("/{asset_id}/unassign", status_code=status.HTTP_200_OK)
async def unassign_asset_from_usr(asset_id: str, current_user: User = Depends(get_current_user),  db: Session = Depends(get_db)):
    
    asset = db.query(Assets).filter(Assets.id == asset_id).first()
    if not asset:
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.UPDATE,
                target_table="assets",
                target_id=asset_id,
                details="Asset not found for unassignment",
                level=LogLevel.INFO
            )
        raise HTTPException(status_code=404, detail="Asset not found")
    
    try:
        resource = build_asset_resource(asset)
        check_full_permission(current_user, "asset", "unassign", db, resource=resource)
    except HTTPException as e:
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="assets",
                target_id=asset_id,
                details=f"Unassignment denied: {e.detail}",
                level=LogLevel.CRITICAL
            )
        raise
    
    if asset.department_id is None and asset.responsible_officer_id is None:
        raise HTTPException(status_code=400, detail="Asset not currently assigned")
    
    old_assignment = {
        "department_id": asset.department_id,
        "responsible_officer_id": asset.responsible_officer_id
    }
    
    asset.department_id = None
    asset.responsible_officer_id = None
    
    try:
        db.commit()
        db.refresh(asset)
        
        lifecycle_event = AssetLifecycleEvents(
            id=generate_id(60),
            asset_id=asset_id,
            event_type="unassigned",
            performed_by=current_user.id,
            details=old_assignment,
            remarks=f"Asset unassigned by {current_user.first_name} {current_user.last_name}"
        )
        db.add(lifecycle_event)
        db.commit()
        
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.UPDATE,
                target_table="assets",
                target_id=asset_id,
                details={"action": "unassigned", "previous_assignment": old_assignment},
                level=LogLevel.INFO
            )
        
        return {"detail": "Asset unassigned successfully"}
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Unassignment failed due to database constraint")

@router.put("/{asset_id}/reassign", status_code=status.HTTP_200_OK)
async def reassign_an_asset_to_user(asset_id: str, resp: AssignAssetUserDep,current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    asset = db.query(Assets).filter(Assets.id == asset_id).first()
    if not asset:
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.UPDATE,
                target_table="assets",
                target_id=asset_id,
                details="Asset not found for reassignment",
                level=LogLevel.INFO
            )
        raise HTTPException(status_code=404, detail="Asset not found")
    
    try:
        resource = build_asset_resource(asset)
        check_full_permission(current_user, "asset", "reassign", db, resource=resource)
    except HTTPException as e:
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="assets",
                target_id=asset_id,
                details=f"Reassignment denied: {e.detail}",
                level=LogLevel.CRITICAL
            )
        raise
    
    if not resp.user_id and not resp.dept_id:
        raise HTTPException(status_code=400, detail="User or department must be specified")
    
    old_assignment = {
        "department_id": asset.department_id,
        "responsible_officer_id": asset.responsible_officer_id
    }
    
    usr = None
    dep = None
    new_assignment_details = {}
    
    if resp.user_id and resp.dept_id:
        usr = db.query(User).filter(User.id == resp.user_id).first()

        dep = db.query(Departments).filter(Departments.dept_id == resp.dept_id).first()
        
        if not usr or not dep:
            raise HTTPException(status_code=400, detail="User or department not found")
        if not usr.status == UserStatus.active:
            raise HTTPException(status_code=400, detail="USer not active")
        
        
        if usr.department_id != resp.dept_id:
            raise HTTPException(status_code=400, detail="User not in specified department")
        
        asset.responsible_officer_id = resp.user_id
        asset.department_id = resp.dept_id
        new_assignment_details = {
            "type": "user_and_department",
            "user_name": f"{usr.first_name} {usr.last_name}",
            "department_name": dep.name
        }
    
    elif resp.user_id:
        usr = db.query(User).filter(User.id == resp.user_id).first()
        if not usr:
            raise HTTPException(status_code=400, detail="User not found")
        if not usr.status == UserStatus.active:
            raise HTTPException(status_code=400, detail="USer not active")
        
        asset.responsible_officer_id = resp.user_id
        asset.department_id = usr.department_id
        new_assignment_details = {
            "type": "user_only",
            "user_name": f"{usr.first_name} {usr.last_name}",
            "department_id": usr.department_id
        }
    
    elif resp.dept_id:
        dep = db.query(Departments).filter(Departments.dept_id == resp.dept_id).first()
        if not dep:
            raise HTTPException(status_code=400, detail="Department not found")
        
        asset.department_id = resp.dept_id
        asset.responsible_officer_id = None
        new_assignment_details = {
            "type": "department_only",
            "department_name": dep.name
        }
    
    try:
        db.commit()
        db.refresh(asset)
        
        lifecycle_event = AssetLifecycleEvents(
            id=generate_id(60),
            asset_id=asset_id,
            event_type="reassigned",
            performed_by=current_user.id,
            details={
                "old_assignment": old_assignment,
                "new_assignment": new_assignment_details
            },
            remarks=f"Asset reassigned by {current_user.first_name} {current_user.last_name}"
        )
        db.add(lifecycle_event)
        db.commit()
        
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.UPDATE,
                target_table="assets",
                target_id=asset_id,
                details={
                    "action": "reassigned",
                    "old_assignment": old_assignment,
                    "new_assignment": new_assignment_details
                },
                level=LogLevel.INFO
            )
        
        return {"detail": "Asset reassigned successfully", "assignment": new_assignment_details}
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Reassignment failed due to database constraint")


@router.get("/{asset_id}/assignment-history")
async def get_assignment_hist(asset_id: str,
                            current_user: User = Depends(get_current_user),
                            db: Session = Depends(get_db)):
    
    if not check_simple_permission(current_user, "asset", "read"):
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="assets",
                target_id=asset_id,
                details="Attempt to view assignment history without permission",
                level=LogLevel.WARNING
            )
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    asset = db.query(Assets).filter(Assets.id == asset_id).first()
    if not asset:
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.VIEW,
                target_table="assets",
                target_id=asset_id,
                details="Asset not found for assignment history",
                level=LogLevel.INFO
            )
        raise HTTPException(status_code=404, detail="Asset not found")
    
    assignment_events = (
        db.query(AssetLifecycleEvents)
        .filter(
            AssetLifecycleEvents.asset_id == asset_id,
            AssetLifecycleEvents.event_type.in_(["assigned", "unassigned", "reassigned"])
        )
        .order_by(AssetLifecycleEvents.event_date.desc())
        .all()
    )
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="assets",
            target_id=asset_id,
            details={"view": "assignment_history", "events_count": len(assignment_events)},
            level=LogLevel.INFO
        )
    
    return assignment_events

@router.get("/m/myassets",status_code=200)
async def list_user_assigned_assets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    user_assets = db.query(Assets).filter(Assets.responsible_officer_id == current_user.id).all()
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="assets",
            target_id=None,
            details={"view": "my_assigned_assets", "count": len(user_assets)},
            level=LogLevel.INFO
        )
    
    return user_assets

@router.get("/m/MyDepAssets",status_code=200)
async def list_my_department_assets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    assets = db.query(Assets).filter(Assets.department_id == current_user.id).all()
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="assets",
            target_id=None,
            details={"view": "my_department_assets", "count": len(assets)},
            level=LogLevel.INFO
        )
    
    p  = [AssetResponse(**add_namedep_asset(i)) for i in assets]
    
    return p
    
@router.get("/assignments/all")
async def list_all_assignments(current_user: User = Depends(get_current_user),
                             db: Session = Depends(get_db)):
    
    if not check_simple_permission(current_user, "asset", "read"):
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="assets",
                target_id=None,
                details="Attempt to list all assignments without permission",
                level=LogLevel.WARNING
            )
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    assigned_assets = (
        db.query(Assets)
        .filter(
            (Assets.responsible_officer_id.isnot(None)) |
            (Assets.department_id.isnot(None))
        )
        .all()
    )
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="assets",
            target_id=None,
            details={"view": "all_assignments", "count": len(assigned_assets)},
            level=LogLevel.INFO
        )
    
    return assigned_assets

@router.get("/assignments/unassigned")
async def list_unassigned_assets(current_user: User = Depends(get_current_user),
                               db: Session = Depends(get_db)):
    
    if not check_simple_permission(current_user, "asset", "read"):
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="assets",
                target_id=None,
                details="Attempt to list unassigned assets without permission",
                level=LogLevel.WARNING
            )
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    unassigned_assets = (
        db.query(Assets)
        .filter(
            Assets.responsible_officer_id.is_(None),
            Assets.department_id.is_(None)
        )
        .all()
    )
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="assets",
            target_id=None,
            details={"view": "unassigned_assets", "count": len(unassigned_assets)},
            level=LogLevel.INFO
        )
    
    return unassigned_assets
