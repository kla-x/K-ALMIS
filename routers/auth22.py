from fastapi import Depends, HTTPException, status, APIRouter, Query, Request, BackgroundTasks
from ..models import User, DeviceFingerprint, IPWhitelist, LoginAttempt, MFACode,TempDisableLog
from ..utilities import get_current_user, pwd_context, generate_id, create_access_token, create_refresh_token, oauth2_scheme, check_token, revoke_tokens, SECRET_KEY, ALGORITHM, get_user_id, revoke_tokens_byid
from ..schemas.secc import LoginRequestSecurity, TokenOutSecurity, MFAVerifyRequest, WhitelistIPRequest, DeviceOut, LoginAttemptOut, ForcePasswordChangeRequest, UnlockAccountRequest
from ..schemas.main import UserStatus
from sqlalchemy.orm import Session
from ..database import get_db
from datetime import datetime, timedelta, timezone
from ..system_vars import ACCESS_TOKEN_EXPIERY, send_emails, sys_logger
from ..services.emailsender import AssetFlowEmailService
from ..sec_utils import *


from ..system_vars import (
    KNOWN_DEVICE_MAX_ATTEMPTS, UNKNOWN_DEVICE_MAX_ATTEMPTS, TEMP_DISABLE_DURATION_HOURS, 
    FINAL_ATTEMPTS_BEFORE_LOCK, FRAUD_SCORE_LIMIT,
    EXPECTED_TIMEZONE, EXPECTED_LANGUAGE, 
    IP_WHITELIST_THRESHOLD, MFA_CODE_EXPIRY_MINUTES
)
from ..services.logger_queue import enqueue_log
from ..schemas.main import  ActionType, LogLevel
import os
from typing import List
from dotenv import load_dotenv

load_dotenv(dotenv_path="./fapi/.env")

if send_emails:
    email_service = AssetFlowEmailService(api_key=os.getenv("SENDINBLUE_API_KEY", "kk"))

router = APIRouter(tags=['Authentication New'], prefix="/api/v1/auth/2")

def get_client_ip(request: Request) -> str:
    if "x-forwarded-for" in request.headers:
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def extract_device_info(request: Request) -> dict:
    user_agent = request.headers.get("user-agent", "")
    return {
        "user_agent": user_agent,
        "accept_language": request.headers.get("accept-language", ""),
        "accept_encoding": request.headers.get("accept-encoding", "")
    }

