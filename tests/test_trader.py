import json
from types import SimpleNamespace

import pytest
from prosperity3bt.datamodel import Order, OrderDepth

from trader import (
    ACO,
    ACO_HISTORY_LENGTH,
    IPR,
    IPR_HISTORY_LENGTH,
    PRODUCTS,
    StrategyMemory,
    Trader,
)


def depth(bids=None, asks=None):
    order_depth = OrderDepth()
    order_depth.buy_orders = bids or {}
    order_depth.sell_orders = asks or {}
    return order_depth


def state(order_depths, positions=None, timestamp=0, trader_data=""):
    return SimpleNamespace(
        order_depths=order_depths,
        position=positions or {},
        timestamp=timestamp,
        traderData=trader_data,
    )


def assert_within_limits(orders, positions):
    for symbol, product_orders in orders.items():
        config = PRODUCTS[symbol]
        position = positions.get(symbol, 0)
        buys = sum(order.quantity for order in product_orders if order.quantity > 0)
        sells = sum(-order.quantity for order in product_orders if order.quantity < 0)
        assert position + buys <= config.position_limit
        assert position - sells >= -config.position_limit
        assert all(order.quantity != 0 for order in product_orders)
        assert all(order.symbol == symbol for order in product_orders)
        assert all(isinstance(order.price, int) for order in product_orders)
        assert all(abs(order.quantity) <= config.max_order_size for order in product_orders)


def rising_ipr_memory(start=10_000.0, count=20):
    return StrategyMemory(
        [],
        [[index * 100, start + index * 0.2] for index in range(count)],
    )


def test_memory_round_trip_is_versioned_and_bounded():
    memory = StrategyMemory(
        [10_000.0 + index for index in range(ACO_HISTORY_LENGTH + 5)],
        [[index * 100, 12_000.0 + index] for index in range(IPR_HISTORY_LENGTH + 5)],
        50,
    )

    raw = memory.encode()
    decoded = StrategyMemory.decode(raw)

    assert json.loads(raw)["v"] == 1
    assert len(decoded.aco_fair_values) == ACO_HISTORY_LENGTH
    assert len(decoded.ipr_observations) == IPR_HISTORY_LENGTH
    assert decoded.ipr_target == 50
    assert len(raw) < 1_500


@pytest.mark.parametrize("raw", ["", "not-json", "[]", '{"v":999}', '{"v":1,"aco":[null]}'])
def test_memory_decode_falls_back_safely(raw):
    decoded = StrategyMemory.decode(raw)
    assert isinstance(decoded, StrategyMemory)
    assert len(decoded.aco_fair_values) <= ACO_HISTORY_LENGTH
    assert len(decoded.ipr_observations) <= IPR_HISTORY_LENGTH


def test_aco_fair_value_is_bounded_and_ignores_one_sided_outlier():
    trader = Trader()
    memory = StrategyMemory([10_000.0], [])

    one_sided = trader._aco_fair_value(depth(bids={50_000: 10}), memory)
    outlier = trader._aco_fair_value(
        depth(bids={49_990: 10}, asks={50_010: -10}),
        memory,
    )

    assert one_sided == 10_000.0
    assert 9_980.0 <= outlier <= 10_020.0


def test_aco_sweeps_profitable_levels_then_posts_non_marketable_quote():
    trader = Trader()
    orders = trader._market_make_aco(
        depth(
            bids={9_985: 10},
            asks={9_990: -10, 9_993: -15, 10_010: -20},
        ),
        0,
        StrategyMemory([10_000.0] * ACO_HISTORY_LENGTH, []),
    )

    buys = [order for order in orders if order.quantity > 0]
    assert [(order.price, order.quantity) for order in buys[:2]] == [
        (9_990, 10),
        (9_993, 15),
    ]
    assert buys[-1].price < 10_010
    assert len({(order.price, order.quantity > 0) for order in orders}) == len(orders)


