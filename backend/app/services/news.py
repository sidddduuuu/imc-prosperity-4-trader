from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
import re
from typing import Optional

import feedparser
import yfinance as yf

from app.services.market_data import normalize_symbol


# Prefer market / stocks / trading desks — not lifestyle or general news.
GENERAL_FEEDS = [
    ("CNBC Stocks", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069"),
    ("CNBC Markets", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"),
    ("CNBC Earnings", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15837362"),
    ("MarketWatch Pulse", "https://feeds.marketwatch.com/marketwatch/marketpulse/"),
    ("Yahoo Finance", "https://finance.yahoo.com/rss/topstories"),
    ("Investing.com", "https://www.investing.com/rss/news_25.rss"),
]

# Must match at least one of these (word-boundary aware where listed as phrases).
_TRADING_INCLUDE = [
    r"\bstock[s]?\b",
    r"\bshares?\b",
    r"\bequity\b",
    r"\bequities\b",
    r"\bmarket[s]?\b",
    r"\btrading\b",
    r"\btrader[s]?\b",
    r"\bwall street\b",
    r"\bnasdaq\b",
    r"\bdow\b",
    r"\bs&p\b",
    r"\bs&p 500\b",
    r"\bspy\b",
    r"\betf[s]?\b",
    r"\boptions?\b",
    r"\bfutures?\b",
    r"\bforex\b",
    r"\bcrypto\b",
    r"\bbitcoin\b",
    r"\bethereum\b",
    r"\bearnings?\b",
    r"\brevenue\b",
    r"\bguidance\b",
    r"\bipo\b",
    r"\bsec\b",
    r"\bfed\b",
    r"\bfederal reserve\b",
    r"\binterest rate[s]?\b",
    r"\brate cut[s]?\b",
    r"\brate hike[s]?\b",
    r"\binflation\b",
    r"\bjobs report\b",
    r"\bjobless claims\b",
    r"\bunemployment\b",
    r"\bpayrolls?\b",
    r"\byield[s]?\b",
    r"\bbond[s]?\b",
    r"\btreasury\b",
    r"\btreasuries\b",
    r"\bcommodity\b",
    r"\bcommodities\b",
    r"\boil price[s]?\b",
    r"\bcrude\b",
    r"\bgold\b",
    r"\bpremarket\b",
    r"\bafter[- ]?hours\b",
    r"\bbull market\b",
    r"\bbear market\b",
    r"\brally\b",
    r"\bselloff\b",
    r"\bsell-off\b",
    r"\bvolatility\b",
    r"\bportfolio\b",
    r"\binvestor[s]?\b",
    r"\binvesting\b",
    r"\binvestment[s]?\b",
    r"\bhedge fund\b",
    r"\bmutual fund\b",
    r"\bbrokerage\b",
    r"\bdividend[s]?\b",
    r"\bvaluation\b",
    r"\bmarket cap\b",
    r"\bmerger\b",
    r"\bacquisition\b",
    r"\btakeover\b",
    r"\bbuyout\b",
    r"\bbuyback\b",
    r"\bto buy\b",
    r"\bbillion\b",
    r"\bmillion deal\b",
    r"\bshort interest\b",
    r"\bupgrade[ds]?\b",
    r"\bdowngrade[ds]?\b",
    r"\banalyst[s]?\b",
    r"\bquarterly\b",
    r"\bfiscal\b",
    r"\bprofit[s]?\b",
    r"\brecession\b",
    r"\bgdp\b",
    r"\bcpi\b",
    r"\bpce\b",
    r"\bfomc\b",
    r"\becb\b",
    r"\bbank of england\b",
    r"\bcentral bank\b",
    r"\bconsumer credit\b",
    r"\bmanufacturing\b",
    r"\bad spending\b",
]

# Drop personal-finance advice, lifestyle, entertainment, politics-only, health curiosities, etc.
_TRADING_EXCLUDE = [
    r"\bmedicare\b",
    r"\bmedicaid\b",
    r"\bsocial security\b",
    r"\bpension payout\b",
    r"\bhospital bill\b",
    r"\bwill i run out of money\b",
    r"\bbuy a house\b",
    r"\bmortgage advice\b",
    r"\bspider-?man\b",
    r"\bimax\b",
    r"\bmovie screen\b",
    r"\bhollywood league soccer\b",
    r"\bmls commissioner\b",
    r"\bcyclospora\b",
    r"\boutbreak\b",
    r"\bcelebrity\b",
    r"\brecipe\b",
    r"\bhoroscope\b",
    r"\btravel tip\b",
    r"\bdating\b",
    r"\bdivorce\b",
    r"\bwill medicare\b",
    r"\bcharitable gesture\b",
    r"\bforgo their\b",
    r"\bt-boned\b",
    r"\bdriver.?s window\b",
    r"\beasing into retirement\b",
    r"\bwhere can i invest it safely\b",  # personal advice columns — keep markets, not advice blogs
    r"\bop-?ed\b",
    r"\bobituary\b",
    r"\brecipe\b",
    r"\bgaming review\b",
    r"\bbox office\b",
]

_INCLUDE_RE = [re.compile(p, re.I) for p in _TRADING_INCLUDE]
_EXCLUDE_RE = [re.compile(p, re.I) for p in _TRADING_EXCLUDE]


def fetch_general_news(limit: int = 40) -> list[dict]:
    items: list[dict] = []
    for source, url in GENERAL_FEEDS:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:20]:
                item = _normalize_entry(entry, source)
                if _is_trading_relevant(item.get("title", ""), item.get("summary", "")):
                    items.append(item)
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
        for article in (ticker.news or [])[: limit * 2]:
            content = article.get("content") or article
            title = content.get("title") or article.get("title") or ""
            summary = content.get("summary") or content.get("description") or ""
            link = ""
            click = content.get("clickThroughUrl") or {}
            if isinstance(click, dict):
                link = click.get("url") or ""
            if not link:
                link = (
                    content.get("canonicalUrl", {}).get("url")
                    if isinstance(content.get("canonicalUrl"), dict)
                    else ""
                )
            if not link:
                link = article.get("link") or ""

            provider = content.get("provider") or {}
            source = provider.get("displayName") if isinstance(provider, dict) else "Yahoo Finance"
            published = content.get("pubDate") or content.get("displayTime") or ""
            if not _is_trading_relevant(title, summary, symbol=symbol):
                continue
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
            for entry in parsed.entries[: limit * 2]:
                item = _normalize_entry(entry, "Yahoo Finance")
                item["symbol"] = symbol
                item["sentiment"] = _simple_sentiment(f"{item['title']} {item['summary']}")
                if not _is_trading_relevant(item["title"], item["summary"], symbol=symbol):
                    continue
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


def _is_trading_relevant(title: str, summary: str = "", symbol: Optional[str] = None) -> bool:
    """Keep markets/trading/earnings; drop lifestyle, advice columns, entertainment."""
    text = f"{title} {summary}".strip()
    if not text:
        return False
    if any(rx.search(text) for rx in _EXCLUDE_RE):
        return False
    if symbol and re.search(rf"\b{re.escape(symbol)}\b", text, re.I):
        return True
    if any(rx.search(text) for rx in _INCLUDE_RE):
        return True
    # Ticker-style symbols in titles: $AAPL, NVDA stock already covered; bare tickers in all-caps
    if re.search(r"\$[A-Z]{1,5}\b", text):
        return True
    return False


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
