from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional,Union,Any,Dict
from ..database import get_db
from ..models import Role, User, Departments
from ..utilities import generate_id,get_current_user,get_changes
from ..system_vars import sys_logger,debugging,default_new_department_status
from ..services.logger_queue import enqueue_log
from ..schemas.main import DepartmentDetails,DepartmentDetailsSimple, DepartmentStatus, CreateDepartment, UserStatus,NoChangesResponse,DepartmentUsers,DepartmentDetailsPublic,UserStatus
from ..services.policy_eval import check_simple_permission,check_full_permission,get_user_perms
from sqlalchemy import or_, func
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload

router = APIRouter(
    prefix="/api/v1/departments", 
    tags=["Departments "]
    )



@router.post("/", status_code=status.HTTP_201_CREATED, response_model=DepartmentDetails)
async def create_department(dep: CreateDepartment,curr: User = Depends(get_current_user),db:Session = Depends(get_db)):
    
    id = generate_id(40)
    det = Departments(
        dept_id = id,
        name = dep.name,
        parent_dept_id = dep.parent_dept_id ,
        entity_type = dep.entity_type ,
        description = dep.description ,
        status = default_new_department_status 
    )
    db.add(det)
    db.commit()
    db.refresh(det)
    return det

@router.get("/",status_code=status.HTTP_200_OK,response_model=List[DepartmentDetails])
async def list_all_departments(curr: User = Depends(get_current_user),db: Session = Depends(get_db)):
    
    deps = db.query(Departments).all()
    return deps

@router.get("/simple",status_code=status.HTTP_200_OK,response_model=List[DepartmentDetailsSimple])
async def list_all_departments_simple(curr: User = Depends(get_current_user),db: Session = Depends(get_db)):
    
    deps = db.query(Departments).all()
    return deps


@router.get("/public",status_code=status.HTTP_200_OK,response_model=List[DepartmentDetailsPublic])
async def list_all_departments_public(db: Session = Depends(get_db)):
    """Lists all active departments"""
    
    deps = db.query(Departments).filter(Departments.status == UserStatus.active).all()
    return deps

@router.get("/heads",status_code=status.HTTP_200_OK,response_model=List[DepartmentDetailsPublic])
async def list_all_departments_public(db: Session = Depends(get_db)):
    """Lists all  departments Heads"""
    
    deps = db.query(Departments).filter(Departments.status == UserStatus.active).all()
    return deps


@router.get("/{dep_id}/users",status_code=status.HTTP_200_OK,response_model=List[DepartmentUsers])
async def get_department_members(dep_id,curr: User = Depends(get_current_user),db: Session = Depends(get_db)):
    users = db.query(User).filter(User.department_id == dep_id).all()
    return users

@router.get("/{dep_id}/hierarchy",status_code=status.HTTP_200_OK )
async def get_department_hierachy(dep_id,curr: User = Depends(get_current_user),db: Session = Depends(get_db)):
    def build_hierarchy(dept) -> Dict[str, Any]:
        return {
            "dept_id": dept.dept_id,
            "name": dept.name,
            "entity_type": dept.entity_type.name if dept.entity_type else None,
            "description": dept.description,
            "status": dept.status.name if dept.status else None,
            "sub_departments": [build_hierarchy(sub) for sub in dept.sub_departments]
        }
    
    dept = db.query(Departments).filter(Departments.dept_id == dep_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    return build_hierarchy(dept)

@router.post("/{dep_id}/status",status_code=status.HTTP_200_OK,response_model=Union[dict ,NoChangesResponse])
async def change_department_status(dep_id,stats: DepartmentStatus,curr: User = Depends(get_current_user),db: Session = Depends(get_db)):
    
    dep = db.query(Departments).filter(Departments.dept_id == dep_id).first()

    if dep.status == stats.status:
        return {"details": "No change applied"}

    dep.status = stats.status

    db.commit()
    db.refresh(dep)
    return {"detail": f"changed status to: {dep.status.value}"}



@router.get("/{dep_id}",status_code=status.HTTP_200_OK,response_model=DepartmentDetails)
async def get_department_by_id(dep_id,curr: User = Depends(get_current_user),db: Session = Depends(get_db)):
    
    
    deps = db.query(Departments).filter(Departments.dept_id == dep_id).first()
    if not deps:
         raise HTTPException(status_code=404, detail="Department not found")
    return deps


@router.delete("/{dep_id}",status_code=status.HTTP_200_OK,response_model=dict)
async def delete_a_department(dep_id,curr: User = Depends(get_current_user),db: Session = Depends(get_db)):

    deps = db.query(Departments).filter(Departments.dept_id == dep_id).first()
    if not deps:
        raise HTTPException(status_code=404, detail="Department not found")
    deps.status = UserStatus.deleted
    db.commit()
    db.refresh(deps)
    return {"detail": "Successfully Deleted"}


@router.put("/{dep_id}",status_code=status.HTTP_200_OK,response_model=Union[dict ,NoChangesResponse])
async def patch_department_details(dep_id,det:CreateDepartment, curr: User = Depends(get_current_user),db: Session = Depends(get_db)):
    

    deps = db.query(Departments).filter(Departments.dept_id == dep_id).first()
    if not deps:
         raise HTTPException(status_code=404, detail="Department not found")

    upd ,changes= get_changes(deps,det)
    
    if changes:
        
        db.commit()
        db.refresh(upd)
        return {"changes": changes}
    
    return {"detail": "No changes supplied"}


