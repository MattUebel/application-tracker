from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select # Import select for async queries
from . import models, schemas
from typing import List, Optional
from pydantic import HttpUrl

# --- Job Application CRUD --- 

async def get_job_application(db: AsyncSession, application_id: int) -> Optional[models.JobApplication]:
    result = await db.execute(select(models.JobApplication).filter(models.JobApplication.id == application_id))
    return result.scalars().first()

async def get_job_applications(db: AsyncSession, skip: int = 0, limit: int = 100, is_active: Optional[bool] = True) -> List[models.JobApplication]:
    query = select(models.JobApplication)
    if is_active is not None:
        query = query.filter(models.JobApplication.is_active == is_active)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def create_job_application(db: AsyncSession, application: schemas.JobApplicationCreate) -> models.JobApplication:
    app_data = application.model_dump()
    if isinstance(app_data.get("url"), HttpUrl):
        app_data["url"] = str(app_data["url"])
    
    db_application = models.JobApplication(**app_data)
    db.add(db_application)
    await db.commit()
    await db.refresh(db_application)
    return db_application

async def update_job_application(db: AsyncSession, application_id: int, application_update: schemas.JobApplicationUpdate) -> Optional[models.JobApplication]:
    db_application = await get_job_application(db, application_id) # Must await here
    if db_application:
        update_data = application_update.model_dump(exclude_unset=True)
        if isinstance(update_data.get("url"), HttpUrl):
            update_data["url"] = str(update_data["url"])
            
        for key, value in update_data.items():
            setattr(db_application, key, value)
        await db.commit()
        await db.refresh(db_application)
    return db_application

async def delete_job_application(db: AsyncSession, application_id: int) -> Optional[models.JobApplication]:
    db_application = await get_job_application(db, application_id) # Must await here
    if db_application:
        await db.delete(db_application)
        await db.commit()
    return db_application # Note: after delete, this object might be in a transient state or detached

async def activate_job_application(db: AsyncSession, application_id: int) -> Optional[models.JobApplication]:
    db_application = await get_job_application(db, application_id) # Must await here
    if db_application:
        db_application.is_active = True
        await db.commit()
        await db.refresh(db_application)
    return db_application

async def deactivate_job_application(db: AsyncSession, application_id: int) -> Optional[models.JobApplication]:
    db_application = await get_job_application(db, application_id) # Must await here
    if db_application:
        db_application.is_active = False
        await db.commit()
        await db.refresh(db_application)
    return db_application

# --- Note CRUD --- 

async def create_note_for_application(db: AsyncSession, note: schemas.NoteCreate, application_id: int) -> models.Note:
    db_note = models.Note(**note.model_dump(), application_id=application_id)
    db.add(db_note)
    await db.commit()
    await db.refresh(db_note)
    return db_note

async def get_notes_for_application(db: AsyncSession, application_id: int) -> List[models.Note]:
    query = select(models.Note).filter(models.Note.application_id == application_id).order_by(desc(models.Note.id))
    result = await db.execute(query)
    return result.scalars().all() 