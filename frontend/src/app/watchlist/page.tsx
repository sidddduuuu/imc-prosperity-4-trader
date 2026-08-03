"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { atlasApi, formatMoney, formatPct } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { SymbolSearch } from "@/components/SymbolSearch";

export default function WatchlistPage() {
  const { token, user } = useAuth();
  const [lists, setLists] = useState<any[]>([]);
  const [symbol, setSymbol] = useState("NVDA");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (!token) return;
    try {
      setLists(await atlasApi.watchlists(token));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }

  useEffect(() => {
    load();
  }, [token]);

  if (!user || !token) {
    return (
      <Gate
        title="Watchlists"
        copy="Log in to save tickers and track them across sessions."
      />
    );
  }

  const wl = lists[0];

  return (
    <div className="min-h-screen bg-mesh">
      <div className="mx-auto max-w-6xl px-5 py-10 md:px-8">
        <p className="text-[11px] uppercase tracking-[0.2em] text-ink-muted">Desk</p>
        <h1 className="mt-2 font-display text-4xl tracking-tight text-ink">Watchlist</h1>
        <div className="mt-6 flex max-w-md gap-2">
          <SymbolSearch value={symbol} onChange={setSymbol} />
          <button
            type="button"
            className="bg-ink px-4 text-sm text-paper"
            onClick={async () => {
              if (!wl) return;
              try {
                await atlasApi.addWatch(token, wl.id, symbol);
                await load();
              } catch (e) {
                setError(e instanceof Error ? e.message : "Add failed");
              }
            }}
          >
            Add
          </button>
        </div>
        {error && <p className="mt-4 text-sm text-alert">{error}</p>}
        <div className="mt-8 divide-y divide-ink/10">
          {(wl?.items || []).map((item: any) => (
            <div key={item.id} className="flex items-center justify-between py-4">
              <div>
                <Link href={`/analyze/${item.symbol}`} className="text-lg text-ink hover:text-signal">
                  {item.symbol}
                </Link>
                {item.quote && (
                  <div className="mt-1 font-mono text-sm text-ink-muted">
                    {formatMoney(item.quote.price)}{" "}
                    <span className={item.quote.change_percent >= 0 ? "text-signal" : "text-alert"}>
                      {formatPct(item.quote.change_percent / 100)}
                    </span>
                  </div>
                )}
              </div>
              <button
                type="button"
                className="text-xs text-ink-muted underline"
                onClick={async () => {
                  await atlasApi.removeWatch(token, wl.id, item.id);
                  await load();
                }}
              >
                Remove
              </button>
            </div>
          ))}
          {wl && wl.items?.length === 0 && (
            <p className="py-8 text-ink-muted">No symbols yet — add your first ticker.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function Gate({ title, copy }: { title: string; copy: string }) {
  return (
    <div className="min-h-[60vh] bg-mesh px-5 py-16 md:px-8">
      <div className="mx-auto max-w-6xl">
        <h1 className="font-display text-4xl tracking-tight text-ink">{title}</h1>
        <p className="mt-3 max-w-lg text-ink-muted">{copy}</p>
        <Link href="/login" className="mt-6 inline-block bg-ink px-5 py-3 text-sm text-paper">
          Log in
        </Link>
      </div>
    </div>
  );
}
