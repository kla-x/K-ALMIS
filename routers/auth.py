from fastapi import Depends, HTTPException, status, APIRouter, Query, Request, BackgroundTasks
from ..models import User, TokenBase,PasswordResetToken
from ..utilities import get_current_user, pwd_context, generate_id, authenticate_user, create_access_token, create_refresh_token,oauth2_scheme, check_token,revoke_tokens, SECRET_KEY,ALGORITHM, get_user_id,create_password_reset_token, validate_reset_token,revoke_tokens_byid
from ..schemas.main import CreateUser,AuthMethod, UserOut, TokenOut,TokenOutId, LoginRequest,UserOutProfile, UserStatus, ChangePassword,PasswordResetResponse, PasswordResetRequest,PasswordReset
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..database import get_db
from datetime import datetime, timedelta, timezone
from ..system_vars import ACCESS_TOKEN_EXPIERY,default_new_user_status, send_emails,sys_logger,default_role_id
from jose import jwt,JWTError
from ..services.emailsender import AssetFlowEmailService
import os
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional

from dotenv import load_dotenv
load_dotenv(dotenv_path="./fapi/.env")

if send_emails:
    email_service = AssetFlowEmailService(api_key=os.getenv("SENDINBLUE_API_KEY", "kk"))
router = APIRouter(
   
    tags=['Authentication'],
    prefix="/api/v1/auth"
)

@router.post("/register", status_code = status.HTTP_201_CREATED,response_model=UserOut)
def user_register(user: CreateUser ,background_tasks: BackgroundTasks,   db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
 
    hashed_pass = pwd_context.hash(user.password)
    user_id = generate_id()

    new_user = User(
        id=user_id,
        profile_pic=user.profile_pic,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone_number=user.phone_number,
        department_id=user.department_id,
        position_title=user.position_title,
        is_accounting_officer=False,
        password_hash=hashed_pass,  
        role_id=default_role_id,
        status=default_new_user_status,
        created_at=datetime.now(timezone.utc),
        last_login=None,
        gov_level=user.gov_level,
        entity_type=user.entity_type,
        entity_name=user.entity_name,
        location=user.location.dict() if user.location else None,
        access_scope='{}',
        is_two_factor_enabled=False,
        last_password_change=None,
        login_attempts=None,
        last_activity_at=None,
        notes=user.notes,
        auth_method=AuthMethod.password,
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user) 
    except IntegrityError as e:
        db.rollback()
        if "foreign key constraint" in str(e.orig).lower():
            raise HTTPException(status_code=400, detail="Invalid department ID")
        raise HTTPException(status_code=400, detail="Db integrity error")


    if send_emails:
        background_tasks.add_task(
            email_service.send_account_created_email,
            str(new_user.email),
            str(new_user.first_name)
        )
    return new_user

@router.post("/login", response_model=TokenOutId, status_code=status.HTTP_200_OK)
def login(login_req: LoginRequest, db:Session = Depends(get_db)):
    user = authenticate_user(login_req.email, login_req.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.status == "deleted":
        raise HTTPException(status_code=401, detail="Account nolonger Exists, contact support")
    if user.status == "inactive" and user.last_login == None:
        raise HTTPException(status_code=401, detail="Account awaiting activation, contact support")
    if user.status != "active":
        raise HTTPException(status_code=401, detail="Account Deactivated, contact support")
    
    #bad imp - discuss use of speciffic atttribute role
    if user.position_title == 'member':
        rolem = user.position_title
    elif user.role_id == '3fef8a21e7f53606402fcd4f692746':
        rolem = "superadmin"
    elif user.role_id =='role_006':
        rolem = "admin"
    else:
        rolem = "member"

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIERY)


    access_token = create_access_token(
        data={"sub": user.email, "id": user.id, "role": rolem,"username": user.first_name, "dept_id": user.department_id}, 
        expires_delta=access_token_expires, db= db
    )

    if login_req.remember_me:
        refresh_token_expiery = timedelta(days=7)
    else:
        refresh_token_expiery = access_token_expires
    
    refresh_token = create_refresh_token( data={"sub": user.email, "user_id": user.id}, expires_delta=refresh_token_expiery, db= db)






    user.last_login = datetime.now(timezone.utc)  
    db.commit()
    return {"access_token": access_token,"refresh_token": refresh_token,"role": rolem ,"dept_id": user.department_id ,"token_type": "bearer","a_expires" : ACCESS_TOKEN_EXPIERY * 60 }

@router.post("/login/oauth2form", response_model=TokenOut)
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    remember_me: Optional[bool] = Query(default=False),
    db: Session = Depends(get_db)
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.status != "active":
        raise HTTPException(status_code=401, detail="Account Deactivated, contact support")
 
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIERY)
    access_token = create_access_token(
        data={"sub": user.email, "id": user.id},
        expires_delta=access_token_expires,
        db=db
    )

    refresh_token_expiery = timedelta(days=7) if remember_me else access_token_expires

    refresh_token = create_refresh_token(
        data={"sub": user.email, "id": user.id},
        expires_delta=refresh_token_expiery,
        db=db
    )

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "a_expires": ACCESS_TOKEN_EXPIERY * 60
    }


