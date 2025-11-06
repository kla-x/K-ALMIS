from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime

class LoginRequestSecurity(BaseModel):
    email: EmailStr
    password: str
    fingerprint: str
    remember_me: bool = False
    timezone: Optional[str] = None
    language: Optional[str] = None

class TokenOutSecurity(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    role: Optional[str] = None
    dept_id: Optional[str] = None
    token_type: str
    a_expires: Optional[int] = None
    req_mfa: int = 0
    pass_change: bool = False
    temp_session_token: Optional[str] = None

    class Config:
        from_attributes = True

class MFAVerifyRequest(BaseModel):
    temp_session_token: str
    mfa_code: str

class WhitelistIPRequest(BaseModel):
    mfa_code: str

class DeviceOut(BaseModel):
    id: str
    fingerprint_hash: str
    device_info: Optional[Dict[str, Any]]
    browser: Optional[str]
    os: Optional[str]
    first_seen: datetime
    last_seen: datetime
    is_trusted: bool
    ip_at_registration: Optional[str]

    class Config:
        from_attributes = True

class LoginAttemptOut(BaseModel):
    id: str
    email: str
    ip_address: str
    success: bool
    failure_reason: Optional[str]
    device_info: Optional[Dict[str, Any]]
    browser: Optional[str]
    os: Optional[str]
    timezone: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True

class ForcePasswordChangeRequest(BaseModel):
    temp_session_token: str
    new_password: str = Field(..., min_length=8)

class UnlockAccountRequest(BaseModel):
    token: str