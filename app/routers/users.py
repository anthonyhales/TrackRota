from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..auth import get_current_user, require_role
from ..models import User, Staff
from ..security import hash_password

router = APIRouter(prefix="/users", tags=["users"])

@router.get("")
def list_users(request: Request):
    db: Session = SessionLocal()
    try:
        current = get_current_user(request, db)
        if not current:
            return RedirectResponse("/login", status_code=303)
        if not require_role(current, {"Admin"}):
            return RedirectResponse("/", status_code=303)

        users = db.query(User).order_by(User.active.desc(), User.email.asc()).all()
        staff = db.query(Staff).order_by(Staff.full_name.asc()).all()
        return request.app.state.templates.TemplateResponse("users.html", {"request": request, "user": current, "users": users, "staff": staff})
    finally:
        db.close()

@router.post("/new")
def create_user(request: Request,
                email: str = Form(...),
                password: str = Form(...),
                role: str = Form(...),
                staff_id: str = Form("")):
    db: Session = SessionLocal()
    try:
        current = get_current_user(request, db)
        if not current:
            return RedirectResponse("/login", status_code=303)
        if not require_role(current, {"Admin"}):
            return RedirectResponse("/", status_code=303)

        u = User(
            email=email.lower().strip(),
            password_hash=hash_password(password),
            role=role,
            staff_id=int(staff_id) if staff_id.strip() else None,
            active=True,
        )
        db.add(u)
        db.commit()
        return RedirectResponse("/users", status_code=303)
    finally:
        db.close()

@router.post("/{user_id}")
def update_user(request: Request,
                user_id: int,
                email: str = Form(...),
                role: str = Form(...),
                staff_id: str = Form(""),
                active: str = Form(None),
                new_password: str = Form("")):
    db: Session = SessionLocal()
    try:
        current = get_current_user(request, db)
        if not current:
            return RedirectResponse("/login", status_code=303)
        if not require_role(current, {"Admin"}):
            return RedirectResponse("/", status_code=303)

        u = db.query(User).filter(User.id == user_id).first()
        if not u:
            return RedirectResponse("/users", status_code=303)

        u.email = email.lower().strip()
        u.role = role
        u.staff_id = int(staff_id) if staff_id.strip() else None
        u.active = (active == "on")
        if new_password.strip():
            u.password_hash = hash_password(new_password.strip())
        db.commit()
        return RedirectResponse("/users", status_code=303)
    finally:
        db.close()
