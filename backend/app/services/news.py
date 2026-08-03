from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional

import feedparser
import httpx
import yfinance as yf

from app.services.market_data import normalize_symbol


GENERAL_FEEDS = [
    ("Yahoo Finance", "https://finance.yahoo.com/rss/topstories"),
    ("CNBC Markets", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"),
    ("MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories/"),
]


def fetch_general_news(limit: int = 40) -> list[dict]:
    items: list[dict] = []
    for source, url in GENERAL_FEEDS:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:15]:
                items.append(_normalize_entry(entry, source))
        except Exception:
            continue

    items.sort(key=lambda x: x.get("_ts", 0), reverse=True)
    cleaned = []
    seen = set()
    for item in items:
        key = item["title"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        item.pop("_ts", None)
        cleaned.append(item)
        if len(cleaned) >= limit:
            break
    return cleaned


def fetch_symbol_news(symbol: str, limit: int = 20) -> list[dict]:
    symbol = normalize_symbol(symbol)
    items: list[dict] = []

    try:
        ticker = yf.Ticker(symbol)
        for article in (ticker.news or [])[:limit]:
            content = article.get("content") or article
            title = content.get("title") or article.get("title") or ""
            summary = content.get("summary") or content.get("description") or ""
            link = ""
            click = content.get("clickThroughUrl") or {}
            if isinstance(click, dict):
                link = click.get("url") or ""
            if not link:
                link = content.get("canonicalUrl", {}).get("url") if isinstance(content.get("canonicalUrl"), dict) else ""
            if not link:
                link = article.get("link") or ""

            provider = content.get("provider") or {}
            source = provider.get("displayName") if isinstance(provider, dict) else "Yahoo Finance"
            published = content.get("pubDate") or content.get("displayTime") or ""
            items.append(
                {
                    "title": title,
                    "summary": summary[:400] if summary else "",
                    "link": link,
                    "published": str(published),
                    "source": source or "Yahoo Finance",
                    "symbol": symbol,
                    "sentiment": _simple_sentiment(f"{title} {summary}"),
                }
            )
    except Exception:
        pass

    # Fallback RSS for ticker
    if len(items) < 5:
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:limit]:
                item = _normalize_entry(entry, "Yahoo Finance")
                item["symbol"] = symbol
                item["sentiment"] = _simple_sentiment(f"{item['title']} {item['summary']}")
                items.append(item)
        except Exception:
            pass

    deduped = []
    seen = set()
    for item in items:
        key = item["title"].strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:limit]


def _normalize_entry(entry, source: str) -> dict:
    published = getattr(entry, "published", "") or getattr(entry, "updated", "")
    ts = 0.0
    if published:
        try:
            ts = parsedate_to_datetime(published).timestamp()
        except Exception:
            try:
                ts = datetime.fromisoformat(published.replace("Z", "+00:00")).timestamp()
            except Exception:
                ts = 0.0

    summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
    # Strip basic HTML
    summary = _strip_html(summary)[:400]

    return {
        "title": getattr(entry, "title", "Untitled"),
        "summary": summary,
        "link": getattr(entry, "link", ""),
        "published": published,
        "source": source,
        "symbol": None,
        "sentiment": _simple_sentiment(f"{getattr(entry, 'title', '')} {summary}"),
        "_ts": ts,
    }


def _strip_html(text: str) -> str:
    import re

    return re.sub(r"<[^>]+>", "", text or "").strip()


def _simple_sentiment(text: str) -> str:
    t = (text or "").lower()
    bullish = [
        "surge",
        "soar",
        "rally",
        "beat",
        "record",
        "growth",
        "upgrade",
        "profit",
        "bull",
        "gain",
        "rise",
        "jump",
        "outperform",
    ]
    bearish = [
        "fall",
        "drop",
        "crash",
        "miss",
        "cut",
        "downgrade",
        "loss",
        "bear",
        "decline",
        "plunge",
        "lawsuit",
        "fraud",
        "layoff",
        "weak",
    ]
    score = sum(1 for w in bullish if w in t) - sum(1 for w in bearish if w in t)
    if score > 0:
        return "bullish"
    if score < 0:
        return "bearish"
    return "neutral"
