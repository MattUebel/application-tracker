from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional
from datetime import date
from decimal import Decimal

# --- Note Schemas ---
class NoteBase(BaseModel):
    content: str

class NoteCreate(NoteBase):
    pass

class Note(NoteBase):
    id: int
    application_id: int

    class Config:
        from_attributes = True # Changed from orm_mode for Pydantic v2

# --- Job Application Schemas ---
class JobApplicationBase(BaseModel):
    company_name: str
    role: str
    application_date: Optional[date] = None
    status: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    url: Optional[HttpUrl] = None
    cover_letter: Optional[bool] = False
    interview_date: Optional[date] = None
    offer: Optional[bool] = False
    salary: Optional[Decimal] = None
    equity: Optional[bool] = False
    bonus: Optional[float] = None # e.g., 0.10 for 10%
    health_coverage: Optional[bool] = False
    pto: Optional[str] = None
    is_active: Optional[bool] = True

class JobApplicationCreate(JobApplicationBase):
    pass

class JobApplicationUpdate(JobApplicationBase):
    # All fields are optional for updates
    company_name: Optional[str] = Field(default=None, min_length=1)
    role: Optional[str] = Field(default=None, min_length=1)
    # Other fields inherit optionality from JobApplicationBase
    # and can be set to None to clear them if the DB allows (which it does for these)
    application_date: Optional[date] = None
    status: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    url: Optional[HttpUrl] = None # Allow setting to None
    cover_letter: Optional[bool] = None
    interview_date: Optional[date] = None
    offer: Optional[bool] = None
    salary: Optional[Decimal] = None
    equity: Optional[bool] = None
    bonus: Optional[float] = None
    health_coverage: Optional[bool] = None
    pto: Optional[str] = None
    is_active: Optional[bool] = None

class JobApplication(JobApplicationBase):
    id: int
    notes: List[Note] = []
    is_active: bool # Must be present when reading from DB

    class Config:
        from_attributes = True # Changed from orm_mode for Pydantic v2

class JobApplicationSimple(BaseModel): # For listing on the main page
    id: int
    company_name: str
    role: str
    application_date: Optional[date] = None
    status: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True 