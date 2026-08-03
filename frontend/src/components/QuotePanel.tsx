import type { Quote } from "@/lib/api";
import { formatCompact, formatMoney } from "@/lib/api";
import Link from "next/link";

export function QuoteStrip({ quotes }: { quotes: Quote[] }) {
  return (
    <div className="flex gap-0 overflow-x-auto border-y border-ink/10">
      {quotes.map((q) => {
        const up = q.change >= 0;
        return (
          <Link
            key={q.symbol}
            href={`/analyze/${q.symbol}`}
            className="min-w-[148px] border-r border-ink/10 px-4 py-3 transition hover:bg-paper-warm"
          >
            <div className="text-xs tracking-wide text-ink-muted">{q.symbol}</div>
            <div className="mt-1 font-mono text-sm tabular-nums">{formatMoney(q.price)}</div>
            <div className={`mt-0.5 font-mono text-xs tabular-nums ${up ? "text-signal" : "text-alert"}`}>
              {up ? "+" : ""}
              {q.change_percent.toFixed(2)}%
            </div>
          </Link>
        );
      })}
    </div>
  );
}

export function QuotePanel({ quote }: { quote: Quote }) {
  const up = quote.change >= 0;
  const rows = [
    ["Open", quote.open != null ? formatMoney(quote.open) : "—"],
    ["High", quote.high != null ? formatMoney(quote.high) : "—"],
    ["Low", quote.low != null ? formatMoney(quote.low) : "—"],
    ["Volume", formatCompact(quote.volume)],
    ["Market cap", formatCompact(quote.market_cap)],
    ["P/E", quote.pe_ratio != null ? quote.pe_ratio.toFixed(2) : "—"],
    ["EPS", quote.eps != null ? formatMoney(quote.eps) : "—"],
    ["52W high", quote.fifty_two_week_high != null ? formatMoney(quote.fifty_two_week_high) : "—"],
    ["52W low", quote.fifty_two_week_low != null ? formatMoney(quote.fifty_two_week_low) : "—"],
    ["Div yield", quote.dividend_yield != null ? `${(quote.dividend_yield * 100).toFixed(2)}%` : "—"],
  ] as const;

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-4xl tracking-tight text-ink md:text-5xl">{quote.symbol}</h1>
          <p className="mt-1 text-ink-muted">{quote.name}</p>
          {(quote.sector || quote.industry) && (
            <p className="mt-2 text-xs uppercase tracking-[0.16em] text-mist">
              {[quote.sector, quote.industry].filter(Boolean).join(" · ")}
            </p>
          )}
        </div>
        <div className="text-right">
          <div className="font-mono text-3xl tabular-nums text-ink">{formatMoney(quote.price)}</div>
          <div className={`mt-1 font-mono text-sm tabular-nums ${up ? "text-signal" : "text-alert"}`}>
            {up ? "+" : ""}
            {quote.change.toFixed(2)} ({up ? "+" : ""}
            {quote.change_percent.toFixed(2)}%)
          </div>
        </div>
      </div>
      <div className="mt-8 grid grid-cols-2 gap-x-8 gap-y-3 sm:grid-cols-3 lg:grid-cols-5">
        {rows.map(([label, value]) => (
          <div key={label}>
            <div className="text-[11px] uppercase tracking-[0.14em] text-ink-muted">{label}</div>
            <div className="mt-1 font-mono text-sm tabular-nums text-ink">{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
