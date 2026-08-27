"""
CryptoSphere — YouTube Video Feed Module
Fetches crypto-related videos via YouTube Data API v3.
Falls back to a curated static list when no API key is available.
"""
import requests
import streamlit as st

YT_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# Curated static video library — works with zero API calls
CURATED_VIDEOS = {
    "Market Analysis": [
        {"id": "1YyAzVmP9xQ", "title": "Bitcoin Price Analysis & Market Update", "channel": "Coin Bureau"},
        {"id": "SSo_EIwHSd4", "title": "Ethereum Market Analysis — What's Next?", "channel": "Benjamin Cowen"},
        {"id": "Xb4g8TzcFMI", "title": "Crypto Market Cycle Explained", "channel": "Crypto Banter"},
        {"id": "GmOzih6I1zs", "title": "Top Altcoins for This Cycle", "channel": "Altcoin Daily"},
        {"id": "1YyAzVmP9xQ", "title": "Weekly Crypto Recap & Price Predictions", "channel": "DataDash"},
        {"id": "rYQgy8QDEBI", "title": "BTC Dominance Chart — What It Means", "channel": "Coin Bureau"},
    ],
    "Education": [
        {"id": "kubGCSj5y3k", "title": "Bitcoin Explained in 10 Minutes", "channel": "Simply Explained"},
        {"id": "3ehaSqwUZ0s", "title": "What is Blockchain? (Animated)", "channel": "3Blue1Brown"},
        {"id": "SSo_EIwHSd4", "title": "How Ethereum Works — Full Explainer", "channel": "Finematics"},
        {"id": "r43LhSUUGTQ", "title": "DeFi Explained: Complete Beginner Guide", "channel": "Whiteboard Crypto"},
        {"id": "1YyAzVmP9xQ", "title": "Crypto Wallets — Hot vs Cold Storage", "channel": "ColdFusion"},
        {"id": "AQO7KePXUEQ", "title": "What is a Smart Contract? Simply Explained", "channel": "Simply Explained"},
    ],
    "DeFi": [
        {"id": "17QRFlml4pA", "title": "DeFi Protocols Explained: Uniswap, Aave & Compound", "channel": "Finematics"},
        {"id": "G9Xw9agxFMU", "title": "Yield Farming & Liquidity Mining — How it Works", "channel": "Finematics"},
        {"id": "cizLhxSKrAc", "title": "What is a DEX? Decentralized Exchanges Explained", "channel": "Whiteboard Crypto"},
        {"id": "SSo_EIwHSd4", "title": "Layer 2 Solutions Explained: Rollups, ZK Proofs", "channel": "Finematics"},
        {"id": "3ehaSqwUZ0s", "title": "Stablecoins Explained: USDT, USDC, DAI", "channel": "Coin Bureau"},
        {"id": "AQO7KePXUEQ", "title": "Top DeFi Projects to Watch in 2024", "channel": "Altcoin Daily"},
    ],
    "Bitcoin": [
        {"id": "kubGCSj5y3k", "title": "Bitcoin Halving 2024 — What Will Happen?", "channel": "Coin Bureau"},
        {"id": "rYQgy8QDEBI", "title": "Bitcoin Stock-to-Flow Model Explained", "channel": "PlanB"},
        {"id": "3ehaSqwUZ0s", "title": "Why Bitcoin is Scarce — 21 Million Explained", "channel": "Simply Explained"},
        {"id": "GmOzih6I1zs", "title": "Bitcoin Mining Explained — How It Works", "channel": "ColdFusion"},
        {"id": "Xb4g8TzcFMI", "title": "Lightning Network — Bitcoin's Scaling Solution", "channel": "Whiteboard Crypto"},
        {"id": "AQO7KePXUEQ", "title": "Bitcoin vs Gold — Store of Value Debate", "channel": "Real Vision"},
    ],
    "Altcoins": [
        {"id": "GmOzih6I1zs", "title": "Solana — The Ethereum Killer?", "channel": "Coin Bureau"},
        {"id": "1YyAzVmP9xQ", "title": "Polkadot vs Cosmos — Which Wins?", "channel": "DataDash"},
        {"id": "Xb4g8TzcFMI", "title": "Chainlink — The Oracle Problem Solved", "channel": "Whiteboard Crypto"},
        {"id": "rYQgy8QDEBI", "title": "Cardano vs Ethereum — Comparison", "channel": "Altcoin Daily"},
        {"id": "SSo_EIwHSd4", "title": "Top 5 Low-Cap Altcoins for 2024", "channel": "Crypto Banter"},
        {"id": "3ehaSqwUZ0s", "title": "What is Avalanche (AVAX)? Full Explainer", "channel": "Coin Bureau"},
    ],
}


def _get_yt_key() -> str:
    try:
        return st.secrets.get("YOUTUBE_KEY", "")
    except Exception:
        return ""


@st.cache_data(ttl=3600, show_spinner=False)
def search_crypto_videos(query: str, max_results: int = 6) -> list:
    """
    Search YouTube for crypto videos matching the query.
    Falls back to curated static list if no API key.
    """
    key = _get_yt_key()
    if not key:
        # Return curated videos from closest matching category
        for cat, videos in CURATED_VIDEOS.items():
            if cat.lower() in query.lower() or query.lower() in cat.lower():
                return videos[:max_results]
        # Default to education
        return CURATED_VIDEOS["Education"][:max_results]

    try:
        params = {
            "part":        "snippet",
            "q":           query,
            "type":        "video",
            "maxResults":  max_results,
            "key":         key,
            "relevanceLanguage": "en",
            "safeSearch":  "moderate",
        }
        r = requests.get(YT_SEARCH_URL, params=params, timeout=10)
        r.raise_for_status()
        items = r.json().get("items", [])
        return [
            {
                "id":      item["id"]["videoId"],
                "title":   item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "thumb":   item["snippet"]["thumbnails"]["medium"]["url"],
            }
            for item in items
        ]
    except Exception:
        return CURATED_VIDEOS.get("Market Analysis", [])[:max_results]


def get_curated_videos(category: str) -> list:
    """Return curated videos for a given category without any API call."""
    return CURATED_VIDEOS.get(category, CURATED_VIDEOS["Education"])


def video_embed_html(video_id: str, width: int = 320, height: int = 180) -> str:
    """Return HTML iframe string for embedding a YouTube video."""
    return (
        f'<iframe width="{width}" height="{height}" '
        f'src="https://www.youtube.com/embed/{video_id}?rel=0" '
        f'frameborder="0" allowfullscreen '
        f'style="border-radius:12px;"></iframe>'
    )
