from fastapi import APIRouter, Depends, HTTPException, status,BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional,Union
from ..database import get_db
from ..models import Role, User,GovLevel,Departments
from ..schemas.main import CreateUserAdmin,AuthMethod
from ..utilities import generate_id,get_current_user,generate_id,pwd_context,get_changes
from ..system_vars import sys_logger,debugging,user_default_pass,default_new_user_status,send_emails,sys_logger
from ..services.logger_queue import enqueue_log
from ..schemas.main import  ActionType, LogLevel,GivePerms,UserStatus,UserOutWithRole, ModifyProfile,ChangeUserStatus,NoChangesResponse,UserOutProfile
from ..services.policy_eval import check_simple_permission,check_full_permission,get_user_perms
from sqlalchemy import or_, func
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload

if send_emails:
    from .auth import email_service
router = APIRouter(
    prefix="/api/v1/users", 
    tags=["Users "]
    )

@router.get("/",status_code=status.HTTP_200_OK,response_model=List[UserOutWithRole])
async def get_all_users_param(current_user: User = Depends(get_current_user),db :Session = Depends(get_db),
                              status: Optional[UserStatus] = None,
                              namecontains: Optional[str] = None,
                              email:Optional[str] = None,
                              last_login:Optional[datetime] = None,
                              phone:Optional [str] = None,

                              location_code: Optional[str] =None,
                              department_id:Optional[str] =None,
                              gov_level: Optional[GovLevel] = None,
                              role_id: Optional[str] = None):
    """use is as a search function

    Args:

      - status (Optional[UserStatus], optional): active,inactive ... Defaults to None.
      - namecontains (Optional[str], optional): part of name. Defaults to None.
      - isactive (Optional[bool], optional): true, false,bool. Defaults to None.
      - email (Optional[str], optional): full email. Defaults to None.
      - last_login (Optional[datetime], optional): timestamp . Defaults to None.
      - phone (Optional[str], optional): 07xbhjb. Defaults to None.
      - role (Optional[str], optional): role name, not id. Defaults to None.

    Raises:
        HTTPException: not fround

    Returns:
        User: _description_
    """

    if not check_simple_permission(current_user, "users","read"):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    

    # returns only users within checker scope
    # - check department or reginal access scope
    # - attribute/roles - department head/ hr/ analytics ==[to imp]
    users = db.query(User)


    if status:
        users= users.filter(User.status == status)
    if namecontains:
        term = namecontains.lower().strip()
        pattern = '%' + '%'.join(term) + '%'
        users = users.filter(
            or_(
                func.lower(User.first_name).like(pattern),
                func.lower(User.last_name).like(pattern),
                func.lower(func.concat(User.first_name, ' ', User.last_name)).like(pattern)
            )
        )
   
    if email:
        users = users.filter(User.email == email)
    if last_login:
        users = users.filter(User.last_login >= last_login)
    if phone:
        users = users.filter(User.phone == phone)
    if role_id:
        users = users.join(User.role).filter(Role.name == role_id)
    if gov_level:
        users = users.filter(User.gov_level == gov_level)
    
    if sys_logger:
        await enqueue_log(
            user_id=current_user.id,
            action=ActionType.VIEW,
            target_table="users",
            target_id=None,
            details={"msg": "search function"},
            level=LogLevel.INFO
            )  
    
    return users.all()

@router.get("/me",status_code=status.HTTP_200_OK,response_model=UserOutProfile)
async def get_my_profile(me :User = Depends(get_current_user),db: Session = Depends(get_db)):
    return me

@router.put("/me",status_code=status.HTTP_200_OK,response_model=Union[UserOutProfile ,NoChangesResponse])
async def patch_my_profile(newval: ModifyProfile, me :User = Depends(get_current_user),db: Session = Depends(get_db)):
    old = db.query(User).filter(User.id == me.id).first()
    newme ,changes= get_changes(old,newval)
    
    if changes:
        
        db.commit()
        db.refresh(newme)
        return newme
    
    return {"detail": "No changes supplied"}


@router.get("/me/permissions",status_code=status.HTTP_200_OK)
async def get_my_allowd_permissions(me :User = Depends(get_current_user),db: Session = Depends(get_db)):
    #acess scope check

    return get_user_perms(user=me,db=db)

@router.get("/me/permissions/{resource}",status_code=status.HTTP_200_OK)
async def get_my_allowed_actions_for_resource(resource ,me :User = Depends(get_current_user),db: Session = Depends(get_db)):
    #acess scope
    #permissions for assigned role= make helper func
    perms = get_user_perms(user=me,db=db)
    specific = [p for p in perms if p.startswith(f"{resource}.")]
    actions =sorted({p.split(".",1)[1] for p in specific})

    return actions

#----------------------------------
@router.get("/{user_id}/permissions",status_code=status.HTTP_200_OK)
async def get_user_permissions_adm(user_id,curr : User = Depends(get_current_user),db: Session = Depends(get_db)):
    #add checks, hr, permissision to check, scope, shouldnt check superior
    perms = get_user_perms(id=user_id,db=db)
    return perms

@router.get("/{user_id}/permissions/{resource}",status_code=status.HTTP_200_OK)
async def get_user_permissions_per_resource_adm(resource,user_id,curr : User = Depends(get_current_user),db: Session = Depends(get_db)):

    perms = get_user_perms(id=user_id,db=db)
    specific = [p for p in perms if p.startswith(f"{resource}.")]
    actions =sorted({p.split(".",1)[1] for p in specific})
    return actions

