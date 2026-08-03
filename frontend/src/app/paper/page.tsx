"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { atlasApi, formatMoney, formatPct } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { SymbolSearch } from "@/components/SymbolSearch";

export default function PaperPage() {
  const { token, user } = useAuth();
  const [account, setAccount] = useState<any>(null);
  const [symbol, setSymbol] = useState("SPY");
  const [shares, setShares] = useState(10);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (!token) return;
    setAccount(await atlasApi.paper(token));
  }

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, [token]);

  if (!user || !token) {
    return (
      <div className="min-h-[60vh] bg-mesh px-5 py-16">
        <div className="mx-auto max-w-6xl">
          <h1 className="font-display text-4xl text-ink">Paper trading</h1>
          <p className="mt-3 text-ink-muted">Log in to trade a simulated $100k account.</p>
          <Link href="/login" className="mt-6 inline-block bg-ink px-5 py-3 text-sm text-paper">
            Log in
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-mesh">
      <div className="mx-auto max-w-6xl px-5 py-10 md:px-8">
        <p className="text-[11px] uppercase tracking-[0.2em] text-ink-muted">Simulate</p>
        <h1 className="mt-2 font-display text-4xl tracking-tight text-ink">Paper desk</h1>

        {account && (
          <div className="mt-8 grid gap-6 sm:grid-cols-4">
            {[
              ["Equity", formatMoney(account.equity)],
              ["Cash", formatMoney(account.cash)],
              ["P&L", formatMoney(account.pnl)],
              ["Return", formatPct(account.pnl_pct)],
            ].map(([label, value]) => (
              <div key={label} className="border-t border-ink/15 pt-3">
                <div className="text-[11px] uppercase tracking-[0.14em] text-ink-muted">{label}</div>
                <div className="mt-1 font-mono text-xl">{value}</div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-8 grid gap-3 border border-ink/10 bg-paper/70 p-5 md:grid-cols-4">
          <SymbolSearch value={symbol} onChange={setSymbol} />
          <input
            type="number"
            min={0.01}
            step={1}
            value={shares}
            onChange={(e) => setShares(Number(e.target.value))}
            className="border border-ink/15 bg-paper px-3 py-2.5 text-sm"
          />
          <button
            type="button"
            className="bg-signal text-sm text-paper"
            onClick={async () => {
              try {
                const res: any = await atlasApi.paperOrder(token, { symbol, side: "buy", shares });
                setAccount(res.account);
              } catch (e) {
                setError(e instanceof Error ? e.message : "Order failed");
              }
            }}
          >
            Buy
          </button>
          <button
            type="button"
            className="bg-alert text-sm text-paper"
            onClick={async () => {
              try {
                const res: any = await atlasApi.paperOrder(token, { symbol, side: "sell", shares });
                setAccount(res.account);
              } catch (e) {
                setError(e instanceof Error ? e.message : "Order failed");
              }
            }}
          >
            Sell
          </button>
        </div>

        <button
          type="button"
          className="mt-3 text-xs text-ink-muted underline"
          onClick={async () => setAccount(await atlasApi.paperReset(token))}
        >
          Reset paper account
        </button>

        {error && <p className="mt-4 text-sm text-alert">{error}</p>}

        <h2 className="mt-10 text-sm uppercase tracking-[0.16em] text-ink-muted">Positions</h2>
        <div className="mt-3 divide-y divide-ink/10">
          {(account?.positions || []).map((p: any) => (
            <div key={p.symbol} className="flex justify-between py-3 text-sm">
              <div>
                <Link href={`/analyze/${p.symbol}`} className="font-medium hover:text-signal">
                  {p.symbol}
                </Link>
                <div className="text-ink-muted">
                  {p.shares} sh @ {formatMoney(p.avg_cost)}
                </div>
              </div>
              <div className="text-right font-mono">
                <div>{formatMoney(p.market_value)}</div>
                <div className={p.pnl >= 0 ? "text-signal" : "text-alert"}>
                  {formatMoney(p.pnl)} ({formatPct(p.pnl_pct)})
                </div>
              </div>
            </div>
          ))}
          {account && account.positions?.length === 0 && (
            <p className="py-6 text-ink-muted">Flat — place a buy to open a position.</p>
          )}
        </div>

        <h2 className="mt-10 text-sm uppercase tracking-[0.16em] text-ink-muted">Orders</h2>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[520px] text-left text-sm">
            <thead>
              <tr className="border-b border-ink/10 text-[11px] uppercase tracking-[0.12em] text-ink-muted">
                <th className="py-2">Time</th>
                <th className="py-2">Side</th>
                <th className="py-2">Symbol</th>
                <th className="py-2">Shares</th>
                <th className="py-2">Price</th>
              </tr>
            </thead>
            <tbody>
              {(account?.orders || []).map((o: any) => (
                <tr key={o.id} className="border-b border-ink/5">
                  <td className="py-2 font-mono text-xs">{o.created_at?.slice(0, 19)}</td>
                  <td className={o.side === "buy" ? "text-signal" : "text-alert"}>{o.side}</td>
                  <td>{o.symbol}</td>
                  <td className="font-mono">{o.shares}</td>
                  <td className="font-mono">{formatMoney(o.price)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
