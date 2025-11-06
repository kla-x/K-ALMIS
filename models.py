from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Text, JSON, ForeignKey, Enum as SQLEnum, DECIMAL, Index, MetaData, Numeric, Interval
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship,Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base
import uuid
import enum
from sqlalchemy.dialects.postgresql import UUID,JSONB
from sqlalchemy.ext.hybrid import hybrid_property

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    
    token = Column(String(150), primary_key=True, index=True)
    user_email = Column(String(50), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
  
class TokenBase(Base):
    __tablename__ = 'usertokens'

    jti = Column(String(40), primary_key=True, index=True)
    iat = Column(DateTime(timezone=True), nullable=False)
    user_id = Column(String(60), ForeignKey('users.id'))
    exp = Column(DateTime(timezone=True), nullable=False)
    token = Column(String(500), nullable=False)
    revoked = Column(Boolean)
    
    user = relationship("User", back_populates="tokens")

class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    deleted = "deleted"
    suspended = "suspended"
    temp_disabled = "temp_disabled"

class GovLevel(str, enum.Enum):
    county = "county"
    national = "national"

class EntityType(str, enum.Enum):
    ministry = "ministry"
    department = "department"
    agency = "agency"
    county_assembly = "county_assembly"
    commission = "commission"
    SAGA = "SAGA"
    state_corporation = "state_corporation"
    county = "county"

class AuthMethod(str, enum.Enum):
    password = "password"
    oauth = "oauth"
    sso = "sso"

class Role(Base):
    __tablename__ = "roles"

    id = Column(String(60), primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True) # "admin", "auditor" c o staff,,
    description = Column(String(255))  
    permissions = Column(JSON, nullable=True)          
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="role")

class DeviceFingerprint(Base):
    __tablename__ = "device_fingerprints"
    
    id = Column(String(60), primary_key=True, index=True)
    user_id = Column(String(60), ForeignKey('users.id'), nullable=False)
    fingerprint_hash = Column(String(255), nullable=False, index=True)
    device_info = Column(JSON, nullable=True)
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    ip_at_registration = Column(String(45), nullable=True)
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    is_deleted = Column(Boolean, default=False, nullable=False)
    is_trusted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="device_fingerprints")

class IPWhitelist(Base):
    __tablename__ = "ip_whitelist"
    
    id = Column(String(60), primary_key=True, index=True)
    user_id = Column(String(60), ForeignKey('users.id'), nullable=False)
    ip_address = Column(String(45), nullable=False, index=True)
    whitelist_type = Column(String(20), nullable=False)
    whitelisted_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="ip_whitelists")

class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    
    id = Column(String(60), primary_key=True, index=True)
    user_id = Column(String(60), ForeignKey('users.id'), nullable=True)
    email = Column(String(120), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    fingerprint_hash = Column(String(255), nullable=True)
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(255), nullable=True)
    location = Column(JSON, nullable=True)
    device_info = Column(JSON, nullable=True)
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)
    language = Column(String(10), nullable=True)
    ip_details = Column(JSON, nullable=True)
    fraud_score = Column(Integer, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    user = relationship("User", back_populates="login_attempts")

class MFACode(Base):
    __tablename__ = "mfa_codes"
    
    id = Column(String(60), primary_key=True, index=True)
    user_id = Column(String(60), ForeignKey('users.id'), nullable=False)
    code = Column(String(10), nullable=False)
    temp_session_token = Column(String(500), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="mfa_codes")

class TempDisableLog(Base):
    __tablename__ = "temp_disable_logs"
    
    id = Column(String(60), primary_key=True, index=True)
    user_id = Column(String(60), ForeignKey('users.id'), nullable=False)
    reason = Column(String(255), nullable=False)
    disabled_at = Column(DateTime(timezone=True), server_default=func.now())
    disabled_until = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="temp_disable_logs")



