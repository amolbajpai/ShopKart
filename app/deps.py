from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_token


def _extract_access_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return request.cookies.get("access_token")


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = _extract_access_token(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(token, "access")
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = _extract_access_token(request)
    if not token:
        return None
    try:
        payload = decode_token(token, "access")
        user = db.get(User, int(payload["sub"]))
        if user and user.is_active:
            return user
    except HTTPException:
        return None
    return None


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user