@router.put("/{user_id}/permissions",status_code=status.HTTP_200_OK)
async def give_user_permissions_adm(user_id ,pp: GivePerms,curr : User = Depends(get_current_user),db: Session = Depends(get_db)):
    #check fist if you have said permission, then give
    user = db.query(User).filter(User.id == user_id).first()

    role_perms = db.query(Role).filter(Role.id == user.role_id).first()
        
    if not role_perms:
        raise HTTPException(status_code=404, detail="Target not Assigned any role")

    rperm = set(role_perms.permissions or [])
    aperm = set(user.assigned_perms or [])

    nperm = []

    for p in pp.permissions:
        if p not in rperm and p not in aperm:
            nperm.append(p)
            aperm.add(p)

    user.assigned_perms = list(aperm)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"added": nperm,"now_has": user.assigned_perms}

@router.get("/{user_id}/permissions/{resource}",status_code=status.HTTP_200_OK)
async def get_user_permissions_by_resource_adm(user_id,resource,curr : User = Depends(get_current_user),db: Session = Depends(get_db)):
    #add checks, hr, permissision to check, scope, shouldnt check superior
    perms = get_user_perms(id=user_id,db=db)
    specific = [p for p in perms if p.startswith(f"{resource}.")]
    actions =sorted({p.split(".",1)[1] for p in specific})

    return actions


@router.get("/{user_id}", response_model=UserOutWithRole)
async def get_user_details(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific user details with resource-based access control"""
    # - confirm checker department below target
    #- checker attributes manage-attributes, HR
    # - else return not enoth perm to view this user
    
    target = db.query(User).options(
        joinedload(User.role),
        joinedload(User.department)
    ).filter(User.id == user_id).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # resource = {
    #     "target_id": target.id,
    #     "target_county": target.location_code,
    #     "target_department": target.department.name if target.department else None,
    #     "target_role": target.role.name if target.role else None,
    #     "is_self": current_user.id == user_id,
    #     "is_same_county": current_user.location_code == target.location_code,
    #     "is_same_department": current_user.department_id == target.department_id
    # }

    # if not check_permission(current_user, "users", "read", db, resource):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return target

@router.post("/", status_code=status.HTTP_201_CREATED,response_model=UserOutWithRole)

async def create_new_user_adm(user: CreateUserAdmin , db: Session = Depends(get_db)):
    # must be hr , has create-user attribute
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
 
    hashed_pass = pwd_context.hash(user_default_pass)
    user_id = generate_id()

    if user.entity_name:
        eval_ent_name=user.entity_name
    else:
        try:
            rl = db.query(Departments).filter(Departments.dept_id == user.department_id).first()
            eval_ent_name = rl.name
        except IntegrityError as e:
            raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED,detail = "invalid department id or entitiy name")

            

    new_user = User(
        id=user_id,
        profile_pic=user.profile_pic,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone_number=user.phone_number,
        department_id=user.department_id,
        position_title=user.position_title,
        is_accounting_officer=False,
        password_hash=hashed_pass,  
        role_id=user.role_id,
        status=user.status,
        created_at=datetime.now(timezone.utc),
        last_login=None,
        gov_level=user.gov_level,
        entity_type=user.entity_type,

        entity_name=eval_ent_name,
        location=user.location.dict(),
        access_scope='{}',
        is_two_factor_enabled=False,
        last_password_change=None,
        login_attempts=None,
        last_activity_at=None,
        notes=user.notes,
        auth_method=AuthMethod.password,
    )

    db.add(new_user)
    db.commit()
    
    db.refresh(new_user) 
    return new_user



@router.put("/{user_id}",status_code=status.HTTP_200_OK,response_model=Union[dict ,NoChangesResponse]) #UserOutWithRole
# hr, change doesnt escalate rank,
async def patch_user_details_adm(user_id,usernd:CreateUserAdmin ,current_user: User = Depends(get_current_user) ,db: Session = Depends(get_db)):

    usr = db.query(User).filter(User.id == user_id).first()

    new_usr, changes = get_changes(usr,usernd)
    if changes:
        
        db.commit()
        db.refresh(new_usr)
        return changes
    

    # raise HTTPException(detail="No changes applied", status_code=200)
    return {"detail": "No changes supplied"}



@router.put("/{user_id}/status", status_code=status.HTTP_200_OK,response_model=Union[dict,UserOutWithRole])
async def patch_user_status(user_id,usernd:ChangeUserStatus ,background_tasks: BackgroundTasks,current_user: User = Depends(get_current_user) ,db: Session = Depends(get_db)):
    #dep head, target subordinate, can update status, in scope,dep,coumty or national, ht

    usr = db.query(User).filter(User.id == user_id).first()
    if not usr:
        raise HTTPException(detail="User not found",status_code=status.HTTP_400_BAD_REQUEST)
    if usr.status == usernd.status :
        return {"detail": "No changes supplied"}

    usr.status = usernd.status
    
    db.commit()
    db.refresh(usr)
    if send_emails:
        background_tasks.add_task(
            email_service.send_account_activated_email,
            str(usr.email),
            str(usr.first_name)
        )
    return {"detail": f"status changed to: {usr.status.value}"}


@router.delete("/{user_id}", status_code=status.HTTP_200_OK,response_model=dict)
async def delete_user(user_id,usernd:ChangeUserStatus ,current_user: User = Depends(get_current_user) ,db: Session = Depends(get_db)):
    #dep head, target subordinate, can update status, in scope,dep,coumty or national, ht

    usr = db.query(User).filter(User.id == user_id).first()
    if usr.status.value == "deleted":
        return {"detail": "User Already Deleted"}
    usr.status = UserStatus.deleted
    db.commit()
    db.refresh(usr)

    return {"detail":f"Success! delete user{usr.id}"}

