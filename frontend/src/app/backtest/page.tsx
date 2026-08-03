"use client";

import { useEffect, useMemo, useState } from "react";
import {
  atlasApi,
  formatMoney,
  type BacktestResult,
  type StrategyInfo,
} from "@/lib/api";
import { EquityChart } from "@/components/EquityChart";
import { MetricsGrid } from "@/components/MetricsGrid";
import { SymbolSearch } from "@/components/SymbolSearch";

function defaultDates() {
  const end = new Date();
  const start = new Date();
  start.setFullYear(end.getFullYear() - 2);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
}

export default function BacktestPage() {
  const dates = useMemo(() => defaultDates(), []);
  const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
  const [symbol, setSymbol] = useState("AAPL");
  const [strategy, setStrategy] = useState("sma_crossover");
  const [start, setStart] = useState(dates.start);
  const [end, setEnd] = useState(dates.end);
  const [capital, setCapital] = useState(100000);
  const [commission, setCommission] = useState(0.001);
  const [params, setParams] = useState<Record<string, number>>({});
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    atlasApi.strategies().then((list) => {
      setStrategies(list);
      const first = list.find((s) => s.id === "sma_crossover") || list[0];
      if (first) {
        setStrategy(first.id);
        const defaults: Record<string, number> = {};
        first.params.forEach((p) => {
          defaults[p.name] = p.default;
        });
        setParams(defaults);
      }
    });
  }, []);

  const selected = strategies.find((s) => s.id === strategy);

  useEffect(() => {
    if (!selected) return;
    const defaults: Record<string, number> = {};
    selected.params.forEach((p) => {
      defaults[p.name] = params[p.name] ?? p.default;
    });
    setParams(defaults);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [strategy, strategies]);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const data = await atlasApi.backtest({
        symbol,
        strategy,
        start,
        end,
        initial_capital: capital,
        commission,
        params,
      });
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Backtest failed");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-mesh">
      <div className="mx-auto max-w-6xl px-5 py-10 md:px-8">
        <p className="text-[11px] uppercase tracking-[0.2em] text-ink-muted">Lab</p>
        <h1 className="mt-2 font-display text-4xl tracking-tight text-ink md:text-5xl">
          Strategy backtester
        </h1>
        <p className="mt-3 max-w-2xl text-ink-muted">
          Configure a strategy, run it on historical prices, and inspect equity, risk, and every fill.
        </p>

        <div className="mt-10 grid gap-10 lg:grid-cols-[320px_1fr]">
          <aside className="space-y-5 border border-ink/10 bg-paper/70 p-5 backdrop-blur-sm">
            <label className="block">
              <span className="text-[11px] uppercase tracking-[0.14em] text-ink-muted">Symbol</span>
              <div className="mt-2">
                <SymbolSearch value={symbol} onChange={setSymbol} />
              </div>
            </label>

            <label className="block">
              <span className="text-[11px] uppercase tracking-[0.14em] text-ink-muted">Strategy</span>
              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                className="mt-2 w-full border border-ink/15 bg-paper px-3 py-2.5 text-sm outline-none"
              >
                {strategies.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
              {selected && (
                <p className="mt-2 text-xs leading-relaxed text-ink-muted">{selected.description}</p>
              )}
            </label>

            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="text-[11px] uppercase tracking-[0.14em] text-ink-muted">Start</span>
                <input
                  type="date"
                  value={start}
                  onChange={(e) => setStart(e.target.value)}
                  className="mt-2 w-full border border-ink/15 bg-paper px-2 py-2 text-sm outline-none"
                />
              </label>
              <label className="block">
                <span className="text-[11px] uppercase tracking-[0.14em] text-ink-muted">End</span>
                <input
                  type="date"
                  value={end}
                  onChange={(e) => setEnd(e.target.value)}
                  className="mt-2 w-full border border-ink/15 bg-paper px-2 py-2 text-sm outline-none"
                />
              </label>
            </div>

            <label className="block">
              <span className="text-[11px] uppercase tracking-[0.14em] text-ink-muted">
                Initial capital
              </span>
              <input
                type="number"
                value={capital}
                onChange={(e) => setCapital(Number(e.target.value))}
                className="mt-2 w-full border border-ink/15 bg-paper px-3 py-2.5 text-sm outline-none"
              />
            </label>

            <label className="block">
              <span className="text-[11px] uppercase tracking-[0.14em] text-ink-muted">
                Commission ({(commission * 100).toFixed(2)}%)
              </span>
              <input
                type="range"
                min={0}
                max={0.01}
                step={0.0005}
                value={commission}
                onChange={(e) => setCommission(Number(e.target.value))}
                className="mt-3 w-full accent-signal"
              />
            </label>

            {selected?.params.map((p) => (
              <label key={p.name} className="block">
                <span className="text-[11px] uppercase tracking-[0.14em] text-ink-muted">
                  {p.label}
                </span>
                <input
                  type="number"
                  step={p.type === "float" ? 0.1 : 1}
                  min={p.min}
                  max={p.max}
                  value={params[p.name] ?? p.default}
                  onChange={(e) =>
                    setParams((prev) => ({ ...prev, [p.name]: Number(e.target.value) }))
                  }
                  className="mt-2 w-full border border-ink/15 bg-paper px-3 py-2.5 text-sm outline-none"
                />
              </label>
            ))}

            <button
              type="button"
              onClick={run}
              disabled={loading}
              className="w-full bg-ink py-3 text-sm text-paper transition hover:bg-ink-soft disabled:opacity-60"
            >
              {loading ? "Running…" : "Run backtest"}
            </button>
            {error && <p className="text-sm text-alert">{error}</p>}
          </aside>

          <section>
            {!result && !loading && (
              <div className="flex h-full min-h-[420px] items-center justify-center border border-dashed border-ink/15 px-6 text-center text-ink-muted">
                Configure a strategy and run a backtest to see equity curves and metrics.
              </div>
            )}
            {loading && (
              <div className="flex h-full min-h-[420px] items-center justify-center text-ink-muted">
                Simulating trades…
              </div>
            )}
            {result && !loading && (
              <div className="space-y-10">
                <div>
                  <h2 className="font-display text-2xl tracking-tight text-ink">
                    {result.symbol} · {selected?.name || result.strategy}
                  </h2>
                  <p className="mt-1 text-sm text-ink-muted">
                    {formatMoney(result.metrics.initial_capital)} →{" "}
                    {formatMoney(result.metrics.final_equity)}
                  </p>
                </div>
                <EquityChart data={result.equity_curve} />
                <MetricsGrid metrics={result.metrics} />

                <div>
                  <h3 className="text-sm uppercase tracking-[0.16em] text-ink-muted">Trade log</h3>
                  <div className="mt-3 overflow-x-auto">
                    <table className="w-full min-w-[560px] text-left text-sm">
                      <thead>
                        <tr className="border-b border-ink/10 text-[11px] uppercase tracking-[0.12em] text-ink-muted">
                          <th className="py-2 font-medium">Date</th>
                          <th className="py-2 font-medium">Side</th>
                          <th className="py-2 font-medium">Price</th>
                          <th className="py-2 font-medium">Shares</th>
                          <th className="py-2 font-medium">Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.trades.map((t, i) => (
                          <tr key={`${t.date}-${t.side}-${i}`} className="border-b border-ink/5">
                            <td className="py-2 font-mono text-xs">{t.date}</td>
                            <td
                              className={`py-2 uppercase ${
                                t.side === "buy" ? "text-signal" : "text-alert"
                              }`}
                            >
                              {t.side}
                            </td>
                            <td className="py-2 font-mono tabular-nums">{formatMoney(t.price)}</td>
                            <td className="py-2 font-mono tabular-nums">{t.shares.toFixed(2)}</td>
                            <td className="py-2 font-mono tabular-nums">{formatMoney(t.value)}</td>
                          </tr>
                        ))}
                        {result.trades.length === 0 && (
                          <tr>
                            <td colSpan={5} className="py-4 text-ink-muted">
                              No trades generated for this configuration.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
