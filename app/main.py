from datetime import datetime
from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from typing import Optional
from decimal import Decimal, InvalidOperation
from pydantic import HttpUrl, ValidationError

from . import crud, models, schemas, database
from .database import get_db

# Create database tables on startup
# models.Base.metadata.create_all(bind=engine) # This will be handled by Alembic or a startup event

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Database tables are managed by Alembic migrations.
    # models.Base.metadata.create_all(bind=engine) # This line is removed
    yield
    # Clean up resources if needed

app = FastAPI(lifespan=lifespan)

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# --- HTML Routes ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: AsyncSession = Depends(get_db), view: Optional[str] = "active"):
    if view == "active":
        applications = await crud.get_job_applications(db, skip=0, limit=100, is_active=True)
    elif view == "inactive":
        applications = await crud.get_job_applications(db, skip=0, limit=100, is_active=False)
    elif view == "all":
        applications = await crud.get_job_applications(db, skip=0, limit=100, is_active=None)
    else: # Default to active
        applications = await crud.get_job_applications(db, skip=0, limit=100, is_active=True)
        view = "active" # Ensure current_view is correctly set

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "applications": applications, "current_year": datetime.now().year, "current_view": view}
    )

@app.get("/inactive", response_class=HTMLResponse)
async def read_inactive_applications(request: Request, db: AsyncSession = Depends(get_db)):
    applications = await crud.get_job_applications(db, skip=0, limit=100, is_active=False)
    return templates.TemplateResponse(
        "inactive_applications.html", # We will create this template later
        {"request": request, "applications": applications, "current_year": datetime.now().year}
    )