@router.post("/login", response_model=TokenOutSecurity, status_code=status.HTTP_200_OK)
async def login(login_req: LoginRequestSecurity, request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    ip_address = get_client_ip(request)
    device_info = extract_device_info(request)
    
    fingerprint_hash = hash_fingerprint(login_req.fingerprint)
    user_timezone = login_req.timezone or "unknown"
    user_language = login_req.language or "unknown"
    
    user = db.query(User).filter(User.email == login_req.email).first()
    
    if not user or not pwd_context.verify(login_req.password, user.password_hash):
        if user:
            login_attempt = LoginAttempt(
                id=generate_id(),
                user_id=user.id,
                email=login_req.email,
                ip_address=ip_address,
                fingerprint_hash=fingerprint_hash,
                success=False,
                failure_reason="Invalid credentials",
                device_info=device_info,
                timezone=user_timezone,
                language=user_language
            )
            db.add(login_attempt)
            
            user.login_attempts += 1
            
            device_known = is_device_known(user.id, fingerprint_hash, db)
            
            if device_known:
                if user.login_attempts >= KNOWN_DEVICE_MAX_ATTEMPTS:
                    if user.status != UserStatus.temp_disabled:
                        temp_disable_account(user, "Too many failed login attempts from known device", db)
                        if send_emails:
                            background_tasks.add_task(email_service.send_account_temp_disabled_email, user.email, user.first_name, TEMP_DISABLE_DURATION_HOURS)
                        if sys_logger:
                            await enqueue_log(user_id=user.id, action=ActionType.ACCOUNT_LOCKED, target_table="users", target_id=user.id, details={"reason": "max_attempts_known_device", "ip": ip_address}, level=LogLevel.WARNING)
                    else:
                        temp_disabled_count = get_failed_attempts_count(user.id, user.temp_disabled_until - timedelta(hours=TEMP_DISABLE_DURATION_HOURS), db) if user.temp_disabled_until else 0
                        if temp_disabled_count >= FINAL_ATTEMPTS_BEFORE_LOCK:
                            deactivate_account(user, "Failed login attempts after temp disable", db)
                            if send_emails:
                                background_tasks.add_task(email_service.send_account_suspended_email, user.email, user.first_name)
                            if sys_logger:
                                await enqueue_log(user_id=user.id, action=ActionType.ACCOUNT_LOCKED, target_table="users", target_id=user.id, details={"reason": "max_attempts_after_temp_disable", "ip": ip_address}, level=LogLevel.CRITICAL)
            else:
                if user.login_attempts >= UNKNOWN_DEVICE_MAX_ATTEMPTS:
                    deactivate_account(user, "Failed login attempts from unknown device", db)
                    if send_emails:
                        background_tasks.add_task(email_service.send_account_suspended_email, user.email, user.first_name)
                    if sys_logger:
                        await enqueue_log(user_id=user.id, action=ActionType.ACCOUNT_LOCKED, target_table="users", target_id=user.id, details={"reason": "max_attempts_unknown_device", "ip": ip_address}, level=LogLevel.CRITICAL)
            
            db.commit()
        
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if is_account_temp_disabled(user):
        hours_remaining = (user.temp_disabled_until - datetime.now(timezone.utc)).total_seconds() / 3600
        raise HTTPException(status_code=403, detail=f"Account temporarily disabled. Try again in {hours_remaining:.1f} hours")
    
    if user.status == UserStatus.temp_disabled and user.temp_disabled_until and datetime.now(timezone.utc) >= user.temp_disabled_until:
        user.status = UserStatus.active
        user.login_attempts = 0
        db.query(TempDisableLog).filter(TempDisableLog.user_id == user.id, TempDisableLog.is_active == True).update({"is_active": False})
        db.commit()
    
    if user.status == UserStatus.deleted:
        raise HTTPException(status_code=401, detail="Account no longer exists, contact support")
    
    if user.status == UserStatus.inactive and user.last_login is None:
        raise HTTPException(status_code=401, detail="Account awaiting activation, contact support")
    
    if user.status == UserStatus.suspended:
        raise HTTPException(status_code=401, detail="Account suspended, contact support")
    
    if user.status != UserStatus.active:
        raise HTTPException(status_code=401, detail="Account not active, contact support")
    
    is_suspicious, ip_det_reason = check_ip_det(ip_address)
    fraud_score = 0
    
    if is_suspicious:
        fraud_score = 100
        login_attempt = LoginAttempt(
            id=generate_id(),
            user_id=user.id,
            email=login_req.email,
            ip_address=ip_address,
            fingerprint_hash=fingerprint_hash,
            success=False,
            failure_reason=f"Suspicious IP detected: {ip_det_reason}",
            device_info=device_info,
            timezone=user_timezone,
            language=user_language,
            ip_details={"suspicious": True, "reason": ip_det_reason},
            fraud_score=fraud_score
        )
        db.add(login_attempt)
        
        temp_disable_account(user, f"Login from suspicious IP: {ip_det_reason}", db)
        
        if send_emails:
            background_tasks.add_task(email_service.send_suspicious_login_blocked_email, user.email, user.first_name, ip_address, ip_det_reason)
        
        if sys_logger:
            await enqueue_log(user_id=user.id, action=ActionType.SUSPICIOUS_ACTIVITY, target_table="users", target_id=user.id, details={"ip": ip_address, "reason": ip_det_reason}, level=LogLevel.CRITICAL)
        
        raise HTTPException(status_code=403, detail="Login blocked due to suspicious activity. Account temporarily disabled.")
    
    device_known = is_device_known(user.id, fingerprint_hash, db)
    ip_whitelisted = is_ip_whitelisted(user.id, ip_address, db)
    
    require_mfa = False
    mfa_reason = ""
    
    if not device_known:
        require_mfa = True
        mfa_reason = "new_device"
        if sys_logger:
            await enqueue_log(user_id=user.id, action=ActionType.NEW_DEVICE_DETECTED, target_table="device_fingerprints", target_id=fingerprint_hash, details={"ip": ip_address, "device_info": device_info}, level=LogLevel.WARNING)
    
    if check_last_login_expiry(user):
        require_mfa = True
        mfa_reason = "last_login_30_days"
    
    if user_timezone != EXPECTED_TIMEZONE and user_timezone != "unknown":
        require_mfa = True
        mfa_reason = "timezone_mismatch"
        
        temp_disable_account(user, f"Login from unexpected timezone: {user_timezone}", db)
        
        unlock_token = create_unlock_account_token(user.id, user.email)
        
        if send_emails:
            background_tasks.add_task(email_service.send_timezone_mismatch_email, user.email, user.first_name, user_timezone, ip_address, device_info, unlock_token)
        
        dept_heads = get_dept_heads(user, db)
        system_notification_handler(["security", "dept_head"], f"User {user.email} attempted login from timezone {user_timezone}")
        
        if sys_logger:
            await enqueue_log(user_id=user.id, action=ActionType.SUSPICIOUS_ACTIVITY, target_table="users", target_id=user.id, details={"ip": ip_address, "timezone": user_timezone, "expected": EXPECTED_TIMEZONE}, level=LogLevel.WARNING)
        
        raise HTTPException(status_code=403, detail="Login blocked due to timezone mismatch. Check your email for unlock instructions.")
    
    if user_language != EXPECTED_LANGUAGE and user_language != "unknown":
        require_mfa = True
        mfa_reason = "language_mismatch"
    
    if not is_within_working_hours():
        require_mfa = True
        mfa_reason = "outside_working_hours"
        
        dept_heads = get_dept_heads(user, db)
        
        if send_emails:
            background_tasks.add_task(email_service.send_out_of_hours_login_notification, user.email, user.first_name, ip_address, device_info)
            for head in dept_heads:
                background_tasks.add_task(email_service.send_out_of_hours_login_notification_admin, head.email, head.first_name, user.email, ip_address, device_info)
        
        system_notification_handler(["me", "dept_head"], f"Out of hours login attempt by {user.email} from {ip_address}")
        
        if sys_logger:
            await enqueue_log(user_id=user.id, action=ActionType.WORKING_HOURS_VIOLATION, target_table="users", target_id=user.id, details={"ip": ip_address, "time": datetime.now(timezone.utc).isoformat()}, level=LogLevel.WARNING)
    
    if fraud_score > FRAUD_SCORE_LIMIT:
        require_mfa = True
        mfa_reason = "high_fraud_score"
    
    password_expired = check_password_expiry(user)
    
    login_attempt = LoginAttempt(
        id=generate_id(),
        user_id=user.id,
        email=login_req.email,
        ip_address=ip_address,
        fingerprint_hash=fingerprint_hash,
        success=True,
        device_info=device_info,
        timezone=user_timezone,
        language=user_language,
        ip_details={"suspicious": is_suspicious, "reason": ip_det_reason},
        fraud_score=fraud_score
    )
    db.add(login_attempt)
    
    user.login_attempts = 0
    
    if not ip_whitelisted:
        successful_logins = count_successful_logins_from_ip(user.id, ip_address, db)
        if successful_logins >= IP_WHITELIST_THRESHOLD:
            whitelist_entry = IPWhitelist(
                id=generate_id(),
                user_id=user.id,
                ip_address=ip_address,
                whitelist_type="auto"
            )
            db.add(whitelist_entry)
            if sys_logger:
                await enqueue_log(user_id=user.id, action=ActionType.CREATE, target_table="ip_whitelist", target_id=whitelist_entry.id, details={"ip": ip_address, "type": "auto"}, level=LogLevel.INFO)
    
    db.commit()
    
    if require_mfa or password_expired:
        temp_session_token = create_temp_session_token(user.id, user.email)
        
        if require_mfa:
            mfa_code = generate_mfa_code()
            mfa_expires = datetime.now(timezone.utc) + timedelta(minutes=MFA_CODE_EXPIRY_MINUTES)
            
            mfa_record = MFACode(
                id=generate_id(),
                user_id=user.id,
                code=mfa_code,
                temp_session_token=temp_session_token,
                expires_at=mfa_expires,
                ip_address=ip_address
            )
            db.add(mfa_record)
            db.commit()
            
            if send_emails:
                background_tasks.add_task(email_service.send_mfa_code_email, user.email, user.first_name, mfa_code, MFA_CODE_EXPIRY_MINUTES)
            
            if sys_logger:
                await enqueue_log(user_id=user.id, action=ActionType.TWO_FA_SENT, target_table="mfa_codes", target_id=mfa_record.id, details={"reason": mfa_reason, "ip": ip_address}, level=LogLevel.INFO)
            
            if not device_known:
                if send_emails:
                    background_tasks.add_task(email_service.send_new_device_login_notification, user.email, user.first_name, ip_address, device_info)
        
        return TokenOutSecurity(
            token_type="temp_session",
            req_mfa=1 if require_mfa else 0,
            pass_change=password_expired,
            temp_session_token=temp_session_token
        )
    
    if user.position_title == 'member':
        rolem = user.position_title
    elif user.role_id == '3fef8a21e7f53606402fcd4f692746':
        rolem = "superadmin"
    elif user.role_id == 'role_006':
        rolem = "admin"
    else:
        rolem = "member"
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIERY)
    access_token = create_access_token(
        data={"sub": user.email, "id": user.id, "role": rolem, "username": user.first_name, "dept_id": user.department_id},
        expires_delta=access_token_expires,
        db=db
    )
    
    if login_req.remember_me:
        refresh_token_expiery = timedelta(days=7)
    else:
        refresh_token_expiery = access_token_expires
    
    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=refresh_token_expiery,
        db=db
    )
    
    if not device_known:
        device = DeviceFingerprint(
            id=generate_id(),
            user_id=user.id,
            fingerprint_hash=fingerprint_hash,
            device_info=device_info,
            ip_at_registration=ip_address,
            is_trusted=True
        )
        db.add(device)
    else:
        db.query(DeviceFingerprint).filter(
            DeviceFingerprint.user_id == user.id,
            DeviceFingerprint.fingerprint_hash == fingerprint_hash
        ).update({"last_seen": datetime.now(timezone.utc)})
    
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    if sys_logger:
        await enqueue_log(user_id=user.id, action=ActionType.LOGIN, target_table="users", target_id=user.id, details={"ip": ip_address, "device": device_info}, level=LogLevel.INFO)
    
    return TokenOutSecurity(
        access_token=access_token,
        refresh_token=refresh_token,
        role=rolem,
        dept_id=user.department_id,
        token_type="bearer",
        a_expires=ACCESS_TOKEN_EXPIERY * 60,
        req_mfa=0,
        pass_change=False
    )

