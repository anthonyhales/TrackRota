from __future__ import annotations
from typing import Optional
from fastapi import Request
from sqlalchemy.orm import Session
from itsdangerous import URLSafeSerializer
import os

from .models import User

SESSION_KEY = "session"

def _serializer() -> URLSafeSerializer:
    secret = os.getenv("APP_SESSION_SECRET", "dev-only-change-me")
    return URLSafeSerializer(secret_key=secret, salt="oncall-rota")

def sign_session(data: dict) -> str:
    return _serializer().dumps(data)

def unsign_session(token: str) -> dict | None:
    try:
        return _serializer().loads(token)
    except Exception:
        return None

def get_current_user(request: Request, db: Session) -> Optional[User]:
    token = request.cookies.get("oncall_session")
    if not token:
        return None
    data = unsign_session(token)
    if not data:
        return None
    user_id = data.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == int(user_id), User.active == True).first()
    return user

def require_role(user: User | None, roles: set[str]) -> bool:
    if not user:
        return False
    return user.role in roles
