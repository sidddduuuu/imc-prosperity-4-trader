#!/usr/bin/env python3
"""Compare ACO inventory-skew values across every checked-in day."""

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

from prosperity3bt.data import LIMITS
from prosperity3bt.file_reader import FileSystemReader
from prosperity3bt.models import TradeMatchingMode
from prosperity3bt.runner import run_backtest

from benchmark import (
    PRODUCT_LIMITS,
    REPOSITORY_ROOT,
    discover_days,
    load_trader,
    make_report,
    summarize_result,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--algorithm", type=Path, default=REPOSITORY_ROOT / "trader.py")
    parser.add_argument("--data", type=Path, default=REPOSITORY_ROOT / "data")
    parser.add_argument(
        "--values",
        type=float,
        nargs="+",
        default=[0.0, 0.04, 0.08, 0.12, 0.16, 0.20],
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPOSITORY_ROOT / "backtests" / "aco-skew-sweep.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    days = discover_days(args.data)
    if not days:
        print(f"No datasets found under {args.data}", file=sys.stderr)
        return 1

    LIMITS.update(PRODUCT_LIMITS)
    reader = FileSystemReader(args.data)
    sweep = []
    for skew in args.values:
        trader_class = load_trader(args.algorithm)
        trader_module = sys.modules[trader_class.__module__]
        symbol = trader_module.ACO
        trader_module.PRODUCTS[symbol] = replace(
            trader_module.PRODUCTS[symbol],
            inventory_skew=skew,
        )

        day_results = []
        for round_number, day_number in days:
            result = run_backtest(
                trader_class(),
                reader,
                round_number,
                day_number,
                False,
                TradeMatchingMode.all,
                True,
                False,
            )
            day_results.append(summarize_result(result))

        report = make_report(day_results)
        aco_metrics = [
            day["products"][symbol]
            for day in day_results
            if symbol in day["products"]
        ]
        row = {
            "inventory_skew": skew,
            "aggregate_pnl": report["summary"]["final_pnl"],
            "max_day_drawdown": report["summary"]["max_day_drawdown"],
            "aco_pnl": round(sum(metric["final_pnl"] for metric in aco_metrics), 3),
            "aco_max_abs_position": max(
                (metric["max_abs_position"] for metric in aco_metrics),
                default=0,
            ),
        }
        sweep.append(row)
        print(
            f"skew={skew:.2f} pnl={row['aggregate_pnl']:,.0f} "
            f"aco_pnl={row['aco_pnl']:,.0f} "
            f"aco_max_position={row['aco_max_abs_position']}"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"schema_version": 1, "results": sweep}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
