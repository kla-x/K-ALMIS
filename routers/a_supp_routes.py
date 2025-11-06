from fastapi import APIRouter,Depends
from ..models import AssetStatus,AssetCondition,AssetCategory,User,MaintenanceType, IssueCategory,PriorityLevel,SeverityLevel,MaintenanceOutcome
from typing import Dict,List
from ..asset_utils import StandardAssetAttributes, LandAttributes,BuildingAttributes,get_required_fields,get_default_attributes
from ..schemas.assets import CategoryInfo
from ..utilities import get_current_user

router = APIRouter(
    prefix="/api/v1/assets/supp",
    tags=["Assets Supporting routes"]
    )

@router.get("/assetstatus", status_code=200,response_model=Dict[str, str])
async def list_asset_statuses(curr: User = Depends(get_current_user)):
    
    return {x.name: x.value for x in AssetStatus }

@router.get("/assetcondition", status_code=200,response_model=Dict[str, str])
async def list_asset_condition(curr: User = Depends(get_current_user)):
    
    return {x.name: x.value for x in AssetCondition}

@router.get("/categories/newlist", status_code=200,response_model=Dict[str, str])
async def list_categories_byname(curr: User = Depends(get_current_user)):


    return {x.name: x.value for x in AssetCategory}


@router.get("/categories/detailed", status_code=200)
async def list_asset_categories_detailed(curr: User = Depends(get_current_user)):
    categories = {
        "Standard Assets": StandardAssetAttributes,
        "Land": LandAttributes,
        "Buildings and building improvements": BuildingAttributes,
    }
    
    result = {}
    
    for category_name, schema_class in categories.items():
        required_fields = get_required_fields(category_name)
        
        schema_instance = schema_class()
        
        if hasattr(schema_instance, '__fields__'):
            all_fields = list(schema_instance.__fields__.keys())
        elif hasattr(schema_instance, 'model_fields'):
            all_fields = list(schema_instance.model_fields.keys())
        else:
            all_fields = list(schema_class.__annotations__.keys())
        
        field_details = {}
        for field_name in all_fields:

            field_type = schema_class.__annotations__.get(field_name, str)

            type_str = str(field_type)
            if "Optional" in type_str:
                if hasattr(field_type, '__args__') and field_type.__args__:
                    actual_type = field_type.__args__[0]
                    type_name = getattr(actual_type, '__name__', str(actual_type))
                else:
                    type_name = "str"
            else:
                type_name = getattr(field_type, '__name__', str(field_type))
            
            field_details[field_name] = {
                "type": type_name,
                "required": field_name in required_fields,
                "description": field_name.replace('_', ' ').title()
            }
        
        result[category_name] = {
            "required_fields": required_fields,
            "all_fields": field_details,
            "schema_name": schema_class.__name__
        }
    
    return {
        "message": "Asset categories and their fields",
        "categories": result
    }


@router.get("/categories/info", response_model=List[CategoryInfo])
async def get_asset_categories_info():
    categories = [
        {
            "category": "Standard Assets",
            "description": "General assets register for standard equipment and items",
            "fields": [
                {"field_name": "asset_description", "field_type": "string", "required": True},
                {"field_name": "make_model", "field_type": "string", "required": False},
                {"field_name": "serial_number", "field_type": "string", "required": False},
                {"field_name": "responsible_officer", "field_type": "string", "required": False}
            ],
            "sample_attributes": get_default_attributes("Standard Assets")
        },
        {
            "category": "Land",
            "description": "Land register for land assets and properties",
            "fields": [
                {"field_name": "description_of_land", "field_type": "string", "required": True},
                {"field_name": "size_hectares", "field_type": "decimal", "required": True},
                {"field_name": "county", "field_type": "string", "required": True},
                {"field_name": "lr_certificate_no", "field_type": "string", "required": False}
            ],
            "sample_attributes": get_default_attributes("Land")
        },
        {
            "category": "Buildings and building improvements",
            "description": "Buildings register for building assets and improvements",
            "fields": [
                {"field_name": "description_name_of_building", "field_type": "string", "required": True},
                {"field_name": "type_of_building", "field_type": "string", "required": True},
                {"field_name": "county", "field_type": "string", "required": True},
                {"field_name": "no_of_floors", "field_type": "integer", "required": False}
            ],
            "sample_attributes": get_default_attributes("Buildings and building improvements")
        }
    ]
    
    return categories


@router.get("/maintain/MaintenanceType",status_code=200,response_model=Dict[str, str])
async def list_maintainance_types(curr: User = Depends(get_current_user)):

    return {x.name: x.value for x in MaintenanceType}

@router.get("/maintain/IssueCategory",status_code=200,response_model=Dict[str, str])
async def list_issue_categories(curr: User = Depends(get_current_user)):

    return {x.name: x.value for x in IssueCategory}
@router.get("/maintain/PriorityLevel",status_code=200,response_model=Dict[str, str])
async def list_priorrity_levels(curr: User = Depends(get_current_user)):

    return {x.name: x.value for x in PriorityLevel}
@router.get("/maintain/SeverityLevel",status_code=200,response_model=Dict[str, str])
async def list_Severerity_level(curr: User = Depends(get_current_user)):

    return {x.name: x.value for x in SeverityLevel}

@router.get("/maintain/maintainanceoutcome",status_code=200,response_model=Dict[str, str])
async def list_the_2_maint_outcomes(curr: User = Depends(get_current_user)):

    return {x.name: x.value for x in MaintenanceOutcome}




