from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, desc, asc
from typing import  Optional, Dict
from sqlalchemy.exc import IntegrityError

import uuid

from decimal import Decimal
from ..database import get_db
from ..models import User, Departments,Assets, AssetLifecycleEvents
from ..schemas.assets import (
    AssetCreate, AssetUpdate, AssetResponse, AssetListResponse,
    AssetSearchParams, AssetStatusUpdate
)
from ..asset_utils import (
    validate_category_attributes,
    calculate_depreciation,
    generate_tag_number,get_required_fields,StandardAssetAttributes,LandAttributes,BuildingAttributes
)

from ..asset_utils import add_namedep_asset
from ..utilities import get_current_user

router = APIRouter(
    prefix="/api/v1/assets",
    tags=["Assets CRUD"]
    )



def create_lifecycle_event(
    db: Session, 
    asset_id: str, 
    event_type: str, 
    user_id: str, 
    details: Optional[Dict] = None,
    remarks: Optional[str] = None
):

    event = AssetLifecycleEvents(
        asset_id=asset_id,
        event_type=event_type,
        performed_by=user_id,
        details=details or {},
        remarks=remarks
    )
    db.add(event)
    return event

def gen_asset_tag(db: Session, category: str, department_id: str) -> str:
    dept = db.query(Departments).filter(Departments.dept_id == department_id).first()
    dept_code = dept.name[:3].upper() if dept else "DEP"
    
    # Get nxt seq no
    last_asset = db.query(Assets).filter(
        Assets.department_id == department_id,
        Assets.category == category,
        Assets.is_deleted == False
    ).count()
    
    sequence = last_asset + 1
    return generate_tag_number(category, dept_code, sequence)




@router.post("/")# response_model=AssetResponse)
async def create_a_new_asset(asset_data: AssetCreate,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):

    if asset_data.specific_attributes:
        try:
            validated_attrs = validate_category_attributes(
                asset_data.category, 
                asset_data.specific_attributes
            )
            asset_data.specific_attributes = validated_attrs
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    if not asset_data.tag_number:
        asset_data.tag_number = gen_asset_tag(
            db, asset_data.category, asset_data.department_id
        )

    existing_asset = db.query(Assets).filter(Assets.tag_number == asset_data.tag_number, Assets.is_deleted == False).first()
    if existing_asset:
        raise HTTPException(status_code=400, detail="Tag number already exists")
    
    asset = Assets(id=str(uuid.uuid4()), created_by=current_user.id, **asset_data.dict())
    
    if asset.acquisition_cost and asset.depreciation_rate and asset.acquisition_date:

        depreciation = calculate_depreciation(asset.acquisition_cost, asset.depreciation_rate, asset.acquisition_date)
        asset.current_value = depreciation["net_book_value"]
    else:
        asset.current_value = asset.acquisition_cost
    try:
        db.add(asset)
        # db.refresh(asset)  # Get the ID
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Department Does not exist")

    #like logging
    # create_lifecycle_event(
        
    #     db, asset.id, "created", current_user.id,id = generate_id(),
    #     details={"category": asset.category, "initial_value": str(asset.acquisition_cost)},
    #     remarks="Asset created in system"
    # )
    
    db.commit()
    db.refresh(asset)
    
    return AssetResponse(**add_namedep_asset(asset))



@router.get("/categories", status_code=200)
def list_asset_categories_simple():   
    categories = {
        "Standard Assets": StandardAssetAttributes,
        "Land": LandAttributes,
        "Buildings and building improvements": BuildingAttributes,
    } 
    result = {}
    for c_name, schema_class in categories.items():
        required_fields = get_required_fields(c_name)
        
        all = list(schema_class.__annotations__.keys())
        
        result[c_name] = {
            "required_fields": required_fields,
            "all_fields": all
        }
    return result


@router.get("/", response_model=AssetListResponse)
async def list_assets_search_func(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    status: Optional[str] = None,
    department_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    query = db.query(Assets).filter(Assets.is_deleted == False)

    if category:
        query = query.filter(Assets.category == category)
    if status:
        query = query.filter(Assets.status == status)
    if department_id:
        query = query.filter(Assets.department_id == department_id)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Assets.description.ilike(search_term),
                Assets.tag_number.ilike(search_term),
                Assets.serial_number.ilike(search_term),
                Assets.location.ilike(search_term)
            )
        )
    
    total = query.count()
    offset = (page - 1) * size
    assets = query.options(
        joinedload(Assets.department),
        joinedload(Assets.responsible_officer)
    ).offset(offset).limit(size).all()
    
    total_pages = (total + size - 1) // size
    
    return AssetListResponse(assets=assets, total=total, page=page, size=size, total_pages=total_pages)

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset_by_id(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):  
    asset = db.query(Assets).options(
        joinedload(Assets.department),
        joinedload(Assets.responsible_officer)
    ).filter(Assets.id == asset_id, Assets.is_deleted == False).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return AssetResponse(**add_namedep_asset(asset))



