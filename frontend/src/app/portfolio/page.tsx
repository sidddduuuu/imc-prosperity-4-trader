"use client";

import { useMemo, useState } from "react";
import { atlasApi, formatPct } from "@/lib/api";
import { EquityChart } from "@/components/EquityChart";

function defaultDates() {
  const end = new Date();
  const start = new Date();
  start.setFullYear(end.getFullYear() - 2);
  return { start: start.toISOString().slice(0, 10), end: end.toISOString().slice(0, 10) };
}

export default function PortfolioPage() {
  const dates = useMemo(() => defaultDates(), []);
  const [symbols, setSymbols] = useState("AAPL,MSFT,NVDA,GOOGL");
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
      const list = symbols
        .split(",")
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean);
      const data = await atlasApi.portfolioBacktest({
        symbols: list,
        strategy,
        start,
        end,
        initial_capital: 100000,
        commission: 0.001,
        params: strategy === "sma_crossover" ? { fast: 20, slow: 50 } : {},
      });
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-mesh">
      <div className="mx-auto max-w-6xl px-5 py-10 md:px-8">
        <p className="text-[11px] uppercase tracking-[0.2em] text-ink-muted">Multi-asset</p>
        <h1 className="mt-2 font-display text-4xl tracking-tight text-ink">
          Portfolio backtest
        </h1>
        <p className="mt-3 max-w-2xl text-ink-muted">
          Equal-weight (or custom) multi-symbol strategy simulation vs buy & hold basket.
        </p>

        <div className="mt-8 space-y-3 border border-ink/10 bg-paper/70 p-5">
          <label className="block">
            <span className="text-[11px] uppercase tracking-[0.14em] text-ink-muted">
              Symbols (comma-separated)
            </span>
            <input
              value={symbols}
              onChange={(e) => setSymbols(e.target.value)}
              className="mt-2 w-full border border-ink/15 bg-paper px-3 py-2.5 text-sm"
            />
          </label>
          <div className="grid gap-3 md:grid-cols-4">
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              className="border border-ink/15 bg-paper px-3 py-2.5 text-sm"
            >
              <option value="buy_and_hold">Buy & Hold</option>
              <option value="sma_crossover">SMA Crossover</option>
              <option value="ema_crossover">EMA Crossover</option>
              <option value="rsi">RSI</option>
              <option value="macd">MACD</option>
            </select>
            <input type="date" value={start} onChange={(e) => setStart(e.target.value)} className="border border-ink/15 bg-paper px-2 py-2 text-sm" />
            <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} className="border border-ink/15 bg-paper px-2 py-2 text-sm" />
            <button type="button" onClick={run} disabled={loading} className="bg-ink text-sm text-paper disabled:opacity-60">
              {loading ? "Running…" : "Run portfolio"}
            </button>
          </div>
        </div>

        {error && <p className="mt-4 text-sm text-alert">{error}</p>}

        {result && (
          <div className="mt-10 space-y-8">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                ["Return", formatPct(result.metrics.total_return)],
                ["Buy & hold", formatPct(result.metrics.buy_hold_return)],
                ["Alpha", formatPct(result.metrics.alpha)],
                ["Sharpe", String(result.metrics.sharpe_ratio)],
              ].map(([label, value]) => (
                <div key={label} className="border-t border-ink/15 pt-3">
                  <div className="text-[11px] uppercase tracking-[0.14em] text-ink-muted">{label}</div>
                  <div className="mt-1 font-mono text-xl">{value}</div>
                </div>
              ))}
            </div>
            <EquityChart data={result.equity_curve} />
            <div>
              <h2 className="text-sm uppercase tracking-[0.16em] text-ink-muted">Legs</h2>
              <div className="mt-3 divide-y divide-ink/10">
                {result.legs.map((leg: any) => (
                  <div key={leg.symbol} className="flex justify-between py-3 text-sm">
                    <div>
                      {leg.symbol} · weight {(leg.weight * 100).toFixed(0)}%
                    </div>
                    <div className="font-mono">{formatPct(leg.metrics.total_return)}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
