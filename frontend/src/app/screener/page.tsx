"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { atlasApi, formatCompact, formatMoney, formatPct } from "@/lib/api";

export default function ScreenerPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [trend, setTrend] = useState("");
  const [rsiMax, setRsiMax] = useState("");
  const [minChange, setMinChange] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const data = await atlasApi.screener({
        trend: trend || undefined,
        rsi_max: rsiMax || undefined,
        min_change_pct: minChange || undefined,
        limit: 30,
      });
      setRows(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Screener failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    run();
  }, []);

  return (
    <div className="min-h-screen bg-mesh">
      <div className="mx-auto max-w-6xl px-5 py-10 md:px-8">
        <p className="text-[11px] uppercase tracking-[0.2em] text-ink-muted">Scan</p>
        <h1 className="mt-2 font-display text-4xl tracking-tight text-ink">Screener</h1>
        <p className="mt-3 max-w-2xl text-ink-muted">
          Filter the liquid universe by trend, RSI, and momentum.
        </p>

        <div className="mt-8 flex flex-wrap items-end gap-3">
          <label className="text-sm">
            <span className="block text-[11px] uppercase tracking-[0.14em] text-ink-muted">Trend</span>
            <select
              value={trend}
              onChange={(e) => setTrend(e.target.value)}
              className="mt-2 border border-ink/15 bg-paper px-3 py-2"
            >
              <option value="">Any</option>
              <option value="bullish">Bullish</option>
              <option value="bearish">Bearish</option>
              <option value="neutral">Neutral</option>
            </select>
          </label>
          <label className="text-sm">
            <span className="block text-[11px] uppercase tracking-[0.14em] text-ink-muted">
              RSI max
            </span>
            <input
              value={rsiMax}
              onChange={(e) => setRsiMax(e.target.value)}
              placeholder="e.g. 35"
              className="mt-2 w-28 border border-ink/15 bg-paper px-3 py-2"
            />
          </label>
          <label className="text-sm">
            <span className="block text-[11px] uppercase tracking-[0.14em] text-ink-muted">
              Min change %
            </span>
            <input
              value={minChange}
              onChange={(e) => setMinChange(e.target.value)}
              placeholder="e.g. 1"
              className="mt-2 w-28 border border-ink/15 bg-paper px-3 py-2"
            />
          </label>
          <button type="button" onClick={run} className="bg-ink px-4 py-2 text-sm text-paper">
            Run screen
          </button>
        </div>

        {loading && <p className="mt-8 text-sm text-ink-muted">Scanning universe…</p>}
        {error && <p className="mt-8 text-sm text-alert">{error}</p>}

        <div className="mt-8 overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead>
              <tr className="border-b border-ink/10 text-[11px] uppercase tracking-[0.12em] text-ink-muted">
                <th className="py-2 font-medium">Symbol</th>
                <th className="py-2 font-medium">Price</th>
                <th className="py-2 font-medium">Change</th>
                <th className="py-2 font-medium">RSI</th>
                <th className="py-2 font-medium">Trend</th>
                <th className="py-2 font-medium">Mkt cap</th>
                <th className="py-2 font-medium">P/E</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.symbol as string} className="border-b border-ink/5">
                  <td className="py-3">
                    <Link href={`/analyze/${r.symbol}`} className="font-medium hover:text-signal">
                      {r.symbol as string}
                    </Link>
                  </td>
                  <td className="py-3 font-mono">{formatMoney(Number(r.price))}</td>
                  <td
                    className={`py-3 font-mono ${
                      Number(r.change_percent) >= 0 ? "text-signal" : "text-alert"
                    }`}
                  >
                    {formatPct(Number(r.change_percent) / 100)}
                  </td>
                  <td className="py-3 font-mono">{r.rsi != null ? String(r.rsi) : "—"}</td>
                  <td className="py-3 capitalize">{String(r.trend)}</td>
                  <td className="py-3 font-mono">{formatCompact(r.market_cap as number)}</td>
                  <td className="py-3 font-mono">
                    {r.pe_ratio != null ? Number(r.pe_ratio).toFixed(1) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
