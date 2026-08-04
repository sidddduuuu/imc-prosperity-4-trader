import json

from scripts.benchmark import compare_with_baseline, discover_days, maximum_drawdown


def test_discover_days_uses_deterministic_round_day_order(tmp_path):
    round_one = tmp_path / "round1"
    round_two = tmp_path / "round2"
    round_one.mkdir()
    round_two.mkdir()
    (round_one / "prices_round_1_day_0.csv").touch()
    (round_one / "prices_round_1_day_-2.csv").touch()
    (round_two / "prices_round_2_day_1.csv").touch()
    (round_two / "trades_round_2_day_1.csv").touch()

    assert discover_days(tmp_path) == [(1, -2), (1, 0), (2, 1)]


def test_maximum_drawdown_includes_loss_below_initial_zero():
    assert maximum_drawdown([5.0, 8.0, 3.0, 10.0, -2.0]) == 12.0
    assert maximum_drawdown([-3.0, -5.0]) == 5.0


def test_baseline_comparison_flags_pnl_regression_and_limit_violation(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps({"summary": {"final_pnl": 1_000.0}}),
        encoding="utf-8",
    )
    report = {
        "summary": {
            "final_pnl": 900.0,
            "limit_violations": 1,
        }
    }

    failures = compare_with_baseline(report, baseline_path, max_pnl_regression=50.0)

    assert len(failures) == 2
    assert "regressed" in failures[0]
    assert "position-limit" in failures[1]