class User(Base):
    __tablename__ = "users"

    id = Column(String(60), primary_key=True, index=True)
    profile_pic=  Column(String(200), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), unique=True, index=True)
    department_id = Column(String(60), ForeignKey('departments.dept_id'), nullable=False)
    
    position_title = Column(String(255), default="member", nullable=False)
    is_accounting_officer = Column(Boolean, default=False, nullable=False)
    password_hash = Column(String, nullable=False)
    role_id = Column(String(50), ForeignKey('roles.id'),nullable=True)
    
    status = Column(SQLEnum(UserStatus), default=UserStatus.inactive, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    
    gov_level = Column(SQLEnum(GovLevel), default=GovLevel.county, nullable=False)
    entity_type = Column(SQLEnum(EntityType), default=EntityType.department, nullable=False)
    entity_name = Column(String(80), nullable=False)
    location = Column(JSON, nullable=True)
    assigned_perms = Column(JSON)
    access_scope = Column(JSON)
    is_two_factor_enabled = Column(Boolean, default=False)
    last_password_change = Column(DateTime(timezone=True))
    login_attempts = Column(Integer, default=0, nullable=False)
    last_activity_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    auth_method = Column(SQLEnum(AuthMethod), default=AuthMethod.password, nullable=False)

    timezone = Column(String(50), default="EAT", nullable=False)
    temp_disabled_until = Column(DateTime(timezone=True), nullable=True)
    
    @hybrid_property
    def is_department_head(self):
        return bool(self.departments_headed or self.departments_deputy)

    @hybrid_property
    def headed_departments(self):
        return list(self.departments_headed + self.departments_deputy)

    @hybrid_property
    def full_name(self):
        return str(self.first_name +' '+ self.last_name)

    tokens = relationship("TokenBase", back_populates="user", cascade="all, delete-orphan")
    department = relationship("Departments", back_populates="users",foreign_keys=[department_id])
    role = relationship("Role", back_populates="user", uselist=False)
    activitylogs = relationship("ActivityLog",back_populates="user")
    assets_responsible_for = relationship("Assets", foreign_keys="Assets.responsible_officer_id", back_populates="responsible_officer")
    assets_checked = relationship("Assets", foreign_keys="Assets.checked_by", back_populates="checked_by_user")
    assets_authorized = relationship("Assets", foreign_keys="Assets.authorized_by", back_populates="authorized_by_user")
    assets_created = relationship("Assets", foreign_keys="Assets.created_by", back_populates="created_by_user")

    departments_headed = relationship("Departments", foreign_keys="Departments.department_head_id", back_populates="department_head")
    departments_deputy = relationship("Departments", foreign_keys="Departments.deputy_head_id", back_populates="deputy_head")

    device_fingerprints = relationship("DeviceFingerprint", back_populates="user", cascade="all, delete-orphan")
    ip_whitelists = relationship("IPWhitelist", back_populates="user", cascade="all, delete-orphan")
    login_attempts = relationship("LoginAttempt", back_populates="user", cascade="all, delete-orphan")
    mfa_codes = relationship("MFACode", back_populates="user", cascade="all, delete-orphan")
    temp_disable_logs = relationship("TempDisableLog", back_populates="user", cascade="all, delete-orphan")

class Departments(Base):
    __tablename__ = "departments"

    dept_id = Column(String(60), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    parent_dept_id = Column(String(60), ForeignKey('departments.dept_id'), nullable=True)
    entity_type = Column(SQLEnum(EntityType), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(UserStatus), default=UserStatus.active,nullable=False)

    department_head_id = Column(String(60), ForeignKey('users.id'), nullable=True)
    deputy_head_id = Column(String(60), ForeignKey('users.id'), nullable=True)  # toa..
    county_code = Column(String(10), nullable=True)

    
    department_head = relationship("User", foreign_keys=[department_head_id], back_populates="departments_headed")
    deputy_head = relationship("User", foreign_keys=[deputy_head_id], back_populates="departments_deputy")

    parent = relationship("Departments", remote_side=[dept_id], backref="sub_departments")
    users = relationship("User", back_populates="department",foreign_keys="User.department_id")
    assets = relationship("Assets", back_populates="department")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(50), ForeignKey('users.id'), nullable=True)  
    action  = Column(String, nullable=True) 
    target_table = Column(String, nullable=True) 
    target_id = Column(String, nullable=True) 
    logg_level =Column(String, nullable=True) 
    details =  Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="activitylogs")