@router.post("/verify-mfa", response_model=TokenOutSecurity, status_code=status.HTTP_200_OK)
async def verify_mfa(mfa_req: MFAVerifyRequest, request: Request, db: Session = Depends(get_db)):
    ip_address = get_client_ip(request)
    
    payload = decode_temp_session_token(mfa_req.temp_session_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    mfa_record = db.query(MFACode).filter(
        MFACode.temp_session_token == mfa_req.temp_session_token,
        MFACode.used == False
    ).first()
    
    if not mfa_record:
        raise HTTPException(status_code=401, detail="Invalid MFA session")
    
    if datetime.now(timezone.utc) > mfa_record.expires_at:
        if sys_logger:
            await enqueue_log(user_id=user.id, action=ActionType.TWO_FA_FAILED, target_table="mfa_codes", target_id=mfa_record.id, details={"reason": "expired", "ip": ip_address}, level=LogLevel.WARNING)
        raise HTTPException(status_code=401, detail="MFA code expired")
    
    if mfa_record.code != mfa_req.mfa_code:
        if sys_logger:
            await enqueue_log(user_id=user.id, action=ActionType.TWO_FA_FAILED, target_table="mfa_codes", target_id=mfa_record.id, details={"reason": "invalid_code", "ip": ip_address}, level=LogLevel.WARNING)
        raise HTTPException(status_code=401, detail="Invalid MFA code")
    
    mfa_record.used = True
    db.commit()
    
    if user.position_title == 'member':
        rolem = user.position_title
    elif user.role_id == '3fef8a21e7f53606402fcd4f692746':
        rolem = "superadmin"
    elif user.role_id == 'role_006':
        rolem = "admin"
    else:
        rolem = "member"
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIERY)
    access_token = create_access_token(
        data={"sub": user.email, "id": user.id, "role": rolem, "username": user.first_name, "dept_id": user.department_id},
        expires_delta=access_token_expires,
        db=db
    )
    
    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires,
        db=db
    )
    
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    if sys_logger:
        await enqueue_log(user_id=user.id, action=ActionType.TWO_FA_VERIFIED, target_table="mfa_codes", target_id=mfa_record.id, details={"ip": ip_address}, level=LogLevel.INFO)
    
    return TokenOutSecurity(
        access_token=access_token,
        refresh_token=refresh_token,
        role=rolem,
        dept_id=user.department_id,
        token_type="bearer",
        a_expires=ACCESS_TOKEN_EXPIERY * 60,
        req_mfa=0,
        pass_change=False
    )

