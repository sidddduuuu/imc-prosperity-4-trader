from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.auth0 import auth0_enabled, verify_auth0_access_token, verify_auth0_id_token
from app.core.config import get_settings
from app.db import models
from app.db.session import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# Sentinel for Auth0-only accounts — never a valid bcrypt hash, so local password login fails closed.
AUTH0_PASSWORD_PLACEHOLDER = "!"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email.lower()).first()


def get_user_by_auth0_sub(db: Session, sub: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.auth0_sub == sub).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    user = get_user_by_email(db, email)
    if (
        not user
        or not user.hashed_password
        or user.hashed_password == AUTH0_PASSWORD_PLACEHOLDER
        or not verify_password(password, user.hashed_password)
    ):
        return None
    return user


def upsert_auth0_user(
    db: Session,
    *,
    sub: str,
    email: str,
    name: str = "",
) -> models.User:
    email = email.lower()
    user = get_user_by_auth0_sub(db, sub) or get_user_by_email(db, email)
    if user:
        user.auth0_sub = sub
        user.email = email
        if name:
            user.name = name
        # Older SQLite schemas still enforce NOT NULL on hashed_password
        if not user.hashed_password:
            user.hashed_password = AUTH0_PASSWORD_PLACEHOLDER
    else:
        user = models.User(
            email=email,
            name=name or email.split("@")[0],
            hashed_password=AUTH0_PASSWORD_PLACEHOLDER,
            auth0_sub=sub,
        )
        db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_current_user_optional(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> Optional[models.User]:
    if not token:
        return None
    settings = get_settings()

    # 1) Atlas HS256 session JWT
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str | None = payload.get("sub")
        if email:
            return get_user_by_email(db, email)
    except JWTError:
        pass

    # 2) Auth0 access token (API audience)
    if auth0_enabled() and settings.auth0_audience:
        try:
            claims = verify_auth0_access_token(token)
            sub = claims.get("sub")
            email = claims.get("email") or claims.get("https://atlas/email")
            if sub:
                user = get_user_by_auth0_sub(db, sub)
                if user:
                    return user
                if email:
                    return upsert_auth0_user(
                        db,
                        sub=sub,
                        email=email,
                        name=claims.get("name") or "",
                    )
        except JWTError:
            pass

    # 3) Auth0 ID token (audience = client id)
    if auth0_enabled():
        try:
            claims = verify_auth0_id_token(token)
            sub = claims.get("sub")
            email = claims.get("email")
            if sub and email:
                return upsert_auth0_user(
                    db,
                    sub=sub,
                    email=email,
                    name=claims.get("name") or "",
                )
        except JWTError:
            pass

    return None


def get_current_user(
    user: Annotated[Optional[models.User], Depends(get_current_user_optional)],
) -> models.User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user
