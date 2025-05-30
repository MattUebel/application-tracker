from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, Numeric, Float, Text
from sqlalchemy.orm import relationship
from .database import Base

class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)
    application_date = Column(Date)
    status = Column(String)
    contact_person = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    url = Column(String, nullable=True)
    cover_letter = Column(Boolean, default=False)
    interview_date = Column(Date, nullable=True)
    offer = Column(Boolean, default=False)
    salary = Column(Numeric(10, 2), nullable=True)  # Assuming (total_digits, decimal_places)
    equity = Column(Boolean, default=False)
    bonus = Column(Float, nullable=True)  # Representing percentage, e.g., 0.10 for 10%
    health_coverage = Column(Boolean, default=False)
    pto = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    notes = relationship("Note", back_populates="application", order_by="desc(Note.id)")

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    application_id = Column(Integer, ForeignKey("job_applications.id"))

    application = relationship("JobApplication", back_populates="notes") 