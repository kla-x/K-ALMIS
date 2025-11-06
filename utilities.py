from .models import User, TokenBase,PasswordResetToken
from fastapi import HTTPException, status, Depends, Request
from typing import Optional
import uuid
from sqlalchemy.orm import Session
import secrets
import random
from jose import jwt,JWTError
import string
from passlib.context import CryptContext
from datetime import datetime,timedelta, timezone
from .database import get_db
from .system_vars import ACCESS_TOKEN_EXPIERY
from fastapi.security import OAuth2PasswordBearer



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/oauth2form")

SECRET_KEY = "jncksndjc34jrnfkj3493n49DNKcjijno5KMLkMkmL9c9JCInoc"
ALGORITHM = "HS256"

def authenticate_user(email: str, password: str,db : Session):
    user = db.query(User).filter(User.email == email).first()
    if not user or not pwd_context.verify(password, user.password_hash):  # type: ignore
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None, db: Session = Depends(get_db)) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc)   + (expires_delta or timedelta(minutes=30))
    jti = str(uuid.uuid4())
    issued_at = datetime.now(timezone.utc)  

    to_encode.update({
        "exp": expire,
        "iat": issued_at,
        "jti": jti,
        "type": "access",
        })

    user = db.query(User).filter(User.id == to_encode["id"]).first()
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    token_entry = TokenBase(
        jti=jti,
        iat=issued_at,
        user_id=data.get("id"),
        exp=expire,
        token=token,
        revoked=False
    )
    db.add(token_entry)
    db.commit()

    return token

def create_refresh_token(data: dict, expires_delta: timedelta | None = None, db: Session = Depends(get_db)) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc)   + (expires_delta or timedelta(minutes=150))
    jti = str(uuid.uuid4())
    issued_at = datetime.now(timezone.utc)  

    to_encode.update({
        "exp": expire,
        "iat": issued_at,
        "jti": jti,
        "type": "refresh"
    })

    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    token_entry = TokenBase(
        jti=jti,
        iat=issued_at,
        user_id=data.get("id"),
        exp=expire,
        token=token,
        revoked=False
    )
    db.add(token_entry)
    db.commit()

  
    return token





def generate_id(len=None):
    """gen any len id, default 36uuid

    Args:
        len (int, optional): lenth of id. Defaults to None.

    Returns:
        str : len passed
    """
    if len is None:
        return str(uuid.uuid4())
    else:

        if len % 2:
            print("cc")

            return f"{secrets.token_hex(len // 2)}{random.choice(string.ascii_letters + string.digits)}"
        return secrets.token_hex(len // 2)

def get_changes(old_obj, new_obj):
    """
    Returns updated object and chenges.
    
    Returns:
        tuple: (updated_old_obj, changes_dict)
        changes_dict is empty if no changes found
    """
    new_data = new_obj.dict(exclude_unset=True)
    changes = {}
    
    for field, new_val in new_data.items():
        old_val = getattr(old_obj, field, None)
        if old_val != new_val:
            changes[field] = {"old": old_val, "new": new_val}
            setattr(old_obj, field, new_val)
    
    return old_obj, changes

def revoke_tokens(request: Request, db: Session) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):

 
        return "not logged in"

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        if not user_id:
     
            return "not logged in"
    except JWTError:
        return "not logged in"

    db.query(TokenBase).filter(TokenBase.user_id == user_id).delete()
    db.commit()
    return "bye"


def revoke_tokens_byid(user_id:str, db:Session):
    db.query(TokenBase).filter(TokenBase.user_id == user_id).delete()
    db.commit()



def check_token(token: str, db: Session) -> bool:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        token_type = payload.get("type")
        if token_type != "access":
            return False
        
       


        token_in_db = db.query(TokenBase).filter_by(jti=jti, revoked=False).first()
        if not token_in_db:

            return False

        if token_in_db.exp < datetime.now(timezone.utc):

            return False

        return True

    except JWTError:
        return False

def get_user_id(token: str, db: Session) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        return user_id
    except JWTError:
        return None

def get_user_email(token: str, db: Session) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        return user_email
    except JWTError:
        return None
    
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    user_id = get_user_id(token, db)
 
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized request")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not foundd")
    
    return user


def generate_reset_token() -> str:
    
    return f"{secrets.token_urlsafe(8)}-{secrets.token_urlsafe(12)}-{secrets.token_urlsafe(12)}-{secrets.token_urlsafe(12)}-{secrets.token_urlsafe(8)}"


def create_password_reset_token(user_email: str, db: Session) -> str:
    db.query(PasswordResetToken).filter(PasswordResetToken.user_email == user_email).delete()
    
    token = generate_reset_token()
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    reset_token = PasswordResetToken(token=token, user_email=user_email, expires_at=expires_at, is_used=False)
    
    db.add(reset_token)
    db.commit()
    
    return token


def validate_reset_token(token: str, db: Session) -> Optional[str]:
    """Validate reset token and return user email if valid"""
    reset_token = db.query(PasswordResetToken).filter(PasswordResetToken.token == token, PasswordResetToken.is_used == False, PasswordResetToken.expires_at > datetime.utcnow()).first()
    
    if reset_token:
        return reset_token.user_email 
    return None


