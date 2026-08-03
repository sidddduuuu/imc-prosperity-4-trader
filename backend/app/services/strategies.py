from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.services.indicators import bollinger, ema, macd, rsi, sma


STRATEGY_CATALOG: list[dict[str, Any]] = [
    {
        "id": "sma_crossover",
        "name": "SMA Crossover",
        "description": "Go long when the fast SMA crosses above the slow SMA; exit on the opposite cross.",
        "params": [
            {"name": "fast", "label": "Fast SMA", "type": "int", "default": 20, "min": 2, "max": 100},
            {"name": "slow", "label": "Slow SMA", "type": "int", "default": 50, "min": 5, "max": 300},
        ],
    },
    {
        "id": "ema_crossover",
        "name": "EMA Crossover",
        "description": "Trend-following entry using exponential moving average crosses.",
        "params": [
            {"name": "fast", "label": "Fast EMA", "type": "int", "default": 12, "min": 2, "max": 100},
            {"name": "slow", "label": "Slow EMA", "type": "int", "default": 26, "min": 5, "max": 300},
        ],
    },
    {
        "id": "rsi",
        "name": "RSI Mean Reversion",
        "description": "Buy when RSI is oversold; sell when RSI is overbought.",
        "params": [
            {"name": "window", "label": "RSI Window", "type": "int", "default": 14, "min": 2, "max": 50},
            {"name": "oversold", "label": "Oversold", "type": "int", "default": 30, "min": 5, "max": 45},
            {"name": "overbought", "label": "Overbought", "type": "int", "default": 70, "min": 55, "max": 95},
        ],
    },
    {
        "id": "macd",
        "name": "MACD Signal Cross",
        "description": "Enter long when MACD crosses above its signal line; exit on cross below.",
        "params": [
            {"name": "fast", "label": "Fast", "type": "int", "default": 12, "min": 2, "max": 50},
            {"name": "slow", "label": "Slow", "type": "int", "default": 26, "min": 5, "max": 100},
            {"name": "signal", "label": "Signal", "type": "int", "default": 9, "min": 2, "max": 40},
        ],
    },
    {
        "id": "bollinger",
        "name": "Bollinger Bounce",
        "description": "Buy near the lower band and exit near the upper band.",
        "params": [
            {"name": "window", "label": "Window", "type": "int", "default": 20, "min": 5, "max": 100},
            {"name": "num_std", "label": "Std Devs", "type": "float", "default": 2.0, "min": 1.0, "max": 4.0},
        ],
    },
    {
        "id": "mean_reversion",
        "name": "Z-Score Mean Reversion",
        "description": "Fade moves when price is a set number of standard deviations from its mean.",
        "params": [
            {"name": "window", "label": "Lookback", "type": "int", "default": 20, "min": 5, "max": 100},
            {"name": "entry_z", "label": "Entry Z", "type": "float", "default": 1.5, "min": 0.5, "max": 4.0},
            {"name": "exit_z", "label": "Exit Z", "type": "float", "default": 0.25, "min": 0.0, "max": 2.0},
        ],
    },
    {
        "id": "buy_and_hold",
        "name": "Buy & Hold",
        "description": "Buy on the first bar and hold through the end of the period.",
        "params": [],
    },
]


def generate_signals(df: pd.DataFrame, strategy: str, params: dict[str, Any] | None = None) -> pd.Series:
    """Return a position series in {0, 1} aligned to df index."""
    params = params or {}
    close = df["close"]

    if strategy == "sma_crossover":
        fast = int(params.get("fast", 20))
        slow = int(params.get("slow", 50))
        if fast >= slow:
            slow = fast + 1
        f = sma(close, fast)
        s = sma(close, slow)
        signal = (f > s).astype(int)
        signal[f.isna() | s.isna()] = 0
        return signal

    if strategy == "ema_crossover":
        fast = int(params.get("fast", 12))
        slow = int(params.get("slow", 26))
        if fast >= slow:
            slow = fast + 1
        f = ema(close, fast)
        s = ema(close, slow)
        signal = (f > s).astype(int)
        signal[f.isna() | s.isna()] = 0
        return signal

    if strategy == "rsi":
        window = int(params.get("window", 14))
        oversold = float(params.get("oversold", 30))
        overbought = float(params.get("overbought", 70))
        r = rsi(close, window)
        position = pd.Series(0, index=df.index, dtype=int)
        holding = False
        for i, val in enumerate(r):
            if np.isnan(val):
                continue
            if not holding and val <= oversold:
                holding = True
            elif holding and val >= overbought:
                holding = False
            position.iloc[i] = 1 if holding else 0
        return position

    if strategy == "macd":
        fast = int(params.get("fast", 12))
        slow = int(params.get("slow", 26))
        signal_p = int(params.get("signal", 9))
        macd_line, signal_line, _ = macd(close, fast, slow, signal_p)
        signal = (macd_line > signal_line).astype(int)
        signal[macd_line.isna() | signal_line.isna()] = 0
        return signal

    if strategy == "bollinger":
        window = int(params.get("window", 20))
        num_std = float(params.get("num_std", 2.0))
        upper, mid, lower = bollinger(close, window, num_std)
        position = pd.Series(0, index=df.index, dtype=int)
        holding = False
        for i in range(len(df)):
            c = close.iloc[i]
            lo = lower.iloc[i]
            up = upper.iloc[i]
            if np.isnan(lo) or np.isnan(up):
                continue
            if not holding and c <= lo:
                holding = True
            elif holding and c >= up:
                holding = False
            position.iloc[i] = 1 if holding else 0
        return position

    if strategy == "mean_reversion":
        window = int(params.get("window", 20))
        entry_z = float(params.get("entry_z", 1.5))
        exit_z = float(params.get("exit_z", 0.25))
        mean = close.rolling(window).mean()
        std = close.rolling(window).std()
        z = (close - mean) / std.replace(0, np.nan)
        position = pd.Series(0, index=df.index, dtype=int)
        holding = False
        for i, val in enumerate(z):
            if np.isnan(val):
                continue
            if not holding and val <= -entry_z:
                holding = True
            elif holding and val >= -exit_z:
                holding = False
            position.iloc[i] = 1 if holding else 0
        return position

    if strategy == "buy_and_hold":
        return pd.Series(1, index=df.index, dtype=int)

    raise ValueError(f"Unknown strategy: {strategy}")
