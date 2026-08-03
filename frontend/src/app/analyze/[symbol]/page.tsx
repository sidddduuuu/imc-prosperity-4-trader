"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  atlasApi,
  type AnalysisResponse,
  type Candle,
  type NewsItem,
  type Quote,
} from "@/lib/api";
import { CandleChart } from "@/components/CandleChart";
import { QuotePanel } from "@/components/QuotePanel";
import { SymbolSearch } from "@/components/SymbolSearch";

export default function AnalyzeSymbolPage() {
  const params = useParams<{ symbol: string }>();
  const router = useRouter();
  const symbol = (params.symbol || "AAPL").toUpperCase();

  const [quote, setQuote] = useState<Quote | null>(null);
  const [candles, setCandles] = useState<Candle[]>([]);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [q, h, a, n] = await Promise.all([
          atlasApi.quote(symbol),
          atlasApi.history(symbol, "1y"),
          atlasApi.analysis(symbol, "1y"),
          atlasApi.news(symbol, 8),
        ]);
        if (cancelled) return;
        setQuote(q);
        setCandles(h.candles);
        setAnalysis(a);
        setNews(n);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Analysis failed");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [symbol]);

  const rsiSeries = useMemo(() => {
    if (!analysis) return [];
    return analysis.indicators
      .filter((p) => p.values.rsi_14 != null)
      .map((p) => ({ time: p.time, rsi: p.values.rsi_14 }));
  }, [analysis]);

  return (
    <div className="min-h-screen bg-mesh">
      <div className="mx-auto max-w-6xl px-5 py-10 md:px-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-[0.2em] text-ink-muted">Analyze</p>
            <h1 className="mt-2 font-display text-3xl tracking-tight text-ink md:text-4xl">
              Technical desk
            </h1>
          </div>
          <div className="w-full max-w-sm">
            <SymbolSearch value={symbol} onChange={(s) => router.push(`/analyze/${s}`)} />
          </div>
        </div>

        {loading && <p className="mt-10 text-sm text-ink-muted">Building analysis…</p>}
        {error && <p className="mt-10 text-sm text-alert">{error}</p>}

        {quote && !loading && (
          <div className="mt-10 space-y-12">
            <QuotePanel quote={quote} />

            {analysis && (
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                {[
                  ["Trend", String(analysis.summary.trend || "—")],
                  ["RSI", `${analysis.summary.rsi ?? "—"} (${analysis.summary.rsi_signal || "—"})`],
                  ["MACD", String(analysis.summary.macd_bias || "—")],
                  ["ATR(14)", String(analysis.summary.atr_14 ?? "—")],
                ].map(([label, value]) => (
                  <div key={label} className="border-t border-ink/15 pt-3">
                    <div className="text-[11px] uppercase tracking-[0.14em] text-ink-muted">
                      {label}
                    </div>
                    <div className="mt-1 text-lg capitalize text-ink">{value}</div>
                  </div>
                ))}
              </div>
            )}

            <div>
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm uppercase tracking-[0.16em] text-ink-muted">Price</h2>
                <Link href={`/backtest`} className="text-sm text-signal hover:underline">
                  Backtest this symbol →
                </Link>
              </div>
              <CandleChart candles={candles} />
            </div>

            {rsiSeries.length > 0 && (
              <div>
                <h2 className="mb-4 text-sm uppercase tracking-[0.16em] text-ink-muted">RSI (14)</h2>
                <div className="h-[220px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={rsiSeries}>
                      <CartesianGrid stroke="rgba(16,20,24,0.06)" vertical={false} />
                      <XAxis dataKey="time" hide />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#5A6672" }} width={36} />
                      <Tooltip />
                      <Area type="monotone" dataKey="rsi" stroke="#0C8F6A" fill="rgba(12,143,106,0.15)" strokeWidth={2} dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            <div>
              <h2 className="text-sm uppercase tracking-[0.16em] text-ink-muted">
                Related headlines
              </h2>
              <div className="mt-4 divide-y divide-ink/10">
                {news.map((item, i) => (
                  <a
                    key={`${item.link}-${i}`}
                    href={item.link || "#"}
                    target="_blank"
                    rel="noreferrer"
                    className="block py-4 transition hover:bg-paper-warm/60"
                  >
                    <div className="text-[11px] uppercase tracking-[0.12em] text-ink-muted">
                      {item.source}
                      {item.sentiment ? ` · ${item.sentiment}` : ""}
                    </div>
                    <div className="mt-1 text-base text-ink">{item.title}</div>
                  </a>
                ))}
                {news.length === 0 && (
                  <p className="py-4 text-sm text-ink-muted">No ticker-specific headlines.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
