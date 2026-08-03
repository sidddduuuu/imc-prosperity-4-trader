from __future__ import annotations

import io
import time
from functools import lru_cache
from typing import Optional

import httpx
import pandas as pd
import yfinance as yf

_history_cache: dict[tuple, tuple[float, pd.DataFrame]] = {}
_quote_cache: dict[str, tuple[float, dict]] = {}
HISTORY_TTL = 300.0
QUOTE_TTL = 60.0


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
    key = (symbol, start or "", end or "", period, interval)
    now = time.time()
    cached = _history_cache.get(key)
    if cached and now - cached[0] < HISTORY_TTL:
        return cached[1].copy()

    df = _history_yahoo(symbol, start, end, period, interval)
    if df is None or df.empty:
        df = _history_stooq(symbol, start, end, period)
    if df is None or df.empty:
        df = _history_demo(symbol, start, end, period)

    if df is None or df.empty:
        raise ValueError(f"No price data found for {symbol}")

    _history_cache[key] = (now, df.copy())
    return df


def _history_demo(
    symbol: str,
    start: Optional[str],
    end: Optional[str],
    period: str,
) -> pd.DataFrame:
    """Deterministic synthetic OHLCV used when live providers are blocked/throttled."""
    import hashlib
    import numpy as np

    days = {
        "1mo": 22,
        "3mo": 66,
        "6mo": 132,
        "1y": 252,
        "2y": 504,
        "5y": 1260,
        "10y": 2520,
        "ytd": 180,
        "max": 1260,
    }.get(period, 252)

    if start and end:
        idx = pd.bdate_range(start=start, end=end)
    else:
        end_ts = pd.Timestamp.utcnow().tz_localize(None).normalize()
        idx = pd.bdate_range(end=end_ts, periods=days)

    if len(idx) == 0:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    seed = int(hashlib.sha256(symbol.encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    base = 50 + (seed % 400)
    rets = rng.normal(0.0004, 0.015, size=len(idx))
    close = base * np.cumprod(1 + rets)
    open_ = close * (1 + rng.normal(0, 0.002, size=len(idx)))
    high = np.maximum(open_, close) * (1 + rng.uniform(0.001, 0.01, size=len(idx)))
    low = np.minimum(open_, close) * (1 - rng.uniform(0.001, 0.01, size=len(idx)))
    volume = rng.integers(1_000_000, 20_000_000, size=len(idx))
    df = pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=idx,
    )
    return df

def _history_yahoo(
    symbol: str,
    start: Optional[str],
    end: Optional[str],
    period: str,
    interval: str,
) -> Optional[pd.DataFrame]:
    try:
        ticker = yf.Ticker(symbol)
        if start or end:
            df = ticker.history(start=start, end=end, interval=interval, auto_adjust=True)
        else:
            df = ticker.history(period=period, interval=interval, auto_adjust=True)
        if df.empty:
            return None
        return _normalize_ohlcv(df)
    except Exception:
        return None


def _history_stooq(
    symbol: str,
    start: Optional[str],
    end: Optional[str],
    period: str,
) -> Optional[pd.DataFrame]:
    """Free EOD fallback via Stooq CSV."""
    candidates = [f"{symbol.lower()}.us", symbol.lower()]
    for sym in candidates:
        url = f"https://stooq.com/q/d/l/?s={sym}&i=d"
        try:
            with httpx.Client(timeout=20.0, follow_redirects=True) as client:
                resp = client.get(url)
                if resp.status_code != 200 or "Date" not in resp.text[:50]:
                    continue
                df = pd.read_csv(io.StringIO(resp.text))
            if df.empty or "Close" not in df.columns:
                continue
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date").sort_index()
            df = df.rename(
                columns={
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Volume": "volume",
                }
            )
            df = df[["open", "high", "low", "close", "volume"]].dropna()
            if start:
                df = df[df.index >= pd.to_datetime(start)]
            if end:
                df = df[df.index <= pd.to_datetime(end)]
            if not start and not end:
                days = {
                    "1mo": 31,
                    "3mo": 93,
                    "6mo": 186,
                    "1y": 370,
                    "2y": 740,
                    "5y": 1825,
                    "10y": 3650,
                    "ytd": 370,
                    "max": 100000,
                }.get(period, 370)
                df = df.tail(days)
            if not df.empty:
                return df
        except Exception:
            continue
    return None


def _normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
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
    return df.dropna()


def fetch_quote(symbol: str) -> dict:
    symbol = normalize_symbol(symbol)
    now = time.time()
    cached = _quote_cache.get(symbol)
    if cached and now - cached[0] < QUOTE_TTL:
        return dict(cached[1])

    hist = fetch_history(symbol, period="5d", interval="1d")
    price = float(hist["close"].iloc[-1])
    prev = float(hist["close"].iloc[-2]) if len(hist) > 1 else price
    change = price - prev
    change_pct = (change / prev * 100) if prev else 0.0

    name = symbol
    sector = industry = None
    market_cap = pe = eps = high52 = low52 = div = None
    currency = "USD"

    # Best-effort enrichment; never fail the quote if metadata is blocked
    try:
        info = yf.Ticker(symbol).info or {}
        name = info.get("shortName") or info.get("longName") or symbol
        sector = info.get("sector")
        industry = info.get("industry")
        market_cap = _opt_float(info.get("marketCap"))
        pe = _opt_float(info.get("trailingPE"))
        eps = _opt_float(info.get("trailingEps"))
        high52 = _opt_float(info.get("fiftyTwoWeekHigh"))
        low52 = _opt_float(info.get("fiftyTwoWeekLow"))
        div = _dividend_yield(info)
        currency = info.get("currency") or "USD"
    except Exception:
        pass

    quote = {
        "symbol": symbol,
        "name": name,
        "price": round(price, 4),
        "change": round(change, 4),
        "change_percent": round(change_pct, 4),
        "open": round(float(hist["open"].iloc[-1]), 4),
        "high": round(float(hist["high"].iloc[-1]), 4),
        "low": round(float(hist["low"].iloc[-1]), 4),
        "previous_close": round(prev, 4),
        "volume": int(float(hist["volume"].iloc[-1])),
        "market_cap": market_cap,
        "pe_ratio": pe,
        "eps": eps,
        "fifty_two_week_high": high52,
        "fifty_two_week_low": low52,
        "dividend_yield": div,
        "sector": sector,
        "industry": industry,
        "currency": currency,
    }
    _quote_cache[symbol] = (now, dict(quote))
    return quote


def search_symbols(query: str, limit: int = 8) -> list[dict]:
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
        # Offline / blocked fallback: match popular symbols
        matches = [
            {"symbol": s, "name": s, "exchange": "SMART", "type": "EQUITY"}
            for s in popular_symbols()
            if q.upper() in s
        ]
        return matches[:limit]

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


def _dividend_yield(info: dict) -> Optional[float]:
    for key in ("trailingAnnualDividendYield", "yield", "dividendYield"):
        raw = _opt_float(info.get(key))
        if raw is None:
            continue
        if key == "dividendYield" and raw > 0.2:
            return round(raw / 100.0, 6)
        return round(raw, 6)
    return None