@app.get("/applications/{application_id}", response_class=HTMLResponse)
async def read_application_detail(
    request: Request, application_id: int, db: AsyncSession = Depends(get_db)
):
    application = await crud.get_job_application(db, application_id=application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    notes = await crud.get_notes_for_application(db, application_id=application_id)
    return templates.TemplateResponse(
        "application_detail.html",
        {"request": request, "application": application, "notes": notes, "current_year": datetime.now().year}
    )

@app.post("/applications/new", response_class=RedirectResponse)
async def create_new_application(
    db: AsyncSession = Depends(get_db),
    company_name: str = Form(...),
    role: str = Form(...),
    application_date: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    contact_person: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    url: Optional[str] = Form(None), # Input as string
    cover_letter: bool = Form(False),
    interview_date: Optional[str] = Form(None),
    offer: bool = Form(False),
    salary: Optional[str] = Form(None),
    equity: bool = Form(False),
    bonus: Optional[str] = Form(None),
    health_coverage: bool = Form(False),
    pto: Optional[str] = Form(None)
):
    from datetime import date as py_date
    from decimal import Decimal, InvalidOperation
    from pydantic import HttpUrl, ValidationError

    # Helper to convert empty strings to None for optional fields
    def empty_str_to_none(value: Optional[str]) -> Optional[str]:
        return None if value == "" else value

    status = empty_str_to_none(status)
    contact_person = empty_str_to_none(contact_person)
    phone = empty_str_to_none(phone)
    pto = empty_str_to_none(pto)
    # url, salary, bonus are handled slightly differently below due to type conversion

    parsed_application_date = None
    if application_date and application_date.strip():
        try:
            parsed_application_date = py_date.fromisoformat(application_date.strip())
        except ValueError:
            # Consider raising HTTPException or adding to an error list
            pass

    parsed_interview_date = None
    if interview_date and interview_date.strip():
        try:
            parsed_interview_date = py_date.fromisoformat(interview_date.strip())
        except ValueError:
            pass

    parsed_salary = None
    if salary and salary.strip():
        try:
            parsed_salary = Decimal(salary.strip())
        except InvalidOperation:
            pass 

    parsed_bonus = None
    if bonus and bonus.strip():
        try:
            bonus_val_str = bonus.strip().rstrip('%')
            if bonus_val_str:
                parsed_bonus = float(bonus_val_str) / 100.0
        except ValueError:
            pass
            
    validated_url_str = None
    if url and url.strip():
        try:
            # Validate first
            pydantic_url = HttpUrl(url.strip())
            # Convert to string for DB
            validated_url_str = str(pydantic_url)
        except ValidationError:
            pass 

    application_data = schemas.JobApplicationCreate(
        company_name=company_name,
        role=role,
        application_date=parsed_application_date,
        status=status,
        contact_person=contact_person,
        phone=phone,
        url=validated_url_str, # Pass the string representation
        cover_letter=cover_letter,
        interview_date=parsed_interview_date,
        offer=offer,
        salary=parsed_salary,
        equity=equity,
        bonus=parsed_bonus,
        health_coverage=health_coverage,
        pto=pto
    )
    await crud.create_job_application(db=db, application=application_data)
    return RedirectResponse(url="/", status_code=303)

@app.get("/applications/{application_id}/edit", response_class=HTMLResponse)
async def edit_application_form(
    request: Request, application_id: int, db: AsyncSession = Depends(get_db)
):
    application = await crud.get_job_application(db, application_id=application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return templates.TemplateResponse(
        "edit_application.html",
        {"request": request, "application": application, "current_year": datetime.now().year}
    )

@app.post("/applications/{application_id}/edit", response_class=RedirectResponse)
async def update_application_submit(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    company_name: str = Form(...),
    role: str = Form(...),
    application_date: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    contact_person: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    cover_letter: bool = Form(False),
    interview_date: Optional[str] = Form(None),
    offer: bool = Form(False),
    salary: Optional[str] = Form(None),
    equity: bool = Form(False),
    bonus: Optional[str] = Form(None),
    health_coverage: bool = Form(False),
    pto: Optional[str] = Form(None)
):
    from datetime import date as py_date
    from decimal import Decimal, InvalidOperation
    from pydantic import HttpUrl, ValidationError

    # Helper to convert empty strings to None for optional fields
    def empty_str_to_none(value: Optional[str]) -> Optional[str]:
        return None if value == "" else value

    db_application = await crud.get_job_application(db, application_id=application_id)
    if db_application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    parsed_application_date = db_application.application_date
    if application_date is not None: # Check if field was submitted
        if application_date.strip() == "": parsed_application_date = None
        else: 
            try: parsed_application_date = py_date.fromisoformat(application_date.strip())
            except ValueError: pass # Keep existing if parse fails but was submitted
    
    parsed_interview_date = db_application.interview_date
    if interview_date is not None:
        if interview_date.strip() == "": parsed_interview_date = None
        else:
            try: parsed_interview_date = py_date.fromisoformat(interview_date.strip())
            except ValueError: pass

    parsed_salary = db_application.salary
    if salary is not None:
        if salary.strip() == "": parsed_salary = None
        else:
            try: parsed_salary = Decimal(salary.strip())
            except InvalidOperation: pass
    
    parsed_bonus = db_application.bonus
    if bonus is not None:
        if bonus.strip() == "": parsed_bonus = None
        else:
            try:
                bonus_val_str = bonus.strip().rstrip('%')
                if bonus_val_str: parsed_bonus = float(bonus_val_str) / 100.0
            except ValueError: pass

    validated_url_str = db_application.url
    if url is not None:
        if url.strip() == "": validated_url_str = None
        else:
            try: 
                pydantic_url = HttpUrl(url.strip())
                validated_url_str = str(pydantic_url)
            except ValidationError: pass

    update_data = schemas.JobApplicationUpdate(
        company_name=company_name, 
        role=role,                 
        application_date=parsed_application_date,
        status=empty_str_to_none(status),
        contact_person=empty_str_to_none(contact_person),
        phone=empty_str_to_none(phone),
        url=validated_url_str, # Pass the string representation or None
        cover_letter=cover_letter,
        interview_date=parsed_interview_date,
        offer=offer,
        salary=parsed_salary,
        equity=equity,
        bonus=parsed_bonus,
        health_coverage=health_coverage,
        pto=empty_str_to_none(pto)
    )

    # Pydantic's exclude_unset=True is not what we want here if we want to allow clearing fields.
    # We pass all fields from the form (or their None equivalent for empty optionals)
    # The schema JobApplicationUpdate has all fields as optional, so this is fine.
    # The CRUD operation will then update only the fields present in the model_dump().
    # However, we are constructing JobApplicationUpdate with all fields (some as None).
    # So, we need to be careful if we want to distinguish between 'not provided' and 'set to None'.
    # For this setup, setting an empty string in the form for an optional text field implies clearing it (setting to None).

    # We want to create a dictionary of only the fields that were actually submitted or have defaults
    # to pass to the CRUD update function, so it only updates those.
    # However, the current Pydantic JobApplicationUpdate schema has all fields as Optional
    # and the crud.update_job_application uses model_dump(exclude_unset=True).
    # This means if a field is not in the Form data (like an unchecked checkbox defaulting to False),
    # it won't be in the update_data if we constructed it from raw form fields.
    # By explicitly constructing JobApplicationUpdate with all form fields, we are making a choice for each.

    updated_app = await crud.update_job_application(db=db, application_id=application_id, application_update=update_data)
    if updated_app is None:
        raise HTTPException(status_code=404, detail="Update failed or application not found")

    return RedirectResponse(url=f"/applications/{application_id}", status_code=303)

@app.post("/applications/{application_id}/notes/new", response_class=RedirectResponse)
async def create_new_note_for_application(
    application_id: int,
    content: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    from datetime import datetime
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # Prepend timestamp to the note content
    final_content = f"[{timestamp}] -- {content}"
    
    note_data = schemas.NoteCreate(content=final_content)
    await crud.create_note_for_application(db=db, note=note_data, application_id=application_id)
    return RedirectResponse(url=f"/applications/{application_id}", status_code=303)

@app.post("/applications/{application_id}/activate", response_class=RedirectResponse)
async def activate_application_route(
    application_id: int, db: AsyncSession = Depends(get_db), source: Optional[str] = Form(None)
):
    await crud.activate_job_application(db, application_id=application_id)
    if source == "inactive_list":
        return RedirectResponse(url="/inactive", status_code=303)
    return RedirectResponse(url="/", status_code=303)

@app.post("/applications/{application_id}/deactivate", response_class=RedirectResponse)
async def deactivate_application_route(
    application_id: int, db: AsyncSession = Depends(get_db)
):
    await crud.deactivate_job_application(db, application_id=application_id)
    return RedirectResponse(url="/", status_code=303)

@app.post("/applications/{application_id}/delete", response_class=RedirectResponse)
async def delete_application_route(
    application_id: int, db: AsyncSession = Depends(get_db), source: Optional[str] = Form(None)
):
    await crud.delete_job_application(db, application_id=application_id)
    if source == "inactive_list":
        return RedirectResponse(url="/inactive", status_code=303)
    return RedirectResponse(url="/", status_code=303)

# Placeholder for API routes if you want to separate them later
# from .routers import applications as application_router
# app.include_router(application_router.router, prefix="/api")

# Simple health check
@app.get("/health")
async def health_check():
    return {"status": "ok"} 