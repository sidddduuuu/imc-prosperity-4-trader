from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from app.services.indicators import compute_indicators
from app.services.market_data import fetch_history, popular_symbols


SCREENER_UNIVERSE = list(popular_symbols()) + [
    "NFLX",
    "CRM",
    "AVGO",
    "XOM",
    "V",
    "BAC",
]


def run_screener(
    min_price: float | None = None,
    max_price: float | None = None,
    min_change_pct: float | None = None,
    trend: str | None = None,
    rsi_max: float | None = None,
    rsi_min: float | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    import time

    rows: list[dict[str, Any]] = []
    for sym in SCREENER_UNIVERSE:
        try:
            hist = fetch_history(sym, period="6mo")
            enriched = compute_indicators(hist)
            latest = enriched.iloc[-1]
            close = float(latest["close"])
            prev = float(enriched["close"].iloc[-2]) if len(enriched) > 1 else close
            change_pct = (close / prev - 1) * 100 if prev else 0.0
            rsi_val = float(latest["rsi_14"]) if pd.notna(latest.get("rsi_14")) else None
            sma50 = float(latest["sma_50"]) if pd.notna(latest.get("sma_50")) else None
            sma200 = float(latest["sma_200"]) if pd.notna(latest.get("sma_200")) else None

            row_trend = "neutral"
            if sma50 and sma200:
                if close > sma50 > sma200:
                    row_trend = "bullish"
                elif close < sma50 < sma200:
                    row_trend = "bearish"

            if min_price is not None and close < min_price:
                continue
            if max_price is not None and close > max_price:
                continue
            if min_change_pct is not None and change_pct < min_change_pct:
                continue
            if trend and row_trend != trend:
                continue
            if rsi_max is not None and (rsi_val is None or rsi_val > rsi_max):
                continue
            if rsi_min is not None and (rsi_val is None or rsi_val < rsi_min):
                continue

            # lightweight quote fields from history to avoid Yahoo quoteSummary spam
            rows.append(
                {
                    "symbol": sym,
                    "name": sym,
                    "price": round(close, 4),
                    "change_percent": round(change_pct, 4),
                    "volume": float(latest["volume"]),
                    "market_cap": None,
                    "pe_ratio": None,
                    "rsi": round(rsi_val, 2) if rsi_val is not None else None,
                    "trend": row_trend,
                    "sector": None,
                }
            )
            time.sleep(0.15)
        except Exception:
            continue

    rows.sort(key=lambda r: r["change_percent"], reverse=True)
    return rows[:limit]


def evaluate_alert(condition: str, threshold: float, price: float, prev_close: float | None) -> bool:
    if condition == "above":
        return price >= threshold
    if condition == "below":
        return price <= threshold
    if condition == "pct_up" and prev_close:
        return ((price - prev_close) / prev_close) * 100 >= threshold
    if condition == "pct_down" and prev_close:
        return ((prev_close - price) / prev_close) * 100 >= threshold
    return False
