from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(default="", max_length=120)


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class WatchlistItemIn(BaseModel):
    symbol: str
    notes: str = ""


class WatchlistItemOut(BaseModel):
    id: int
    symbol: str
    notes: str
    quote: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True


class WatchlistOut(BaseModel):
    id: int
    name: str
    items: list[WatchlistItemOut] = []

    class Config:
        from_attributes = True


class WatchlistCreate(BaseModel):
    name: str = "Default"


class SavedBacktestIn(BaseModel):
    name: str
    symbol: str
    strategy: str
    params: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)


class SavedBacktestOut(BaseModel):
    id: int
    name: str
    symbol: str
    strategy: str
    params: dict[str, Any]
    result: dict[str, Any]
    created_at: datetime


class AlertIn(BaseModel):
    symbol: str
    condition: str = Field(pattern="^(above|below|pct_up|pct_down)$")
    threshold: float
    message: str = ""


class AlertOut(BaseModel):
    id: int
    symbol: str
    condition: str
    threshold: float
    active: bool
    triggered: bool
    message: str
    created_at: datetime
    triggered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaperOrderIn(BaseModel):
    symbol: str
    side: str = Field(pattern="^(buy|sell)$")
    shares: float = Field(gt=0)
    order_type: str = "market"


class PortfolioBacktestIn(BaseModel):
    symbols: list[str] = Field(min_length=1, max_length=12)
    weights: Optional[list[float]] = None
    strategy: str = "buy_and_hold"
    start: str
    end: str
    initial_capital: float = 100_000
    commission: float = 0.001
    params: dict[str, Any] = Field(default_factory=dict)


class AdvancedBacktestIn(BaseModel):
    symbol: str
    strategy: str
    start: str
    end: str
    initial_capital: float = 100_000
    commission: float = 0.001
    params: dict[str, Any] = Field(default_factory=dict)
    walk_forward_windows: int = Field(4, ge=2, le=12)
    monte_carlo_runs: int = Field(200, ge=50, le=2000)


class SharedStrategyIn(BaseModel):
    title: str
    description: str = ""
    strategy: str
    params: dict[str, Any] = Field(default_factory=dict)
    symbol_example: str = "SPY"


class SharedStrategyOut(BaseModel):
    id: int
    title: str
    description: str
    strategy: str
    params: dict[str, Any]
    symbol_example: str
    likes: int
    author: str
    created_at: datetime


class AIBriefIn(BaseModel):
    symbol: str
    include_news: bool = True


def dumps(data: Any) -> str:
    return json.dumps(data, default=str)


def loads(raw: str) -> Any:
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
