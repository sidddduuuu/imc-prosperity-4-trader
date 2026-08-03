from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.api import router

app = FastAPI(
    title="Atlas",
    description="All-in-one stock analysis and strategy backtesting platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "Atlas",
        "tagline": "Every signal. One terminal.",
        "docs": "/docs",
    }
