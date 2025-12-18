from __future__ import annotations
from datetime import date, timedelta, datetime
from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..auth import get_current_user, require_role
from ..models import ShiftType, Staff, RotaEntry
from ..utils import week_dates, start_of_week, now_local
from ..models import ShiftType, Staff, RotaEntry, TimeOff


router = APIRouter(prefix="/rota", tags=["rota"])

@router.get("")
def rota_week(request: Request, week: str | None = Query(default=None)):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)

        can_edit = require_role(user, {"Admin", "Manager"})

        if week:
            try:
                d = datetime.strptime(week, "%Y-%m-%d").date()
            except ValueError:
                d = now_local().date()
        else:
            d = now_local().date()

        days = week_dates(d)
        week_start = start_of_week(d)
        prev_week = (week_start - timedelta(days=7)).isoformat()
        next_week = (week_start + timedelta(days=7)).isoformat()

        shift_types = (
            db.query(ShiftType)
            .filter(ShiftType.active == True)
            .order_by(ShiftType.name.asc())
            .all()
        )

        staff = (
            db.query(Staff)
            .filter(Staff.active == True)
            .order_by(Staff.full_name.asc())
            .all()
        )

        entries = db.query(RotaEntry).filter(RotaEntry.shift_date.in_(days)).all()
        entry_map = {(e.shift_date, e.shift_type_id): e for e in entries}

        # ---- ALPHA 1.1: time off awareness ----

        week_start_day = days[0]
        week_end_day = days[-1]

        time_off_items = (
            db.query(TimeOff)
            .filter(
                TimeOff.start_date <= week_end_day,
                TimeOff.end_date >= week_start_day,
            )
            .all()
        )

        unavailable: set[tuple[int, date]] = set()
        for t in time_off_items:
            cur = t.start_date
            while cur <= t.end_date:
                if week_start_day <= cur <= week_end_day:
                    unavailable.add((t.staff_id, cur))
                cur += timedelta(days=1)

        conflicts: set[tuple[date, int]] = set()
        for (day, shift_type_id), e in entry_map.items():
            if e and e.staff_id and (e.staff_id, day) in unavailable:
                conflicts.add((day, shift_type_id))
                today = now_local().date()
        return request.app.state.templates.TemplateResponse(
            "rota_week.html",
            {
                "request": request,
                "user": user,
                "can_edit": can_edit,
                "days": days,
                "today": today,
                "week_start": week_start,
                "prev_week": prev_week,
                "next_week": next_week,
                "shift_types": shift_types,
                "staff": staff,
                "entry_map": entry_map,
                "unavailable": unavailable,
                "conflicts": conflicts,
                
            },
        )

    finally:
        db.close()

@router.post("/assign")
def assign(request: Request,
           shift_date: str = Form(...),
           shift_type_id: int = Form(...),
           staff_id: str = Form(""),
           notes: str = Form("")):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)
        if not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/rota", status_code=303)

        d = datetime.strptime(shift_date, "%Y-%m-%d").date()
        st_id = int(shift_type_id)
        staff_id_val = int(staff_id) if staff_id.strip() else None

        entry = db.query(RotaEntry).filter(RotaEntry.shift_date == d, RotaEntry.shift_type_id == st_id).first()
        if not entry:
            entry = RotaEntry(shift_date=d, shift_type_id=st_id, staff_id=staff_id_val, notes=notes.strip() or None)
            db.add(entry)
        else:
            entry.staff_id = staff_id_val
            entry.notes = notes.strip() or None
        db.commit()

        week_start = (d - timedelta(days=d.weekday())).isoformat()
        return RedirectResponse(f"/rota?week={week_start}", status_code=303)
    finally:
        db.close()
