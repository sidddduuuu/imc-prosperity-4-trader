"use client";

import { useEffect, useState } from "react";
import { atlasApi, type NewsItem } from "@/lib/api";
import { SymbolSearch } from "@/components/SymbolSearch";
import { ExternalLink } from "lucide-react";

function sentimentClass(s?: string | null) {
  if (s === "bullish") return "text-signal";
  if (s === "bearish") return "text-alert";
  return "text-ink-muted";
}

export default function NewsPage() {
  const [symbol, setSymbol] = useState("");
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await atlasApi.news(symbol || undefined, 40);
        if (!cancelled) setItems(data);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load news");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [symbol]);

  return (
    <div className="min-h-screen bg-mesh">
      <div className="mx-auto max-w-6xl px-5 py-10 md:px-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-[0.2em] text-ink-muted">Wire</p>
            <h1 className="mt-2 font-display text-4xl tracking-tight text-ink md:text-5xl">
              Trading news
            </h1>
            <p className="mt-3 max-w-xl text-ink-muted">
              Markets, stocks, earnings, and macro that moves price — no lifestyle fluff.
              Filter by ticker or browse the tape.
            </p>
          </div>
          <div className="w-full max-w-sm">
            <SymbolSearch
              value={symbol}
              onChange={(s) => setSymbol(s)}
              placeholder="Filter by ticker…"
            />
            {symbol && (
              <button
                type="button"
                className="mt-2 text-xs text-ink-muted underline"
                onClick={() => setSymbol("")}
              >
                Clear filter
              </button>
            )}
          </div>
        </div>

        {loading && <p className="mt-10 text-sm text-ink-muted">Fetching headlines…</p>}
        {error && <p className="mt-10 text-sm text-alert">{error}</p>}

        <div className="mt-10 divide-y divide-ink/10">
          {items.map((item, idx) => (
            <article key={`${item.link}-${idx}`} className="py-6">
              <div className="flex flex-wrap items-center gap-3 text-[11px] uppercase tracking-[0.14em] text-ink-muted">
                <span>{item.source}</span>
                {item.published && <span>· {item.published}</span>}
                {item.symbol && <span>· {item.symbol}</span>}
                {item.sentiment && (
                  <span className={sentimentClass(item.sentiment)}>{item.sentiment}</span>
                )}
              </div>
              <a
                href={item.link || "#"}
                target="_blank"
                rel="noreferrer"
                className="group mt-2 inline-flex items-start gap-2"
              >
                <h2 className="text-xl leading-snug text-ink transition group-hover:text-signal md:text-2xl">
                  {item.title}
                </h2>
                <ExternalLink size={14} className="mt-2 shrink-0 text-mist opacity-0 transition group-hover:opacity-100" />
              </a>
              {item.summary && (
                <p className="mt-2 max-w-3xl text-sm leading-relaxed text-ink-muted">{item.summary}</p>
              )}
            </article>
          ))}
          {!loading && items.length === 0 && (
            <p className="py-10 text-ink-muted">No headlines found.</p>
          )}
        </div>
      </div>
    </div>
  );
}
