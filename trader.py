"""
IMC Prosperity 4 - Round 1 Trader
===================================
Products: ASH_COATED_OSMIUM, INTARIAN_PEPPER_ROOT
Position limit: 50 each

ASH_COATED_OSMIUM  → Market making. Price is rock-stable ~10000 (stdev ~5).
                     Use book mid-price as fair value, quote ±ACO_EDGE ticks.
                     Skew quotes by inventory to stay neutral.

INTARIAN_PEPPER_ROOT → Trend following. Price rises ~1000/day linearly.
                        Stay max long (50) at all times.

Backtest:
    /opt/anaconda3/bin/prosperity3bt trader.py 1 --no-out --merge-pnl --data data
"""

from typing import List, Dict
try:
    from datamodel import Order, OrderDepth, TradingState
except ImportError:
    from prosperity3bt.datamodel import Order, OrderDepth, TradingState

POSITION_LIMIT = 50

ACO_EDGE = 7         # half-spread to quote around fair value
ACO_SKEW = 0.0      # ticks of quote skew per unit of net inventory


class Trader:
    def run(self, state: TradingState):
        orders: Dict[str, List[Order]] = {}

        for product, order_depth in state.order_depths.items():
            pos = state.position.get(product, 0)

            if product == "ASH_COATED_OSMIUM":
                orders[product] = self._market_make_aco(order_depth, pos)
            elif product == "INTARIAN_PEPPER_ROOT":
                orders[product] = self._trend_follow_ipr(order_depth, pos)
            else:
                orders[product] = []

        return orders, 0, ""

    # ------------------------------------------------------------------
    # ASH_COATED_OSMIUM — Market Making
    # ------------------------------------------------------------------
    def _market_make_aco(self, od: OrderDepth, pos: int) -> List[Order]:
        orders = []

        best_bid = max(od.buy_orders) if od.buy_orders else None
        best_ask = min(od.sell_orders) if od.sell_orders else None

        # Fair value: book mid-price, clamped near known fair 10000.
        if best_bid and best_ask:
            fv = (best_bid + best_ask) / 2
        elif best_bid:
            fv = best_bid + ACO_EDGE
        elif best_ask:
            fv = best_ask - ACO_EDGE
        else:
            fv = 10000.0

        # Inventory skew: shift both quotes toward zero position.
        skew = int(pos * ACO_SKEW)
        bid_px = round(fv) - ACO_EDGE - skew
        ask_px = round(fv) + ACO_EDGE - skew

        # First: lift any resting asks below our bid, hit any bids above our ask.
        if best_ask is not None and best_ask <= bid_px:
            can_buy = POSITION_LIMIT - pos
            vol = min(-od.sell_orders[best_ask], can_buy)
            if vol > 0:
                orders.append(Order("ASH_COATED_OSMIUM", best_ask, vol))

        if best_bid is not None and best_bid >= ask_px:
            can_sell = POSITION_LIMIT + pos
            vol = min(od.buy_orders[best_bid], can_sell)
            if vol > 0:
                orders.append(Order("ASH_COATED_OSMIUM", best_bid, -vol))

        # Post passive quotes with remaining capacity.
        buy_cap = POSITION_LIMIT - pos - sum(o.quantity for o in orders if o.quantity > 0)
        sell_cap = POSITION_LIMIT + pos - sum(-o.quantity for o in orders if o.quantity < 0)

        if buy_cap > 0:
            orders.append(Order("ASH_COATED_OSMIUM", bid_px, buy_cap))
        if sell_cap > 0:
            orders.append(Order("ASH_COATED_OSMIUM", ask_px, -sell_cap))

        return orders

    # ------------------------------------------------------------------
    # INTARIAN_PEPPER_ROOT — Trend Following (hold max long)
    # ------------------------------------------------------------------
    def _trend_follow_ipr(self, od: OrderDepth, pos: int) -> List[Order]:
        orders = []
        can_buy = POSITION_LIMIT - pos

        if can_buy <= 0 or not od.sell_orders:
            return orders

        remaining = can_buy
        for ask_px in sorted(od.sell_orders.keys()):
            if remaining <= 0:
                break
            vol = min(-od.sell_orders[ask_px], remaining)
            orders.append(Order("INTARIAN_PEPPER_ROOT", ask_px, vol))
            remaining -= vol

        return orders