class PolicyEffect(str, enum.Enum):
    ALLOW = "allow"
    DENY = "deny"

class ABACPolicy(Base):
    __tablename__ = "abac_policies"
    
    id = Column(Integer, primary_key=True)
    description = Column(Text, nullable=False)
    effect = Column(SQLEnum(PolicyEffect), nullable=False, default=PolicyEffect.ALLOW)
    
    user_attributes = Column(JSON, nullable=False) # e.g., {"position_title": "Accounting Officer"}
    action_names = Column(JSONB, nullable=False) # e.g., ["asset.approve_disposal", "asset.write_off"]
    resource_attributes = Column(JSON, nullable=False) # e.g., {"category": "ICT_EQUIPMENT", "status": "Operational"}
    
    priority = Column(Integer, default=0, nullable=False) # not sure if needed
    is_active = Column(Boolean, default=True, nullable=False)

class AssetCategory(str, enum.Enum):
    STANDARD_ASSETS = "Standard Assets"
    LAND = "Land"
    BUILDINGS = "Buildings and building improvements"
    ROAD_INFRASTRUCTURE = "Road infrastructure"
    RAILWAY_INFRASTRUCTURE = "Railway infrastructure"
    OTHER_INFRASTRUCTURE = "Other Infrastructure"
    MOTOR_VEHICLES = "Motor vehicles, other transport Equipment"
    ICT_EQUIPMENT = "Computers and other ICT equipment"
    FURNITURE_FITTINGS = "Furniture, fittings & equipment"
    INVESTMENT_PROPERTY = "Investment property"
    LEASED_ASSETS = "Leased Assets"
    HERITAGE_ASSETS = "Heritage assets"
    WORK_IN_PROGRESS = "Work in Progress"
    INTANGIBLE_ASSETS = "Intangible assets"
    BIOLOGICAL_ASSETS = "Biological assets"
    SUBSOIL_ASSETS = "Subsoil assets"
    PLANT_MACHINERY = "Plant and Machinery"
    PORTABLE_ATTRACTIVE = "Portable and attractive items"


class AssetStatus(str, enum.Enum):
    OPERATIONAL = "Operational"
    UNDER_MAINTENANCE = "Under Maintenance"
    IMPAIRED = "Impaired"
    DISPOSED = "Disposed"
    HELD_FOR_SALE = "Held for Sale"
    RETIRED = "Retired"
    LOST_STOLEN = "Lost/Stolen"
    WORK_IN_PROGRESS = "Work in Progress"
    

class AssetCondition(str, enum.Enum):
    NEW = "new"
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

class TransferStatus(str, enum.Enum):
    INITIATED = "initiated"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PENDING = "pending"

class MaintenanceStatus(str, enum.Enum):
    INITIATED = "initiated"
    SCHEDULED = "scheduled" 
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class DisposalStatus(str, enum.Enum):
    INITIATED = "initiated"
    SCHEDULED = "scheduled"
    APPROVED = "approved" 
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    UNDONE = "undone"

