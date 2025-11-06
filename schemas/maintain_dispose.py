from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional
from decimal import Decimal

 

class MaintenanceInitiateReq(BaseModel):
    maintenance_type: Optional[str]
    issue_category: Optional[str]
    priority: Optional[str]
    severity: Optional[str]
    description: Optional[str]

class MaintenanceScheduleReq(BaseModel):
    maintenance_type: Optional[str] = None
    issue_category: Optional[str] = None
    priority: Optional[str] = None
    severity: Optional[str] = None
    description: str
    issue_type: str
    maintenance_date: date
    status: Optional[str] = None

class MaintenanceApproveReq(BaseModel):
    approved: bool = True  


class MaintenanceStartReq(BaseModel):
    notes: Optional[str] = None




class MaintenanceResp(BaseModel):
    id: str
    asset_id: str
    maintenance_type: Optional[str]
    issue_category: Optional[str]
    priority: Optional[str]
    severity: Optional[str]
    description: Optional[str]
    status: str
    request_date: datetime
    maintenance_date: Optional[date]
    resolved_date: Optional[datetime]
    assigned_to: Optional[str]
    notes: Optional[str]

    class Config:
        orm_mode = True


class MaintenanceHistResp(MaintenanceResp):
    requested_by: Optional[str]
    approved_by: Optional[str]

class MaintenanceCompleteReq(BaseModel):
    cost: Optional[float] = None
    outcome: Optional[str] = None
    notes: Optional[str] = None


class MaintenanceCompleteResp(BaseModel):
    id: str
    asset_id: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration: Optional[str]
    cost: Optional[float]
    paid_by: Optional[str]
    outcome: Optional[str]
    notes: Optional[str]

    class Config:
        orm_mode = True

    
#-------------------

class DisposalInitiateReq(BaseModel):
    reason: str
    
class DisposalScheduleReq(BaseModel):
    disposal_date: date
    disposal_method: Optional[str] = None
    
class DisposalApproveReq(BaseModel):
    pass
    
class DisposalExecuteReq(BaseModel):
    proceeds_amount: Optional[Decimal] = None
    disposal_cost: Optional[Decimal] = None
    disposal_method: Optional[str] = None
    remarks: Optional[str] = None
    
class DisposalUndoReq(BaseModel):
    justification: str
    
class DisposalResp(BaseModel):
    msg: str
    
class DisposalHistResp(BaseModel):
    id: str
    asset_id: str
    disposal_method: Optional[str]
    disposal_date: Optional[date]
    approved_by: Optional[str]
    proceeds_amount: Optional[Decimal]
    disposal_cost: Optional[Decimal]
    remarks: Optional[str]
    status: str
    
    class Config:
        from_attributes = True

