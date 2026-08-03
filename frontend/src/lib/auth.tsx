"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useUser } from "@auth0/nextjs-auth0/client";

export type AuthUser = {
  id: number | string;
  email: string;
  name: string;
  picture?: string | null;
};

type AuthState = {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  auth0Enabled: boolean;
  login: (email?: string, password?: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
  authHeaders: () => HeadersInit;
};

const AuthContext = createContext<AuthState | null>(null);
const TOKEN_KEY = "atlas_token";
const USER_KEY = "atlas_user";

export function AuthProvider({ children }: { children: ReactNode }) {
  const { user: auth0User, isLoading: auth0Loading, error: auth0Error } = useUser();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [auth0Enabled, setAuth0Enabled] = useState(false);

  const persist = useCallback((t: string, u: AuthUser) => {
    localStorage.setItem(TOKEN_KEY, t);
    localStorage.setItem(USER_KEY, JSON.stringify(u));
    setToken(t);
    setUser(u);
  }, []);

  const clearLocal = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  }, []);

  // Detect Auth0 + sync session → Atlas JWT
  useEffect(() => {
    let cancelled = false;

    async function sync() {
      if (auth0Loading) return;

      try {
        const status = await fetch("/api/atlas/auth-status", { cache: "no-store" });
        if (status.ok) {
          const data = await status.json();
          if (!cancelled) setAuth0Enabled(Boolean(data.configured));
        }
      } catch {
        /* ignore */
      }

      // Also reflect backend Auth0 verifier config
      try {
        const cfg = await fetch("/api/auth/config", { cache: "no-store" });
        if (cfg.ok) {
          const data = await cfg.json();
          if (!cancelled && data?.auth0?.enabled) setAuth0Enabled(true);
        }
      } catch {
        /* ignore */
      }

      if (auth0User) {
        try {
          const res = await fetch("/api/atlas/session", { cache: "no-store" });
          if (res.status === 503) {
            if (!cancelled) setAuth0Enabled(false);
          } else if (res.ok) {
            const data = await res.json();
            if (!cancelled && data.access_token && data.user) {
              persist(data.access_token, {
                id: data.user.id,
                email: data.user.email,
                name: data.user.name || data.auth0_user?.name || data.user.email,
                picture: data.auth0_user?.picture,
              });
              if (!cancelled) setAuth0Enabled(true);
              if (!cancelled) setLoading(false);
              return;
            }
          }
        } catch {
          /* fall through */
        }
      }

      try {
        const t = localStorage.getItem(TOKEN_KEY);
        const u = localStorage.getItem(USER_KEY);
        if (!cancelled && t && u) {
          setToken(t);
          setUser(JSON.parse(u));
        } else if (!cancelled && !auth0User) {
          clearLocal();
        }
      } catch {
        /* ignore */
      }

      if (!cancelled) setLoading(false);
    }

    sync();
    return () => {
      cancelled = true;
    };
  }, [auth0User, auth0Loading, persist, clearLocal]);

  const login = useCallback(async (email?: string, password?: string) => {
    // Prefer Auth0 Universal Login when configured
    if (!email && !password) {
      window.location.href = "/auth/login";
      return;
    }
    if (!email || !password) {
      window.location.href = "/auth/login";
      return;
    }
    const body = new URLSearchParams();
    body.set("username", email);
    body.set("password", password);
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) throw new Error("Invalid credentials");
    const data = await res.json();
    persist(data.access_token, data.user);
  }, [persist]);

  const register = useCallback(
    async (email: string, password: string, name = "") => {
      // Auth0 signup hint when using Universal Login
      if (auth0Enabled) {
        window.location.href = "/auth/login?screen_hint=signup";
        return;
      }
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, name }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Registration failed");
      }
      const data = await res.json();
      persist(data.access_token, data.user);
    },
    [auth0Enabled, persist]
  );

  const logout = useCallback(() => {
    clearLocal();
    if (auth0Enabled) {
      window.location.href = "/auth/logout";
      return;
    }
  }, [auth0Enabled, clearLocal]);

  const authHeaders = useCallback((): HeadersInit => {
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, [token]);

  const value = useMemo(
    () => ({
      user,
      token,
      loading: loading || auth0Loading,
      auth0Enabled,
      login,
      register,
      logout,
      authHeaders,
    }),
    [user, token, loading, auth0Loading, auth0Enabled, login, register, logout, authHeaders]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