class Assets(Base):
    __tablename__ = "assets"

    id = Column(String(60), primary_key=True, index=True)
    pic =  Column(String(200), nullable=True)
    other_pics = Column(JSON,nullable=True,default='{}')
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(SQLEnum(AssetCategory), nullable=False, index=True)
    tag_number = Column(String(100), unique=True, index=True)
    serial_number = Column(String(100), index=True)
    barcode = Column(String(100), unique=True, index=True, nullable=True)
    qr_code = Column(String(500), nullable=True)
    department_id = Column(String(60), ForeignKey('departments.dept_id'), nullable=True)
    responsible_officer_id = Column(String(60), ForeignKey('users.id'), nullable=True)
    location = Column(JSON,nullable = True)
    
    status = Column(SQLEnum(AssetStatus), default=AssetStatus.OPERATIONAL, nullable=False, index=True)
    condition = Column(SQLEnum(AssetCondition), default=AssetCondition.GOOD)

    #  finance info
    acquisition_date = Column(Date)
    acquisition_cost = Column(DECIMAL(18, 2), nullable=False)
    source_of_funds = Column(String(100))
    current_value = Column(DECIMAL(18, 2))# smthin called Net Book Value
    depreciation_rate = Column(DECIMAL(5, 2))
    useful_life_years = Column(Integer)
    
    # Dispose
    disposal_date = Column(Date)
    disposal_value = Column(DECIMAL(18, 2))
    disposal_method = Column(String(100))

    # Additional Information
    is_portable_attractive = Column(Boolean, default=False)
    insurance_details = Column(JSON)  # {"provider": "X", "policy_no": "Y", "expiry": "date"}
    maintenance_schedule = Column(JSON)
    revaluation_history = Column(JSON)
    specific_attributes = Column(JSON) 
    
    # audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(60), ForeignKey('users.id'))
    is_deleted = Column(Boolean, default=False)
    checked_by = Column(String(60), ForeignKey('users.id'), nullable=True)
    authorized_by = Column(String(60), ForeignKey('users.id'), nullable=True)

    department = relationship("Departments", back_populates="assets")
    responsible_officer = relationship("User", foreign_keys=[responsible_officer_id], back_populates="assets_responsible_for")
    created_by_user = relationship("User", foreign_keys=[created_by],back_populates="assets_created")
    lifecycle_events = relationship("AssetLifecycleEvents", back_populates="asset")
    transfers = relationship("AssetTransfers", back_populates="asset")
    maintenance_requests = relationship("MaintenanceRequests", back_populates="asset")
    disposals = relationship("AssetDisposals", back_populates="asset")
    checked_by_user = relationship("User", foreign_keys=[checked_by], back_populates="assets_checked")
    authorized_by_user = relationship("User", foreign_keys=[authorized_by], back_populates="assets_authorized")

