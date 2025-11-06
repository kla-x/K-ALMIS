import os
import hashlib
import secrets
import requests
from typing import Tuple, List, Optional
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models import User, DeviceFingerprint, IPWhitelist, LoginAttempt, TempDisableLog, UserStatus
from .system_vars import (
    FRAUD_SCORE_LIMIT, TEMP_DISABLE_DURATION_HOURS, PASSWORD_EXPIRY_DAYS,
    WORKING_HOURS_START, WORKING_HOURS_END, INACTIVE_ACCOUNT_DAYS,
    MFA_CODE_LENGTH, TEMP_SESSION_TOKEN_EXPIRY_MINUTES, UNLOCK_ACCOUNT_TOKEN_EXPIRY_MINUTES
)
from .utilities import generate_id, SECRET_KEY, ALGORITHM

load_dotenv(dotenv_path="./fapi/.env")
ABUSEDB_KEY = os.getenv("ABUSEDB_KEY")
SECRET_KEY_FP = os.getenv("SECRET_KEY_FP", "default_fp_secret_key_change_me")


def check_ip_det(ip: str) -> Tuple[bool, str]:
    if not ABUSEDB_KEY:
        return True, "missing ABUSEDB_KEY"

    url = "https://api.abuseipdb.com/api/v2/check"
    params = {"ipAddress": ip, "maxAgeInDays": "90"}
    headers = {"Accept": "application/json", "Key": ABUSEDB_KEY}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=6)
        resp.raise_for_status()
        payload = resp.json().get("data", {})
    except Exception as e:
        return True, f"abusedb_error: {e}"

    country = (payload.get("countryCode") or "").upper()
    hostnames = payload.get("hostnames") or []
    usage = (payload.get("usageType") or "").lower()
    isp = (payload.get("isp") or "").lower()
    domain = (payload.get("domain") or "").lower()
    is_tor = payload.get("isTor") is True
    abuse_score = int(payload.get("abuseConfidenceScore") or 0)

    reasons = []
    suspicious = False

    if is_tor or any(k in isp for k in ("vpn", "proxy")) or any(k in domain for k in ("vpn", "proxy", "tor")):
        suspicious = True
        reasons.append("vpn/proxy/tor detected")

    if any(k in usage for k in ("data center", "datacenter", "web hosting", "hosting", "transit")):
        suspicious = True
        reasons.append(f"hosting/datacenter ({usage or 'unknown'})")

    if hostnames:
        suspicious = True
        reasons.append(f"hostnames: {', '.join(hostnames)}")

    if country and country != "KE":
        suspicious = True
        reasons.append(f"foreign country: {country}")

    if abuse_score > FRAUD_SCORE_LIMIT:
        suspicious = True
        reasons.append(f"abuse_score: {abuse_score}")

    summary = f"isp: {isp or payload.get('isp')}, country: {country or 'unknown'}, abuse_score: {abuse_score}, usage: {usage or 'unknown'}"
    return (suspicious, "; ".join(reasons) if reasons else summary)


def hash_fingerprint(fingerprint: str) -> str:
    if not fingerprint:
        return ""
    
    salted = f"{fingerprint}{SECRET_KEY_FP}"
 
    hash_obj = hashlib.sha256(salted.encode('utf-8'))
    
    return hash_obj.hexdigest()


def is_device_known(user_id: str, fingerprint_hash: str, db: Session) -> bool:

    device = db.query(DeviceFingerprint).filter(
        and_(
            DeviceFingerprint.user_id == user_id,
            DeviceFingerprint.fingerprint_hash == fingerprint_hash,
            DeviceFingerprint.is_deleted == False
        )
    ).first()
    
    return device is not None

def is_ip_whitelisted(user_id: str, ip_address: str, db: Session) -> bool:
    whitelist = db.query(IPWhitelist).filter(
        and_(
            IPWhitelist.user_id == user_id,
            IPWhitelist.ip_address == ip_address
        )
    ).first()
    
    return whitelist is not None


def temp_disable_account(user: User, reason: str, db: Session) -> None:
    disabled_until = datetime.now(timezone.utc) + timedelta(hours=TEMP_DISABLE_DURATION_HOURS)
    
    user.status = UserStatus.temp_disabled
    user.temp_disabled_until = disabled_until
    
    log_entry = TempDisableLog(
        id=generate_id(),
        user_id=user.id,
        reason=reason,
        disabled_until=disabled_until,
        is_active=True
    )
    
    db.add(log_entry)
    db.commit()


