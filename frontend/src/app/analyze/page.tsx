"use client";

import { useRouter } from "next/navigation";
import { SymbolSearch } from "@/components/SymbolSearch";

export default function AnalyzeIndexPage() {
  const router = useRouter();

  return (
    <div className="min-h-[70vh] bg-mesh">
      <div className="mx-auto flex max-w-6xl flex-col items-start px-5 py-16 md:px-8">
        <p className="text-[11px] uppercase tracking-[0.2em] text-ink-muted">Research</p>
        <h1 className="mt-2 font-display text-4xl tracking-tight text-ink md:text-5xl">
          Stock analysis
        </h1>
        <p className="mt-3 max-w-xl text-ink-muted">
          Pull quotes, technical indicators, trend bias, and chart history for any listed equity.
        </p>
        <div className="mt-8 w-full max-w-md">
          <SymbolSearch
            value=""
            onChange={(symbol) => router.push(`/analyze/${symbol}`)}
            placeholder="Enter a ticker to analyze…"
          />
        </div>
        <div className="mt-8 flex flex-wrap gap-2">
          {["AAPL", "NVDA", "MSFT", "TSLA", "SPY", "AMD"].map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => router.push(`/analyze/${s}`)}
              className="border border-ink/15 px-3 py-1.5 text-sm text-ink-muted transition hover:border-ink/30 hover:text-ink"
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
