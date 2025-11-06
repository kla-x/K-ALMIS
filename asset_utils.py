
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime, date
from pydantic import BaseModel, validator
from enum import Enum
from .models import Assets


def add_namedep_asset(asset: Assets) -> dict:
    return {
        **asset.__dict__,
        "department_name": asset.department.name if asset.department else None,
        "responsible_officer_name": (
            asset.responsible_officer.full_name if asset.responsible_officer else None
        ),
    }

class StandardAssetAttributes(BaseModel):
    make_model: Optional[str] = None
    date_of_delivery: Optional[date] = None
    payment_voucher_number: Optional[str] = None
    original_location: Optional[str] = None
    replacement_date: Optional[date] = None
    notes: Optional[str] = None

class LandAttributes(BaseModel):
    gps_coordinates: Optional[str] = None
    polygon_coordinates: Optional[Dict] = None 
    lr_certificate_no: Optional[str] = None
    document_of_ownership: Optional[str] = None
    proprietorship_details: Optional[str] = None
    
    # Land Specific Details
    size_hectares: Optional[Decimal] = None
    ownership_status: Optional[str] = None  # Freehold/Leasehold
    registration_date: Optional[date] = None
    disputed_status: Optional[str] = None  # Disputed/Undisputed
    encumbrances: Optional[str] = None
    planned_unplanned: Optional[str] = None
    purpose_use_of_land: Optional[str] = None
    surveyed_status: Optional[str] = None  # Surveyed/Not Surveyed
    
    change_of_use_date: Optional[date] = None
    annual_rental_income: Optional[Decimal] = None
  

class BuildingAttributes(BaseModel):
    building_ownership: Optional[str] = None
    building_no: Optional[str] = None
    institution_no: Optional[str] = None
    street: Optional[str] = None
    lr_no: Optional[str] = None
    
    size_of_land_ha: Optional[Decimal] = None
    ownership_status: Optional[str] = None  # Freehold/Leasehold
    building_construction_date: Optional[date] = None
    lease_start_date: Optional[date] = None
    type_of_building: Optional[str] = None  # Permanent/Temporary
    designated_use: Optional[str] = None
    period_of_lease: Optional[int] = None
    no_of_floors: Optional[int] = None
    plinth_area_sq_feet: Optional[Decimal] = None

    cost_of_construction: Optional[Decimal] = None
    valuation: Optional[Decimal] = None
    annual_rental_income: Optional[Decimal] = None

def get_category_schema(category: str) -> Optional[BaseModel]:
    """Get the appropriate schema for a given asset category"""
    schema_mapping = {
        "Standard Assets": StandardAssetAttributes,
        "Land": LandAttributes,
        "Buildings and building improvements": BuildingAttributes,
    }
    return schema_mapping.get(category)

def validate_category_attributes(category: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
    """Validate category-specific attributes against their schema"""
    schema_class = get_category_schema(category)
    if not schema_class:
        # if not implemented  return as it s
        return attributes
    
    try:
        validated = schema_class(**attributes)
        return validated.dict(exclude_none=True)
    except Exception as e:
        raise ValueError(f"Invalid attributes for category {category}: {str(e)}")

def get_required_fields(category: str) -> List[str]:
    """Get required fields for a specific asset category"""
    required_fields_mapping = {
        "Standard Assets": ["asset_description", "acquisition_cost_kshs"],
        "Land": ["description_of_land", "size_hectares", "county"],
        "Buildings and building improvements": ["description_name_of_building", "type_of_building", "county"]
    }
    return required_fields_mapping.get(category, [])

def get_default_attributes(category: str) -> Dict[str, Any]:
    """Get default attributes structure for a category"""
    schema_class = get_category_schema(category)
    if not schema_class:
        return {}
    
    # Return empty instance of schema as dict
    return schema_class().dict()

def format_attributes_for_display(category: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
    """Format category-specific attributes for display purposes"""
    if not attributes:
        return {}
     
    formatted = {}
    for key, value in attributes.items():
        if value is not None:
            
            display_key = key.replace('_', ' ').title() #change case to normal
   
            if isinstance(value, Decimal):
                formatted[display_key] = f"KES {value:,.2f}"
            elif isinstance(value, date):
                formatted[display_key] = value.strftime("%Y-%m-%d")
            elif isinstance(value, str) and key.endswith('_date'):
                formatted[display_key] = value
            else:
                formatted[display_key] = value
    
    return formatted

def extract_searchable_text(category: str, attributes: Dict[str, Any]) -> str:
    """Extract searchable text from category-specific attributes"""
    if not attributes:
        return ""
    
    searchable_fields = {
        "Standard Assets": ["asset_description", "make_model", "serial_number"],
        "Land": ["description_of_land", "nearest_town_location", "lr_certificate_no"],
        "Buildings and building improvements": ["description_name_of_building", "street", "designated_use"]
    }
    
    fields = searchable_fields.get(category, list(attributes.keys()))
    searchable_values = []
    
    for field in fields:
        if field in attributes and attributes[field]:
            searchable_values.append(str(attributes[field]))
    
    return " ".join(searchable_values)

def calculate_depreciation(
    acquisition_cost: Decimal, 
    depreciation_rate: Decimal, 
    acquisition_date: date,
    calculation_date: Optional[date] = None
) -> Dict[str, Decimal]:
    """calc depreciation vals"""
    if calculation_date is None:
        calculation_date = date.today()
    
    years_elapsed = Decimal((calculation_date - acquisition_date).days) / Decimal("365.25")
    annual_depreciation = acquisition_cost * (depreciation_rate / Decimal("100"))
    accumulated_depreciation = min(annual_depreciation * years_elapsed, acquisition_cost)
    net_book_value = acquisition_cost - accumulated_depreciation
    
    return {
        "annual_depreciation": annual_depreciation,
        "accumulated_depreciation": accumulated_depreciation,
        "net_book_value": net_book_value
    }

def generate_tag_number(category: str, department_code: str, sequence: int) -> str:
    """Generate asset tag number based on category and department"""
    category_codes = {
        "Standard Assets": "STD",
        "Land": "LND", 
        "Buildings and building improvements": "BLD",
        "ICT_EQUIPMENT": "ICT",
        "MOTOR_VEHICLES": "VEH"
    }
    
    category_code = category_codes.get(category, "AST")
    return f"{category_code}-{department_code}-{sequence:05d}"

def get_category_specific_reports_fields(category: str) -> List[Dict[str, str]]:
    """Get fields that should be included in reports for specific categories"""
    report_fields = {
        "Land": [
            {"field": "lr_certificate_no", "label": "L.R. Certificate No."},
            {"field": "size_hectares", "label": "Size (Ha)"},
            {"field": "ownership_status", "label": "Ownership Status"},
            {"field": "county", "label": "County"}
        ],
        "Buildings and building improvements": [
            {"field": "type_of_building", "label": "Building Type"},
            {"field": "no_of_floors", "label": "No. of Floors"},
            {"field": "plinth_area_sq_feet", "label": "Plinth Area (Sq Ft)"},
            {"field": "county", "label": "County"}
        ],
        "Standard Assets": [
            {"field": "make_model", "label": "Make & Model"},
            {"field": "serial_number", "label": "Serial Number"},
            {"field": "asset_condition", "label": "Condition"}
        ]
    }
    
    return report_fields.get(category, [])