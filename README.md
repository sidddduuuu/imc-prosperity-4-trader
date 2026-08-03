# Atlas

All-in-one stock analysis and strategy backtesting platform.

## Stack

- **Backend**: FastAPI + pandas + yfinance — market data, news, technical analysis, backtester
- **Frontend**: Next.js + Tailwind + lightweight-charts + Recharts

## Features

- Strategy backtester (SMA/EMA crossover, RSI, MACD, Bollinger, mean reversion, buy & hold)
- Equity curves vs buy & hold with Sharpe, Sortino, max drawdown, win rate, trade logs
- Candlestick charts and live quotes
- Market news feeds with ticker filter and simple sentiment
- Technical analysis desk (RSI, MACD bias, trend, ATR, moving averages)

## Run locally

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 — API calls are proxied to the backend via Next.js rewrites.

API docs: http://localhost:8000/docs

## Note

The original IMC Prosperity `trader.py` and `data/` folder are preserved unchanged.
