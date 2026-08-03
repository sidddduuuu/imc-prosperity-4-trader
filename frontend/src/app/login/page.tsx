"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";

function LoginInner() {
  const { login, register, auth0Enabled, loading } = useAuth();
  const router = useRouter();
  const search = useSearchParams();
  const returnTo = search.get("returnTo") || "/markets";
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Prefer Auth0 Universal Login — landing already owns the "Login to trade" CTA
  useEffect(() => {
    if (loading) return;
    if (auth0Enabled) {
      const dest = `/auth/login?returnTo=${encodeURIComponent(returnTo)}`;
      window.location.replace(dest);
    }
  }, [auth0Enabled, loading, returnTo]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password, name);
      router.push(returnTo.startsWith("/") ? returnTo : "/markets");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Auth failed");
    } finally {
      setBusy(false);
    }
  }

  if (auth0Enabled || loading) {
    return (
      <div className="min-h-[70vh] bg-mesh">
        <div className="mx-auto max-w-md px-5 py-16 md:px-8">
          <p className="text-[11px] uppercase tracking-[0.2em] text-ink-muted">Account</p>
          <h1 className="mt-2 font-display text-4xl tracking-tight text-ink">Signing in…</h1>
          <p className="mt-3 text-sm text-ink-muted">Redirecting to secure login.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[70vh] bg-mesh">
      <div className="mx-auto max-w-md px-5 py-16 md:px-8">
        <p className="text-[11px] uppercase tracking-[0.2em] text-ink-muted">Account</p>
        <h1 className="mt-2 font-display text-4xl tracking-tight text-ink">Sign in</h1>
        <p className="mt-3 text-sm text-ink-muted">
          Local auth is active — add Auth0 env vars to enable Universal Login.
        </p>

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

        <p className="mt-6 text-xs text-ink-muted">
          Prefer the homepage CTA.{" "}
          <Link href="/" className="underline">
            Back to Atlas
          </Link>
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[70vh] bg-mesh">
          <div className="mx-auto max-w-md px-5 py-16 md:px-8">
            <h1 className="font-display text-4xl tracking-tight text-ink">Sign in</h1>
          </div>
        </div>
      }
    >
      <LoginInner />
    </Suspense>
  );
}
