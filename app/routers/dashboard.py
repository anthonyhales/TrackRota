from datetime import date, timedelta
from fastapi import APIRouter, Request
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..auth import get_current_user
from ..models import ShiftType, RotaEntry, Staff
from ..utils import now_local

router = APIRouter()

@router.get("/")
def dashboard(request: Request):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            from fastapi.responses import RedirectResponse
            return RedirectResponse("/login", status_code=303)

        today = now_local().date()
        next_7 = [today + timedelta(days=i) for i in range(7)]
        shift_types = db.query(ShiftType).filter(ShiftType.active == True).order_by(ShiftType.name.asc()).all()

        entries = (
            db.query(RotaEntry)
            .filter(RotaEntry.shift_date.in_(next_7))
            .all()
        )
        # map (date, shift_type_id) -> entry
        entry_map = {(e.shift_date, e.shift_type_id): e for e in entries}

        # Who is on call today: list of shift types and staff assigned
        today_items = []
        for st in shift_types:
            e = entry_map.get((today, st.id))
            staff = None
            if e and e.staff_id:
                staff = db.query(Staff).filter(Staff.id == e.staff_id).first()
            today_items.append({"shift_type": st, "entry": e, "staff": staff})

        return request.app.state.templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": user,
                "today": today,
                "next_7": next_7,
                "shift_types": shift_types,
                "entry_map": entry_map,
                "today_items": today_items,
            },
        )
    finally:
        db.close()
