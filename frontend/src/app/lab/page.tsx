"use client";

import { useMemo, useState } from "react";
import { atlasApi, formatPct } from "@/lib/api";
import { SymbolSearch } from "@/components/SymbolSearch";
import { EquityChart } from "@/components/EquityChart";
import { MetricsGrid } from "@/components/MetricsGrid";

function defaultDates() {
  const end = new Date();
  const start = new Date();
  start.setFullYear(end.getFullYear() - 3);
  return { start: start.toISOString().slice(0, 10), end: end.toISOString().slice(0, 10) };
}

export default function LabPage() {
  const dates = useMemo(() => defaultDates(), []);
  const [symbol, setSymbol] = useState("AAPL");
  const [strategy, setStrategy] = useState("sma_crossover");
  const [start, setStart] = useState(dates.start);
  const [end, setEnd] = useState(dates.end);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const data = await atlasApi.advancedBacktest({
        symbol,
        strategy,
        start,
        end,
        initial_capital: 100000,
        commission: 0.001,
        params: strategy === "sma_crossover" ? { fast: 20, slow: 50 } : {},
        walk_forward_windows: 4,
        monte_carlo_runs: 200,
      });
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lab run failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-mesh">
      <div className="mx-auto max-w-6xl px-5 py-10 md:px-8">
        <p className="text-[11px] uppercase tracking-[0.2em] text-ink-muted">Quant</p>
        <h1 className="mt-2 font-display text-4xl tracking-tight text-ink">Research lab</h1>
        <p className="mt-3 max-w-2xl text-ink-muted">
          Walk-forward folds and Monte Carlo reshuffles on completed trade pairs.
        </p>

        <div className="mt-8 grid gap-3 border border-ink/10 bg-paper/70 p-5 md:grid-cols-5">
          <SymbolSearch value={symbol} onChange={setSymbol} />
          <select
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
            className="border border-ink/15 bg-paper px-3 py-2.5 text-sm"
          >
            <option value="sma_crossover">SMA Crossover</option>
            <option value="ema_crossover">EMA Crossover</option>
            <option value="rsi">RSI</option>
            <option value="macd">MACD</option>
            <option value="bollinger">Bollinger</option>
            <option value="mean_reversion">Mean reversion</option>
          </select>
          <input type="date" value={start} onChange={(e) => setStart(e.target.value)} className="border border-ink/15 bg-paper px-2 py-2 text-sm" />
          <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} className="border border-ink/15 bg-paper px-2 py-2 text-sm" />
          <button type="button" onClick={run} disabled={loading} className="bg-ink text-sm text-paper disabled:opacity-60">
            {loading ? "Running…" : "Run lab"}
          </button>
        </div>

        {error && <p className="mt-4 text-sm text-alert">{error}</p>}

        {result && (
          <div className="mt-10 space-y-10">
            <div>
              <h2 className="font-display text-2xl text-ink">
                {result.symbol} · base backtest
              </h2>
              <div className="mt-4">
                <EquityChart data={result.base.equity_curve} />
              </div>
              <div className="mt-6">
                <MetricsGrid metrics={result.base.metrics} />
              </div>
            </div>

            <div>
              <h2 className="text-sm uppercase tracking-[0.16em] text-ink-muted">Walk-forward</h2>
              <p className="mt-2 text-sm text-ink-muted">
                Avg return {formatPct(result.walk_forward.summary.avg_return)} · Avg Sharpe{" "}
                {result.walk_forward.summary.avg_sharpe} · Positive folds{" "}
                {result.walk_forward.summary.positive_folds}/{result.walk_forward.summary.fold_count}
              </p>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full min-w-[560px] text-left text-sm">
                  <thead>
                    <tr className="border-b border-ink/10 text-[11px] uppercase tracking-[0.12em] text-ink-muted">
                      <th className="py-2">Fold</th>
                      <th className="py-2">Start</th>
                      <th className="py-2">End</th>
                      <th className="py-2">Return</th>
                      <th className="py-2">Sharpe</th>
                      <th className="py-2">Max DD</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.walk_forward.folds.map((f: any) => (
                      <tr key={f.fold} className="border-b border-ink/5">
                        <td className="py-2">{f.fold}</td>
                        <td className="py-2 font-mono text-xs">{f.start}</td>
                        <td className="py-2 font-mono text-xs">{f.end}</td>
                        <td className="py-2 font-mono">{formatPct(f.total_return)}</td>
                        <td className="py-2 font-mono">{f.sharpe_ratio}</td>
                        <td className="py-2 font-mono">{formatPct(f.max_drawdown)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div>
              <h2 className="text-sm uppercase tracking-[0.16em] text-ink-muted">Monte Carlo</h2>
              {result.monte_carlo.message ? (
                <p className="mt-2 text-sm text-ink-muted">{result.monte_carlo.message}</p>
              ) : (
                <div className="mt-4 grid gap-4 sm:grid-cols-3 lg:grid-cols-6">
                  {Object.entries(result.monte_carlo.percentiles).map(([k, v]) => (
                    <div key={k} className="border-t border-ink/15 pt-3">
                      <div className="text-[11px] uppercase tracking-[0.14em] text-ink-muted">{k}</div>
                      <div className="mt-1 font-mono">{formatPct(Number(v))}</div>
                    </div>
                  ))}
                  <div className="border-t border-ink/15 pt-3">
                    <div className="text-[11px] uppercase tracking-[0.14em] text-ink-muted">
                      P(profit)
                    </div>
                    <div className="mt-1 font-mono">
                      {formatPct(result.monte_carlo.prob_profit)}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
