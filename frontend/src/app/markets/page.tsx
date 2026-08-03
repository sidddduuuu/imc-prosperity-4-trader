"use client";

import { useCallback, useEffect, useState } from "react";
import { atlasApi, type Candle, type Quote } from "@/lib/api";
import { CandleChart } from "@/components/CandleChart";
import { QuotePanel, QuoteStrip } from "@/components/QuotePanel";
import { SymbolSearch } from "@/components/SymbolSearch";

const PERIODS = ["3mo", "6mo", "1y", "2y", "5y"] as const;

export default function MarketsPage() {
  const [symbol, setSymbol] = useState("SPY");
  const [period, setPeriod] = useState<(typeof PERIODS)[number]>("1y");
  const [quote, setQuote] = useState<Quote | null>(null);
  const [candles, setCandles] = useState<Candle[]>([]);
  const [popular, setPopular] = useState<Quote[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (sym: string, per: string) => {
    setLoading(true);
    setError(null);
    try {
      const [q, h] = await Promise.all([atlasApi.quote(sym), atlasApi.history(sym, per)]);
      setQuote(q);
      setCandles(h.candles);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load market data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(symbol, period);
  }, [symbol, period, load]);

  useEffect(() => {
    atlasApi.popular().then(setPopular).catch(() => undefined);
  }, []);

  return (
    <div className="bg-mesh min-h-screen">
      {popular.length > 0 && <QuoteStrip quotes={popular} />}
      <div className="mx-auto max-w-6xl px-5 py-10 md:px-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-[0.2em] text-ink-muted">Markets</p>
            <h1 className="mt-2 font-display text-4xl tracking-tight text-ink">Charts</h1>
          </div>
          <div className="w-full max-w-sm">
            <SymbolSearch value={symbol} onChange={setSymbol} />
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-2">
          {PERIODS.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setPeriod(p)}
              className={`px-3 py-1.5 text-xs uppercase tracking-wide transition ${
                period === p ? "bg-ink text-paper" : "border border-ink/15 text-ink-muted hover:text-ink"
              }`}
            >
              {p}
            </button>
          ))}
        </div>

        {error && <p className="mt-6 text-sm text-alert">{error}</p>}
        {loading && !quote && <p className="mt-10 text-sm text-ink-muted">Loading market data…</p>}

        {quote && (
          <div className="mt-10 space-y-10">
            <QuotePanel quote={quote} />
            <CandleChart candles={candles} />
          </div>
        )}
      </div>
    </div>
  );
}
