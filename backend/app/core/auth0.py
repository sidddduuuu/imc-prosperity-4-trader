from __future__ import annotations

import time
from functools import lru_cache
from typing import Any, Optional

import httpx
from jose import JWTError, jwt

from app.core.config import get_settings

_jwks_cache: dict[str, Any] = {"fetched_at": 0.0, "keys": None}
JWKS_TTL = 3600.0


def auth0_enabled() -> bool:
    settings = get_settings()
    return bool(settings.auth0_domain and settings.auth0_client_id)


def _issuer() -> str:
    domain = (get_settings().auth0_domain or "").rstrip("/")
    if domain.startswith("http"):
        return domain if domain.endswith("/") else f"{domain}/"
    return f"https://{domain}/"


def _jwks_url() -> str:
    return f"{_issuer()}.well-known/jwks.json"


def get_jwks() -> dict[str, Any]:
    now = time.time()
    if _jwks_cache["keys"] and now - float(_jwks_cache["fetched_at"]) < JWKS_TTL:
        return _jwks_cache["keys"]
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(_jwks_url())
        resp.raise_for_status()
        data = resp.json()
    _jwks_cache["keys"] = data
    _jwks_cache["fetched_at"] = now
    return data


def _rsa_key_for_token(token: str) -> dict[str, Any]:
    unverified = jwt.get_unverified_header(token)
    kid = unverified.get("kid")
    jwks = get_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    # refresh once if kid miss
    _jwks_cache["fetched_at"] = 0
    jwks = get_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    raise JWTError("Unable to find matching Auth0 JWKS key")


def verify_auth0_id_token(id_token: str) -> dict[str, Any]:
    """Validate Auth0 ID token (audience = client_id)."""
    settings = get_settings()
    if not auth0_enabled():
        raise JWTError("Auth0 is not configured")
    key = _rsa_key_for_token(id_token)
    return jwt.decode(
        id_token,
        key,
        algorithms=["RS256"],
        audience=settings.auth0_client_id,
        issuer=_issuer(),
        options={"verify_at_hash": False},
    )


def verify_auth0_access_token(access_token: str) -> dict[str, Any]:
    """Validate Auth0 access token when AUTH0_AUDIENCE is configured."""
    settings = get_settings()
    if not auth0_enabled() or not settings.auth0_audience:
        raise JWTError("Auth0 API audience is not configured")
    key = _rsa_key_for_token(access_token)
    return jwt.decode(
        access_token,
        key,
        algorithms=["RS256"],
        audience=settings.auth0_audience,
        issuer=_issuer(),
    )


@lru_cache
def auth0_issuer() -> Optional[str]:
    if not auth0_enabled():
        return None
    return _issuer()
