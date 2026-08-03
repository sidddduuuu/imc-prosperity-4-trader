"use client";

import { motion } from "framer-motion";
import { ArrowRight, LineChart, Newspaper, Radar } from "lucide-react";

const features = [
  {
    href: "/backtest",
    title: "Strategy backtester",
    copy: "SMA, EMA, RSI, MACD, Bollinger, mean-reversion — plus walk-forward and Monte Carlo in the lab.",
    icon: Radar,
  },
  {
    href: "/markets",
    title: "Charts & screener",
    copy: "Candles, quotes, and a momentum/RSI/trend screener across the liquid universe.",
    icon: LineChart,
  },
  {
    href: "/paper",
    title: "Paper & alerts",
    copy: "Simulated trading desk, price alerts, watchlists, community strategies, and AI briefs.",
    icon: Newspaper,
  },
];

export default function HomePage() {
  return (
    <div>
      <section className="relative min-h-[88vh] overflow-hidden bg-mesh grid-fine">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -left-24 top-24 h-72 w-72 animate-drift rounded-full bg-signal/20 blur-3xl" />
          <div className="absolute bottom-10 right-0 h-80 w-80 animate-drift rounded-full bg-[#3D5A80]/20 blur-3xl [animation-delay:2s]" />
          <svg
            className="absolute inset-x-0 bottom-0 h-[42%] w-full opacity-70"
            viewBox="0 0 1200 320"
            preserveAspectRatio="none"
            aria-hidden
          >
            <path
              d="M0,220 C120,180 180,260 300,210 C420,160 480,90 600,120 C720,150 780,240 900,200 C1020,160 1100,100 1200,130 L1200,320 L0,320 Z"
              fill="rgba(12,143,106,0.12)"
            />
            <path
              d="M0,250 C150,230 220,180 340,200 C460,220 520,280 640,240 C760,200 820,140 960,170 C1080,195 1140,230 1200,210 L1200,320 L0,320 Z"
              fill="none"
              stroke="#0C8F6A"
              strokeWidth="2"
              className="animate-pulse-soft"
            />
          </svg>
        </div>

        <div className="relative mx-auto flex min-h-[88vh] max-w-6xl flex-col justify-center px-5 py-20 md:px-8">
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="font-display text-5xl tracking-tight text-ink sm:text-7xl md:text-8xl"
          >
            ATLAS
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.08 }}
            className="mt-6 max-w-2xl text-balance text-2xl font-medium leading-snug text-ink sm:text-3xl md:text-4xl"
          >
            Every signal. One terminal.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.16 }}
            className="mt-5 max-w-xl text-base leading-relaxed text-ink-muted sm:text-lg"
          >
            Backtest strategies, read the tape, chart the move, and analyze any equity —
            built for traders who want the whole desk in one place.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.24 }}
            className="mt-10 flex flex-wrap gap-3"
          >
            <a
              href="/auth/login?returnTo=/backtest"
              className="inline-flex items-center gap-2 bg-ink px-6 py-3 text-sm text-paper transition hover:bg-ink-soft"
            >
              Sign in to trade <ArrowRight size={16} />
            </a>
            <a
              href="/auth/login?returnTo=/markets"
              className="inline-flex items-center gap-2 border border-ink/20 px-6 py-3 text-sm text-ink transition hover:border-ink/40"
            >
              Enter terminal
            </a>
          </motion.div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-20 md:px-8">
        <p className="text-[11px] uppercase tracking-[0.2em] text-ink-muted">What you get</p>
        <h2 className="mt-3 max-w-xl font-display text-3xl tracking-tight text-ink md:text-4xl">
          Research, test, and trade from a single workspace.
        </h2>
        <div className="mt-12 grid gap-10 md:grid-cols-3">
          {features.map((f, i) => (
            <motion.div
              key={f.href}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.45, delay: i * 0.08 }}
            >
              <a href={`/auth/login?returnTo=${f.href}`} className="group block">
                <f.icon className="text-signal" size={22} strokeWidth={1.75} />
                <h3 className="mt-4 text-xl text-ink group-hover:text-signal">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-ink-muted">{f.copy}</p>
              </a>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="border-t border-ink/10 bg-ink text-paper">
        <div className="mx-auto flex max-w-6xl flex-col gap-6 px-5 py-16 md:flex-row md:items-end md:justify-between md:px-8">
          <div>
            <p className="font-display text-3xl tracking-tight md:text-4xl">Ready to test an edge?</p>
            <p className="mt-3 max-w-md text-sm text-paper/70">
              Load any ticker, pick a strategy, and see equity curves, drawdowns, Sharpe, and trade
              logs in seconds.
            </p>
          </div>
          <a
            href="/auth/login?returnTo=/backtest"
            className="inline-flex items-center gap-2 bg-signal px-6 py-3 text-sm text-paper transition hover:bg-signal-bright"
          >
            Start backtesting <ArrowRight size={16} />
          </a>
        </div>
      </section>

      <footer className="border-t border-ink/10 py-8 text-center text-xs text-ink-muted">
        Atlas · Market data via Yahoo Finance · For research use
      </footer>
    </div>
  );
}
