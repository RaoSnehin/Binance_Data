"""
CryptoSphere — News Feed Module
Aggregates crypto news from:
  1. CryptoPanic API (free tier — no credit card)
  2. RSS feeds: CoinDesk, CoinTelegraph, Decrypt (via feedparser)
Falls back gracefully when keys or network are unavailable.
"""
import requests
import streamlit as st
from datetime import datetime, timezone
import time

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

CRYPTOPANIC_BASE = "https://cryptopanic.com/api/v1/posts/"

RSS_FEEDS = {
    "CoinDesk":       "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "CoinTelegraph":  "https://cointelegraph.com/rss",
    "Decrypt":        "https://decrypt.co/feed",
    "Bitcoin Magazine":"https://bitcoinmagazine.com/feed",
}


def _get_cp_key() -> str:
    try:
        return st.secrets.get("CRYPTOPANIC_KEY", "")
    except Exception:
        return ""


@st.cache_data(ttl=300, show_spinner=False)
def get_crypto_news(filter_type: str = "hot", currency: str = "", limit: int = 30) -> list:
    """
    Return a list of news dicts. Tries CryptoPanic first, then RSS fallback.

    Each item has:
        title, url, source, published_at (str), currencies, sentiment, is_hot
    """
    articles = _fetch_cryptopanic(filter_type, currency, limit)
    if not articles:
        articles = _fetch_rss(limit)
    return articles[:limit]


def _fetch_cryptopanic(filter_type: str, currency: str, limit: int) -> list:
    key = _get_cp_key()
    params = {
        "auth_token": key if key else "anonymous",
        "public": "true",
        "kind": "news",
        "limit": min(limit, 50),
    }
    if filter_type in ("hot", "rising", "bullish", "bearish", "important"):
        params["filter"] = filter_type
    if currency:
        params["currencies"] = currency.upper()
    try:
        r = requests.get(CRYPTOPANIC_BASE, params=params, timeout=10)
        r.raise_for_status()
        items = r.json().get("results", [])
        out = []
        for item in items:
            votes   = item.get("votes", {})
            pos     = votes.get("positive", 0)
            neg     = votes.get("negative", 0)
            if pos > neg:   sentiment = "bullish"
            elif neg > pos: sentiment = "bearish"
            else:           sentiment = "neutral"
            currs = [c["code"] for c in item.get("currencies", [])]
            pub   = item.get("published_at", "")
            out.append({
                "title":        item.get("title", ""),
                "url":          item.get("url", "#"),
                "source":       item.get("source", {}).get("title", "Unknown"),
                "published_at": _humanize_time(pub),
                "currencies":   currs,
                "sentiment":    sentiment,
                "is_hot":       bool(item.get("votes", {}).get("important", 0) > 2),
            })
        return out
    except Exception:
        return []


def _fetch_rss(limit: int) -> list:
    if not HAS_FEEDPARSER:
        return _stub_news(limit)
    out = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                pub = ""
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    pub = _humanize_time(dt.isoformat())
                out.append({
                    "title":        entry.get("title", ""),
                    "url":          entry.get("link", "#"),
                    "source":       source,
                    "published_at": pub or "Recently",
                    "currencies":   [],
                    "sentiment":    "neutral",
                    "is_hot":       False,
                })
        except Exception:
            continue
    return out[:limit] if out else _stub_news(limit)


def _stub_news(limit: int) -> list:
    stubs = [
        {"title": "Bitcoin Surges Past $65K as Institutional Demand Grows", "url": "https://coindesk.com", "source": "CoinDesk", "published_at": "2h ago", "currencies": ["BTC"], "sentiment": "bullish", "is_hot": True},
        {"title": "Ethereum Layer 2 Solutions See Record Transaction Volume", "url": "https://cointelegraph.com", "source": "CoinTelegraph", "published_at": "4h ago", "currencies": ["ETH"], "sentiment": "bullish", "is_hot": False},
        {"title": "SEC Delays Decision on Spot Ethereum ETF Applications", "url": "https://coindesk.com", "source": "CoinDesk", "published_at": "6h ago", "currencies": ["ETH"], "sentiment": "bearish", "is_hot": True},
        {"title": "Solana DeFi Ecosystem Reaches $8B Total Value Locked", "url": "https://decrypt.co", "source": "Decrypt", "published_at": "8h ago", "currencies": ["SOL"], "sentiment": "bullish", "is_hot": False},
        {"title": "Binance Reports Record Monthly Trading Volume in Q1", "url": "https://cointelegraph.com", "source": "CoinTelegraph", "published_at": "10h ago", "currencies": ["BNB"], "sentiment": "neutral", "is_hot": False},
        {"title": "Crypto Market Cap Recovers to $2.5T After Weekend Dip", "url": "https://coindesk.com", "source": "CoinDesk", "published_at": "12h ago", "currencies": [], "sentiment": "bullish", "is_hot": False},
    ]
    return stubs[:limit]


def _humanize_time(iso_str: str) -> str:
    """Convert ISO timestamp to human-readable 'X ago' string."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = int((now - dt).total_seconds())
        if diff < 60:     return f"{diff}s ago"
        if diff < 3600:   return f"{diff//60}m ago"
        if diff < 86400:  return f"{diff//3600}h ago"
        return f"{diff//86400}d ago"
    except Exception:
        return iso_str[:10]
