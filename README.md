# Atlas Terminal

Production-oriented stock analysis and strategy backtesting platform.

## Features

- Charts, quotes, technical analysis, news wire
- Strategy backtester + **portfolio backtests**
- **Walk-forward** and **Monte Carlo** research lab
- Auth, **watchlists**, **alerts**, **saved backtests**
- **Paper trading** desk
- **Screener**, **community strategies**, AI desk briefs
- Rate limiting, disclaimers, Docker / Render / Vercel deploy configs

## Authentication (Auth0)

Atlas uses **Auth0 Universal Login** via `@auth0/nextjs-auth0` (Auth0 for AI Agents / OIDC).

1. Create a **Regular Web Application** in the [Auth0 Dashboard](https://manage.auth0.com/)
2. Allowed Callback URLs: `http://localhost:3000/auth/callback`
3. Allowed Logout URLs: `http://localhost:3000`
4. Copy env vars into `frontend/.env.local` and `backend/.env` (see `.env.example`)

```bash
# generate AUTH0_SECRET
openssl rand -hex 32
```

| Variable | Where |
|----------|--------|
| `AUTH0_DOMAIN` | frontend + backend (no `https://`) |
| `AUTH0_CLIENT_ID` | frontend + backend |
| `AUTH0_CLIENT_SECRET` | frontend |
| `AUTH0_SECRET` | frontend (cookie encryption) |
| `APP_BASE_URL` | frontend |
| `AUTH0_AUDIENCE` | optional API identifier |

Login flow: `/auth/login` → Auth0 → `/auth/callback` → Atlas syncs the ID token to `/api/auth/auth0` and issues an API session JWT for watchlists/paper/alerts.

Without Auth0 env vars, local email/password auth remains available for development.

## Stack

- Backend: FastAPI + SQLAlchemy (SQLite default, Postgres via `DATABASE_URL`) + yfinance
- Frontend: Next.js + Auth0 + Tailwind + lightweight-charts + Recharts
- Auth: Auth0 OIDC (preferred) with local JWT fallback

## Run locally

```bash
./scripts/dev.sh
```

Or separately:

```bash
# backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8000

# frontend
cd frontend && npm install && npm run dev
```

Open http://localhost:3000 — API docs at http://localhost:8000/docs

## Free deploy

1. **Backend** → [Render](https://render.com) free web service  
   - Root: `backend`  
   - Build: `pip install -r requirements.txt`  
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`  
   - Env: `SECRET_KEY`, `PYTHONPATH=.`, `DATABASE_URL=sqlite:///./data/atlas.db`, `CORS_ORIGINS=*`

2. **Frontend** → [Vercel](https://vercel.com) Hobby  
   - Root: `frontend`  
   - Env: `API_URL=https://YOUR-RENDER-SERVICE.onrender.com`

See `render.yaml`, `docker-compose.yml`, and `.env.example`.

## Note

IMC Prosperity `trader.py` and `data/round1` are preserved. Atlas market data uses Yahoo/RSS for the free demo — use a licensed vendor before commercial use.
