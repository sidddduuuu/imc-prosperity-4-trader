from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db import models
from app.db.session import get_db
from app.models.terminal import (
    AlertIn,
    AlertOut,
    AIBriefIn,
    AdvancedBacktestIn,
    PaperOrderIn,
    PortfolioBacktestIn,
    SavedBacktestIn,
    SavedBacktestOut,
    SharedStrategyIn,
    SharedStrategyOut,
    WatchlistCreate,
    WatchlistItemIn,
    WatchlistOut,
    dumps,
    loads,
)
from app.services.advanced import run_monte_carlo, run_portfolio_backtest, run_walk_forward
from app.services.ai_brief import build_ai_brief, build_local_brief
from app.services.backtester import run_backtest
from app.services.market_data import fetch_history, fetch_quote, normalize_symbol
from app.services.paper import get_or_create_paper_account, paper_portfolio_snapshot, place_paper_order
from app.services.screener import evaluate_alert, run_screener

router = APIRouter(tags=["terminal"])


# ---------- Watchlists ----------
@router.get("/watchlists", response_model=list[WatchlistOut])
def list_watchlists(
    user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    if not user.watchlists:
        wl = models.Watchlist(user_id=user.id, name="Default")
        db.add(wl)
        db.commit()
        db.refresh(user)
    out = []
    for wl in user.watchlists:
        items = []
        for item in wl.items:
            quote = None
            try:
                quote = fetch_quote(item.symbol)
            except Exception:
                pass
            items.append(
                {
                    "id": item.id,
                    "symbol": item.symbol,
                    "notes": item.notes,
                    "quote": quote,
                }
            )
        out.append({"id": wl.id, "name": wl.name, "items": items})
    return out


@router.post("/watchlists", response_model=WatchlistOut)
def create_watchlist(
    body: WatchlistCreate,
    user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    wl = models.Watchlist(user_id=user.id, name=body.name)
    db.add(wl)
    db.commit()
    db.refresh(wl)
    return {"id": wl.id, "name": wl.name, "items": []}


@router.post("/watchlists/{watchlist_id}/items")
def add_watchlist_item(
    watchlist_id: int,
    body: WatchlistItemIn,
    user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    wl = (
        db.query(models.Watchlist)
        .filter(models.Watchlist.id == watchlist_id, models.Watchlist.user_id == user.id)
        .first()
    )
    if not wl:
        raise HTTPException(404, "Watchlist not found")
    symbol = normalize_symbol(body.symbol)
    existing = (
        db.query(models.WatchlistItem)
        .filter(models.WatchlistItem.watchlist_id == wl.id, models.WatchlistItem.symbol == symbol)
        .first()
    )
    if existing:
        raise HTTPException(400, "Symbol already on watchlist")
    item = models.WatchlistItem(watchlist_id=wl.id, symbol=symbol, notes=body.notes)
    db.add(item)
    db.commit()
    return {"ok": True, "symbol": symbol}


@router.delete("/watchlists/{watchlist_id}/items/{item_id}")
def remove_watchlist_item(
    watchlist_id: int,
    item_id: int,
    user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    wl = (
        db.query(models.Watchlist)
        .filter(models.Watchlist.id == watchlist_id, models.Watchlist.user_id == user.id)
        .first()
    )
    if not wl:
        raise HTTPException(404, "Watchlist not found")
    item = (
        db.query(models.WatchlistItem)
        .filter(models.WatchlistItem.id == item_id, models.WatchlistItem.watchlist_id == wl.id)
        .first()
    )
    if not item:
        raise HTTPException(404, "Item not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


# ---------- Saved backtests ----------
@router.get("/saved-backtests", response_model=list[SavedBacktestOut])
def list_saved_backtests(
    user: Annotated[models.User, Depends(get_current_user)],
):
    return [
        SavedBacktestOut(
            id=b.id,
            name=b.name,
            symbol=b.symbol,
            strategy=b.strategy,
            params=loads(b.params_json),
            result=loads(b.result_json),
            created_at=b.created_at,
        )
        for b in user.saved_backtests
    ]


@router.post("/saved-backtests", response_model=SavedBacktestOut)
def save_backtest(
    body: SavedBacktestIn,
    user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    row = models.SavedBacktest(
        user_id=user.id,
        name=body.name,
        symbol=normalize_symbol(body.symbol),
        strategy=body.strategy,
        params_json=dumps(body.params),
        result_json=dumps(body.result),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return SavedBacktestOut(
        id=row.id,
        name=row.name,
        symbol=row.symbol,
        strategy=row.strategy,
        params=body.params,
        result=body.result,
        created_at=row.created_at,
    )


@router.delete("/saved-backtests/{backtest_id}")
def delete_saved_backtest(
    backtest_id: int,
    user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    row = (
        db.query(models.SavedBacktest)
        .filter(models.SavedBacktest.id == backtest_id, models.SavedBacktest.user_id == user.id)
        .first()
    )
    if not row:
        raise HTTPException(404, "Not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


# ---------- Alerts ----------
@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(user: Annotated[models.User, Depends(get_current_user)]):
    return user.alerts


@router.post("/alerts", response_model=AlertOut)
def create_alert(
    body: AlertIn,
    user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    alert = models.Alert(
        user_id=user.id,
        symbol=normalize_symbol(body.symbol),
        condition=body.condition,
        threshold=body.threshold,
        message=body.message,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/alerts/check")
def check_alerts(
    user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    triggered = []
    for alert in user.alerts:
        if not alert.active or alert.triggered:
            continue
        try:
            q = fetch_quote(alert.symbol)
            hit = evaluate_alert(
                alert.condition, alert.threshold, q["price"], q.get("previous_close")
            )
            if hit:
                alert.triggered = True
                alert.active = False
                alert.triggered_at = datetime.now(timezone.utc)
                triggered.append(
                    {
                        "id": alert.id,
                        "symbol": alert.symbol,
                        "condition": alert.condition,
                        "threshold": alert.threshold,
                        "price": q["price"],
                        "message": alert.message or f"{alert.symbol} alert triggered",
                    }
                )
        except Exception:
            continue
    db.commit()
    return {"triggered": triggered}


@router.delete("/alerts/{alert_id}")
def delete_alert(
    alert_id: int,
    user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    alert = (
        db.query(models.Alert)
        .filter(models.Alert.id == alert_id, models.Alert.user_id == user.id)
        .first()
    )
    if not alert:
        raise HTTPException(404, "Not found")
    db.delete(alert)
    db.commit()
    return {"ok": True}


# ---------- Screener ----------
@router.get("/screener")
def screener(
    min_price: float | None = None,
    max_price: float | None = None,
    min_change_pct: float | None = None,
    trend: str | None = None,
    rsi_max: float | None = None,
    rsi_min: float | None = None,
    limit: int = Query(25, ge=1, le=50),
):
    return run_screener(
        min_price=min_price,
        max_price=max_price,
        min_change_pct=min_change_pct,
        trend=trend,
        rsi_max=rsi_max,
        rsi_min=rsi_min,
        limit=limit,
    )


# ---------- Paper trading ----------
@router.get("/paper")
def paper_account(
    user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    acct = get_or_create_paper_account(db, user)
    return paper_portfolio_snapshot(db, acct)


@router.post("/paper/order")
def paper_order(
    body: PaperOrderIn,
    user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    acct = get_or_create_paper_account(db, user)
    order = place_paper_order(db, acct, body.symbol, body.side, body.shares)
    return {
        "order": {
            "id": order.id,
            "symbol": order.symbol,
            "side": order.side,
            "shares": order.shares,
            "price": order.price,
            "value": order.value,
        },
        "account": paper_portfolio_snapshot(db, acct),
    }


@router.post("/paper/reset")
def paper_reset(
    user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    acct = get_or_create_paper_account(db, user)
    for pos in list(acct.positions):
        db.delete(pos)
    for order in list(acct.orders):
        db.delete(order)
    from app.core.config import get_settings

    acct.cash = get_settings().paper_starting_cash
    acct.starting_cash = get_settings().paper_starting_cash
    db.commit()
    return paper_portfolio_snapshot(db, acct)


# ---------- Portfolio / advanced backtests ----------
@router.post("/backtest/portfolio")
def portfolio_backtest(body: PortfolioBacktestIn):
    try:
        return run_portfolio_backtest(
            symbols=body.symbols,
            start=body.start,
            end=body.end,
            strategy=body.strategy,
            params=body.params,
            weights=body.weights,
            initial_capital=body.initial_capital,
            commission=body.commission,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Portfolio backtest failed: {exc}") from exc


@router.post("/backtest/advanced")
def advanced_backtest(body: AdvancedBacktestIn):
    try:
        df = fetch_history(body.symbol, start=body.start, end=body.end)
        base = run_backtest(
            df,
            body.strategy,
            body.params,
            body.initial_capital,
            body.commission,
        )
        walk = run_walk_forward(
            df,
            body.strategy,
            body.params,
            windows=body.walk_forward_windows,
            initial_capital=body.initial_capital,
            commission=body.commission,
        )
        mc = run_monte_carlo(
            base["trades"],
            initial_capital=body.initial_capital,
            runs=body.monte_carlo_runs,
        )
        return {
            "symbol": normalize_symbol(body.symbol),
            "strategy": body.strategy,
            "base": base,
            "walk_forward": walk,
            "monte_carlo": mc,
        }
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Advanced backtest failed: {exc}") from exc


# ---------- Community strategies ----------
@router.get("/community/strategies", response_model=list[SharedStrategyOut])
def list_community(db: Annotated[Session, Depends(get_db)]):
    rows = db.query(models.SharedStrategy).order_by(models.SharedStrategy.likes.desc()).limit(50)
    return [
        SharedStrategyOut(
            id=r.id,
            title=r.title,
            description=r.description,
            strategy=r.strategy,
            params=loads(r.params_json),
            symbol_example=r.symbol_example,
            likes=r.likes,
            author=r.user.name or r.user.email.split("@")[0],
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.post("/community/strategies", response_model=SharedStrategyOut)
def share_strategy(
    body: SharedStrategyIn,
    user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    row = models.SharedStrategy(
        user_id=user.id,
        title=body.title,
        description=body.description,
        strategy=body.strategy,
        params_json=dumps(body.params),
        symbol_example=normalize_symbol(body.symbol_example),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return SharedStrategyOut(
        id=row.id,
        title=row.title,
        description=row.description,
        strategy=row.strategy,
        params=body.params,
        symbol_example=row.symbol_example,
        likes=0,
        author=user.name or user.email.split("@")[0],
        created_at=row.created_at,
    )


@router.post("/community/strategies/{strategy_id}/like")
def like_strategy(strategy_id: int, db: Annotated[Session, Depends(get_db)]):
    row = db.query(models.SharedStrategy).filter(models.SharedStrategy.id == strategy_id).first()
    if not row:
        raise HTTPException(404, "Not found")
    row.likes += 1
    db.commit()
    return {"likes": row.likes}


# ---------- AI brief ----------
@router.post("/ai/brief")
async def ai_brief(body: AIBriefIn):
    try:
        return await build_ai_brief(body.symbol, include_news=body.include_news)
    except Exception:
        return build_local_brief(body.symbol, include_news=body.include_news)


# ---------- WebSocket quotes ----------
@router.websocket("/ws/quotes")
async def ws_quotes(websocket: WebSocket):
    await websocket.accept()
    import asyncio

    try:
        # first message may contain symbols JSON
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=10)
        try:
            payload = json.loads(raw)
            symbols = [normalize_symbol(s) for s in payload.get("symbols", ["SPY", "QQQ", "AAPL"])]
        except Exception:
            symbols = ["SPY", "QQQ", "AAPL"]

        while True:
            quotes = []
            for sym in symbols[:12]:
                try:
                    quotes.append(fetch_quote(sym))
                except Exception:
                    continue
            await websocket.send_json({"type": "quotes", "data": quotes})
            await asyncio.sleep(5)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        return
    except Exception:
        await websocket.close()
