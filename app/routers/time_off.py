from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..auth import get_current_user, require_role
from ..models import TimeOff, Staff

router = APIRouter(prefix="/time-off", tags=["time-off"])


@router.get("")
def time_off_list(request: Request):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)
        if not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/", status_code=303)

        staff = db.query(Staff).filter(Staff.active == True).order_by(Staff.full_name.asc()).all()
        items = (
            db.query(TimeOff)
            .order_by(TimeOff.start_date.desc(), TimeOff.end_date.desc())
            .all()
        )

        # preload staff names
        staff_map = {s.id: s for s in staff}
        return request.app.state.templates.TemplateResponse(
            "time_off.html",
            {"request": request, "user": user, "staff": staff, "items": items, "staff_map": staff_map},
        )
    finally:
        db.close()


@router.post("/new")
def time_off_create(
    request: Request,
    staff_id: int = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    reason: str = Form(""),
):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)
        if not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/", status_code=303)

        sd = datetime.strptime(start_date, "%Y-%m-%d").date()
        ed = datetime.strptime(end_date, "%Y-%m-%d").date()
        if ed < sd:
            # swap if user entered backwards
            sd, ed = ed, sd

        item = TimeOff(
            staff_id=int(staff_id),
            start_date=sd,
            end_date=ed,
            reason=reason.strip() or None,
        )
        db.add(item)
        db.commit()
        return RedirectResponse("/time-off", status_code=303)
    finally:
        db.close()


@router.post("/{time_off_id}/delete")
def time_off_delete(request: Request, time_off_id: int):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)
        if not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/", status_code=303)

        item = db.query(TimeOff).filter(TimeOff.id == time_off_id).first()
        if item:
            db.delete(item)
            db.commit()
        return RedirectResponse("/time-off", status_code=303)
    finally:
        db.close()
