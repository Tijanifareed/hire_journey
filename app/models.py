from sqlalchemy import Column, Index, Integer, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import datetime
from enum import Enum as PyEnum
from app.enums.timezones import TimezoneEnum





class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=False, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    timezone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    profile_picture = Column(String, nullable=True)
    
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")

    
class ApplicationStatus(PyEnum):
    not_applied = "Not Applied"
    applied = "Applied"
    interview = "Interview"
    offer = "Offer"
    rejected = "Rejected"    


class Application(Base):
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_title = Column(String(255), index=True, nullable=False)
    company = Column(String(255), nullable=False)
    status = Column(Enum(ApplicationStatus, name="applicationstatus"),
                                         default=ApplicationStatus.not_applied,
                                         nullable=False)
    applied_date = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(String, nullable=True)
    job_description = Column(String, nullable=True)
    job_link = Column(String, nullable=True)
    interview_date_utc = Column(DateTime, nullable=True)
    interview_date = Column(DateTime, nullable=True)
    interview_timezone = Column(String, nullable=True)
    follow_up_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="applications")
    analyses = relationship("AiAnalysis", back_populates="application", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="application", cascade="all, delete-orphan")
    application_timelines = relationship("ApplicationTimeline", back_populates="application", cascade="all, delete-orphan")
    interview_preps = relationship("InterviewPrep", back_populates="application", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_applications_user_id_id", "user_id", "id"),
    )

    
class AiAnalysis(Base):
    __tablename__ = "ai_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    ats_score = Column(Integer, nullable=False, default=0,)
    keyword_Match = Column(Boolean, nullable=False, default=False)
    suggestions = Column(String(255), nullable=True)   
    
    application = relationship("Application", back_populates="analyses")
    resume = relationship("Resume", back_populates="analyses") 
    
    
    
class ApplicationTimeline(Base):
    __tablename__ = "application_timelines"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    stage = Column(String(255), nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(String, nullable=True)
   
    # Many-to-one
    application = relationship("Application", back_populates="application_timelines")    
    
class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    file_url = Column(String(255), nullable=False)
    public_id = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)    
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Many-to-one
    user = relationship("User", back_populates="resumes")
    analyses = relationship("AiAnalysis", back_populates="resume", cascade="all, delete-orphan")
  
  
  
class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  # e.g., "Interview Reminder", "Status Update"
    message = Column(String(255), nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    is_sent = Column(Boolean, default=False)
    
    # Many-to-oneJ
    user = relationship("User", back_populates="notifications")
    application = relationship("Application", back_populates="notifications")
    
   
class InterviewPrep(Base):
    __tablename__ = "interview_preps"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    category = Column(String, nullable=False, ) 
    question = Column(String, nullable=True)
    
    # Many-to-one
    application = relationship("Application", back_populates="interview_preps")    
    
    
class PasswordReset(Base):
    __tablename__ = "password_resets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    code = Column(String(10), nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.datetime.utcnow() + datetime.timedelta(minutes=10))    