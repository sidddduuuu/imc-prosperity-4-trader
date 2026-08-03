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

## Stack

- Backend: FastAPI + SQLAlchemy (SQLite default, Postgres via `DATABASE_URL`) + yfinance
- Frontend: Next.js + Tailwind + lightweight-charts + Recharts

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
