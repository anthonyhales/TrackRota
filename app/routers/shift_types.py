from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..auth import get_current_user, require_role
from ..models import Rota, ShiftType

router = APIRouter(prefix="/shift-types", tags=["shift-types"])


@router.get("")
def list_shift_types(
    request: Request,
    rota_id: int | None = Query(default=None),
):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/", status_code=303)

        # Load rotas
        rotas = (
            db.query(Rota)
            .filter(Rota.active == True)
            .order_by(Rota.name.asc())
            .all()
        )

        if not rotas:
            return RedirectResponse("/", status_code=303)

        # Resolve current rota
        if rota_id:
            current_rota = next((r for r in rotas if r.id == rota_id), None)
        else:
            current_rota = None

        if current_rota is None:
            current_rota = rotas[0]

        # Load shift types for rota
        items = (
            db.query(ShiftType)
            .filter(ShiftType.rota_id == current_rota.id)
            .order_by(ShiftType.active.desc(), ShiftType.name.asc())
            .all()
        )

        return request.app.state.templates.TemplateResponse(
            "shift_types.html",
            {
                "request": request,
                "user": user,
                "rotas": rotas,
                "current_rota": current_rota,
                "items": items,
            },
        )

    finally:
        db.close()


@router.post("/new")
def create_shift_type(
    request: Request,
    rota_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    active: str = Form("on"),
):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/", status_code=303)

        st = ShiftType(
            rota_id=rota_id,
            name=name.strip(),
            description=description.strip() or None,
            active=(active == "on"),
        )
        db.add(st)
        db.commit()

        return RedirectResponse(
            f"/shift-types?rota_id={rota_id}",
            status_code=303,
        )

    finally:
        db.close()


@router.post("/{shift_type_id}")
def update_shift_type(
    request: Request,
    shift_type_id: int,
    rota_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    active: str = Form(None),
):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)

        if not require_role(user, {"Admin", "Manager"}):
            return RedirectResponse("/", status_code=303)

        st = (
            db.query(ShiftType)
            .filter(
                ShiftType.id == shift_type_id,
                ShiftType.rota_id == rota_id,
            )
            .first()
        )

        if not st:
            return RedirectResponse("/shift-types", status_code=303)

        st.name = name.strip()
        st.description = description.strip() or None
        st.active = (active == "on")
        db.commit()

        return RedirectResponse(
            f"/shift-types?rota_id={rota_id}",
            status_code=303,
        )
    
    

    finally:
        db.close()

@router.post("/{shift_type_id}/delete")
def delete_shift_type(request: Request, shift_type_id: int):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)

        # 🔒 Admin only
        if user.role != "Admin":
            return RedirectResponse("/shift-types", status_code=303)

        st = db.query(ShiftType).filter(ShiftType.id == shift_type_id).first()
        if not st:
            return RedirectResponse("/shift-types", status_code=303)

        # Optional safety: block delete if used in rota
        in_use = db.query(Rota).filter(
            Rota.shift_type_id == shift_type_id
        ).first()
        if in_use:
            # You could flash a message later; for now just refuse
            return RedirectResponse("/shift-types", status_code=303)

        db.delete(st)
        db.commit()

        return RedirectResponse("/shift-types", status_code=303)
    finally:
        db.close()
