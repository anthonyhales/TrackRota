from fastapi import FastAPI
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os
app = FastAPI()
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
from .routers.time_off import router as time_off_router
from .version import APP_VERSION
from .update_check import get_latest_release

import re
def normalize(v: str) -> tuple[int, ...]:
    """
    Converts versions like:
    v1.2.3
    1.2.3-alpha
    1.2.X
    into a comparable tuple (1, 2, 3)
    """
    parts = re.findall(r"\d+", v)
    return tuple(int(p) for p in parts)
    
@app.on_event("startup")
def check_for_updates():
    release = get_latest_release()
    if release:
        latest = normalize(release["tag"])
        current = normalize(APP_VERSION)

        app.state.latest_version = release
        app.state.update_available = latest > current
    else:
        app.state.latest_version = None
        app.state.update_available = False

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

@app.middleware("http")
async def add_version_to_request(request: Request, call_next):
    request.state.app_version = APP_VERSION
    response = await call_next(request)
    return response

# Routers
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(staff_router)
app.include_router(shift_types_router)
app.include_router(rota_router)
app.include_router(users_router)
app.include_router(settings_router)
app.include_router(time_off_router)
