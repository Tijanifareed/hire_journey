from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import random
import smtplib
from fastapi import Depends, HTTPException,  status
from email import encoders
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
import cloudinary
import cloudinary.uploader
from sqlalchemy.orm import Session


from app import database, models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/applications/login-app")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY")
REFRESH_TOKEN_EXPIRE_DAYS = 7

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#      try:
#           payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#           email: str = payload.get("sub")
#           user = db.query(models.User).filter(models.User.email == email).first()
#           if not user:
#                raise HTTPException(status_code=401, detail="Invalid credentials")
#           return user
     
#      except JWTError:
#          raise HTTPException(
#               status_code=status.HTTP_401_UNAUTHORIZED, 
#               detail="Could not validate credentials",
#            )   
         
    


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("sub")

        if id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = db.query(models.User).filter(models.User.id == int(id)).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    


def create_access_token(data: dict, expires_delta: timedelta = None):
     to_encode = data.copy()
     expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
     to_encode.update({"exp": expire})
     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)


def refresh_token(refresh_token:  str):
    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # optionally check if refresh token is in DB and valid
        data = {"sub": user_id}
        access_token = create_access_token(data)
        new_refresh_token = create_refresh_token(data)

        return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


def genarate_reset_token():
     return str(random.randint(100000, 999999))


def send_mail(subject, body, to_email, attachments=None, html=False):
    recipients = [to_email] if isinstance(to_email, str) else to_email

    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    from_addr = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_addr, password)

            for email in recipients:
                msg = MIMEMultipart("mixed")
                msg["Subject"] = subject
                msg["From"] = from_addr
                msg["To"] = email

                # Always create an alternative section
                alt = MIMEMultipart("alternative")
                msg.attach(alt)

                # Add body
                if html:
                    alt.attach(MIMEText("This email contains HTML. Please view in an HTML-capable client.", "plain"))
                    alt.attach(MIMEText(body, "html"))
                else:
                    alt.attach(MIMEText(body, "plain"))

                # Handle attachments
                if attachments:
                    for attachment in attachments:
                        if isinstance(attachment, str):
                            with open(attachment, "rb") as f:
                                part = MIMEBase("application", "octet-stream")
                                part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(attachment)}"')
                            msg.attach(part)

                        elif isinstance(attachment, tuple):
                            filename, file_bytes, mime_type = attachment
                            if mime_type.startswith("text/calendar"):
                                # ICS should be inside the alternative part
                                ics_part = MIMEText(file_bytes.decode("utf-8"), "calendar", "utf-8")
                                ics_part.add_header("Content-Type", "text/calendar; method=REQUEST; charset=UTF-8")
                                ics_part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
                                ics_part.add_header("Content-Class", "urn:content-classes:calendarmessage")
                                alt.attach(ics_part)
                            else:
                                maintype, subtype = mime_type.split("/", 1)
                                part = MIMEBase(maintype, subtype)
                                part.set_payload(file_bytes)
                                encoders.encode_base64(part)
                                part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
                                msg.attach(part)
                        else:
                            raise ValueError(f"Unsupported attachment type: {type(attachment)}")

                server.sendmail(from_addr, email, msg.as_string())

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")



def backill_user_plans():
    from app.models import User, UserPlan
    db = database.SessionLocal()
    
    users = db.query(User).all()
    for user in users:
        existing = db.query(UserPlan).filter_by(user_id=user.id).first()
        if not existing:
            new_plan = UserPlan(user_id=user.id, plan="free")
            db.add(new_plan)
    db.commit()
    print("✅ Backfilled user_plans for all existing users")
        



# def check_feature_access(db: Session, user_id: int, feature_name: str) -> bool:
#     """Check if a user can use a feature, update usage if allowed."""

#     now = datetime.utcnow()

#     # 1. Get the user's plan
#     plan = db.query(models.UserPlan).filter(models.UserPlan.user_id == user_id).first()
#     if not plan:
#         # create default free plan if missing
#         plan = models.UserPlan(user_id=user_id, plan="free")
#         db.add(plan)
#         db.commit()
#         return check_feature_access(db, user_id, feature_name)

#     # 2. Handle Pro Users
#     if plan.plan == "pro":
#         # if expired + 5 day grace period → downgrade to free
#         if plan.plan_expires_at and now > plan.plan_expires_at + timedelta(days=5):
#             plan.plan = "free"
#             plan.plan_expires_at = None
#             db.commit()
#             # fall through to free logic 👇
#         else:
#             return True  # still valid pro, unlimited ✅

#     # 3. Free Plan Logic
#     free_limits = {
#         "ai_analysis": 10,
#         "jd_screenshot": 3,
#         "jd_url": 10,
#         "application": 3,
#     }

#     max_limit = free_limits.get(feature_name)
#     if not max_limit:
#         return True  # unrestricted feature

#     usage = db.query(models.FeatureUsage).filter(
#         models.FeatureUsage.user_id == user_id,
#         models.FeatureUsage.feature == feature_name
#     ).first()

#     if usage:
#         # check if the cycle expired
#         if now > usage.period_end:
#             # reset usage cycle
#             usage.used_count = 1
#             usage.period_start = now
#             usage.period_end = now + timedelta(days=31)
#         else:
#             if usage.used_count >= max_limit:
#                 return False  # ❌ limit reached
#             usage.used_count += 1
#         usage.updated_at = now
#     else:
#         # first time using this feature
#         usage = models.FeatureUsage(
#             user_id=user_id,
#             feature=feature_name,
#             used_count=1,
#             period_start=now,
#             period_end=now + timedelta(days=31),
#             created_at=now,
#             updated_at=now
#         )
#         db.add(usage)

#     db.commit()
#     return True


from sqlalchemy import select, update
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

def check_feature_access(db: Session, user_id: int, feature_name: str) -> bool:
    """Check if a user can use a feature, update usage if allowed, safe for concurrent requests."""

    now = datetime.utcnow()

    # 1. Get the user's plan
    plan = db.query(models.UserPlan).filter(models.UserPlan.user_id == user_id).first()
    if not plan:
        plan = models.UserPlan(user_id=user_id, plan="free")
        db.add(plan)
        db.commit()

    # 2. Handle Pro Users
    if plan.plan == "pro":
        if plan.plan_expires_at and now > plan.plan_expires_at + timedelta(days=5):
            plan.plan = "free"
            plan.plan_expires_at = None
            db.commit()
        else:
            return True

    # 3. Free Plan Logic
    free_limits = {
        "ai_analysis": 10,
        "jd_screenshot": 3,
        "jd_url": 10,
        "application": 4,
    }

    max_limit = free_limits.get(feature_name)
    if not max_limit:
        return True

    # --- Use FOR UPDATE to lock the row ---
    usage = db.query(models.FeatureUsage).filter(
        models.FeatureUsage.user_id == user_id,
        models.FeatureUsage.feature == feature_name
    ).with_for_update(nowait=True).first()

    if usage:
        if now > usage.period_end:
            usage.used_count = 1
            usage.period_start = now
            usage.period_end = now + timedelta(days=31)
        else:
            if usage.used_count >= max_limit:
                return False
            usage.used_count += 1
        usage.updated_at = now
    else:
        usage = models.FeatureUsage(
            user_id=user_id,
            feature=feature_name,
            used_count=1,
            period_start=now,
            period_end=now + timedelta(days=31),
            created_at=now,
            updated_at=now
        )
        db.add(usage)

    db.commit()
    return True
