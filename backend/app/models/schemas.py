from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class StrategyType(str, Enum):
    SMA_CROSSOVER = "sma_crossover"
    EMA_CROSSOVER = "ema_crossover"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER = "bollinger"
    BUY_AND_HOLD = "buy_and_hold"
    MEAN_REVERSION = "mean_reversion"


class BacktestRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=12, examples=["AAPL"])
    strategy: StrategyType = StrategyType.SMA_CROSSOVER
    start: str = Field(..., description="YYYY-MM-DD", examples=["2023-01-01"])
    end: str = Field(..., description="YYYY-MM-DD", examples=["2024-12-31"])
    initial_capital: float = Field(100_000, gt=0)
    commission: float = Field(0.001, ge=0, le=0.05)
    params: dict[str, Any] = Field(default_factory=dict)


class TradeRecord(BaseModel):
    date: str
    side: str
    price: float
    shares: float
    value: float
    commission: float


class EquityPoint(BaseModel):
    date: str
    equity: float
    buy_hold: float
    drawdown: float


class BacktestMetrics(BaseModel):
    total_return: float
    buy_hold_return: float
    alpha: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_return: float
    volatility: float
    final_equity: float
    initial_capital: float


class BacktestResult(BaseModel):
    symbol: str
    strategy: str
    params: dict[str, Any]
    metrics: BacktestMetrics
    equity_curve: list[EquityPoint]
    trades: list[TradeRecord]
    signals: list[dict[str, Any]]


class QuoteResponse(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    previous_close: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    dividend_yield: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    currency: str = "USD"


class Candle(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class HistoryResponse(BaseModel):
    symbol: str
    interval: str
    candles: list[Candle]


class NewsItem(BaseModel):
    title: str
    summary: str
    link: str
    published: str
    source: str
    symbol: Optional[str] = None
    sentiment: Optional[str] = None


class IndicatorPoint(BaseModel):
    time: str
    values: dict[str, float]


class AnalysisResponse(BaseModel):
    symbol: str
    indicators: list[IndicatorPoint]
    summary: dict[str, Any]


class StrategyInfo(BaseModel):
    id: str
    name: str
    description: str
    params: list[dict[str, Any]]
