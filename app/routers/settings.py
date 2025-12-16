import os
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("")
def settings_page(request: Request):
    db: Session = SessionLocal()
    try:
        user = get_current_user(request, db)
        if not user:
            return RedirectResponse("/login", status_code=303)
        if not require_role(user, {"Admin"}):
            return RedirectResponse("/", status_code=303)

        org_name = os.getenv("APP_ORG_NAME", "Your Organisation")
        tz = os.getenv("APP_TIMEZONE", "Europe/London")
        return request.app.state.templates.TemplateResponse("settings.html", {"request": request, "user": user, "org_name": org_name, "tz": tz})
    finally:
        db.close()

@router.post("")
def update_settings(request: Request, org_name: str = Form(...), timezone: str = Form(...)):
    # For ALPHA v1 we store settings in environment variables; next version will store in DB.
    # This endpoint simply redirects with a note.
    return RedirectResponse("/settings?note=Settings+are+environment-based+in+ALPHA+v1", status_code=303)
