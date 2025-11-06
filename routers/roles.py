from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from ..database import get_db
from ..models import Role, User
from ..schemas.main import RoleCreate, RoleOut,UsersWithRoleX,RoleUpdate
from ..utilities import generate_id,get_current_user,generate_id
from ..system_vars import sys_logger,debugging
from ..services.logger_queue import enqueue_log
from ..schemas.main import  ActionType, LogLevel
from ..services.policy_eval import check_simple_permission,require_specific_role,check_full_permission


router = APIRouter(
    prefix="/api/v1/roles", 
    tags=["Roles"]
    )

@router.post("/no-auth-crit", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
async def create_role_noperm(rdata: RoleCreate,db:Session = Depends(get_db)):
    id = generate_id(30)
    role = Role(id =id,name=rdata.name, description =rdata.description ,permissions=rdata.permissions)
    db.add(role)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Role with name '{rdata.name}' already exists")

    db.refresh(role)

    if sys_logger:
        await enqueue_log(
            user_id=None,
            action=ActionType.CREATE,
            target_table="roles",
            target_id=id,
            details={"route": "no-auth-crit", "payload": rdata.dict(exclude_unset=True)},
            level=LogLevel.INFO
        )
    return role


@router.post("/", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
async def create_role(rdata: RoleCreate,current_user: User = Depends(get_current_user) ,db:Session = Depends(get_db)):
    state,det = require_specific_role(current_user,['super_user_do'])
    if not state:
        if sys_logger:
            await enqueue_log(
               user_id=current_user.id,
               action=ActionType.SUSPICIOUS_ACTIVITY,
               target_table="roles",
               target_id=None,
               details=f"Insufficient permissions to create role {rdata.dict(exclude_unset=True)}",
               level=LogLevel.CRITICAL)
        
        raise HTTPException(status_code=403, detail=det)
    idd = generate_id(30)
    role = Role(id = idd ,name=rdata.name,description =rdata.description, permissions=rdata.permissions)

        
    db.add(role)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Role with name '{rdata.name}' already exists")

    db.refresh(role)

    if sys_logger:
        await enqueue_log(
           user_id=current_user.id,
           action=ActionType.CREATE,
           target_table="roles",
           target_id=idd,
           details=None,
           level=LogLevel.INFO)
    return role

@router.get("/", response_model=List[RoleOut])
async def list_roles(db: Session = Depends(get_db)):
    
    
    # if not check_simple_permission(current_user, "role", "read"):
    #     if sys_logger:
    #         await enqueue_log(
    #             user_id=current_user.id,
    #             action=ActionType.SUSPICIOUS_ACTIVITY,
    #             target_table="roles",
    #             target_id=None,
    #             details="Attempt to list roles without permission",
    #             level=LogLevel.WARNING
    #         )
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if sys_logger:
        await enqueue_log(
            user_id="no_user",
            action=ActionType.VIEW,
            target_table="roles",
            target_id=None,
            details=None,
            level=LogLevel.INFO
    )
    roles = db.query(Role).all()
    if debugging:
        print("\n\n\n\n\n\nreturnung role\n\n\n")
    if roles: 
        return roles 
    else:
        return []
    


@router.get("/{role_id}", response_model=RoleOut)
async def get_role(role_id: str,db:Session = Depends(get_db)):
    if not check_simple_permission(current_user, "role", "read"):
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="roles",
                target_id=role_id,
                details="Attempt to get role without permission",
                level=LogLevel.WARNING
            )
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="roles",
            target_id=role_id,
            details=None,
            level=LogLevel.INFO
            ) 
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.VIEW,
                target_table="roles",
                target_id=role_id,
                details="Role not found",
                level=LogLevel.INFO
            )
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.get("/{role_id}/permissions")
async def get_role_permissions(role_id: str,current_user: User = Depends(get_current_user) ,db:Session = Depends(get_db)):
    if not check_simple_permission(current_user, "role", "read"):
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="roles",
                target_id=role_id,
                details="Attempt to read role permissions without permission",
                level=LogLevel.WARNING
            )
        raise HTTPException(status_code=403, detail="Not enough permissions")
    

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.VIEW,
                target_table="roles",
                target_id=role_id,
                details="Role not found when fetching permissions",
                level=LogLevel.INFO
            )
        raise HTTPException(status_code=404, detail="Role not found")
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="roles",
            target_id=role_id,
            details="Fetched role permissions",
            level=LogLevel.INFO
        )
    
    return role.permissions or {}


