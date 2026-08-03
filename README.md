# IMC Prosperity 4 Round 1 trader

This repository contains a causal, stateful strategy for:

- `ASH_COATED_OSMIUM` (ACO): bounded fair-value market making with inventory-aware quotes.
- `INTARIAN_PEPPER_ROOT` (IPR): trend-targeted execution with slippage and end-of-session risk controls.

Both products have a position limit of 50. `trader.py` is the submission artifact; tests, historical data, and benchmark tooling support local development.

## Setup

Python 3.10 or newer is required. The development dependencies are pinned so a clean checkout can reproduce the same environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

The platform provides a top-level `datamodel` module. Locally, `trader.py` falls back to the compatible model bundled with `prosperity3bt`.

## Run checks

```bash
python -m pytest
python scripts/benchmark.py
```

The benchmark discovers every `data/round*/prices_round_*_day_*.csv` file, runs days in deterministic order, and writes `backtests/latest.json`. It reports:

- final PnL and maximum drawdown by day and product;
- fill count and traded volume;
- maximum and final inventory;
- position-limit violations.

Once `benchmarks/baseline.json` is present, enforce the checked-in PnL baseline with:

```bash
python scripts/benchmark.py \
  --baseline benchmarks/baseline.json \
  --max-pnl-regression 0
```

The public `prosperity3bt` release predates the Prosperity 4 product names. The benchmark script registers the published Round 1 limits before invoking the unmodified simulator.

## Strategy

### ASH_COATED_OSMIUM

ACO's valid historical mid prices are centered around 10,000 with daily standard deviations of roughly 4.5–5.7 ticks. The strategy:

1. Computes a top-level microprice when both sides exist.
2. Bounds each observation to 20 ticks around a rolling median; one-sided and empty books retain the last robust reference.
3. Quotes seven ticks around fair value.
4. Shifts both prices by `0.16 × position`, making liquidation more attractive as inventory grows.
5. Takes every visible level favorable to its acceptable price, then posts residual non-marketable quotes.

### INTARIAN_PEPPER_ROOT

IPR rose approximately 1,000 ticks within each historical day, but a permanent maximum-long position is unsafe if that regime changes. The strategy:

1. Fits a linear trend to the last 40 causal midpoint observations.
2. Maps strong/weak positive and negative slopes to targets of `±50` and `±25`.
3. Buys or sells only visible liquidity within ten ticks of the current reference.
4. Tapers target exposure during the final 19,900 timestamp units.

Historical rows, day numbers, and future prices are never used by `Trader`.

## Persistent state and risk validation

`Trader.run` serializes a versioned, compact JSON payload through `traderData`. It contains only bounded ACO fair-value history and IPR trend observations. Missing, corrupt, or unsupported state safely cold-starts.

Before orders are returned, a shared validator:

- ignores unknown or mismatched symbols;
- rejects invalid prices and quantities;
- removes accidental duplicate side/price orders;
- caps each order at its configured maximum;
- clips aggregate buy and sell capacity to worst-case position bounds.

The unit suite exercises empty, one-sided, crossed, multi-level, outlier, and boundary-position books.

## Historical benchmark

The checked-in baseline is generated only after the full suite and all three datasets pass. See `benchmarks/baseline.json` for machine-readable per-day and per-product results.

## Submission

Upload `trader.py` to the Prosperity platform. Do not upload the local `prosperity3bt` package or development files. The import order ensures the platform's `datamodel` is used when available.
