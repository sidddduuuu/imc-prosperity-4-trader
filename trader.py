"""Stateful, risk-bounded IMC Prosperity 4 Round 1 trader."""

import json
import math
import statistics
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

try:
    from datamodel import Order, OrderDepth, TradingState
except ImportError:
    from prosperity3bt.datamodel import Order, OrderDepth, TradingState

ACO = "ASH_COATED_OSMIUM"
IPR = "INTARIAN_PEPPER_ROOT"
MEMORY_VERSION = 1
ACO_ANCHOR = 10_000.0
ACO_HISTORY_LENGTH = 21
ACO_FAIR_VALUE_BOUND = 20.0
IPR_HISTORY_LENGTH = 40
IPR_MIN_SIGNAL_POINTS = 12
SESSION_END_TIMESTAMP = 999_900
IPR_TAPER_START_TIMESTAMP = 980_000


@dataclass(frozen=True)
class ProductConfig:
    symbol: str
    position_limit: int
    max_order_size: int
    edge: int = 0
    inventory_skew: float = 0.0
    max_slippage: int = 0


PRODUCTS: Dict[str, ProductConfig] = {
    ACO: ProductConfig(
        symbol=ACO,
        position_limit=50,
        max_order_size=50,
        edge=7,
        inventory_skew=0.16,
    ),
    IPR: ProductConfig(
        symbol=IPR,
        position_limit=50,
        max_order_size=50,
        max_slippage=10,
    ),
}


@dataclass
class StrategyMemory:
    aco_fair_values: List[float]
    ipr_observations: List[List[float]]

    @classmethod
    def empty(cls) -> "StrategyMemory":
        return cls([], [])

    @classmethod
    def decode(cls, raw: str) -> "StrategyMemory":
        if not raw:
            return cls.empty()

        try:
            payload = json.loads(raw)
            if payload.get("v") != MEMORY_VERSION:
                return cls.empty()

            aco = [
                float(value)
                for value in payload.get("aco", [])
                if isinstance(value, (int, float)) and math.isfinite(value)
            ][-ACO_HISTORY_LENGTH:]

            ipr: List[List[float]] = []
            for item in payload.get("ipr", [])[-IPR_HISTORY_LENGTH:]:
                if (
                    isinstance(item, list)
                    and len(item) == 2
                    and isinstance(item[0], (int, float))
                    and isinstance(item[1], (int, float))
                    and math.isfinite(item[0])
                    and math.isfinite(item[1])
                ):
                    ipr.append([int(item[0]), float(item[1])])

            return cls(aco, ipr)
        except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
            return cls.empty()

    def encode(self) -> str:
        payload = {
            "v": MEMORY_VERSION,
            "aco": [round(value, 3) for value in self.aco_fair_values[-ACO_HISTORY_LENGTH:]],
            "ipr": [
                [int(timestamp), round(value, 3)]
                for timestamp, value in self.ipr_observations[-IPR_HISTORY_LENGTH:]
            ],
        }
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)


