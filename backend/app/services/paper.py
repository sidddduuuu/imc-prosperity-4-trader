from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models
from app.services.market_data import fetch_quote, normalize_symbol


def get_or_create_paper_account(db: Session, user: models.User) -> models.PaperAccount:
    if user.paper_account:
        return user.paper_account
    settings = get_settings()
    acct = models.PaperAccount(
        user_id=user.id,
        cash=settings.paper_starting_cash,
        starting_cash=settings.paper_starting_cash,
    )
    db.add(acct)
    db.commit()
    db.refresh(acct)
    return acct


def place_paper_order(
    db: Session,
    account: models.PaperAccount,
    symbol: str,
    side: str,
    shares: float,
) -> models.PaperOrder:
    symbol = normalize_symbol(symbol)
    quote = fetch_quote(symbol)
    price = float(quote["price"])
    if price <= 0:
        raise HTTPException(400, "Invalid market price")

    value = shares * price
    pos = (
        db.query(models.PaperPosition)
        .filter(models.PaperPosition.account_id == account.id, models.PaperPosition.symbol == symbol)
        .first()
    )

    if side == "buy":
        if value > account.cash:
            raise HTTPException(400, "Insufficient paper cash")
        account.cash -= value
        if pos:
            total_cost = pos.avg_cost * pos.shares + value
            pos.shares += shares
            pos.avg_cost = total_cost / pos.shares if pos.shares else 0
        else:
            pos = models.PaperPosition(
                account_id=account.id, symbol=symbol, shares=shares, avg_cost=price
            )
            db.add(pos)
    else:
        if not pos or pos.shares < shares:
            raise HTTPException(400, "Insufficient shares to sell")
        account.cash += value
        pos.shares -= shares
        if pos.shares <= 1e-8:
            db.delete(pos)

    account.updated_at = datetime.now(timezone.utc)
    order = models.PaperOrder(
        account_id=account.id,
        symbol=symbol,
        side=side,
        shares=shares,
        price=price,
        value=round(value, 2),
        status="filled",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def paper_portfolio_snapshot(db: Session, account: models.PaperAccount) -> dict:
    positions = []
    equity = account.cash
    for pos in account.positions:
        if pos.shares <= 0:
            continue
        try:
            q = fetch_quote(pos.symbol)
            mkt = q["price"]
        except Exception:
            mkt = pos.avg_cost
        market_value = pos.shares * mkt
        equity += market_value
        pnl = (mkt - pos.avg_cost) * pos.shares
        positions.append(
            {
                "symbol": pos.symbol,
                "shares": round(pos.shares, 6),
                "avg_cost": round(pos.avg_cost, 4),
                "price": round(mkt, 4),
                "market_value": round(market_value, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round((mkt / pos.avg_cost - 1) if pos.avg_cost else 0, 6),
            }
        )
    return {
        "cash": round(account.cash, 2),
        "starting_cash": round(account.starting_cash, 2),
        "equity": round(equity, 2),
        "pnl": round(equity - account.starting_cash, 2),
        "pnl_pct": round((equity / account.starting_cash - 1) if account.starting_cash else 0, 6),
        "positions": positions,
        "orders": [
            {
                "id": o.id,
                "symbol": o.symbol,
                "side": o.side,
                "shares": o.shares,
                "price": o.price,
                "value": o.value,
                "status": o.status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in account.orders[:50]
        ],
    }