def deactivate_account(user: User, reason: str, db: Session) -> None:
    user.status = UserStatus.suspended
    user.temp_disabled_until = None

    log_entry = TempDisableLog(
        id=generate_id(),
        user_id=user.id,
        reason=f"SUSPENDED: {reason}",
        disabled_until=datetime.now(timezone.utc) + timedelta(days=36500),
        is_active=True
    )
    
    db.add(log_entry)
    db.commit()


def is_account_temp_disabled(user: User) -> bool:
    if user.status != UserStatus.temp_disabled:
        return False
    
    if not user.temp_disabled_until:
        return False

    if datetime.now(timezone.utc) >= user.temp_disabled_until:
        return False
    
    return True


def get_failed_attempts_count(user_id: str, since_datetime: datetime, db: Session) -> int:
    count = db.query(LoginAttempt).filter(
        and_(
            LoginAttempt.user_id == user_id,
            LoginAttempt.success == False,
            LoginAttempt.timestamp >= since_datetime
        )
    ).count()
    
    return count


def count_successful_logins_from_ip(user_id: str, ip_address: str, db: Session) -> int:
    count = db.query(LoginAttempt).filter(
        and_(
            LoginAttempt.user_id == user_id,
            LoginAttempt.ip_address == ip_address,
            LoginAttempt.success == True
        )
    ).count()
    
    return count


def check_last_login_expiry(user: User) -> bool:
    if not user.last_login:
        return True
    
    days_since_login = (datetime.now(timezone.utc) - user.last_login).days
    
    return days_since_login >= INACTIVE_ACCOUNT_DAYS


def check_password_expiry(user: User) -> bool:
    if not user.last_password_change:
        if not user.created_at:
            return True
        
        days_since_creation = (datetime.now(timezone.utc) - user.created_at).days
        return days_since_creation >= PASSWORD_EXPIRY_DAYS
    
    days_since_change = (datetime.now(timezone.utc) - user.last_password_change).days
    
    return days_since_change >= PASSWORD_EXPIRY_DAYS


def is_within_working_hours() -> bool:
    eat_offset = timedelta(hours=3)
    current_time_eat = datetime.now(timezone.utc) + eat_offset
    
    current_hour = current_time_eat.hour

    return WORKING_HOURS_START <= current_hour < WORKING_HOURS_END


def generate_mfa_code() -> str:
    code = ''.join([str(secrets.randbelow(10)) for _ in range(MFA_CODE_LENGTH)])
    
    return code


def create_temp_session_token(user_id: str, email: str) -> str:

    expire = datetime.now(timezone.utc) + timedelta(minutes=TEMP_SESSION_TOKEN_EXPIRY_MINUTES)
    jti = generate_id()
    issued_at = datetime.now(timezone.utc)
    
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expire,
        "iat": issued_at,
        "jti": jti,
        "type": "temp_sess"
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return token


def decode_temp_session_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "temp_sess":
            return None
        
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            return None
        
        return payload
    
    except JWTError:
        return None


def create_unlock_account_token(user_id: str, user_email: str) -> str:

    expire = datetime.now(timezone.utc) + timedelta(minutes=UNLOCK_ACCOUNT_TOKEN_EXPIRY_MINUTES)
    jti = generate_id()
    issued_at = datetime.now(timezone.utc)
    
    payload = {
        "user_id": user_id,
        "email": user_email,
        "exp": expire,
        "iat": issued_at,
        "jti": jti,
        "type": "u_acc"
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return token


def decode_unlock_account_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "u_acc":
            return None
        
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            return None
        
        return payload
    
    except JWTError:
        return None


def get_dept_heads(user: User, db: Session) -> List[User]:
    from .models import Departments
    
    if not user.department_id:
        return []
    
    department = db.query(Departments).filter(
        Departments.dept_id == user.department_id
    ).first()
    
    if not department:
        return []
    
    heads = []
    if department.department_head_id:
        head = db.query(User).filter(User.id == department.department_head_id).first()
        if head:
            heads.append(head)

    if department.deputy_head_id:
        deputy = db.query(User).filter(User.id == department.deputy_head_id).first()
        if deputy:
            heads.append(deputy)
    
    return heads


def system_notification_handler(to_users: List[str], msg: str) -> None:
    """
    for de fucha.
    
    Args:
        to_users: List user types n roles (e.g., ["security", "dept_head", "me"])# expound for edge
        msg: notifiction message
    """
    # in  messages and email
    # This could send in-app notifications, emails, SMS, etc.
    pass