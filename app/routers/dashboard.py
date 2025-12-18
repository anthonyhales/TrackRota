from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..auth import get_current_user
from ..models import Rota
from ..utils import now_local

router = APIRouter()

@router.get("/")
def dashboard(request: Request):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # Load all active rotas
        rotas = (
            db.query(Rota)
            .filter(Rota.active == True)
            .order_by(Rota.name.asc())
            .all()
        )

        favourite_ids = user.favourite_rotas or []

        favourite_rotas = []
        other_rotas = []

        for rota in rotas:
            if rota.id in favourite_ids:
                favourite_rotas.append(rota)
            else:
                other_rotas.append(rota)

        return request.app.state.templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": user,
                "today": now_local().date(),
                "favourite_rotas": favourite_rotas,
                "other_rotas": other_rotas,
            },
        )

    finally:
        db.close()
