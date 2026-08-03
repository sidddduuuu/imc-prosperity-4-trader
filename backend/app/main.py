from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.db.session import init_db
from app.routers.api import router as market_router
from app.routers.auth import router as auth_router
from app.routers.terminal import router as terminal_router

settings = get_settings()

app = FastAPI(
    title="Atlas",
    description="Production trading terminal — backtesting, charts, news, paper trading, and research",
    version="2.0.0",
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_rate_buckets: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/ws"):
        return await call_next(request)
    client = request.client.host if request.client else "unknown"
    now = time.time()
    bucket = _rate_buckets[client]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= settings.rate_limit_per_minute:
        return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
    bucket.append(now)
    return await call_next(request)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(market_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(terminal_router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "Atlas",
        "version": "2.0.0",
        "tagline": "Every signal. One terminal.",
        "docs": "/docs",
        "disclaimer": settings.disclaimer,
    }
