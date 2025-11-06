from pydantic import BaseModel, Field, EmailStr
from typing import Dict, Any, Optional, ClassVar,List,Union
import enum
from datetime import datetime
from ..models import GovLevel, EntityType
from .location import LocationPreview

class LogLevel(str,  enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ActionType(str,  enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    VIEW = "view"
    EXPORT = "export"
    IMPORT = "import"
    INVENTORY_ADD = "inventory_add"
    INVENTORY_REMOVE = "inventory_remove"
    SALE_RECORD = "sale_record"
    PERMISSION_DENIED ="permission_denied"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET_REQUEST = "password_reset_request" 
    PASSWORD_RESET_COMPLETE = "password_reset_complete"
    TWO_FA_SENT = "two_fa_sent"
    TWO_FA_VERIFIED = "two_fa_verified"
    TWO_FA_FAILED = "two_fa_failed"
    NEW_DEVICE_DETECTED = "new_device_detected"
    NEW_IP_DETECTED = "new_ip_detected"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SESSION_HIJACK_DETECTED = "session_hijack_detected"
    FORCED_LOGOUT = "forced_logout"
    WORKING_HOURS_VIOLATION = "working_hours_violation"
    BRUTE_FORCE_DETECTED = "brute_force_detected"
    IP_BANNED = "ip_banned"
    ADMIN_OVERRIDE = "admin_override"
    CONCURRENT_SESSION_WARNING = "concurrent_session_warning"
    DEVICE_TRUSTED = "device_trusted"

class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    deleted = "deleted"
    suspended = "suspended"

class UserStatus2(str, enum.Enum):
    active = "active"
    suspended = "suspended"

class AuthMethod(str, enum.Enum):
    password = "password"
    oauth = "oauth"
    sso = "sso"

 
class RoleOutt(BaseModel):
    # id: str
    name: str
    description: str
    # permissions: dict[str, list[str]]

    class Config:
        from_attributes = True

class RoleOuttid(BaseModel):
    id: str
    name: str
    description: str
    # permissions: dict[str, list[str]]

    class Config:
        from_attributes = True

    

class ChangePassword(BaseModel):
    old_password: str
    old_password2: str
    new_password: str
class PasswordReset(BaseModel):
    token: str
    new_password: str

class PasswordResetRequest(BaseModel):
    email: str
    
class PasswordResetResponse(BaseModel):
    message: str
    success: bool

    
class CreateUser(BaseModel):
    profile_pic: Optional[str] = "http://profile.com/some/pic/here"
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = "25412345678"
    department_id: Optional[str] = None
    # role_id: str
    position_title: Optional[str] = "member"
    gov_level: Optional[GovLevel] = GovLevel.county
    entity_type: Optional[EntityType] = EntityType.department
    entity_name: Optional[str] = None
    location: Optional[LocationPreview] = None
    notes: Optional[str] = None
    password:  str = Field(..., min_length=6, max_length=30)  
    class Config:
        from_attributes = True

class ChangeUserStatus(BaseModel):
    status: UserStatus2 = UserStatus2.suspended

class NoChangesResponse(BaseModel):
    detail: str
class CreateUserAdmin(CreateUser):
    password: ClassVar[None] = None
    role_id: Optional[str] = None
    status: Optional[str] = None

class PatchUserAdmin(CreateUser):
    password: ClassVar[None] = None
    role_id: ClassVar[None] = None
 
class UserOut(CreateUser):  
    password: ClassVar[None] = None  
    role_id: ClassVar[None] = None
    status: Optional[str] = None
    id: str

    created_at : datetime
    updated_at : Optional[datetime] = None
    
class UserOutProfile(UserOut):
    status: str
    role: RoleOuttid
    is_department_head: Optional[bool] = False 
    created_at : datetime

    updated_at : Optional[datetime] = None
    last_login :Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    last_password_change: Optional[datetime] = None
    access_scope: Union [Dict[str, Any],str]


class GivePerms(BaseModel):
    permissions: list[str]


class AdminUpdateUser(BaseModel):
    status: UserStatus
    role_id: str
    email: EmailStr
    is_active: bool = False


class ModifyProfile(BaseModel):
    profile_pic: Optional[str] = None
    # email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None

class UserNameOut(BaseModel):
    username: str


class DeleteUser(BaseModel):
    status: UserStatus
    is_active: bool = False


class UsersWithRoleX(BaseModel):
    id:str
    first_name:str
    entity_name:str
    email: EmailStr



class UserOutWithRole(UserOut):
    status: UserStatus
    role: Optional[RoleOutt] = None

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    a_expires: int

class TokenOutId(TokenOut):
    role:str
    dept_id:str
    
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False
# ---------------------------[ ROLES ]--------------------------
class RoleCreate(BaseModel):
    name: str = Field(..., example="admin")  # type: ignore
    description:str
    permissions: List[str] = Field(
        ...,  # type: ignore
        example={
            "resource.action","resource.action2","resource2.action"
           }
    )

class RoleOut(BaseModel):
    id:str
    description:str
    name: str = Field(..., example="admin")  # type: ignore
    permissions: List[str] = Field(
        ...,  # type: ignore
        example={
            "resource.action","resource.action2","resource2.action"
           }
    )
class RoleUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    permissions: Optional[List[str]]



class CreateDepartment(BaseModel):
    name : Optional[str] = None 
    parent_dept_id : Optional[str] = None 
    entity_type : Optional[EntityType] = EntityType.department 
    description : Optional[str] = None 

class DepartmentDetails(BaseModel):
    dept_id : str    
    name : Optional[str] = None 
    parent_dept_id : Optional[str] = None 
    entity_type : Optional[EntityType] = EntityType.department 
    description : Optional[str] = None 
    status : Optional[UserStatus] = UserStatus.active  

class DepartmentDetailsSimple(BaseModel):
    dept_id : str    
    name : Optional[str] = None 

class DepartmentDetailsPublic(BaseModel):
    dept_id : str
    name : Optional[str] = None
    entity_type : Optional[EntityType] = EntityType.department

class DepartmentStatus(BaseModel):
    status: UserStatus2 = UserStatus2.active
class DepartmentUsers(UsersWithRoleX):
    position_title: Optional[str] = None 