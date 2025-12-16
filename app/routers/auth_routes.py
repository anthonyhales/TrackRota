from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models import User
from ..security import verify_password
from ..auth import sign_session

router = APIRouter()

@router.get("/login")
def login_page(request: Request):
    return request.app.state.templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.lower().strip(), User.active == True).first()
        if not user or not verify_password(password, user.password_hash):
            return request.app.state.templates.TemplateResponse("login.html", {"request": request, "error": "Invalid email or password."})
        resp = RedirectResponse(url="/", status_code=303)
        resp.set_cookie(
            "oncall_session",
            sign_session({"user_id": user.id}),
            httponly=True,
            samesite="lax",
        )
        return resp
    finally:
        db.close()

@router.post("/logout")
def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie("oncall_session")
    return resp
