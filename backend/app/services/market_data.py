from __future__ import annotations

from functools import lru_cache
from typing import Optional

import pandas as pd
import yfinance as yf


def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper()


def fetch_history(
    symbol: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    symbol = normalize_symbol(symbol)
    ticker = yf.Ticker(symbol)

    if start or end:
        df = ticker.history(start=start, end=end, interval=interval, auto_adjust=True)
    else:
        df = ticker.history(period=period, interval=interval, auto_adjust=True)

    if df.empty:
        raise ValueError(f"No price data found for {symbol}")

    df = df.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )
    df = df[["open", "high", "low", "close", "volume"]].copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df = df.dropna()
    return df


def fetch_quote(symbol: str) -> dict:
    symbol = normalize_symbol(symbol)
    ticker = yf.Ticker(symbol)
    info = ticker.info or {}
    fast = ticker.fast_info

    price = float(getattr(fast, "last_price", None) or info.get("currentPrice") or info.get("regularMarketPrice") or 0)
    prev = float(
        getattr(fast, "previous_close", None)
        or info.get("previousClose")
        or info.get("regularMarketPreviousClose")
        or price
    )
    change = price - prev
    change_pct = (change / prev * 100) if prev else 0.0

    return {
        "symbol": symbol,
        "name": info.get("shortName") or info.get("longName") or symbol,
        "price": round(price, 4),
        "change": round(change, 4),
        "change_percent": round(change_pct, 4),
        "open": _opt_float(info.get("open") or info.get("regularMarketOpen")),
        "high": _opt_float(info.get("dayHigh") or info.get("regularMarketDayHigh")),
        "low": _opt_float(info.get("dayLow") or info.get("regularMarketDayLow")),
        "previous_close": round(prev, 4),
        "volume": _opt_int(info.get("volume") or info.get("regularMarketVolume")),
        "market_cap": _opt_float(info.get("marketCap") or getattr(fast, "market_cap", None)),
        "pe_ratio": _opt_float(info.get("trailingPE")),
        "eps": _opt_float(info.get("trailingEps")),
        "fifty_two_week_high": _opt_float(info.get("fiftyTwoWeekHigh")),
        "fifty_two_week_low": _opt_float(info.get("fiftyTwoWeekLow")),
        "dividend_yield": _dividend_yield(info),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "currency": info.get("currency") or "USD",
    }


def search_symbols(query: str, limit: int = 8) -> list[dict]:
    """Lightweight symbol search via Yahoo autocomplete."""
    import httpx

    q = query.strip()
    if not q:
        return []

    url = "https://query1.finance.yahoo.com/v1/finance/search"
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.get(url, params={"q": q, "quotesCount": limit, "newsCount": 0})
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []

    results = []
    for item in data.get("quotes", []):
        if item.get("quoteType") not in {"EQUITY", "ETF", "INDEX", "CRYPTOCURRENCY"}:
            continue
        results.append(
            {
                "symbol": item.get("symbol"),
                "name": item.get("shortname") or item.get("longname") or item.get("symbol"),
                "exchange": item.get("exchDisp") or item.get("exchange"),
                "type": item.get("quoteType"),
            }
        )
    return results[:limit]


@lru_cache(maxsize=32)
def popular_symbols() -> tuple[str, ...]:
    return (
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "NVDA",
        "META",
        "TSLA",
        "SPY",
        "QQQ",
        "IWM",
        "AMD",
        "JPM",
    )


def _opt_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _opt_int(value) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _dividend_yield(info: dict) -> Optional[float]:
    """Return dividend yield as a fraction (0.012 = 1.2%)."""
    for key in ("trailingAnnualDividendYield", "yield", "dividendYield"):
        raw = _opt_float(info.get(key))
        if raw is None:
            continue
        # Some Yahoo fields arrive as percent points (e.g. 1.01 => 1.01%).
        if key == "dividendYield" and raw > 0.2:
            return round(raw / 100.0, 6)
        return round(raw, 6)
    return None
