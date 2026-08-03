from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.services.strategies import generate_signals


def run_backtest(
    df: pd.DataFrame,
    strategy: str,
    params: dict[str, Any] | None = None,
    initial_capital: float = 100_000.0,
    commission: float = 0.001,
) -> dict[str, Any]:
    params = params or {}
    data = df.copy().sort_index()
    if data.empty:
        raise ValueError("No market data available for backtest")

    raw_signal = generate_signals(data, strategy, params)
    # Trade on next bar open to avoid look-ahead bias
    position = raw_signal.shift(1).fillna(0).astype(int)

    cash = float(initial_capital)
    shares = 0.0
    equity_curve: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    signal_points: list[dict[str, Any]] = []

    first_close = float(data["close"].iloc[0])
    bh_shares = initial_capital / first_close

    peak = initial_capital
    prev_pos = 0

    for i, (ts, row) in enumerate(data.iterrows()):
        price = float(row["close"])
        open_px = float(row["open"])
        target = int(position.iloc[i])
        date_str = ts.strftime("%Y-%m-%d")

        if target != prev_pos:
            if target == 1 and shares == 0:
                # Buy with available cash
                cost_per_share = open_px * (1 + commission)
                buy_shares = cash / cost_per_share
                trade_value = buy_shares * open_px
                fee = trade_value * commission
                cash -= trade_value + fee
                shares = buy_shares
                trades.append(
                    {
                        "date": date_str,
                        "side": "buy",
                        "price": round(open_px, 4),
                        "shares": round(buy_shares, 6),
                        "value": round(trade_value, 2),
                        "commission": round(fee, 2),
                    }
                )
                signal_points.append({"date": date_str, "type": "buy", "price": round(open_px, 4)})
            elif target == 0 and shares > 0:
                trade_value = shares * open_px
                fee = trade_value * commission
                cash += trade_value - fee
                trades.append(
                    {
                        "date": date_str,
                        "side": "sell",
                        "price": round(open_px, 4),
                        "shares": round(shares, 6),
                        "value": round(trade_value, 2),
                        "commission": round(fee, 2),
                    }
                )
                signal_points.append({"date": date_str, "type": "sell", "price": round(open_px, 4)})
                shares = 0.0
            prev_pos = target

        equity = cash + shares * price
        bh_equity = bh_shares * price
        peak = max(peak, equity)
        drawdown = (equity - peak) / peak if peak else 0.0

        equity_curve.append(
            {
                "date": date_str,
                "equity": round(equity, 2),
                "buy_hold": round(bh_equity, 2),
                "drawdown": round(drawdown, 6),
            }
        )

    final_equity = equity_curve[-1]["equity"]
    metrics = _compute_metrics(
        equity_curve=equity_curve,
        trades=trades,
        initial_capital=initial_capital,
        final_equity=final_equity,
        buy_hold_final=equity_curve[-1]["buy_hold"],
    )

    return {
        "params": params,
        "metrics": metrics,
        "equity_curve": equity_curve,
        "trades": trades,
        "signals": signal_points,
    }


def _compute_metrics(
    equity_curve: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    initial_capital: float,
    final_equity: float,
    buy_hold_final: float,
) -> dict[str, Any]:
    equities = pd.Series([p["equity"] for p in equity_curve], dtype=float)
    returns = equities.pct_change().dropna()

    total_return = (final_equity / initial_capital) - 1
    buy_hold_return = (buy_hold_final / initial_capital) - 1
    alpha = total_return - buy_hold_return

    volatility = float(returns.std() * np.sqrt(252)) if len(returns) > 1 else 0.0
    mean_daily = float(returns.mean()) if len(returns) else 0.0
    sharpe = (mean_daily * 252) / volatility if volatility > 0 else 0.0

    downside = returns[returns < 0]
    downside_vol = float(downside.std() * np.sqrt(252)) if len(downside) > 1 else 0.0
    sortino = (mean_daily * 252) / downside_vol if downside_vol > 0 else 0.0

    drawdowns = [p["drawdown"] for p in equity_curve]
    max_drawdown = float(min(drawdowns)) if drawdowns else 0.0

    # Pair buy/sell for win rate
    trade_returns: list[float] = []
    i = 0
    while i < len(trades) - 1:
        if trades[i]["side"] == "buy" and trades[i + 1]["side"] == "sell":
            buy_val = trades[i]["value"] + trades[i]["commission"]
            sell_val = trades[i + 1]["value"] - trades[i + 1]["commission"]
            if buy_val > 0:
                trade_returns.append((sell_val / buy_val) - 1)
            i += 2
        else:
            i += 1

    wins = [r for r in trade_returns if r > 0]
    losses = [r for r in trade_returns if r <= 0]
    win_rate = len(wins) / len(trade_returns) if trade_returns else 0.0
    gross_profit = sum(wins) if wins else 0.0
    gross_loss = abs(sum(losses)) if losses else 0.0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)
    if profit_factor == float("inf"):
        profit_factor = 99.99

    avg_trade = float(np.mean(trade_returns)) if trade_returns else 0.0

    return {
        "total_return": round(total_return, 6),
        "buy_hold_return": round(buy_hold_return, 6),
        "alpha": round(alpha, 6),
        "sharpe_ratio": round(sharpe, 4),
        "sortino_ratio": round(sortino, 4),
        "max_drawdown": round(max_drawdown, 6),
        "win_rate": round(win_rate, 4),
        "profit_factor": round(float(profit_factor), 4),
        "total_trades": len(trades),
        "avg_trade_return": round(avg_trade, 6),
        "volatility": round(volatility, 6),
        "final_equity": round(final_equity, 2),
        "initial_capital": round(initial_capital, 2),
    }
