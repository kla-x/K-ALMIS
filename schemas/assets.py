from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime, date
from enum import Enum
from .location import LocationPreview

from ..models import AssetCategory as AssetCategoryEnum
from ..models import AssetStatus as AssetStatusEnum
from ..models  import AssetCondition as AssetConditionEnum
from ..models import TransferStatus as TransferStatusEnum

# Base schemas
class AssetBase(BaseModel):
    name: str
    pic: Optional[str] = None
    other_pics: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    category: AssetCategoryEnum
    tag_number: Optional[str] = None
    serial_number: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    responsible_officer_id: Optional[str] = None
    responsible_officer_name: Optional[str] = None
    location: Optional[LocationPreview] = None
    status: AssetStatusEnum = AssetStatusEnum.OPERATIONAL
    condition: AssetConditionEnum = AssetConditionEnum.GOOD
    acquisition_date: Optional[date] = None
    acquisition_cost: Decimal
    source_of_funds: Optional[str] = None
    depreciation_rate: Optional[Decimal] = None
    useful_life_years: Optional[int] = None
    is_portable_attractive: bool = False
    insurance_details: Optional[Dict[str, Any]] = None
    maintenance_schedule: Optional[Dict[str, Any]] = None
    specific_attributes: Optional[Dict[str, Any]] = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    description: Optional[str] = None
    tag_number: Optional[str] = None
    pic: Optional[str] = None
    other_pics: Optional[Dict[str, Any]] = None
    serial_number: Optional[str] = None
    responsible_officer_id: Optional[str] = None
    responsible_officer_name: Optional[str] = None
    location: Optional[LocationPreview] = None
    condition: Optional[AssetConditionEnum] = None
    acquisition_date: Optional[date] = None
    acquisition_cost: Optional[Decimal] = None
    source_of_funds: Optional[str] = None
    depreciation_rate: Optional[Decimal] = None
    useful_life_years: Optional[int] = None
    is_portable_attractive: Optional[bool] = None
    insurance_details: Optional[Dict[str, Any]] = None
    maintenance_schedule: Optional[Dict[str, Any]] = None
    specific_attributes: Optional[Dict[str, Any]] = None

class AssetStatusUpdate(BaseModel):
    status: AssetStatusEnum
    remarks: Optional[str] = None

class AssetLocationUpdate(BaseModel):
    location: Optional[LocationPreview] = None
    remarks: Optional[str] = None

# Responses
class AssetResponse(AssetBase):
    id: str
    barcode: Optional[str] = None
    qr_code: Optional[str] = None
    current_value: Optional[Decimal] = None
    disposal_date: Optional[date] = None
    disposal_value: Optional[Decimal] = None
    disposal_method: Optional[str] = None
    revaluation_history: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    
    department_name: Optional[str] = None
    responsible_officer_name: Optional[str] = None

    class Config:
        from_attributes = True

class AssetListResponse(BaseModel):
    assets: List[AssetResponse]
    total: int
    page: int
    size: int
    total_pages: int

# Transfer
class AssetTransfereInitiate(BaseModel):
    asset_id: str
    to_user_id: Optional[str] = None
    to_dept_id: Optional[str] = None
    transfer_reason: Optional[str] = None
    remarks: Optional[str] = None

class AssetTransferResponse(BaseModel):
    id: int
    asset_id: str
    from_user_id: Optional[str] = None
    to_user_id: Optional[str] = None
    from_dept_id: Optional[str] = None
    to_dept_id: Optional[str] = None
    initiated_by: str
    initiated_date: datetime
    approved_by: Optional[str] = None
    approval_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    status: TransferStatusEnum
    transfer_reason: Optional[str] = None
    remarks: Optional[str] = None
    
    asset_description: Optional[str] = None
    from_user_name: Optional[str] = None
    to_user_name: Optional[str] = None

    class Config:
        from_attributes = True

class TransferApproval(BaseModel):
    approve: bool
    remarks: Optional[str] = None

# Lifecycle
class AssetLifecycleEventResponse(BaseModel):
    id: int
    asset_id: str
    event_type: str
    event_date: datetime
    performed_by: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    remarks: Optional[str] = None
    performed_by_name: Optional[str] = None

    class Config:
        from_attributes = True

# Search
class AssetSearchParams(BaseModel):
    query: Optional[str] = None
    category: Optional[AssetCategoryEnum] = None
    status: Optional[AssetStatusEnum] = None
    condition: Optional[AssetConditionEnum] = None
    department_id: Optional[str] = None
    responsible_officer_id: Optional[str] = None
    location: Optional[LocationPreview] = None
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    acquisition_date_from: Optional[date] = None
    acquisition_date_to: Optional[date] = None
    page: int = 1
    size: int = 20
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"

class TransSearchParams(BaseModel):
    u_from: Optional[str] = None
    d_from: Optional[str] = None
    u_to: Optional[str] = None
    d_to: Optional[str] = None
    init_by: Optional[str] = None
    f_init_date: Optional[date] = None
    t_init_date: Optional[date] = None
    approv_by: Optional[str] = None
    f_approv_date: Optional[date] = None
    t_approv_date: Optional[date] = None
    status: Optional[str] = None

# QR,bar code
class QRCodeResponse(BaseModel):
    qr_code_data: str
    qr_code_image_url: Optional[str] = None

class BarcodeResponse(BaseModel):
    barcode: str
    barcode_image_url: Optional[str] = None

# Reports
class AssetSummaryReport(BaseModel):
    total_assets: int
    total_value: Decimal
    by_category: Dict[str, Dict[str, Any]]
    by_status: Dict[str, Dict[str, Any]]
    by_condition: Dict[str, Dict[str, Any]]

class DepartmentAssetReport(BaseModel):
    department_id: str
    department_name: str
    total_assets: int
    total_value: Decimal
    assets_by_category: Dict[str, int]
    assets_by_status: Dict[str, int]
    top_assets: List[AssetResponse]

# oth
class CategoryFieldInfo(BaseModel):
    field_name: str
    field_type: str
    required: bool
    description: Optional[str] = None

class CategoryInfo(BaseModel):
    category: str
    description: str
    fields: List[CategoryFieldInfo]
    sample_attributes: Optional[Dict[str, Any]] = None

class AssignAssetUserDep(BaseModel):
    user_id : Optional[str] = None
    dept_id : Optional[str] = None