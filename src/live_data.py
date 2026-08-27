"""
CryptoSphere — Live Data Module
Fetches real-time crypto data from CoinGecko API.
Gracefully falls back to cached/stub data if API is unavailable or rate-limited.
"""
import requests
import streamlit as st
import pandas as pd
from datetime import datetime

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

def _get_headers():
    """Build headers, optionally including API key from Streamlit secrets."""
    headers = {"accept": "application/json"}
    try:
        key = st.secrets.get("COINGECKO_KEY", "")
        if key:
            headers["x-cg-demo-api-key"] = key
    except Exception:
        pass
    return headers


@st.cache_data(ttl=60, show_spinner=False)
def get_top_coins(n: int = 100) -> pd.DataFrame:
    """Return top N coins by market cap with live price data."""
    try:
        url = f"{COINGECKO_BASE}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": min(n, 250),
            "page": 1,
            "sparkline": True,
            "price_change_percentage": "1h,24h,7d",
        }
        r = requests.get(url, headers=_get_headers(), params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data)
        # Normalise column names
        rename = {
            "id": "coin_id",
            "symbol": "symbol",
            "name": "name",
            "current_price": "price_usd",
            "market_cap": "market_cap",
            "total_volume": "volume_24h",
            "price_change_percentage_24h": "change_24h",
            "price_change_percentage_1h_in_currency": "change_1h",
            "price_change_percentage_7d_in_currency": "change_7d",
            "market_cap_rank": "rank",
            "image": "image_url",
            "sparkline_in_7d": "sparkline",
            "ath": "ath",
            "ath_change_percentage": "ath_change_pct",
            "circulating_supply": "circulating_supply",
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        return df
    except Exception:
        return _stub_coins(n)


@st.cache_data(ttl=60, show_spinner=False)
def get_global_stats() -> dict:
    """Return global crypto market statistics."""
    try:
        r = requests.get(f"{COINGECKO_BASE}/global", headers=_get_headers(), timeout=8)
        r.raise_for_status()
        d = r.json().get("data", {})
        mcap = d.get("total_market_cap", {}).get("usd", 0)
        vol  = d.get("total_volume", {}).get("usd", 0)
        btc_dom = d.get("market_cap_percentage", {}).get("btc", 0)
        eth_dom = d.get("market_cap_percentage", {}).get("eth", 0)
        active  = d.get("active_cryptocurrencies", 0)
        change  = d.get("market_cap_change_percentage_24h_usd", 0)
        return {
            "total_market_cap": mcap,
            "total_volume_24h": vol,
            "btc_dominance": btc_dom,
            "eth_dominance": eth_dom,
            "active_coins": active,
            "market_cap_change_24h": change,
        }
    except Exception:
        return {
            "total_market_cap": 2.45e12,
            "total_volume_24h": 98e9,
            "btc_dominance": 54.2,
            "eth_dominance": 17.1,
            "active_coins": 13500,
            "market_cap_change_24h": 1.23,
        }


@st.cache_data(ttl=300, show_spinner=False)
def get_coin_detail(coin_id: str) -> dict:
    """Return detailed info for a specific coin."""
    try:
        r = requests.get(
            f"{COINGECKO_BASE}/coins/{coin_id}",
            headers=_get_headers(),
            params={"localization": False, "tickers": False, "community_data": True,
                    "developer_data": False},
            timeout=10,
        )
        r.raise_for_status()
        d = r.json()
        desc = d.get("description", {}).get("en", "")
        # Strip HTML tags
        import re
        desc = re.sub(r"<[^>]+>", "", desc)[:800]
        return {
            "name": d.get("name", coin_id),
            "symbol": d.get("symbol", "").upper(),
            "description": desc,
            "homepage": (d.get("links", {}).get("homepage") or [""])[0],
            "twitter": d.get("links", {}).get("twitter_screen_name", ""),
            "reddit": d.get("links", {}).get("subreddit_url", ""),
            "genesis_date": d.get("genesis_date", "N/A"),
            "hashing_algorithm": d.get("hashing_algorithm", "N/A"),
            "sentiment_votes_up": d.get("sentiment_votes_up_percentage", 0),
            "sentiment_votes_down": d.get("sentiment_votes_down_percentage", 0),
        }
    except Exception:
        return {"name": coin_id, "symbol": coin_id.upper(), "description": "Data unavailable.", "homepage": ""}


@st.cache_data(ttl=300, show_spinner=False)
def get_coin_history(coin_id: str, days: int = 30) -> pd.DataFrame:
    """Return OHLCV history for a coin as a DataFrame."""
    try:
        r = requests.get(
            f"{COINGECKO_BASE}/coins/{coin_id}/market_chart",
            headers=_get_headers(),
            params={"vs_currency": "usd", "days": days, "interval": "daily" if days > 7 else "hourly"},
            timeout=12,
        )
        r.raise_for_status()
        data = r.json()
        prices = data.get("prices", [])
        volumes = data.get("total_volumes", [])
        df = pd.DataFrame(prices, columns=["timestamp_ms", "price"])
        df["date"] = pd.to_datetime(df["timestamp_ms"], unit="ms")
        if volumes:
            vol_df = pd.DataFrame(volumes, columns=["timestamp_ms", "volume"])
            df["volume"] = vol_df["volume"].values
        df = df.drop(columns=["timestamp_ms"])
        return df
    except Exception:
        return pd.DataFrame(columns=["date", "price", "volume"])


# ── Stub data for offline / rate-limited state ────────────────────────────

def _stub_coins(n: int) -> pd.DataFrame:
    stubs = [
        ("bitcoin","BTC","Bitcoin",65000,1.25e12,45e9,2.1,0.3,8.5,1,"https://assets.coingecko.com/coins/images/1/large/bitcoin.png"),
        ("ethereum","ETH","Ethereum",3200,3.8e11,22e9,-0.5,-0.1,4.2,2,"https://assets.coingecko.com/coins/images/279/large/ethereum.png"),
        ("binancecoin","BNB","BNB",580,8.4e10,2.1e9,1.2,0.2,3.1,3,"https://assets.coingecko.com/coins/images/825/large/bnb-icon2_2x.png"),
        ("solana","SOL","Solana",155,7.1e10,4.5e9,3.4,0.8,12.1,4,"https://assets.coingecko.com/coins/images/4128/large/solana.png"),
        ("ripple","XRP","XRP",0.52,2.9e10,1.8e9,-1.1,-0.4,-2.3,5,"https://assets.coingecko.com/coins/images/44/large/xrp-symbol-white-128.png"),
    ]
    rows = []
    for s in stubs[:n]:
        rows.append({
            "coin_id": s[0], "symbol": s[1], "name": s[2], "price_usd": s[3],
            "market_cap": s[4], "volume_24h": s[5], "change_24h": s[6],
            "change_1h": s[7], "change_7d": s[8], "rank": s[9], "image_url": s[10],
        })
    return pd.DataFrame(rows)
