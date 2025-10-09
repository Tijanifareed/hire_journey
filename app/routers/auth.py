from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from app import database
from app.schema.schemas import ChangePasswordRequest, ForgotPasswordRequest, RefreshRequest, TimeZoneRequest, TokenResponse
from app.enums.timezones import TimezoneEnum
from app.utils.utils import create_refresh_token, get_current_user, refresh_token, send_mail
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, database
from app.schema.schemas import ForgotPasswordRequest, ResetPasswordRequest, UserCreate, UserLogin
from passlib.hash import bcrypt
from app.utils.utils import create_access_token, genarate_reset_token, get_current_user, send_mail
import logging

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        


@router.post("/create-account")
def create_account(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        return JSONResponse(
        status_code=400,
        content={"status": "error", "message": "Email already registered"}
    )
    hashed_password = bcrypt.hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    user_plan = models.UserPlan(user_id=db_user.id, plan="free")
    db.add(user_plan)
    db.commit()
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Account created successfully",
            "data":{
                "user_id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "timezone": db_user.timezone,
            }
        }
    )
    
    
@router.post("/login")
def login_app(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not bcrypt.verify(user.password, db_user.password_hash):
          return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Invalid Credentials"}
            )
    data={"sub": str(db_user.id)}      
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    return JSONResponse(
        status_code=200,
        content={
        "status": "success",
        "message": "Login Successfull",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "data":{
            
            "user_id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "timezone": db_user.timezone,
            "profile_picture": db_user.profile_picture
        }
        }
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(body: RefreshRequest):
    return refresh_token(body.refresh_token)


@router.get("/me")
def return_me(current_user: models.User = Depends(get_current_user)):
    return JSONResponse(
        status_code=200,
        content={
            "message": f"Hello, {current_user.username}. You are authenticated!",
            "data": current_user
        }
        )


reset_code_cache = {}
@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == request.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Email not Registered")
    code = genarate_reset_token()
    reset_entry = models.PasswordReset(
        user_id=db_user.id,
        code=code,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(reset_entry)
    db.commit()
    send_mail(
        "Password Reset Code",
        f"Your password reset code is: {code}",
        request.email,
        html=False
    )
    return {
        "message": "Reset code sent to your email",
        "code": code  # For testing purposes only; remove in production
        }
    

@router.post("/verify-reset-code")
def verify_reset_code(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == request.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Email not Registered")
    reset_entry = db.query(models.PasswordReset).filter(
        models.PasswordReset.user_id == db_user.id,
        models.PasswordReset.code == request.token,
        models.PasswordReset.expires_at > datetime.utcnow()
    ).first()
    if not reset_entry:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")
    # Delete The reset code after successful verification
    db.delete(reset_entry)
    db.commit()
    return {"message": "Reset code verified successfully. You can now reset your password."}


@router.post("/reset-password")
def reset_password(request: ChangePasswordRequest, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == request.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Email not Registered")
    hashed_password = bcrypt.hash(request.new_password)
    db_user.password_hash = hashed_password
    db.commit()
    db.query(models.PasswordReset).filter(
        models.PasswordReset.user_id == db_user.id
    ).delete()
    db.commit()
    return {"message": "Password reset successfully"}


@router.post("/add-timezone")
def add_timezone(timezone_request: TimeZoneRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        tz_value = TimezoneEnum[timezone_request.timezone].value
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid timezone provided")
    
    # Re-fetch user from DB to ensure it's attached to the session
    db_user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.timezone = tz_value
    db.commit()
    db.refresh(db_user)
   
    return {
        "message": "Timezone added successfully",
        "timezone": db_user.timezone
    }
    

# def cleanup_expired_reset_codes(db: Session):
#     db.query(models.PasswordReset).filter(
#         models.PasswordReset.expires_at < datetime.utcnow()
#     ).delete()
#     db.commit()        




def cleanup_expired_reset_codes(db: Session):
    try:
        deleted = db.query(models.PasswordReset).filter(
            models.PasswordReset.expires_at < datetime.utcnow()
        ).delete(synchronize_session=False)
        db.commit()
        logging.info(f"✅ Cleanup ran: deleted {deleted} expired reset codes")
    except Exception as e:
        db.rollback()
        logging.error(f"❌ Cleanup failed: {e}")

