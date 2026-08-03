from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def ema(series: pd.Series, window: int) -> pd.Series:
    return series.ewm(span=window, adjust=False).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(
    series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def bollinger(
    series: pd.Series, window: int = 20, num_std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    mid = sma(series, window)
    std = series.rolling(window=window, min_periods=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=window, min_periods=window).mean()


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["sma_20"] = sma(out["close"], 20)
    out["sma_50"] = sma(out["close"], 50)
    out["sma_200"] = sma(out["close"], 200)
    out["ema_12"] = ema(out["close"], 12)
    out["ema_26"] = ema(out["close"], 26)
    out["rsi_14"] = rsi(out["close"], 14)
    macd_line, signal_line, hist = macd(out["close"])
    out["macd"] = macd_line
    out["macd_signal"] = signal_line
    out["macd_hist"] = hist
    upper, mid, lower = bollinger(out["close"])
    out["bb_upper"] = upper
    out["bb_mid"] = mid
    out["bb_lower"] = lower
    out["atr_14"] = atr(out)
    return out


def indicator_summary(df: pd.DataFrame) -> dict[str, Any]:
    latest = df.dropna(subset=["close"]).iloc[-1]
    close = float(latest["close"])

    rsi_val = float(latest.get("rsi_14") or 50)
    if rsi_val >= 70:
        rsi_signal = "overbought"
    elif rsi_val <= 30:
        rsi_signal = "oversold"
    else:
        rsi_signal = "neutral"

    sma50 = latest.get("sma_50")
    sma200 = latest.get("sma_200")
    trend = "neutral"
    if pd.notna(sma50) and pd.notna(sma200):
        if close > float(sma50) > float(sma200):
            trend = "bullish"
        elif close < float(sma50) < float(sma200):
            trend = "bearish"

    macd_hist = latest.get("macd_hist")
    macd_bias = "neutral"
    if pd.notna(macd_hist):
        macd_bias = "bullish" if float(macd_hist) > 0 else "bearish"

    return {
        "price": round(close, 4),
        "rsi": round(rsi_val, 2),
        "rsi_signal": rsi_signal,
        "trend": trend,
        "macd_bias": macd_bias,
        "sma_20": _round_or_none(latest.get("sma_20")),
        "sma_50": _round_or_none(latest.get("sma_50")),
        "sma_200": _round_or_none(latest.get("sma_200")),
        "atr_14": _round_or_none(latest.get("atr_14")),
        "bb_upper": _round_or_none(latest.get("bb_upper")),
        "bb_lower": _round_or_none(latest.get("bb_lower")),
    }


def _round_or_none(value, ndigits: int = 4):
    try:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None
        if pd.isna(value):
            return None
        return round(float(value), ndigits)
    except (TypeError, ValueError):
        return None