def test_aco_inventory_skew_moves_quotes_toward_flat():
    trader = Trader()

    short_orders = trader._market_make_aco(
        depth(bids={9_990: 10}, asks={10_010: -10}),
        -25,
        StrategyMemory([10_000.0], []),
    )
    flat_orders = trader._market_make_aco(
        depth(bids={9_990: 10}, asks={10_010: -10}),
        0,
        StrategyMemory([10_000.0], []),
    )
    long_orders = trader._market_make_aco(
        depth(bids={9_990: 10}, asks={10_010: -10}),
        25,
        StrategyMemory([10_000.0], []),
    )

    short_bid = max(order.price for order in short_orders if order.quantity > 0)
    flat_bid = max(order.price for order in flat_orders if order.quantity > 0)
    long_bid = max(order.price for order in long_orders if order.quantity > 0)
    short_ask = min(order.price for order in short_orders if order.quantity < 0)
    flat_ask = min(order.price for order in flat_orders if order.quantity < 0)
    long_ask = min(order.price for order in long_orders if order.quantity < 0)

    assert short_bid > flat_bid > long_bid
    assert short_ask > flat_ask > long_ask


def test_ipr_rejects_ask_above_slippage_guard():
    trader = Trader()
    memory = rising_ipr_memory()
    orders = trader._trade_ipr(
        depth(
            bids={10_002: 20},
            asks={10_006: -10, 10_100: -40},
        ),
        0,
        2_000,
        memory,
    )

    assert [(order.price, order.quantity) for order in orders] == [(10_006, 10)]


def test_ipr_can_exit_or_reverse_when_trend_reverses():
    trader = Trader()
    falling = StrategyMemory(
        [],
        [[index * 100, 10_000.0 - index * 0.2] for index in range(20)],
    )
    orders = trader._trade_ipr(
        depth(bids={9_994: 50}, asks={10_006: -50}),
        25,
        2_000,
        falling,
    )

    assert orders
    assert all(order.quantity < 0 for order in orders)


def test_ipr_target_tapers_to_flat_at_end_of_session():
    trader = Trader()
    assert trader._ipr_target_position(0.1, 500_000, 20) == 50
    assert 0 < trader._ipr_target_position(0.1, 990_000, 20) < 50
    assert trader._ipr_target_position(0.1, 999_900, 20) == 0


def test_ipr_target_uses_hysteresis_to_avoid_churn():
    trader = Trader()
    assert trader._ipr_target_position(0.0, 500_000, 20, previous_target=50) == 50
    assert trader._ipr_target_position(-0.02, 500_000, 20, previous_target=50) == -25


def test_validator_clips_invalid_duplicate_and_excess_orders():
    trader = Trader()
    proposed = {
        ACO: [
            Order(ACO, 9_990, 75),
            Order(ACO, 9_990, 10),
            Order(IPR, 10_000, 10),
            Order(ACO, -1, 10),
            Order(ACO, 10_010, -75),
        ],
        "UNKNOWN": [Order("UNKNOWN", 1, 1)],
    }

    safe = trader._validate_orders(proposed, {ACO: 25})

    assert [(order.price, order.quantity) for order in safe[ACO]] == [
        (9_990, 25),
        (10_010, -50),
    ]
    assert "UNKNOWN" not in safe
    assert trader.last_validation_errors
    assert_within_limits(safe, {ACO: 25})


@pytest.mark.parametrize("position", [-50, -49, 0, 49, 50])
@pytest.mark.parametrize("symbol", [ACO, IPR])
def test_run_respects_limits_at_boundary_positions(symbol, position):
    trader = Trader()
    books = {
        ACO: depth(
            bids={10_020: 50, 10_010: 50},
            asks={9_980: -50, 9_990: -50},
        ),
        IPR: depth(
            bids={9_990: 100},
            asks={10_010: -100},
        ),
    }
    memory = rising_ipr_memory().encode()
    positions = {symbol: position}

    orders, conversions, trader_data = trader.run(
        state({symbol: books[symbol]}, positions, timestamp=2_000, trader_data=memory)
    )

    assert conversions == 0
    assert StrategyMemory.decode(trader_data)
    assert_within_limits(orders, positions)


def test_run_ignores_unknown_products_and_persists_state():
    trader = Trader()
    orders, _, trader_data = trader.run(
        state(
            {
                ACO: depth(bids={9_990: 10}, asks={10_010: -10}),
                "UNKNOWN": depth(bids={1: 1}, asks={2: -1}),
            },
            timestamp=100,
        )
    )

    assert "UNKNOWN" not in orders
    assert ACO in orders
    assert StrategyMemory.decode(trader_data).aco_fair_values
