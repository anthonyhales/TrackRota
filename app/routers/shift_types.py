from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..auth import get_current_user, require_role
from ..models import ShiftType

router = APIRouter(prefix="/shift-types", tags=["shift-types"])

@router.get("")
def list_shift_types(request: Request):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)
        if not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/", status_code=303)

        items = db.query(ShiftType).order_by(ShiftType.active.desc(), ShiftType.name.asc()).all()
        return request.app.state.templates.TemplateResponse("shift_types.html", {"request": request, "user": user, "items": items})
    finally:
        db.close()

@router.post("/new")
def create_shift_type(request: Request, name: str = Form(...), description: str = Form(""), active: str = Form("on")):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)
        if not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/", status_code=303)

        st = ShiftType(name=name.strip(), description=description.strip() or None, active=(active == "on"))
        db.add(st)
        db.commit()
        return RedirectResponse("/shift-types", status_code=303)
    finally:
        db.close()

@router.post("/{shift_type_id}")
def update_shift_type(request: Request, shift_type_id: int, name: str = Form(...), description: str = Form(""), active: str = Form(None)):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)
        if not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/", status_code=303)

        st = db.query(ShiftType).filter(ShiftType.id == shift_type_id).first()
        if not st:
            return RedirectResponse("/shift-types", status_code=303)

        st.name = name.strip()
        st.description = description.strip() or None
        st.active = (active == "on")
        db.commit()
        return RedirectResponse("/shift-types", status_code=303)
    finally:
        db.close()
