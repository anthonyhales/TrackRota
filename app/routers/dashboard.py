from datetime import timedelta
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..auth import get_current_user
from ..models import Rota, ShiftType, RotaEntry, Staff
from ..utils import now_local

router = APIRouter()


def is_favourite(user, rota_id: int) -> bool:
    """
    Safe helper: user.favourite_rotas is a JSON list of rota IDs
    """
    if not user or not user.favourite_rotas:
        return False
    return rota_id in user.favourite_rotas


@router.get("/")
def dashboard(request: Request):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)

        today = now_local().date()
        next_7 = [today + timedelta(days=i) for i in range(7)]

        # Load all active rotas
        rotas = (
            db.query(Rota)
            .filter(Rota.active == True)
            .order_by(Rota.name.asc())
            .all()
        )

        dashboard_rotas = []

        for rota in rotas:
            shift_types = (
                db.query(ShiftType)
                .filter(
                    ShiftType.active == True,
                    ShiftType.rota_id == rota.id,
                )
                .order_by(ShiftType.name.asc())
                .all()
            )

            entries = (
                db.query(RotaEntry)
                .filter(
                    RotaEntry.rota_id == rota.id,
                    RotaEntry.shift_date.in_(next_7),
                )
                .all()
            )

            entry_map = {(e.shift_date, e.shift_type_id): e for e in entries}

            today_items = []
            for st in shift_types:
                e = entry_map.get((today, st.id))
                staff = None
                if e and e.staff_id:
                    staff = (
                        db.query(Staff)
                        .filter(Staff.id == e.staff_id)
                        .first()
                    )

                today_items.append({
                    "shift_type": st,
                    "entry": e,
                    "staff": staff,
                })

            dashboard_rotas.append({
                "rota": rota,
                "is_favourite": is_favourite(user, rota.id),
                "today_items": today_items,
            })

        # Optional: favourites first
        dashboard_rotas.sort(
            key=lambda r: (not r["is_favourite"], r["rota"].name.lower())
        )

        return request.app.state.templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": user,
                "today": today,
                "dashboard_rotas": dashboard_rotas,
            },
        )

    finally:
        db.close()


@router.post("/rotas/{rota_id}/toggle-favourite")
def toggle_favourite(request: Request, rota_id: int):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)

        favs = user.favourite_rotas or []

        if rota_id in favs:
            favs.remove(rota_id)
        else:
            favs.append(rota_id)

        user.favourite_rotas = favs
        db.commit()

        return RedirectResponse("/", status_code=303)

    finally:
        db.close()
