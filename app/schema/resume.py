from pydantic import BaseModel
from typing import List, Optional

class Experience(BaseModel):
    company: str
    role: str
    startDate: str
    endDate: Optional[str] = None
    achievements: List[str]

class Education(BaseModel):
    institution: str
    degree: str
    field: Optional[str] = None
    startDate: str
    endDate: Optional[str] = None

class Extras(BaseModel):
    certifications: Optional[List[str]] = None
    languages: Optional[List[str]] = None

class PersonalInfo(BaseModel):
    fullName: str
    title: Optional[str] = None
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None

class ResumeData(BaseModel):
    personalInfo: PersonalInfo
    summary: Optional[str] = None
    experience: List[Experience]
    education: List[Education]
    skills: List[str]
    extras: Optional[Extras] = None
