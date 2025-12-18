from __future__ import annotations

from datetime import date, timedelta, datetime
from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..auth import get_current_user, require_role
from ..models import Rota, ShiftType, Staff, RotaEntry, TimeOff
from ..utils import week_dates, start_of_week, now_local

router = APIRouter(prefix="/rota", tags=["rota"])


@router.get("")
def rota_week(
    request: Request,
    week: str | None = Query(default=None),
    rota_id: int | None = Query(default=None),
):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)

        can_edit = require_role(user, {"Admin", "Manager"})

        # Resolve date
        if week:
            try:
                d = datetime.strptime(week, "%Y-%m-%d").date()
            except ValueError:
                d = now_local().date()
        else:
            d = now_local().date()

        days = week_dates(d)
        today = now_local().date()
        week_start = start_of_week(d)
        prev_week = (week_start - timedelta(days=7)).isoformat()
        next_week = (week_start + timedelta(days=7)).isoformat()

        # ---- ROTAS ----
        rotas = (
            db.query(Rota)
            .filter(Rota.active == True)
            .order_by(Rota.name.asc())
            .all()
        )

        if not rotas:
            return RedirectResponse("/", status_code=303)

        if rota_id:
            current_rota = next((r for r in rotas if r.id == rota_id), None)
        else:
            current_rota = None

        if current_rota is None:
            current_rota = rotas[0]

        # ---- SHIFT TYPES (per rota) ----
        shift_types = (
            db.query(ShiftType)
            .filter(
                ShiftType.active == True,
                ShiftType.rota_id == current_rota.id,
            )
            .order_by(ShiftType.name.asc())
            .all()
        )

        # ---- STAFF ----
        staff = (
            db.query(Staff)
            .filter(Staff.active == True)
            .order_by(Staff.full_name.asc())
            .all()
        )

        # ---- ROTA ENTRIES (per rota + week) ----
        entries = (
            db.query(RotaEntry)
            .filter(
                RotaEntry.rota_id == current_rota.id,
                RotaEntry.shift_date.in_(days),
            )
            .all()
        )
        entry_map = {(e.shift_date, e.shift_type_id): e for e in entries}

        # ---- TIME OFF / CONFLICTS ----
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
                "rotas": rotas,
                "current_rota": current_rota,
                "rota_id": current_rota.id,
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
def assign(
    request: Request,
    rota_id: int = Form(...),
    shift_date: str = Form(...),
    shift_type_id: int = Form(...),
    staff_id: str = Form(""),
    notes: str = Form(""),
):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/rota", status_code=303)

        d = datetime.strptime(shift_date, "%Y-%m-%d").date()
        st_id = int(shift_type_id)
        rid = int(rota_id)
        staff_id_val = int(staff_id) if staff_id.strip() else None

        entry = (
            db.query(RotaEntry)
            .filter(
                RotaEntry.rota_id == rid,
                RotaEntry.shift_date == d,
                RotaEntry.shift_type_id == st_id,
            )
            .first()
        )

        if not entry:
            entry = RotaEntry(
                rota_id=rid,
                shift_date=d,
                shift_type_id=st_id,
                staff_id=staff_id_val,
                notes=notes.strip() or None,
            )
            db.add(entry)
        else:
            entry.staff_id = staff_id_val
            entry.notes = notes.strip() or None

        db.commit()

        week_start = (d - timedelta(days=d.weekday())).isoformat()
        return RedirectResponse(
            f"/rota?rota_id={rid}&week={week_start}",
            status_code=303,
        )

    finally:
        db.close()