@router.post("/logout")
async def logout(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    if not check_token(token, db):
        return "not logged in"
    return revoke_tokens(request, db)

@router.get("/protected")
async def protected_route_test(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    if not check_token(token, db):
        raise HTTPException(status_code=401, detail="Token invalid or revoked")
    
    return {"msg": "You are authorized"}


@router.post("/refresh")
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        user_id = payload.get("id")
        token_type = payload.get("type")
        
        if token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
       
        token_record = db.query(TokenBase).filter(
            TokenBase.jti == jti,
            TokenBase.revoked == False
        ).first()
        
        if not token_record:
            raise HTTPException(status_code=401, detail="Refresh token not found or revoked")
        
        if token_record.exp < datetime.now(timezone.utc): 
            raise HTTPException(status_code=401, detail="Refresh token expired")
    
        db.query(TokenBase).filter(
            TokenBase.user_id == user_id,
            TokenBase.revoked == False
        ).update({"revoked": True})
        db.commit()     

        original_expiry = token_record.exp
        now = datetime.now(timezone.utc)
        remaining = original_expiry - now
        remaining_seconds = max(60, int(remaining.total_seconds()))
        
        new_access_token = create_access_token(
            data={"sub": payload.get("sub"), "id": user_id},
            expires_delta=timedelta(seconds=remaining_seconds),
            db=db
        )  

        new_refresh_token = create_refresh_token(
            data={"sub": payload.get("sub"), "id": user_id},
            expires_delta=timedelta(seconds=remaining_seconds),
            db=db
        )
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": remaining_seconds
        }
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
@router.post("/change-password", status_code=status.HTTP_200_OK)
async def prifile_change_password(req : ChangePassword, curr_user :User = Depends(get_current_user), db: Session = Depends(get_db)):
   
    if req.old_password != req.old_password2:
        raise  HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, detail="Old Passwords dont match")
   
    user = authenticate_user(curr_user.email,req.old_password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if req.old_password == req.new_password:
         raise HTTPException(status_code=401, detail="Old password and new password cannot be thesame")
    
    password_hash = pwd_context.hash(req.new_password)
    user.password_hash = password_hash
    db.commit()
    db.refresh(user)

    return {"msg": "password updated successfully"}

@router.post("/request-password-reset", response_model=PasswordResetResponse)
async def request_password_reset(reset_request: PasswordResetRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == reset_request.email).first()
    
    if not user:
        return PasswordResetResponse(
            message="If an account with this email exists, a password reset link has been sent.",
            success=True
        )
    
    if user.status == "deleted":
        return PasswordResetResponse(
            message="If an account with this email exists, a password reset link has been sent.",
            success=True
        )
    
    reset_token = create_password_reset_token(user.email, db)

    background_tasks.add_task(
        email_service.send_password_reset_email,
        user.email,
        str(user.first_name),
        reset_token
    )
    
    return PasswordResetResponse(
        message="If an account with this email exists, a password reset link has been sent.",
        success=True
    )

@router.get("/password-reset", response_model=dict)
async def check_password_reset_token(token: str = Query(...), db: Session = Depends(get_db)):

    user_email = validate_reset_token(token, db)
    
    if not user_email:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )
    
    user = db.query(User).filter(User.email == user_email).first()
    
    return {
        "message": "Valid reset token",
        "token": token,
        "user_email": user_email,
        "user_name": user.first_name if user else None,
        "success": True
    }

@router.post("/password-reset", response_model=PasswordResetResponse)
async def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):

    user_email = validate_reset_token(reset_data.token, db)
    
    if not user_email:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )
    

    user = db.query(User).filter(User.email == user_email).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    if len(reset_data.new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters long"
        )
    

    hashed_password = pwd_context.hash(reset_data.new_password)
    
    user.password_hash = hashed_password
    
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == reset_data.token
    ).first()
    
    if reset_token:
        reset_token.is_used = True
    
    revoke_tokens_byid(user.id, db)
    
    db.commit()
    
    return PasswordResetResponse(
        message="Password reset successfully. Please login with your new password.",
        success=True
    )




@router.get("/me", response_model=UserOutProfile, status_code=status.HTTP_200_OK)
def get_my_profile(token: str = Depends(oauth2_scheme),db:Session = Depends(get_db)):

    if not check_token(token, db):
        raise HTTPException(status_code=401, detail="Token invalid or revoked")
    
    user_id = get_user_id(token,db)
    if not user_id:
        raise HTTPException(status_code=401, detail="An Error Has occured")
    
    profile = db.query(User).filter(User.id == user_id).first()
    
    return profile 