@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(asset_id: str, asset_data: AssetUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):    
    asset = db.query(Assets).filter(Assets.id == asset_id, Assets.is_deleted == False).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if asset_data.specific_attributes:
        try:
            validated_attrs = validate_category_attributes(
                asset.category, 
                asset_data.specific_attributes
            )
            asset_data.specific_attributes = validated_attrs
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    changes = {}
    update_data = asset_data.dict(exclude_none=True)
    
    for field, nval in update_data.items():
        oval = getattr(asset, field)
        if oval != nval:
            changes[field] = {"old": str(oval), "new": str(nval)}
            setattr(asset, field, nval)
    
    # Recalculate depreciation if changes
    if any(field in changes for field in ['acquisition_cost', 'depreciation_rate', 'acquisition_date']):
        if asset.acquisition_cost and asset.depreciation_rate and asset.acquisition_date:
            depreciation = calculate_depreciation(asset.acquisition_cost,  asset.depreciation_rate,  asset.acquisition_date)
            asset.current_value = depreciation["net_book_value"]
            changes['current_value'] = {"new": str(asset.current_value)}
    
    if changes:
        create_lifecycle_event(
            db, asset.id, "updated", current_user.id,
            details={"changes": changes},
            remarks="Asset information updated"
        )
    
    db.commit()
    db.refresh(asset)
    
    return AssetResponse(**add_namedep_asset(asset))

@router.patch("/{asset_id}/status", response_model=AssetResponse)
async def update_asset_status(asset_id: str, status_data: AssetStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    asset = db.query(Assets).filter(Assets.id == asset_id, Assets.is_deleted == False).first()


    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    old_status = asset.status
    asset.status = status_data.status
    
    create_lifecycle_event(db, asset.id, "status_changed", current_user.id,
        details={
            "old_status": old_status,
            "new_status": status_data.status
        },
        remarks=status_data.remarks or f"Status changed from {old_status} to {status_data.status}"
    )
    
    db.commit()
    db.refresh(asset)
    
    return AssetResponse(**add_namedep_asset(asset))

@router.delete("/{asset_id}")
async def delete_asset(asset_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    asset = db.query(Assets).filter(Assets.id == asset_id, Assets.is_deleted == False).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    asset.is_deleted = True
    
    create_lifecycle_event(db, asset.id, "deleted", current_user.id, remarks="Asset deleted from system")
    db.commit()
    
    return {"message": "Asset deleted successfully"}

@router.get("/a/search/advanced", response_model=AssetListResponse)
async def advanced_asset_search_adm(params: AssetSearchParams = Depends(),db: Session = Depends(get_db), cu: User =  Depends(get_current_user)):
 
    query = db.query(Assets).filter(Assets.is_deleted == False)

    if params.query:
        search_term = f"%{params.query}%"
        query = query.filter(
            or_(
                Assets.description.ilike(search_term),
                Assets.tag_number.ilike(search_term),
                Assets.serial_number.ilike(search_term)
       
            )
        )
    
    if params.category:
        query = query.filter(Assets.category == params.category)
    if params.status:
        query = query.filter(Assets.status == params.status)
    if params.condition:
        query = query.filter(Assets.condition == params.condition)
    if params.department_id:
        query = query.filter(Assets.department_id == params.department_id)
    if params.responsible_officer_id:
        query = query.filter(Assets.responsible_officer_id == params.responsible_officer_id)
    if params.location:
        query = query.filter(Assets.location.ilike(f"%{params.location}%"))
    if params.min_value:
        query = query.filter(Assets.current_value >= params.min_value)
    if params.max_value:
        query = query.filter(Assets.current_value <= params.max_value)
    if params.acquisition_date_from:
        query = query.filter(Assets.acquisition_date >= params.acquisition_date_from)
    if params.acquisition_date_to:
        query = query.filter(Assets.acquisition_date <= params.acquisition_date_to)
    
    sort_column = getattr(Assets, params.sort_by, Assets.created_at)
    if params.sort_order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))
    
    total = query.count()
    
    offset = (params.page - 1) * params.size
    assets = query.options(joinedload(Assets.department),joinedload(Assets.responsible_officer)).offset(offset).limit(params.size).all()
    
    total_pages = (total + params.size - 1) // params.size
    
    return AssetListResponse(assets=assets, total=total, page=params.page, size=params.size, total_pages=total_pages)