@router.post("/force-password-change", status_code=status.HTTP_200_OK)
async def force_password_change(pass_req: ForcePasswordChangeRequest, request: Request, db: Session = Depends(get_db)):
    ip_address = get_client_ip(request)
    
    payload = decode_temp_session_token(pass_req.temp_session_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    hashed_pass = pwd_context.hash(pass_req.new_password)
    user.password_hash = hashed_pass
    user.last_password_change = datetime.now(timezone.utc)
    user.login_attempts = 0
    
    revoke_tokens_byid(user.id, db)
    
    db.commit()
    
    if sys_logger:
        await enqueue_log(user_id=user.id, action=ActionType.PASSWORD_CHANGE, target_table="users", target_id=user.id, details={"ip": ip_address, "forced": True}, level=LogLevel.INFO)
    
    return {"message": "Password changed successfully. Please login again."}

@router.post("/whitelist-ip", status_code=status.HTTP_200_OK)
async def whitelist_ip(whitelist_req: WhitelistIPRequest, request: Request, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ip_address = get_client_ip(request)
    
    mfa_record = db.query(MFACode).filter(
        MFACode.user_id == current_user.id,
        MFACode.code == whitelist_req.mfa_code,
        MFACode.used == False
    ).order_by(MFACode.created_at.desc()).first()
    
    if not mfa_record:
        raise HTTPException(status_code=401, detail="Invalid MFA code")
    
    if datetime.now(timezone.utc) > mfa_record.expires_at:
        raise HTTPException(status_code=401, detail="MFA code expired")
    
    mfa_record.used = True
    
    existing = db.query(IPWhitelist).filter(
        IPWhitelist.user_id == current_user.id,
        IPWhitelist.ip_address == ip_address
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="IP already whitelisted")
    
    whitelist_entry = IPWhitelist(
        id=generate_id(),
        user_id=current_user.id,
        ip_address=ip_address,
        whitelist_type="manual"
    )
    db.add(whitelist_entry)
    db.commit()
    
    if sys_logger:
        await enqueue_log(user_id=current_user.id, action=ActionType.CREATE, target_table="ip_whitelist", target_id=whitelist_entry.id, details={"ip": ip_address, "type": "manual"}, level=LogLevel.INFO)
    
    return {"message": "IP address whitelisted successfully"}

@router.get("/devices", response_model=List[DeviceOut], status_code=status.HTTP_200_OK)
async def list_devices(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    devices = db.query(DeviceFingerprint).filter(
        DeviceFingerprint.user_id == current_user.id,
        DeviceFingerprint.is_deleted == False
    ).order_by(DeviceFingerprint.last_seen.desc()).all()
    
    return devices

@router.delete("/devices/{fingerprint_hash}", status_code=status.HTTP_200_OK)
async def forget_device(fingerprint_hash: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    device = db.query(DeviceFingerprint).filter(
        DeviceFingerprint.user_id == current_user.id,
        DeviceFingerprint.fingerprint_hash == fingerprint_hash,
        DeviceFingerprint.is_deleted == False
    ).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.is_deleted = True
    db.commit()
    
    if sys_logger:
        await enqueue_log(user_id=current_user.id, action=ActionType.DELETE, target_table="device_fingerprints", target_id=device.id, details={"fingerprint_hash": fingerprint_hash}, level=LogLevel.INFO)
    
    return {"message": "Device forgotten successfully"}

@router.get("/login-history", response_model=List[LoginAttemptOut], status_code=status.HTTP_200_OK)
async def get_login_history(limit: int = Query(20, le=100), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    attempts = db.query(LoginAttempt).filter(
        LoginAttempt.user_id == current_user.id
    ).order_by(LoginAttempt.timestamp.desc()).limit(limit).all()
    
    return attempts

@router.post("/unlock-account", status_code=status.HTTP_200_OK)
async def unlock_account(unlock_req: UnlockAccountRequest, request: Request, db: Session = Depends(get_db)):
    ip_address = get_client_ip(request)
    
    payload = decode_unlock_account_token(unlock_req.token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired unlock token")
    
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.status == UserStatus.temp_disabled:
        user.status = UserStatus.active
        user.temp_disabled_until = None
        user.login_attempts = 0
        
        db.query(TempDisableLog).filter(
            TempDisableLog.user_id == user.id,
            TempDisableLog.is_active == True
        ).update({"is_active": False})
        
        db.commit()
        
        if sys_logger:
            await enqueue_log(user_id=user.id, action=ActionType.ACCOUNT_UNLOCKED, target_table="users", target_id=user.id, details={"ip": ip_address, "method": "unlock_token"}, level=LogLevel.INFO)
        
        return {"message": "Account unlocked successfully. You can now login."}
    
    return {"message": "Account is already active"}