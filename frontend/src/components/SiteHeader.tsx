"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Menu, X } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { OptionsMenu } from "@/components/OptionsMenu";

const links = [
  { href: "/markets", label: "Markets" },
  { href: "/screener", label: "Screener" },
  { href: "/backtest", label: "Backtest" },
  { href: "/paper", label: "Paper" },
  { href: "/news", label: "News" },
  { href: "/watchlist", label: "Watchlist" },
];

const wheelOptions = [
  { href: "/markets", label: "Markets" },
  { href: "/screener", label: "Screener" },
  { href: "/backtest", label: "Backtest" },
  { href: "/paper", label: "Paper" },
  { href: "/news", label: "News" },
  { href: "/watchlist", label: "Watchlist" },
  { href: "/analyze", label: "Analyze" },
  { href: "/alerts", label: "Alerts" },
  { href: "/lab", label: "Lab" },
  { href: "/portfolio", label: "Portfolio" },
  { href: "/community", label: "Community" },
  { href: "/login", label: "Account" },
];

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [optionsOpen, setOptionsOpen] = useState(false);
  const { user, logout } = useAuth();

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-ink/10 bg-paper/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4 md:px-8">
          <Link href="/" className="group flex shrink-0 items-baseline gap-2">
            <span className="font-display text-2xl tracking-tight text-ink md:text-[1.7rem]">
              ATLAS
            </span>
            <span className="hidden text-[11px] uppercase tracking-[0.22em] text-ink-muted lg:inline">
              Terminal
            </span>
          </Link>

          <nav className="hidden items-center gap-5 xl:flex">
            {links.map((link) => {
              const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`text-sm tracking-wide transition ${
                    active ? "text-signal" : "text-ink-muted hover:text-ink"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
            <button
              type="button"
              onClick={() => setOptionsOpen(true)}
              className="text-sm tracking-wide text-ink-muted transition hover:text-ink"
            >
              Options
            </button>
            {user ? (
              <div className="flex items-center gap-3">
                <span className="max-w-[120px] truncate text-sm text-ink-muted">
                  {user.name || user.email}
                </span>
                <a
                  href="/auth/logout"
                  onClick={(e) => {
                    e.preventDefault();
                    logout();
                  }}
                  className="text-sm text-ink-muted hover:text-ink"
                >
                  Log out
                </a>
              </div>
            ) : (
              <a href="/auth/login" className="text-sm text-ink-muted hover:text-ink">
                Log in
              </a>
            )}
            <Link
              href="/backtest"
              className="rounded-sm bg-ink px-4 py-2 text-sm text-paper transition hover:bg-ink-soft"
            >
              Run strategy
            </Link>
          </nav>

          <div className="flex items-center gap-2 xl:hidden">
            <button
              type="button"
              onClick={() => setOptionsOpen(true)}
              className="border border-ink/15 px-3 py-1.5 text-xs uppercase tracking-[0.14em] text-ink-muted"
            >
              Options
            </button>
            <button
              type="button"
              aria-label="Toggle menu"
              onClick={() => setOpen((v) => !v)}
            >
              {open ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>

        {open && (
          <div className="border-t border-ink/10 bg-paper px-5 py-4 xl:hidden">
            <div className="flex flex-col gap-3">
              {links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setOpen(false)}
                  className="text-base text-ink"
                >
                  {link.label}
                </Link>
              ))}
              <button
                type="button"
                className="text-left text-base text-ink"
                onClick={() => {
                  setOpen(false);
                  setOptionsOpen(true);
                }}
              >
                All options…
              </button>
              {user ? (
                <button
                  type="button"
                  onClick={() => {
                    logout();
                    setOpen(false);
                  }}
                  className="text-left text-ink"
                >
                  Log out
                </button>
              ) : (
                <Link href="/login" onClick={() => setOpen(false)} className="text-ink">
                  Log in
                </Link>
              )}
            </div>
          </div>
        )}
      </header>

      <OptionsMenu
        open={optionsOpen}
        onClose={() => setOptionsOpen(false)}
        options={wheelOptions}
      />
    </>
  );
}
