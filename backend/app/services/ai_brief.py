from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.services.indicators import compute_indicators, indicator_summary
from app.services.market_data import fetch_history, fetch_quote
from app.services.news import fetch_symbol_news


def build_local_brief(symbol: str, include_news: bool = True) -> dict[str, Any]:
    quote = fetch_quote(symbol)
    hist = fetch_history(symbol, period="6mo")
    summary = indicator_summary(compute_indicators(hist))
    news = fetch_symbol_news(symbol, limit=5) if include_news else []

    bullets = [
        f"{quote['name']} ({quote['symbol']}) last {quote['price']} ({quote['change_percent']:+.2f}%).",
        f"Trend bias looks {summary.get('trend')}; RSI {summary.get('rsi')} ({summary.get('rsi_signal')}); MACD {summary.get('macd_bias')}.",
    ]
    if news:
        bullets.append(f"Latest headline: {news[0]['title']}")

    return {
        "symbol": quote["symbol"],
        "provider": "local",
        "brief": " ".join(bullets),
        "summary": summary,
        "quote": quote,
        "news": news,
        "disclaimer": get_settings().disclaimer,
    }


async def build_ai_brief(symbol: str, include_news: bool = True) -> dict[str, Any]:
    local = build_local_brief(symbol, include_news=include_news)
    settings = get_settings()
    api_key = settings.openrouter_api_key or settings.fireworks_api_key
    if not api_key:
        return local

    headlines = "; ".join(n["title"] for n in local.get("news", [])[:5])
    prompt = (
        f"Write a concise 4-bullet trader brief for {symbol}. "
        f"Price data: {local['quote']}. Indicators: {local['summary']}. "
        f"Headlines: {headlines}. "
        "No investment advice. Be factual and cautious."
    )

    try:
        if settings.openrouter_api_key:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.openrouter_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "openai/gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                resp.raise_for_status()
                text = resp.json()["choices"][0]["message"]["content"]
                local["brief"] = text
                local["provider"] = "openrouter"
        elif settings.fireworks_api_key:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.fireworks.ai/inference/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.fireworks_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "accounts/fireworks/models/llama-v3p1-8b-instruct",
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                resp.raise_for_status()
                text = resp.json()["choices"][0]["message"]["content"]
                local["brief"] = text
                local["provider"] = "fireworks"
    except Exception:
        local["provider"] = "local_fallback"

    return local
