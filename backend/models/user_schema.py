from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class ExperienceLevel(str, Enum):
    ENTRY = 'entry'
    INTERMEDIATE = 'intermediate'
    SENIOR = 'senior'
    EXPERT = 'expert'

class ContactInfo(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None

class Education(BaseModel):
    # contact information from resume
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    description: Optional[str] = None
    location: Optional[str] = None

class Experience(BaseModel):
    """Work experience entry"""
    company: str
    title: str
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    current: Optional[bool] = False
    description: List[str]  # List of bullet points
    skills_used: Optional[List[str]] = []

class Skill(BaseModel):
    """Individual skill with optional proficiency"""
    name: str
    category: Optional[str] = None  # e.g., "Programming", "Soft Skills"
    proficiency: Optional[str] = None
    years: Optional[float] = None

class ResumeData(BaseModel):
    """Complete parsed resume data"""
    contact_info: ContactInfo  
    summary: Optional[str] = None
    education: List[Education] = []
    experience: List[Experience] = []
    skills: List[Skill] = []
    certifications: Optional[List[str]] = []
    languages: Optional[List[Dict[str, str]]] = []
    projects: Optional[List[Dict[str, str]]] = []
    raw_text: str
    metadata: Optional[Dict] = Field(
        default_factory=dict,
        description="Additional metadata about the parsed resume"
    )

    class Config:
        """Pydantic model configuration"""
        json_schema_extra = {
            "example": {
                "contact_info": {
                    "name": "Pods",
                    "email": "joblessguy.ixine@gmail.com",
                    "phone": "+1-123-456-7890",
                    "location": "New York, NY"
                },
                "summary": "Experienced in testing for 2 years but looking to switch job to data science/ML...",
                "education": [{
                    "institution": "Institute of Aeronautical Engineering",
                    "degree": "Bachelor of Technology",
                    "field_of_study": "Information Technology",
                    "start_date": "2019-09-01T00:00:00",
                    "end_date": "2023-05-30T00:00:00"
                }]
            }
        }