@router.post("/{role_id}/permissions/add")
async def add_permission(role_id: str,permission: str,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    perms = set(role.permissions or [])
    if permission in perms:
        raise HTTPException(status_code=400, detail=f"Permission '{permission}' already exists in role")

    perms.add(permission)
    role.permissions = list(perms)
    db.commit()
    db.refresh(role)

    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.UPDATE,
            target_table="roles",
            target_id=role_id,
            details={"added_permission": permission},
            level=LogLevel.INFO,
        )

    return {"detail": f"Permission '{permission}' added", "permissions": role.permissions}


@router.post("/{role_id}/permissions/remove")
async def remove_permission(role_id: str,permission: str,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    perms = set(role.permissions or [])
    if permission not in perms:
        raise HTTPException(status_code=400, detail=f"Permission '{permission}' not found in role")

    perms.remove(permission)
    role.permissions = list(perms)
    db.commit()
    db.refresh(role)

    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.UPDATE,
            target_table="roles",
            target_id=role_id,
            details={"removed_permission": permission},
            level=LogLevel.INFO,
        )

    return {"detail": f"Permission '{permission}' removed", "permissions": role.permissions}

@router.put("/{role_id}", response_model=RoleOut)
async def update_role(role_id: str, rdata: RoleUpdate,current_user: User = Depends(get_current_user) ,db:Session = Depends(get_db)):
    # if not check_simple_permission(current_user, "role", "update"):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    try:
        check_full_permission(current_user, "role", "update", db, resource=None)
    except HTTPException as e:
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="roles",
                target_id=role_id,
                details=f"Update denied: {e.detail}",
                level=LogLevel.CRITICAL
            )
        raise

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.UPDATE,
                target_table="roles",
                target_id=role_id,
                details="Role not found for update",
                level=LogLevel.INFO
            )
        raise HTTPException(status_code=404, detail="Role not found")
    
    changes = {}
    update_data = rdata.dict(exclude_unset=True)
    for field, value in update_data.items():
        old_value = getattr(role, field)
        if old_value != value:
            setattr(role, field, value)
            changes[field] = {"old": old_value, "new": value}
  
    role.name = rdata.name
    role.permissions = rdata.permissions
    db.commit()
    db.refresh(role)


    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.UPDATE,
            target_table="roles",
            target_id=role_id,
            details=changes or rdata.dict(exclude_unset=True),
            level=LogLevel.INFO
        )

    return role

@router.delete("/{role_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_role(role_id: str,current_user: User = Depends(get_current_user) ,db:Session = Depends(get_db)):
    # if not check_simple_permission(current_user, "role", "delete"):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    try:
        check_full_permission(current_user, "role", "delete", db, resource=None)
    except HTTPException as e:
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="roles",
                target_id=role_id,
                details=f"Delete denied: {e.detail}",
                level=LogLevel.CRITICAL
            )
        raise

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.DELETE,
                target_table="roles",
                target_id=role_id,
                details="Role not found for delete",
                level=LogLevel.INFO
            )
        raise HTTPException(status_code=404, detail="Role not found")
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.DELETE,
            target_table="roles",
            target_id=role_id,
            details=None,
            level=LogLevel.INFO
        )
    db.delete(role)
    db.commit()

    return {"detail": f"deleted role: {role.id}"}

@router.get("/user/{role_id}",status_code=status.HTTP_200_OK, response_model=List[UsersWithRoleX])
async def get_all_users_with_role(role_id: str,current_user: User = Depends(get_current_user) ,db:Session = Depends(get_db)):
    if not check_simple_permission(current_user, "role", "read"):
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="roles",
                target_id=role_id,
                details="Attempt to list users with role without role.read",
                level=LogLevel.WARNING
            )
        raise HTTPException(status_code=403, detail="Not enough permissions (role.read)")

    if not check_simple_permission(current_user, "users", "read"):
        if sys_logger:
            await enqueue_log(
                user_id=current_user.id,
                action=ActionType.SUSPICIOUS_ACTIVITY,
                target_table="users",
                target_id=None,
                details="Attempt to list users with role without users.read",
                level=LogLevel.WARNING
            )
        raise HTTPException(status_code=403, detail="Not enough permissions (users.read)")

    users = db.query(User).filter(User.role_id == role_id).all()
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="roles",
            target_id=role_id,
            details={"view": f"all users with role {role_id}", "count": len(users)},
            level=LogLevel.INFO
        )
    return users