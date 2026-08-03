from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_user_by_email,
    hash_password,
)
from app.db import models
from app.db.session import get_db
from app.models.terminal import TokenOut, UserCreate, UserOut
from app.services.paper import get_or_create_paper_account

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
def register(body: UserCreate, db: Annotated[Session, Depends(get_db)]):
    if get_user_by_email(db, body.email):
        raise HTTPException(400, "Email already registered")
    user = models.User(
        email=body.email.lower(),
        name=body.name or body.email.split("@")[0],
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    get_or_create_paper_account(db, user)
    token = create_access_token(user.email)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.email)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: Annotated[models.User, Depends(get_current_user)]):
    return user


@router.get("/config")
def public_config():
    settings = get_settings()
    return {
        "app": settings.app_name,
        "environment": settings.environment,
        "disclaimer": settings.disclaimer,
        "features": {
            "auth": True,
            "watchlists": True,
            "screener": True,
            "alerts": True,
            "paper_trading": True,
            "portfolio_backtest": True,
            "walk_forward": True,
            "monte_carlo": True,
            "community": True,
            "ai_briefs": bool(settings.openrouter_api_key or settings.fireworks_api_key),
            "websocket_quotes": True,
        },
        "market_data_provider": settings.market_data_provider,
    }