class Trader:
    def __init__(self) -> None:
        self.last_validation_errors: List[str] = []

    def run(self, state: TradingState):
        memory = StrategyMemory.decode(getattr(state, "traderData", ""))
        orders: Dict[str, List[Order]] = {}

        for symbol, order_depth in state.order_depths.items():
            if symbol not in PRODUCTS:
                continue

            position = state.position.get(symbol, 0)
            if symbol == ACO:
                orders[symbol] = self._market_make_aco(order_depth, position, memory)
            elif symbol == IPR:
                orders[symbol] = self._trade_ipr(
                    order_depth,
                    position,
                    int(getattr(state, "timestamp", 0)),
                    memory,
                )

        safe_orders = self._validate_orders(orders, getattr(state, "position", {}))
        return safe_orders, 0, memory.encode()

    def _market_make_aco(
        self,
        order_depth: OrderDepth,
        position: int,
        memory: StrategyMemory,
    ) -> List[Order]:
        config = PRODUCTS[ACO]
        orders: List[Order] = []
        fair_value = self._aco_fair_value(order_depth, memory)
        skew = position * config.inventory_skew

        acceptable_buy = math.floor(fair_value - config.edge - skew)
        acceptable_sell = math.ceil(fair_value + config.edge - skew)
        buy_capacity = max(0, config.position_limit - position)
        sell_capacity = max(0, config.position_limit + position)

        remaining_asks = {
            price: max(0, -volume)
            for price, volume in order_depth.sell_orders.items()
            if volume < 0
        }
        for price in sorted(remaining_asks):
            if price > acceptable_buy or buy_capacity <= 0:
                break
            quantity = min(remaining_asks[price], buy_capacity, config.max_order_size)
            if quantity > 0:
                orders.append(Order(config.symbol, price, quantity))
                buy_capacity -= quantity
                remaining_asks[price] -= quantity

        remaining_bids = {
            price: max(0, volume)
            for price, volume in order_depth.buy_orders.items()
            if volume > 0
        }
        for price in sorted(remaining_bids, reverse=True):
            if price < acceptable_sell or sell_capacity <= 0:
                break
            quantity = min(remaining_bids[price], sell_capacity, config.max_order_size)
            if quantity > 0:
                orders.append(Order(config.symbol, price, -quantity))
                sell_capacity -= quantity
                remaining_bids[price] -= quantity

        best_remaining_ask = min(
            (price for price, quantity in remaining_asks.items() if quantity > 0),
            default=None,
        )
        best_remaining_bid = max(
            (price for price, quantity in remaining_bids.items() if quantity > 0),
            default=None,
        )

        if buy_capacity > 0:
            passive_bid = acceptable_buy
            if best_remaining_ask is not None:
                passive_bid = min(passive_bid, best_remaining_ask - 1)
            while any(order.quantity > 0 and order.price == passive_bid for order in orders):
                passive_bid -= 1
            orders.append(
                Order(config.symbol, passive_bid, min(buy_capacity, config.max_order_size))
            )

        if sell_capacity > 0:
            passive_ask = acceptable_sell
            if best_remaining_bid is not None:
                passive_ask = max(passive_ask, best_remaining_bid + 1)
            while any(order.quantity < 0 and order.price == passive_ask for order in orders):
                passive_ask += 1
            orders.append(
                Order(config.symbol, passive_ask, -min(sell_capacity, config.max_order_size))
            )

        return orders

    def _aco_fair_value(
        self,
        order_depth: OrderDepth,
        memory: StrategyMemory,
    ) -> float:
        reference = (
            statistics.median(memory.aco_fair_values)
            if memory.aco_fair_values
            else ACO_ANCHOR
        )
        best_bid = max(order_depth.buy_orders, default=None)
        best_ask = min(order_depth.sell_orders, default=None)

        if best_bid is None or best_ask is None:
            return reference

        bid_volume = max(0, order_depth.buy_orders[best_bid])
        ask_volume = max(0, -order_depth.sell_orders[best_ask])
        total_volume = bid_volume + ask_volume
        if total_volume:
            observed = (best_ask * bid_volume + best_bid * ask_volume) / total_volume
        else:
            observed = (best_bid + best_ask) / 2

        bounded = min(
            reference + ACO_FAIR_VALUE_BOUND,
            max(reference - ACO_FAIR_VALUE_BOUND, observed),
        )
        memory.aco_fair_values.append(bounded)
        memory.aco_fair_values = memory.aco_fair_values[-ACO_HISTORY_LENGTH:]
        return statistics.median(memory.aco_fair_values)

    def _trade_ipr(
        self,
        order_depth: OrderDepth,
        position: int,
        timestamp: int,
        memory: StrategyMemory,
    ) -> List[Order]:
        config = PRODUCTS[IPR]
        reference, slope = self._ipr_signal(order_depth, timestamp, memory)
        target = self._ipr_target_position(slope, timestamp, len(memory.ipr_observations))
        delta = target - position
        orders: List[Order] = []

        if delta > 0:
            maximum_buy_price = math.floor(reference + config.max_slippage)
            remaining = min(delta, config.position_limit - position)
            for price in sorted(order_depth.sell_orders):
                if price > maximum_buy_price or remaining <= 0:
                    break
                available = max(0, -order_depth.sell_orders[price])
                quantity = min(available, remaining, config.max_order_size)
                if quantity > 0:
                    orders.append(Order(config.symbol, price, quantity))
                    remaining -= quantity
        elif delta < 0:
            minimum_sell_price = math.ceil(reference - config.max_slippage)
            remaining = min(-delta, config.position_limit + position)
            for price in sorted(order_depth.buy_orders, reverse=True):
                if price < minimum_sell_price or remaining <= 0:
                    break
                available = max(0, order_depth.buy_orders[price])
                quantity = min(available, remaining, config.max_order_size)
                if quantity > 0:
                    orders.append(Order(config.symbol, price, -quantity))
                    remaining -= quantity

        return orders

    def _ipr_signal(
        self,
        order_depth: OrderDepth,
        timestamp: int,
        memory: StrategyMemory,
    ) -> Tuple[float, Optional[float]]:
        best_bid = max(order_depth.buy_orders, default=None)
        best_ask = min(order_depth.sell_orders, default=None)

        if best_bid is not None and best_ask is not None:
            reference = (best_bid + best_ask) / 2
        elif memory.ipr_observations:
            reference = memory.ipr_observations[-1][1]
        elif best_bid is not None:
            reference = float(best_bid)
        elif best_ask is not None:
            reference = float(best_ask)
        else:
            return 0.0, None

        if memory.ipr_observations and memory.ipr_observations[-1][0] == timestamp:
            memory.ipr_observations[-1] = [timestamp, reference]
        else:
            memory.ipr_observations.append([timestamp, reference])
        memory.ipr_observations = memory.ipr_observations[-IPR_HISTORY_LENGTH:]

        if len(memory.ipr_observations) < IPR_MIN_SIGNAL_POINTS:
            return reference, None

        first_timestamp = memory.ipr_observations[0][0]
        x_values = [
            (observation_timestamp - first_timestamp) / 100
            for observation_timestamp, _ in memory.ipr_observations
        ]
        y_values = [value for _, value in memory.ipr_observations]
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)
        denominator = sum((value - x_mean) ** 2 for value in x_values)
        if denominator == 0:
            return reference, 0.0

        slope = sum(
            (x_value - x_mean) * (y_value - y_mean)
            for x_value, y_value in zip(x_values, y_values)
        ) / denominator
        return reference, slope

    def _ipr_target_position(
        self,
        slope: Optional[float],
        timestamp: int,
        observation_count: int,
    ) -> int:
        if slope is None or observation_count < IPR_MIN_SIGNAL_POINTS:
            target = 0
        elif slope >= 0.04:
            target = 50
        elif slope >= 0.015:
            target = 25
        elif slope <= -0.04:
            target = -50
        elif slope <= -0.015:
            target = -25
        else:
            target = 0

        if timestamp >= IPR_TAPER_START_TIMESTAMP:
            horizon = max(0, SESSION_END_TIMESTAMP - timestamp)
            taper_length = SESSION_END_TIMESTAMP - IPR_TAPER_START_TIMESTAMP
            target = round(target * horizon / taper_length)

        return target

    def _validate_orders(
        self,
        proposed: Dict[str, List[Order]],
        positions: Dict[str, int],
    ) -> Dict[str, List[Order]]:
        safe: Dict[str, List[Order]] = {}
        self.last_validation_errors = []

        for symbol, product_orders in proposed.items():
            config = PRODUCTS.get(symbol)
            if config is None:
                self.last_validation_errors.append(f"ignored unknown product {symbol}")
                continue

            position = positions.get(symbol, 0)
            buy_capacity = max(0, config.position_limit - position)
            sell_capacity = max(0, config.position_limit + position)
            accepted: List[Order] = []
            seen = set()

            for order in product_orders:
                if order.symbol != symbol:
                    self.last_validation_errors.append(
                        f"ignored mismatched symbol {order.symbol} under {symbol}"
                    )
                    continue
                if (
                    isinstance(order.price, bool)
                    or not isinstance(order.price, int)
                    or order.price <= 0
                ):
                    self.last_validation_errors.append(f"ignored invalid price for {symbol}")
                    continue
                if (
                    isinstance(order.quantity, bool)
                    or not isinstance(order.quantity, int)
                    or order.quantity == 0
                ):
                    self.last_validation_errors.append(f"ignored invalid quantity for {symbol}")
                    continue

                side = 1 if order.quantity > 0 else -1
                key = (order.price, side)
                if key in seen:
                    self.last_validation_errors.append(
                        f"ignored duplicate {symbol} order at {order.price}"
                    )
                    continue

                requested = min(abs(order.quantity), config.max_order_size)
                if side > 0:
                    quantity = min(requested, buy_capacity)
                    buy_capacity -= quantity
                else:
                    quantity = min(requested, sell_capacity)
                    sell_capacity -= quantity

                if quantity <= 0:
                    self.last_validation_errors.append(
                        f"ignored capacity-exceeding {symbol} order"
                    )
                    continue

                if quantity != abs(order.quantity):
                    self.last_validation_errors.append(f"clipped {symbol} order at {order.price}")
                accepted.append(Order(symbol, order.price, side * quantity))
                seen.add(key)

            if accepted:
                safe[symbol] = accepted

        return safe
