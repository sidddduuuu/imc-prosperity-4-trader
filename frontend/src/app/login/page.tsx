"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { login, register, auth0Enabled, loading } = useAuth();
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password, name);
      router.push("/watchlist");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Auth failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-[70vh] bg-mesh">
      <div className="mx-auto max-w-md px-5 py-16 md:px-8">
        <p className="text-[11px] uppercase tracking-[0.2em] text-ink-muted">Account</p>
        <h1 className="mt-2 font-display text-4xl tracking-tight text-ink">Sign in</h1>
        <p className="mt-3 text-sm text-ink-muted">
          {auth0Enabled
            ? "Secure authentication via Auth0 Universal Login."
            : "Local auth is active — add Auth0 env vars to enable Universal Login."}
        </p>

        {auth0Enabled && (
          <div className="mt-8 space-y-3">
            <a
              href="/auth/login"
              className="flex w-full items-center justify-center bg-ink py-3 text-sm text-paper transition hover:bg-ink-soft"
            >
              Continue with Auth0
            </a>
            <a
              href="/auth/login?screen_hint=signup"
              className="flex w-full items-center justify-center border border-ink/20 py-3 text-sm text-ink transition hover:border-ink/40"
            >
              Create Auth0 account
            </a>
            <p className="pt-2 text-center text-xs text-ink-muted">
              Uses Auth0 for AI Agents–ready OIDC login (social, password, MFA as configured in your
              tenant).
            </p>
          </div>
        )}

        {!auth0Enabled && !loading && (
          <form onSubmit={onSubmit} className="mt-8 space-y-4 border border-ink/10 bg-paper/70 p-5">
            {mode === "register" && (
              <label className="block">
                <span className="text-[11px] uppercase tracking-[0.14em] text-ink-muted">Name</span>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-2 w-full border border-ink/15 bg-paper px-3 py-2.5 text-sm outline-none"
                />
              </label>
            )}
            <label className="block">
              <span className="text-[11px] uppercase tracking-[0.14em] text-ink-muted">Email</span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-2 w-full border border-ink/15 bg-paper px-3 py-2.5 text-sm outline-none"
              />
            </label>
            <label className="block">
              <span className="text-[11px] uppercase tracking-[0.14em] text-ink-muted">Password</span>
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-2 w-full border border-ink/15 bg-paper px-3 py-2.5 text-sm outline-none"
              />
            </label>
            {error && <p className="text-sm text-alert">{error}</p>}
            <button
              type="submit"
              disabled={busy}
              className="w-full bg-ink py-3 text-sm text-paper disabled:opacity-60"
            >
              {busy ? "Working…" : mode === "login" ? "Log in" : "Create account"}
            </button>
            <button
              type="button"
              className="w-full text-sm text-ink-muted underline"
              onClick={() => setMode(mode === "login" ? "register" : "login")}
            >
              {mode === "login" ? "Need an account? Register" : "Have an account? Log in"}
            </button>
          </form>
        )}

        <p className="mt-6 text-xs text-ink-muted">
          Or continue without an account for public charts and backtests.{" "}
          <Link href="/markets" className="underline">
            Explore markets
          </Link>
        </p>
      </div>
    </div>
  );
}