class AssetLifecycleEvents(Base): #logging 2, work alongside the other
    __tablename__ = "asset_lifecycle_events"

    id = Column(String(60), primary_key=True, index=True)
    asset_id = Column(String(60), ForeignKey("assets.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # like created, activated, transferred
    event_date = Column(DateTime, default=func.now())
    performed_by = Column(String(60), ForeignKey("users.id"))
    details = Column(JSON) 
    remarks = Column(Text)

    asset = relationship("Assets", back_populates="lifecycle_events")
    performed_by_user = relationship("User")

class AssetTransfers(Base):
    __tablename__ = "asset_transfers"

    id = Column(String(60), primary_key=True, index=True)
    asset_id = Column(String(60), ForeignKey("assets.id"), nullable=False)
    
    #details
    from_user_id = Column(String(60), ForeignKey("users.id"))
    to_user_id = Column(String(60), ForeignKey("users.id"))
    from_dept_id = Column(String(60), ForeignKey("departments.dept_id"))
    to_dept_id = Column(String(60), ForeignKey("departments.dept_id"))
    
    initiated_by = Column(String(60), ForeignKey("users.id"))
    initiated_date = Column(DateTime, default=func.now())
    approved_by = Column(String(60), ForeignKey("users.id"))
    approval_date = Column(DateTime)
    completed_date = Column(DateTime)
    
    status = Column(SQLEnum(TransferStatus), default=TransferStatus.INITIATED)
    transfer_reason = Column(Text)
    remarks = Column(Text)
 
    asset = relationship("Assets", back_populates="transfers")
    from_user = relationship("User", foreign_keys=[from_user_id])
    to_user = relationship("User", foreign_keys=[to_user_id])
    initiated_by_user = relationship("User", foreign_keys=[initiated_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])


# Add these Enums near your other enums
class MaintenanceType(str, enum.Enum):
    CORRECTIVE = "corrective" 
    PREVENTIVE = "preventive" 
    MAJOR = "major" 
    MANUFACTURER = "manufacturer" 
    REFURBISHMENT = "refurbishment"
    ENHANCEMENT = "enhancement"
    DEFERRED = "deferred"

class IssueCategory(str, enum.Enum):
    MECHANICAL_FAILURE = "mechanical_failure"
    MECHANICAL_ISSUE = "mechanical_issue"
    ELECTRICAL = "electrical"
    SOFTWARE = "software"
    PHYSICAL_DAMAGE = "physical_damage"
    THEFT_LOSS = "theft_loss"
    OBSOLESCENCE = "obsolescence"
    FIRE_NATURAL = "fire_or_natural_disaster"
    COMPLIANCE = "compliance"
    OTHER = "other"

class PriorityLevel(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class SeverityLevel(str, enum.Enum):
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"
class MaintenanceOutcome(str, enum.Enum):
    FIXED = "fixed"
    NOT_FIXED = "not_fixed"

class MaintenanceRequests(Base):
    __tablename__ = "maintenance_requests"

    id = Column(String(60), primary_key=True, index=True)
    asset_id = Column(String(60), ForeignKey("assets.id"), nullable=False)
    requested_by = Column(String(60), ForeignKey("users.id"))
    request_date = Column(DateTime, default=func.now())
    issue_type = Column(String(50))
    description = Column(Text)
    status =  Column(SQLEnum(MaintenanceStatus), default=MaintenanceStatus.INITIATED, nullable=True, index=True)
    assigned_to = Column(String(60), ForeignKey("users.id"))
    resolved_date = Column(DateTime)
    maintenance_date = Column(DateTime)
    notes = Column(Text)

    maintenance_type = Column(SQLEnum(MaintenanceType), nullable=False, default=MaintenanceType.CORRECTIVE, index=True)
    issue_category = Column(SQLEnum(IssueCategory), nullable=False, index=True)
    priority = Column(SQLEnum(PriorityLevel), default=PriorityLevel.MEDIUM, nullable=False, index=True)
    severity = Column(SQLEnum(SeverityLevel), default=SeverityLevel.MINOR, nullable=True)

    cost = Column(Numeric(12, 2), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Interval, nullable=True)

    outcome = Column(SQLEnum(MaintenanceOutcome),default=MaintenanceOutcome.FIXED, nullable=True)

    asset = relationship("Assets", back_populates="maintenance_requests")
    requester = relationship("User", foreign_keys=[requested_by])
    assignee = relationship("User", foreign_keys=[assigned_to])

class AssetDisposals(Base):# define further, saw donations etc for dispose
    __tablename__ = "asset_disposals"

    id = Column(String(60), primary_key=True, index=True)
    asset_id = Column(String(60), ForeignKey("assets.id"), nullable=False)
    status =  Column(SQLEnum(DisposalStatus), default=DisposalStatus.INITIATED, nullable=True, index=True)
    disposal_method = Column(String(100))
    disposal_date = Column(Date)
    approved_by = Column(String(60), ForeignKey("users.id"))
    proceeds_amount = Column(DECIMAL(18, 2))
    disposal_cost = Column(DECIMAL(18, 2))
    remarks = Column(Text)

    asset = relationship("Assets", back_populates="disposals")
    approver = relationship("User")

class AssetRevaluations(Base):
    __tablename__ = "asset_revaluations"

    id = Column(String(60), primary_key=True, index=True)
    asset_id = Column(String(60), ForeignKey("assets.id"), nullable=False)
    revaluation_date = Column(Date)
    previous_value = Column(DECIMAL(18, 2))
    new_value = Column(DECIMAL(18, 2))
    revaluation_method = Column(String(100))
    performed_by = Column(String(60), ForeignKey("users.id"))
    next_revaluation_date = Column(Date)
    remarks = Column(Text)

    asset = relationship("Assets")
    revaluator = relationship("User")
