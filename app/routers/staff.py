from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..auth import get_current_user, require_role
from ..models import Staff

router = APIRouter(prefix="/staff", tags=["staff"])

@router.get("")
def list_staff(request: Request):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)
        if not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/", status_code=303)

        staff = db.query(Staff).order_by(Staff.active.desc(), Staff.full_name.asc()).all()
        return request.app.state.templates.TemplateResponse("staff_list.html", {"request": request, "user": user, "staff": staff})
    finally:
        db.close()

@router.get("/new")
def new_staff_form(request: Request):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)
        if not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/", status_code=303)
        return request.app.state.templates.TemplateResponse("staff_form.html", {"request": request, "user": user, "staff_member": None})
    finally:
        db.close()

@router.post("/new")
def create_staff(request: Request,
                 full_name: str = Form(...),
                 email: str = Form(""),
                 phone: str = Form(""),
                 team: str = Form(""),
                 active: str = Form("on")):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)
        if not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/", status_code=303)

        s = Staff(
            full_name=full_name.strip(),
            email=email.strip() or None,
            phone=phone.strip() or None,
            team=team.strip() or None,
            active=(active == "on"),
        )
        db.add(s)
        db.commit()
        return RedirectResponse("/staff", status_code=303)
    finally:
        db.close()

@router.get("/{staff_id}")
def edit_staff_form(request: Request, staff_id: int):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)
        if not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/", status_code=303)

        s = db.query(Staff).filter(Staff.id == staff_id).first()
        if not s:
            return RedirectResponse("/staff", status_code=303)

        return request.app.state.templates.TemplateResponse("staff_form.html", {"request": request, "user": user, "staff_member": s})
    finally:
        db.close()

@router.post("/{staff_id}")
def update_staff(request: Request,
                 staff_id: int,
                 full_name: str = Form(...),
                 email: str = Form(""),
                 phone: str = Form(""),
                 team: str = Form(""),
                 active: str = Form(None)):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)
        if not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/", status_code=303)

        s = db.query(Staff).filter(Staff.id == staff_id).first()
        if not s:
            return RedirectResponse("/staff", status_code=303)

        s.full_name = full_name.strip()
        s.email = email.strip() or None
        s.phone = phone.strip() or None
        s.team = team.strip() or None
        s.active = (active == "on")
        db.commit()
        return RedirectResponse("/staff", status_code=303)
    finally:
        db.close()
