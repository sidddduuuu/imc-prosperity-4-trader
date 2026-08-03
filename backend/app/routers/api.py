from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    AnalysisResponse,
    BacktestRequest,
    BacktestResult,
    Candle,
    HistoryResponse,
    IndicatorPoint,
    NewsItem,
    QuoteResponse,
    StrategyInfo,
)
from app.services.backtester import run_backtest
from app.services.indicators import compute_indicators, indicator_summary
from app.services.market_data import fetch_history, fetch_quote, popular_symbols, search_symbols
from app.services.news import fetch_general_news, fetch_symbol_news
from app.services.strategies import STRATEGY_CATALOG

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "service": "atlas"}


@router.get("/strategies", response_model=list[StrategyInfo])
def list_strategies():
    return STRATEGY_CATALOG


@router.post("/backtest", response_model=BacktestResult)
def backtest(req: BacktestRequest):
    try:
        df = fetch_history(req.symbol, start=req.start, end=req.end)
        result = run_backtest(
            df,
            strategy=req.strategy.value,
            params=req.params,
            initial_capital=req.initial_capital,
            commission=req.commission,
        )
        return {
            "symbol": req.symbol.upper(),
            "strategy": req.strategy.value,
            **result,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Backtest failed: {exc}") from exc


@router.get("/quote/{symbol}", response_model=QuoteResponse)
def quote(symbol: str):
    try:
        return fetch_quote(symbol)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Quote unavailable: {exc}") from exc


@router.get("/history/{symbol}", response_model=HistoryResponse)
def history(
    symbol: str,
    period: str = Query("1y", pattern="^(1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$"),
    interval: str = Query("1d", pattern="^(1d|1wk|1mo)$"),
    start: str | None = None,
    end: str | None = None,
):
    try:
        df = fetch_history(symbol, start=start, end=end, period=period, interval=interval)
        candles = [
            Candle(
                time=ts.strftime("%Y-%m-%d"),
                open=round(float(row.open), 4),
                high=round(float(row.high), 4),
                low=round(float(row.low), 4),
                close=round(float(row.close), 4),
                volume=float(row.volume),
            )
            for ts, row in df.iterrows()
        ]
        return HistoryResponse(symbol=symbol.upper(), interval=interval, candles=candles)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"History fetch failed: {exc}") from exc


@router.get("/news", response_model=list[NewsItem])
def news(symbol: str | None = None, limit: int = Query(30, ge=1, le=100)):
    try:
        if symbol:
            return fetch_symbol_news(symbol, limit=limit)
        return fetch_general_news(limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"News fetch failed: {exc}") from exc


@router.get("/analysis/{symbol}", response_model=AnalysisResponse)
def analysis(
    symbol: str,
    period: str = Query("1y", pattern="^(3mo|6mo|1y|2y|5y)$"),
):
    try:
        df = fetch_history(symbol, period=period, interval="1d")
        enriched = compute_indicators(df)
        points: list[IndicatorPoint] = []
        cols = [
            "sma_20",
            "sma_50",
            "sma_200",
            "rsi_14",
            "macd",
            "macd_signal",
            "macd_hist",
            "bb_upper",
            "bb_mid",
            "bb_lower",
            "atr_14",
            "close",
        ]
        for ts, row in enriched.iterrows():
            values = {}
            for col in cols:
                val = row.get(col)
                if val is not None and val == val:  # not NaN
                    values[col] = round(float(val), 4)
            if values:
                points.append(IndicatorPoint(time=ts.strftime("%Y-%m-%d"), values=values))
        return AnalysisResponse(
            symbol=symbol.upper(),
            indicators=points,
            summary=indicator_summary(enriched),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Analysis failed: {exc}") from exc


@router.get("/search")
def search(q: str = Query(..., min_length=1), limit: int = Query(8, ge=1, le=20)):
    return search_symbols(q, limit=limit)


@router.get("/popular")
def popular():
    quotes = []
    for sym in popular_symbols():
        try:
            quotes.append(fetch_quote(sym))
        except Exception:
            continue
    return quotes
