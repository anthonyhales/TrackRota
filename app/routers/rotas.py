from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..auth import get_current_user, require_role
from ..models import Rota

router = APIRouter(prefix="/rotas", tags=["rotas"])


@router.get("")
def list_rotas(request: Request):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user or not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/", status_code=303)

        rotas = db.query(Rota).order_by(Rota.active.desc(), Rota.name.asc()).all()

        return request.app.state.templates.TemplateResponse(
            "rotas.html",
            {
                "request": request,
                "user": user,
                "rotas": rotas,
            },
        )
    finally:
        db.close()


@router.post("/new")
def create_rota(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    active: str = Form("on"),
):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user or not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/", status_code=303)

        db.add(
            Rota(
                name=name.strip(),
                description=description.strip() or None,
                active=(active == "on"),
            )
        )
        db.commit()
        return RedirectResponse("/rotas", status_code=303)
    finally:
        db.close()


@router.post("/{rota_id}")
def update_rota(
    request: Request,
    rota_id: int,
    name: str = Form(...),
    description: str = Form(""),
    active: str = Form(None),
):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user or not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/", status_code=303)

        rota = db.query(Rota).filter(Rota.id == rota_id).first()
        if rota:
            rota.name = name.strip()
            rota.description = description.strip() or None
            rota.active = (active == "on")
            db.commit()

        return RedirectResponse("/rotas", status_code=303)
    finally:
        db.close()
