from pydantic import BaseModel, EmailStr, HttpUrl
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Enum

from app.enums.timezones import TimezoneEnum

class UserCreate(BaseModel):
     username: str
     email: EmailStr
     password: str
     
     
class UserLogin(BaseModel):
    email: EmailStr
    password: str     
    
class ApplicationStatus(str, Enum):
    applied = "Applied"
    interview = "Interview"
    offer = "Offer"
    rejected = "Rejected"    
    
class AddApplicationRequest(BaseModel):
    job_title: str
    company: str
    status: str = ApplicationStatus.applied
    applied_date: Optional[datetime] = None
    notes: Optional[str] = None
    job_description: Optional[str] = None
    job_link: str
    

    
class UpdateApplicationRequest(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    status: Optional[str] = None
    applied_date: Optional[datetime] = None
    notes: Optional[str] = None
    job_description: Optional[str] = None
    job_link: Optional[str] = None    
    interview_date: Optional[datetime] = None
    interview_timezone: Optional[str] = None
    
class ProfileUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    timezone: Optional[str] = None
    

     
class InterviewDateRequest(BaseModel):
    interview_date: str  
    timezone: str      
     
class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    
class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str  
    
class AddResumeRequest(BaseModel):
    title: str
    file_url: str
    public_id: str     
    
class TimeZoneRequest(BaseModel):
    timezone: str = TimezoneEnum.UTC    
    
class ApplicationStats(BaseModel):
    applied: int
    interview: int
    offer: int
    rejected: int

class StatsResponse(BaseModel):
    data: ApplicationStats
    
    
 
class RecentApplicationResponse(BaseModel):
    id: int
    job_title: str
    company_name: str
    status: str
    time_ago: str       
    
    
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    
class RefreshRequest(BaseModel):
    refresh_token: str        
    
    
    
class ResetPasswordRequest(BaseModel):
    token: str       
    email: str 
        
class ChangePasswordRequest(BaseModel):
    email: str
    new_password: str        