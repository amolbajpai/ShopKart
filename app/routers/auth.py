import secrets
from datetime import datetime

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import RefreshToken, User
from app.schemas import LoginIn, RefreshIn, RegisterIn, TokenPair, UserOut
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

oauth = OAuth()
if settings.google_client_id:
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
if settings.github_client_id:
    oauth.register(
        name="github",
        client_id=settings.github_client_id,
        client_secret=settings.github_client_secret,
        authorize_url="https://github.com/login/oauth/authorize",
        access_token_url="https://github.com/login/oauth/access_token",
        api_base_url="https://api.github.com/",
        client_kwargs={"scope": "user:email"},
    )


def _set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    response.set_cookie(
        "access_token",
        access,
        httponly=True,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    response.set_cookie(
        "refresh_token",
        refresh,
        httponly=True,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


def _issue_tokens(db: Session, user: User) -> TokenPair:
    access = create_access_token(user.id, user.email, user.is_admin)
    jti = secrets.token_hex(16)
    refresh, expires = create_refresh_token(user.id, jti)
    db.add(RefreshToken(user_id=user.id, token_hash=hash_token(refresh), expires_at=expires))
    db.commit()
    return TokenPair(access_token=access, refresh_token=refresh)


def _upsert_oauth_user(db: Session, email: str, name: str, provider: str, oauth_id: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.oauth_provider = provider
        user.oauth_id = oauth_id
        if name and not user.full_name:
            user.full_name = name
        db.commit()
        db.refresh(user)
        return user
    user = User(
        email=email,
        hashed_password=None,
        full_name=name or email.split("@")[0],
        oauth_provider=provider,
        oauth_id=oauth_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/register", response_model=TokenPair)
def register(payload: RegisterIn, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    tokens = _issue_tokens(db, user)
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return tokens


@router.post("/login", response_model=TokenPair)
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    tokens = _issue_tokens(db, user)
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return tokens


@router.post("/refresh", response_model=TokenPair)
def refresh(
    request: Request,
    response: Response,
    payload: RefreshIn = RefreshIn(),
    db: Session = Depends(get_db),
):
    raw = payload.refresh_token or request.cookies.get("refresh_token")
    if not raw:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    data = decode_token(raw, "refresh")
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_token(raw)).first()
    if not stored or stored.revoked or stored.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired")
    stored.revoked = True
    user = db.get(User, int(data["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    tokens = _issue_tokens(db, user)
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return tokens


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    raw = request.cookies.get("refresh_token")
    if raw:
        stored = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_token(raw)).first()
        if stored:
            stored.revoked = True
            db.commit()
    _clear_auth_cookies(response)
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/providers")
def providers():
    return {
        "google": bool(settings.google_client_id and settings.google_client_secret),
        "github": bool(settings.github_client_id and settings.github_client_secret),
    }


@router.get("/oauth/{provider}")
async def oauth_start(provider: str, request: Request):
    if provider not in ("google", "github"):
        raise HTTPException(status_code=404, detail="Unknown provider")
    client = oauth.create_client(provider)
    if client is None:
        raise HTTPException(status_code=400, detail=f"{provider.title()} OAuth is not configured")
    redirect_uri = f"{settings.oauth_redirect_base}/api/auth/oauth/{provider}/callback"
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, request: Request, db: Session = Depends(get_db)):
    if provider not in ("google", "github"):
        raise HTTPException(status_code=404, detail="Unknown provider")
    client = oauth.create_client(provider)
    if client is None:
        raise HTTPException(status_code=400, detail=f"{provider.title()} OAuth is not configured")
    token = await client.authorize_access_token(request)

    if provider == "google":
        info = token.get("userinfo") or await client.userinfo(token=token)
        email = info.get("email")
        name = info.get("name") or ""
        oauth_id = str(info.get("sub") or "")
    else:
        resp = await client.get("user", token=token)
        profile = resp.json()
        email = profile.get("email")
        if not email:
            emails = (await client.get("user/emails", token=token)).json()
            primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
            email = (primary or (emails[0] if emails else {})).get("email")
        name = profile.get("name") or profile.get("login") or ""
        oauth_id = str(profile.get("id") or "")

    if not email:
        raise HTTPException(status_code=400, detail="OAuth provider did not return an email")

    user = _upsert_oauth_user(db, email.lower(), name, provider, oauth_id)
    tokens = _issue_tokens(db, user)
    from starlette.responses import RedirectResponse

    redirect = RedirectResponse(url="/", status_code=302)
    _set_auth_cookies(redirect, tokens.access_token, tokens.refresh_token)
    return redirect
