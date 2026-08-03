export type StrategyParam = {
  name: string;
  label: string;
  type: "int" | "float";
  default: number;
  min: number;
  max: number;
};

export type StrategyInfo = {
  id: string;
  name: string;
  description: string;
  params: StrategyParam[];
};

export type Quote = {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  open?: number | null;
  high?: number | null;
  low?: number | null;
  previous_close?: number | null;
  volume?: number | null;
  market_cap?: number | null;
  pe_ratio?: number | null;
  eps?: number | null;
  fifty_two_week_high?: number | null;
  fifty_two_week_low?: number | null;
  dividend_yield?: number | null;
  sector?: string | null;
  industry?: string | null;
  currency: string;
};

export type Candle = {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type NewsItem = {
  title: string;
  summary: string;
  link: string;
  published: string;
  source: string;
  symbol?: string | null;
  sentiment?: string | null;
};

export type BacktestMetrics = {
  total_return: number;
  buy_hold_return: number;
  alpha: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  avg_trade_return: number;
  volatility: number;
  final_equity: number;
  initial_capital: number;
};

export type EquityPoint = {
  date: string;
  equity: number;
  buy_hold: number;
  drawdown: number;
};

export type TradeRecord = {
  date: string;
  side: string;
  price: number;
  shares: number;
  value: number;
  commission: number;
};

export type BacktestResult = {
  symbol: string;
  strategy: string;
  params: Record<string, number>;
  metrics: BacktestMetrics;
  equity_curve: EquityPoint[];
  trades: TradeRecord[];
  signals: { date: string; type: string; price: number }[];
};

export type AnalysisResponse = {
  symbol: string;
  indicators: { time: string; values: Record<string, number> }[];
  summary: Record<string, string | number | null>;
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json();
}

function authInit(token?: string | null, init?: RequestInit): RequestInit {
  return {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers || {}),
    },
  };
}

export const atlasApi = {
  strategies: () => api<StrategyInfo[]>("/api/strategies"),
  quote: (symbol: string) => api<Quote>(`/api/quote/${encodeURIComponent(symbol)}`),
  history: (symbol: string, period = "1y") =>
    api<{ symbol: string; interval: string; candles: Candle[] }>(
      `/api/history/${encodeURIComponent(symbol)}?period=${period}`
    ),
  news: (symbol?: string, limit = 30) =>
    api<NewsItem[]>(
      symbol
        ? `/api/news?symbol=${encodeURIComponent(symbol)}&limit=${limit}`
        : `/api/news?limit=${limit}`
    ),
  analysis: (symbol: string, period = "1y") =>
    api<AnalysisResponse>(`/api/analysis/${encodeURIComponent(symbol)}?period=${period}`),
  search: (q: string) =>
    api<{ symbol: string; name: string; exchange?: string; type?: string }[]>(
      `/api/search?q=${encodeURIComponent(q)}`
    ),
  popular: () => api<Quote[]>("/api/popular"),
  backtest: (body: {
    symbol: string;
    strategy: string;
    start: string;
    end: string;
    initial_capital: number;
    commission: number;
    params: Record<string, number>;
  }) =>
    api<BacktestResult>("/api/backtest", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  config: () =>
    api<{
      disclaimer: string;
      features: Record<string, boolean>;
      market_data_provider: string;
    }>("/api/auth/config"),
  screener: (params: Record<string, string | number | undefined> = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "") qs.set(k, String(v));
    });
    return api<Record<string, unknown>[]>(`/api/screener?${qs.toString()}`);
  },
  watchlists: (token: string) => api<any[]>("/api/watchlists", authInit(token)),
  addWatch: (token: string, watchlistId: number, symbol: string) =>
    api(`/api/watchlists/${watchlistId}/items`, authInit(token, {
      method: "POST",
      body: JSON.stringify({ symbol }),
    })),
  removeWatch: (token: string, watchlistId: number, itemId: number) =>
    api(`/api/watchlists/${watchlistId}/items/${itemId}`, authInit(token, { method: "DELETE" })),
  alerts: (token: string) => api<any[]>("/api/alerts", authInit(token)),
  createAlert: (
    token: string,
    body: { symbol: string; condition: string; threshold: number; message?: string }
  ) => api("/api/alerts", authInit(token, { method: "POST", body: JSON.stringify(body) })),
  checkAlerts: (token: string) =>
    api<{ triggered: any[] }>("/api/alerts/check", authInit(token, { method: "POST" })),
  deleteAlert: (token: string, id: number) =>
    api(`/api/alerts/${id}`, authInit(token, { method: "DELETE" })),
  paper: (token: string) => api<any>("/api/paper", authInit(token)),
  paperOrder: (token: string, body: { symbol: string; side: string; shares: number }) =>
    api("/api/paper/order", authInit(token, { method: "POST", body: JSON.stringify(body) })),
  paperReset: (token: string) =>
    api("/api/paper/reset", authInit(token, { method: "POST" })),
  saveBacktest: (token: string, body: any) =>
    api("/api/saved-backtests", authInit(token, { method: "POST", body: JSON.stringify(body) })),
  savedBacktests: (token: string) => api<any[]>("/api/saved-backtests", authInit(token)),
  portfolioBacktest: (body: any) =>
    api("/api/backtest/portfolio", { method: "POST", body: JSON.stringify(body) }),
  advancedBacktest: (body: any) =>
    api("/api/backtest/advanced", { method: "POST", body: JSON.stringify(body) }),
  community: () => api<any[]>("/api/community/strategies"),
  shareStrategy: (token: string, body: any) =>
    api("/api/community/strategies", authInit(token, { method: "POST", body: JSON.stringify(body) })),
  likeStrategy: (id: number) =>
    api(`/api/community/strategies/${id}/like`, { method: "POST" }),
  aiBrief: (symbol: string) =>
    api<any>("/api/ai/brief", { method: "POST", body: JSON.stringify({ symbol, include_news: true }) }),
};

export function formatMoney(n: number, digits = 2) {
  return n.toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: digits,
  });
}

export function formatPct(n: number, digits = 2) {
  const pct = n * (Math.abs(n) <= 1 ? 100 : 1);
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(digits)}%`;
}

export function formatCompact(n: number | null | undefined) {
  if (n == null) return "—";
  return Intl.NumberFormat(undefined, {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(n);
}
