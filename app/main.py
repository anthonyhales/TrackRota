from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from .db import engine, SessionLocal
from .models import Base, User, ShiftType
from .security import hash_password

from .routers.auth_routes import router as auth_router
from .routers.dashboard import router as dashboard_router
from .routers.staff import router as staff_router
from .routers.shift_types import router as shift_types_router
from .routers.rota import router as rota_router
from .routers.users import router as users_router
from .routers.settings import router as settings_router

app = FastAPI(title="On Call Tracker - ALPHA 1")

# Static
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")
app.state.templates = templates

def bootstrap_defaults(db: Session):
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Default shift types if missing
    if db.query(ShiftType).count() == 0:
        db.add_all([
            ShiftType(name="Primary", description="Primary on-call"),
            ShiftType(name="Secondary", description="Secondary on-call"),
        ])
        db.commit()

    # Bootstrap admin if env vars provided and no admin exists
    admin_email = os.getenv("APP_BOOTSTRAP_ADMIN_EMAIL")
    admin_password = os.getenv("APP_BOOTSTRAP_ADMIN_PASSWORD")
    if admin_email and admin_password:
        existing = db.query(User).filter(User.email == admin_email.lower().strip()).first()
        if not existing:
            db.add(User(
                email=admin_email.lower().strip(),
                password_hash=hash_password(admin_password),
                role="Admin",
                active=True,
            ))
            db.commit()

@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        bootstrap_defaults(db)
    finally:
        db.close()

# Routers
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(staff_router)
app.include_router(shift_types_router)
app.include_router(rota_router)
app.include_router(users_router)
app.include_router(settings_router)
