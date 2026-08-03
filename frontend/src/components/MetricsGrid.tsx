import { formatMoney, formatPct } from "@/lib/api";
import type { BacktestMetrics } from "@/lib/api";

type Props = {
  metrics: BacktestMetrics;
};

function Metric({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "up" | "down" | "neutral";
}) {
  const color =
    tone === "up" ? "text-signal" : tone === "down" ? "text-alert" : "text-ink";
  return (
    <div className="border-b border-ink/10 py-3">
      <div className="text-[11px] uppercase tracking-[0.16em] text-ink-muted">{label}</div>
      <div className={`mt-1 font-mono text-lg tabular-nums ${color}`}>{value}</div>
    </div>
  );
}

export function MetricsGrid({ metrics }: Props) {
  const tone = (n: number): "up" | "down" | "neutral" =>
    n > 0 ? "up" : n < 0 ? "down" : "neutral";

  return (
    <div className="grid grid-cols-2 gap-x-6 sm:grid-cols-3 lg:grid-cols-4">
      <Metric label="Total return" value={formatPct(metrics.total_return)} tone={tone(metrics.total_return)} />
      <Metric label="Buy & hold" value={formatPct(metrics.buy_hold_return)} tone={tone(metrics.buy_hold_return)} />
      <Metric label="Alpha" value={formatPct(metrics.alpha)} tone={tone(metrics.alpha)} />
      <Metric label="Sharpe" value={metrics.sharpe_ratio.toFixed(2)} />
      <Metric label="Sortino" value={metrics.sortino_ratio.toFixed(2)} />
      <Metric label="Max drawdown" value={formatPct(metrics.max_drawdown)} tone="down" />
      <Metric label="Win rate" value={formatPct(metrics.win_rate)} />
      <Metric label="Profit factor" value={metrics.profit_factor.toFixed(2)} />
      <Metric label="Trades" value={String(metrics.total_trades)} />
      <Metric label="Volatility" value={formatPct(metrics.volatility)} />
      <Metric label="Final equity" value={formatMoney(metrics.final_equity)} />
      <Metric label="Avg trade" value={formatPct(metrics.avg_trade_return)} tone={tone(metrics.avg_trade_return)} />
    </div>
  );
}
