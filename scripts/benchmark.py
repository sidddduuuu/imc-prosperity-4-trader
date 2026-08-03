#!/usr/bin/env python3
"""Run every checked-in Round 1 dataset and emit deterministic JSON metrics."""

import argparse
import importlib.metadata
import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from prosperity3bt.data import LIMITS
from prosperity3bt.file_reader import FileSystemReader
from prosperity3bt.models import BacktestResult, TradeMatchingMode
from prosperity3bt.runner import run_backtest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DAY_PATTERN = re.compile(r"prices_round_(?P<round>\\d+)_day_(?P<day>-?\\d+)\\.csv$")
PRODUCT_LIMITS = {
    "ASH_COATED_OSMIUM": 50,
    "INTARIAN_PEPPER_ROOT": 50,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--algorithm", type=Path, default=REPOSITORY_ROOT / "trader.py")
    parser.add_argument("--data", type=Path, default=REPOSITORY_ROOT / "data")
    parser.add_argument(
        "--output",
        type=Path,
        default=REPOSITORY_ROOT / "backtests" / "latest.json",
    )
    parser.add_argument("--baseline", type=Path)
    parser.add_argument(
        "--max-pnl-regression",
        type=float,
        default=0.0,
        help="Maximum aggregate PnL decrease allowed relative to --baseline.",
    )
    return parser.parse_args()


def discover_days(data_root: Path) -> List[Tuple[int, int]]:
    days = []
    for path in data_root.glob("round*/prices_round_*_day_*.csv"):
        match = DAY_PATTERN.match(path.name)
        if match:
            days.append((int(match.group("round")), int(match.group("day"))))
    return sorted(set(days))


def load_trader(path: Path):
    spec = importlib.util.spec_from_file_location("benchmark_trader", path.resolve())
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import algorithm from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if not hasattr(module, "Trader"):
        raise RuntimeError(f"{path} does not expose Trader")
    return module.Trader


def maximum_drawdown(values: Iterable[float]) -> float:
    peak = 0.0
    drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        drawdown = max(drawdown, peak - value)
    return drawdown


def summarize_result(result: BacktestResult) -> Dict[str, Any]:
    pnl_by_product: Dict[str, List[float]] = defaultdict(list)
    pnl_by_timestamp: Dict[int, float] = defaultdict(float)
    for row in result.activity_logs:
        timestamp = int(row.columns[1])
        product = str(row.columns[2])
        pnl = float(row.columns[-1])
        pnl_by_product[product].append(pnl)
        pnl_by_timestamp[timestamp] += pnl

    fill_count: Dict[str, int] = defaultdict(int)
    traded_volume: Dict[str, int] = defaultdict(int)
    position: Dict[str, int] = defaultdict(int)
    max_abs_position: Dict[str, int] = defaultdict(int)
    for row in result.trades:
        trade = row.trade
        if trade.buyer != "SUBMISSION" and trade.seller != "SUBMISSION":
            continue
        signed_quantity = trade.quantity if trade.buyer == "SUBMISSION" else -trade.quantity
        fill_count[trade.symbol] += 1
        traded_volume[trade.symbol] += trade.quantity
        position[trade.symbol] += signed_quantity
        max_abs_position[trade.symbol] = max(
            max_abs_position[trade.symbol],
            abs(position[trade.symbol]),
        )

    products = {}
    for product in sorted(pnl_by_product):
        values = pnl_by_product[product]
        products[product] = {
            "final_pnl": round(values[-1], 3),
            "max_drawdown": round(maximum_drawdown(values), 3),
            "fill_count": fill_count[product],
            "traded_volume": traded_volume[product],
            "max_abs_position": max_abs_position[product],
            "final_position": position[product],
        }

    limit_violations = [
        row.sandbox_log
        for row in result.sandbox_logs
        if "exceeded limit" in row.sandbox_log
    ]
    aggregate_values = [pnl_by_timestamp[key] for key in sorted(pnl_by_timestamp)]
    return {
        "round": result.round_num,
        "day": result.day_num,
        "final_pnl": round(sum(item["final_pnl"] for item in products.values()), 3),
        "max_drawdown": round(maximum_drawdown(aggregate_values), 3),
        "limit_violations": len(limit_violations),
        "products": products,
    }


def make_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "backtester": f"prosperity3bt {importlib.metadata.version('prosperity3bt')}",
        "days": results,
        "summary": {
            "final_pnl": round(sum(result["final_pnl"] for result in results), 3),
            "max_day_drawdown": round(
                max((result["max_drawdown"] for result in results), default=0.0),
                3,
            ),
            "limit_violations": sum(result["limit_violations"] for result in results),
        },
    }


def compare_with_baseline(
    report: Dict[str, Any],
    baseline_path: Path,
    max_pnl_regression: float,
) -> List[str]:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    current_pnl = float(report["summary"]["final_pnl"])
    baseline_pnl = float(baseline["summary"]["final_pnl"])
    failures = []
    if current_pnl < baseline_pnl - max_pnl_regression:
        failures.append(
            f"aggregate PnL regressed by {baseline_pnl - current_pnl:,.3f}; "
            f"allowed {max_pnl_regression:,.3f}"
        )
    if report["summary"]["limit_violations"]:
        failures.append(f"{report['summary']['limit_violations']} position-limit violations")
    return failures


def main() -> int:
    args = parse_args()
    days = discover_days(args.data)
    if not days:
        print(f"No datasets found under {args.data}", file=sys.stderr)
        return 1

    LIMITS.update(PRODUCT_LIMITS)
    trader_class = load_trader(args.algorithm)
    reader = FileSystemReader(args.data)
    results = []
    for round_number, day_number in days:
        print(f"Backtesting round {round_number} day {day_number}...", flush=True)
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
        summary = summarize_result(result)
        results.append(summary)
        print(
            f"  PnL {summary['final_pnl']:,.0f}; "
            f"drawdown {summary['max_drawdown']:,.0f}; "
            f"limit violations {summary['limit_violations']}"
        )

    report = make_report(results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Aggregate PnL: {report['summary']['final_pnl']:,.0f}")
    print(f"Wrote {args.output}")

    failures = []
    if args.baseline:
        failures = compare_with_baseline(report, args.baseline, args.max_pnl_regression)
    elif report["summary"]["limit_violations"]:
        failures.append(f"{report['summary']['limit_violations']} position-limit violations")

    if failures:
        for failure in failures:
            print(f"Regression: {failure}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
