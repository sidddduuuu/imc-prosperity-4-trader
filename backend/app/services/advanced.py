from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.services.backtester import run_backtest
from app.services.market_data import fetch_history, normalize_symbol


def run_portfolio_backtest(
    symbols: list[str],
    start: str,
    end: str,
    strategy: str = "buy_and_hold",
    params: dict[str, Any] | None = None,
    weights: list[float] | None = None,
    initial_capital: float = 100_000.0,
    commission: float = 0.001,
) -> dict[str, Any]:
    symbols = [normalize_symbol(s) for s in symbols]
    if weights is None:
        weights = [1 / len(symbols)] * len(symbols)
    if len(weights) != len(symbols):
        raise ValueError("weights must match symbols length")
    total_w = sum(weights)
    if total_w <= 0:
        raise ValueError("weights must sum > 0")
    weights = [w / total_w for w in weights]

    legs = []
    equity_frames = []
    for sym, w in zip(symbols, weights):
        df = fetch_history(sym, start=start, end=end)
        capital = initial_capital * w
        result = run_backtest(df, strategy, params, capital, commission)
        legs.append(
            {
                "symbol": sym,
                "weight": round(w, 4),
                "metrics": result["metrics"],
                "trades": len(result["trades"]),
            }
        )
        series = pd.Series(
            {p["date"]: p["equity"] for p in result["equity_curve"]},
            name=sym,
        )
        equity_frames.append(series)

    combined = pd.concat(equity_frames, axis=1).sort_index().ffill().dropna(how="all")
    portfolio_equity = combined.sum(axis=1)
    first = float(portfolio_equity.iloc[0])
    # rescale to initial capital start
    if first > 0:
        portfolio_equity = portfolio_equity / first * initial_capital

    # buy & hold equal weight benchmark from closes
    closes = []
    for sym in symbols:
        df = fetch_history(sym, start=start, end=end)
        closes.append(df["close"].rename(sym))
    close_df = pd.concat(closes, axis=1).sort_index().ffill().dropna()
    norm = close_df / close_df.iloc[0]
    bh = (norm * weights).sum(axis=1) * initial_capital

    equity_curve = []
    peak = initial_capital
    for dt, eq in portfolio_equity.items():
        d = str(dt)[:10]
        bh_val = float(bh.get(dt, eq)) if dt in bh.index else float(eq)
        peak = max(peak, float(eq))
        dd = (float(eq) - peak) / peak if peak else 0
        equity_curve.append(
            {
                "date": d,
                "equity": round(float(eq), 2),
                "buy_hold": round(bh_val, 2),
                "drawdown": round(dd, 6),
            }
        )

    final = float(portfolio_equity.iloc[-1])
    rets = portfolio_equity.pct_change().dropna()
    vol = float(rets.std() * np.sqrt(252)) if len(rets) > 1 else 0.0
    sharpe = float((rets.mean() * 252) / vol) if vol > 0 else 0.0
    total_return = final / initial_capital - 1
    bh_final = float(bh.iloc[-1]) if len(bh) else initial_capital
    bh_return = bh_final / initial_capital - 1
    max_dd = min(p["drawdown"] for p in equity_curve) if equity_curve else 0

    return {
        "symbols": symbols,
        "weights": [round(w, 4) for w in weights],
        "strategy": strategy,
        "params": params or {},
        "legs": legs,
        "equity_curve": equity_curve,
        "metrics": {
            "total_return": round(total_return, 6),
            "buy_hold_return": round(bh_return, 6),
            "alpha": round(total_return - bh_return, 6),
            "sharpe_ratio": round(sharpe, 4),
            "max_drawdown": round(max_dd, 6),
            "volatility": round(vol, 6),
            "final_equity": round(final, 2),
            "initial_capital": round(initial_capital, 2),
            "legs": len(legs),
        },
    }


def run_walk_forward(
    df: pd.DataFrame,
    strategy: str,
    params: dict[str, Any] | None,
    windows: int = 4,
    initial_capital: float = 100_000.0,
    commission: float = 0.001,
) -> dict[str, Any]:
    n = len(df)
    if n < windows * 30:
        raise ValueError("Not enough history for walk-forward windows")
    chunk = n // windows
    folds = []
    for i in range(windows):
        start_i = i * chunk
        end_i = n if i == windows - 1 else (i + 1) * chunk
        # train = prior data unused for signal params here (strategies are rule-based);
        # evaluate OOS on fold slice
        fold_df = df.iloc[start_i:end_i]
        if len(fold_df) < 20:
            continue
        result = run_backtest(fold_df, strategy, params, initial_capital, commission)
        folds.append(
            {
                "fold": i + 1,
                "start": fold_df.index[0].strftime("%Y-%m-%d"),
                "end": fold_df.index[-1].strftime("%Y-%m-%d"),
                "total_return": result["metrics"]["total_return"],
                "sharpe_ratio": result["metrics"]["sharpe_ratio"],
                "max_drawdown": result["metrics"]["max_drawdown"],
                "trades": result["metrics"]["total_trades"],
            }
        )
    avg_return = float(np.mean([f["total_return"] for f in folds])) if folds else 0
    avg_sharpe = float(np.mean([f["sharpe_ratio"] for f in folds])) if folds else 0
    return {
        "windows": windows,
        "folds": folds,
        "summary": {
            "avg_return": round(avg_return, 6),
            "avg_sharpe": round(avg_sharpe, 4),
            "positive_folds": sum(1 for f in folds if f["total_return"] > 0),
            "fold_count": len(folds),
        },
    }


def run_monte_carlo(
    trades: list[dict[str, Any]],
    initial_capital: float = 100_000.0,
    runs: int = 200,
) -> dict[str, Any]:
    # Reconstruct trade pair returns
    pair_returns: list[float] = []
    i = 0
    while i < len(trades) - 1:
        if trades[i]["side"] == "buy" and trades[i + 1]["side"] == "sell":
            buy_val = trades[i]["value"] + trades[i]["commission"]
            sell_val = trades[i + 1]["value"] - trades[i + 1]["commission"]
            if buy_val > 0:
                pair_returns.append(sell_val / buy_val - 1)
            i += 2
        else:
            i += 1

    if not pair_returns:
        return {
            "runs": runs,
            "message": "Not enough completed trade pairs for Monte Carlo",
            "percentiles": {},
            "paths_sample": [],
        }

    rng = np.random.default_rng(42)
    finals = []
    sample_paths = []
    for r in range(runs):
        shuffled = rng.permutation(pair_returns)
        equity = initial_capital
        path = [equity]
        for ret in shuffled:
            equity *= 1 + ret
            path.append(equity)
        finals.append(equity)
        if r < 25:
            sample_paths.append([round(x, 2) for x in path])

    finals_arr = np.array(finals)
    returns = finals_arr / initial_capital - 1
    return {
        "runs": runs,
        "trade_pairs": len(pair_returns),
        "percentiles": {
            "p5": round(float(np.percentile(returns, 5)), 6),
            "p25": round(float(np.percentile(returns, 25)), 6),
            "p50": round(float(np.percentile(returns, 50)), 6),
            "p75": round(float(np.percentile(returns, 75)), 6),
            "p95": round(float(np.percentile(returns, 95)), 6),
        },
        "prob_profit": round(float((returns > 0).mean()), 4),
        "mean_final_return": round(float(returns.mean()), 6),
        "paths_sample": sample_paths,
    }
