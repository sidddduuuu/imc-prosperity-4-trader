"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { atlasApi, formatMoney } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { SymbolSearch } from "@/components/SymbolSearch";

export default function AlertsPage() {
  const { token, user } = useAuth();
  const [alerts, setAlerts] = useState<any[]>([]);
  const [symbol, setSymbol] = useState("AAPL");
  const [condition, setCondition] = useState("above");
  const [threshold, setThreshold] = useState(200);
  const [triggered, setTriggered] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (!token) return;
    setAlerts(await atlasApi.alerts(token));
  }

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, [token]);

  if (!user || !token) {
    return (
      <div className="min-h-[60vh] bg-mesh px-5 py-16">
        <div className="mx-auto max-w-6xl">
          <h1 className="font-display text-4xl text-ink">Alerts</h1>
          <p className="mt-3 text-ink-muted">Log in to create price and momentum alerts.</p>
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
        <p className="text-[11px] uppercase tracking-[0.2em] text-ink-muted">Signals</p>
        <h1 className="mt-2 font-display text-4xl tracking-tight text-ink">Alerts</h1>

        <div className="mt-8 grid gap-3 border border-ink/10 bg-paper/70 p-5 md:grid-cols-4">
          <SymbolSearch value={symbol} onChange={setSymbol} />
          <select
            value={condition}
            onChange={(e) => setCondition(e.target.value)}
            className="border border-ink/15 bg-paper px-3 py-2.5 text-sm"
          >
            <option value="above">Price above</option>
            <option value="below">Price below</option>
            <option value="pct_up">% up today</option>
            <option value="pct_down">% down today</option>
          </select>
          <input
            type="number"
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
            className="border border-ink/15 bg-paper px-3 py-2.5 text-sm"
          />
          <button
            type="button"
            className="bg-ink text-sm text-paper"
            onClick={async () => {
              try {
                await atlasApi.createAlert(token, { symbol, condition, threshold });
                await load();
              } catch (e) {
                setError(e instanceof Error ? e.message : "Failed");
              }
            }}
          >
            Create alert
          </button>
        </div>

        <div className="mt-4 flex gap-3">
          <button
            type="button"
            className="border border-ink/15 px-4 py-2 text-sm"
            onClick={async () => {
              const res = await atlasApi.checkAlerts(token);
              setTriggered(res.triggered);
              await load();
            }}
          >
            Check now
          </button>
        </div>

        {error && <p className="mt-4 text-sm text-alert">{error}</p>}
        {triggered.length > 0 && (
          <div className="mt-4 border border-signal/30 bg-signal/10 p-4 text-sm">
            {triggered.map((t) => (
              <div key={t.id}>
                Triggered {t.symbol} @ {formatMoney(t.price)} — {t.message}
              </div>
            ))}
          </div>
        )}

        <div className="mt-8 divide-y divide-ink/10">
          {alerts.map((a) => (
            <div key={a.id} className="flex items-center justify-between py-4 text-sm">
              <div>
                <span className="font-medium">{a.symbol}</span> · {a.condition} {a.threshold}
                <span className="ml-3 text-ink-muted">
                  {a.triggered ? "triggered" : a.active ? "active" : "inactive"}
                </span>
              </div>
              <button
                type="button"
                className="text-xs underline text-ink-muted"
                onClick={async () => {
                  await atlasApi.deleteAlert(token, a.id);
                  await load();
                }}
              >
                Delete
              </button>
            </div>
          ))}
          {alerts.length === 0 && <p className="py-8 text-ink-muted">No alerts yet.</p>}
        </div>
      </div>
    </div>
  );
}
