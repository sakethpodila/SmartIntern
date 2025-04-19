from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
from backend.models.user_schema import ExperienceLevel

class JobSearchParameters(BaseModel):
    query: str
    location: Optional[str] = None
    experience_level: Optional[ExperienceLevel] = None
    job_type: Optional[str] = None
    remote: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    
    class Config: 
        json_schema_extra = {
            'example': {
                'query': 'python developer', 
                'location': 'Wakanda',
                'experience_level': 'INTERMEDIATE', 
                'remote': True,
                'limit': 10, 
                'offset': 0
            }

        }

class JobPost(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    description: str
    requirements: List[str]
    salary_range: Optional[str] = None
    posted_date: Optional[datetime] = None
    job_type: Optional[str] = None
    url: Optional[HttpUrl] = None
    experience_level: Optional[ExperienceLevel] = None
    remote: Optional[bool] = False

    class Config:
        json_schema_extra = {
            'example': {
                'job_id': '123456',
                'title': 'Senior Python',
                'company': 'Tech Corp',
                'location': 'Wakanda, forest', 
                'description': 'Looking for soliders',
                'requirements': [
                     "5+ years Python experience",
                    "Experience with FastAPI",
                    "Knowledge of SQL databases"
                ],
                'salary_range': 'INR 24,00,000',
                'job_type': 'Full-time', 
                'remote': True
            }
        }