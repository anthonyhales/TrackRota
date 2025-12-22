from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os
import re
from .db_migrations import ensure_column_exists

from .db import engine, SessionLocal
from .models import (
    Base,
    User,
    Staff,
    ShiftType,
    RotaEntry,
    TimeOff,
    Rota,
)
from .security import hash_password
from .version import APP_VERSION
from .version import BUILD_NUMBER
from .update_check import get_latest_release

from .routers.auth_routes import router as auth_router
from .routers.dashboard import router as dashboard_router
from .routers.staff import router as staff_router
from .routers.shift_types import router as shift_types_router
from .routers.rota import router as rota_router
from .routers.users import router as users_router
from .routers.settings import router as settings_router
from .routers.time_off import router as time_off_router
from .routers.rotas import router as rotas_router


# -------------------------------------------------
# App
# -------------------------------------------------

app = FastAPI()


# -------------------------------------------------
# Templates & static
# -------------------------------------------------

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")
app.state.templates = templates


# -------------------------------------------------
# Version helpers
# -------------------------------------------------

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


# -------------------------------------------------
# Bootstrap data
# -------------------------------------------------

def bootstrap_defaults(db: Session):
    # Create tables first
    Base.metadata.create_all(bind=engine)

    # ---- lightweight migrations ----
    ensure_column_exists(
        db,
        table="users",
        column="favourite_rotas",
        column_sql="TEXT",
    )

    # Ensure at least one rota exists
    if db.query(Rota).count() == 0:
        default_rota = Rota(
            name="Primary On Call",
            description="Default rota",
            active=True,
        )
        db.add(default_rota)
        db.commit()

    default_rota = (
        db.query(Rota)
        .filter(Rota.active == True)
        .order_by(Rota.id.asc())
        .first()
    )

    # Default shift types
    if default_rota and db.query(ShiftType).count() == 0:
        db.add_all(
            [
                ShiftType(
                    rota_id=default_rota.id,
                    name="Primary",
                    description="Primary on call",
                    active=True,
                ),
                ShiftType(
                    rota_id=default_rota.id,
                    name="Secondary",
                    description="Secondary on call",
                    active=True,
                ),
            ]
        )
        db.commit()

    # Bootstrap admin user (optional)
    admin_email = os.getenv("APP_BOOTSTRAP_ADMIN_EMAIL")
    admin_password = os.getenv("APP_BOOTSTRAP_ADMIN_PASSWORD")

    if admin_email and admin_password:
        existing = (
            db.query(User)
            .filter(User.email == admin_email.lower().strip())
            .first()
        )
        if not existing:
            db.add(
                User(
                    email=admin_email.lower().strip(),
                    password_hash=hash_password(admin_password),
                    role="Admin",
                    active=True,
                )
            )
            db.commit()


# -------------------------------------------------
# Startup events
# -------------------------------------------------

@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        bootstrap_defaults(db)
    finally:
        db.close()


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


# -------------------------------------------------
# Middleware
# -------------------------------------------------

@app.middleware("http")
async def add_version_to_request(request: Request, call_next):
    request.state.app_version = APP_VERSION
    request.state.build_number = BUILD_NUMBER
    response = await call_next(request)
    return response


# -------------------------------------------------
# Routers
# -------------------------------------------------

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(staff_router)
app.include_router(shift_types_router)
app.include_router(rota_router)
app.include_router(users_router)
app.include_router(settings_router)
app.include_router(time_off_router)
app.include_router(rotas_router)
