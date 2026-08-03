"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { atlasApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function CommunityPage() {
  const { token, user } = useAuth();
  const [items, setItems] = useState<any[]>([]);
  const [title, setTitle] = useState("");
  const [strategy, setStrategy] = useState("sma_crossover");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setItems(await atlasApi.community());
  }

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, []);

  return (
    <div className="min-h-screen bg-mesh">
      <div className="mx-auto max-w-6xl px-5 py-10 md:px-8">
        <p className="text-[11px] uppercase tracking-[0.2em] text-ink-muted">Share</p>
        <h1 className="mt-2 font-display text-4xl tracking-tight text-ink">Community</h1>
        <p className="mt-3 max-w-2xl text-ink-muted">
          Publish strategy configs for others to try in the backtester.
        </p>

        {user && token && (
          <div className="mt-8 space-y-3 border border-ink/10 bg-paper/70 p-5">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Strategy title"
              className="w-full border border-ink/15 bg-paper px-3 py-2.5 text-sm"
            />
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What edge are you sharing?"
              className="h-24 w-full border border-ink/15 bg-paper px-3 py-2.5 text-sm"
            />
            <div className="flex flex-wrap gap-3">
              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                className="border border-ink/15 bg-paper px-3 py-2 text-sm"
              >
                <option value="sma_crossover">SMA Crossover</option>
                <option value="ema_crossover">EMA Crossover</option>
                <option value="rsi">RSI</option>
                <option value="macd">MACD</option>
                <option value="bollinger">Bollinger</option>
                <option value="mean_reversion">Mean reversion</option>
              </select>
              <button
                type="button"
                className="bg-ink px-4 py-2 text-sm text-paper"
                onClick={async () => {
                  try {
                    await atlasApi.shareStrategy(token, {
                      title,
                      description,
                      strategy,
                      params: {},
                      symbol_example: "SPY",
                    });
                    setTitle("");
                    setDescription("");
                    await load();
                  } catch (e) {
                    setError(e instanceof Error ? e.message : "Share failed");
                  }
                }}
              >
                Publish
              </button>
            </div>
          </div>
        )}

        {!user && (
          <p className="mt-6 text-sm text-ink-muted">
            <Link href="/login" className="underline">
              Log in
            </Link>{" "}
            to publish strategies.
          </p>
        )}

        {error && <p className="mt-4 text-sm text-alert">{error}</p>}

        <div className="mt-10 divide-y divide-ink/10">
          {items.map((item) => (
            <article key={item.id} className="py-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl text-ink">{item.title}</h2>
                  <p className="mt-1 text-xs uppercase tracking-[0.14em] text-ink-muted">
                    {item.author} · {item.strategy} · {item.symbol_example}
                  </p>
                </div>
                <button
                  type="button"
                  className="border border-ink/15 px-3 py-1.5 text-xs"
                  onClick={async () => {
                    await atlasApi.likeStrategy(item.id);
                    await load();
                  }}
                >
                  ★ {item.likes}
                </button>
              </div>
              {item.description && (
                <p className="mt-3 max-w-3xl text-sm text-ink-muted">{item.description}</p>
              )}
              <Link
                href={`/backtest`}
                className="mt-3 inline-block text-sm text-signal hover:underline"
              >
                Open in backtester →
              </Link>
            </article>
          ))}
          {items.length === 0 && <p className="py-8 text-ink-muted">No shared strategies yet.</p>}
        </div>
      </div>
    </div>
  );
}
