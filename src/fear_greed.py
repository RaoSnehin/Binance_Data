"""
CryptoSphere — Fear & Greed Index Module
Fetches the Crypto Fear & Greed Index from Alternative.me (free, no key required).
"""
import requests
import streamlit as st

ALTME_URL = "https://api.alternative.me/fng/?limit=10&format=json"


@st.cache_data(ttl=3600, show_spinner=False)
def get_fear_greed() -> dict:
    """
    Returns the current Fear & Greed index.

    Returns dict with:
        value       : int 0-100
        label       : str e.g. "Extreme Fear", "Greed"
        timestamp   : str
        history     : list of (value, label, timestamp) for last 10 days
    """
    try:
        r = requests.get(ALTME_URL, timeout=8)
        r.raise_for_status()
        data = r.json().get("data", [])
        current = data[0] if data else {}
        history = [
            {"value": int(d["value"]), "label": d["value_classification"],
             "date": d.get("timestamp", "")}
            for d in data
        ]
        return {
            "value": int(current.get("value", 50)),
            "label": current.get("value_classification", "Neutral"),
            "timestamp": current.get("timestamp", ""),
            "history": history,
        }
    except Exception:
        return {"value": 55, "label": "Greed", "timestamp": "", "history": []}


def fear_greed_color(value: int) -> str:
    """Map F&G value to a hex color."""
    if value <= 20:
        return "#EF4444"   # Extreme Fear — red
    elif value <= 40:
        return "#F97316"   # Fear — orange
    elif value <= 60:
        return "#EAB308"   # Neutral — yellow
    elif value <= 80:
        return "#22C55E"   # Greed — green
    else:
        return "#15803D"   # Extreme Greed — dark green


def fear_greed_emoji(value: int) -> str:
    if value <= 20:   return "😱"
    elif value <= 40: return "😰"
    elif value <= 60: return "😐"
    elif value <= 80: return "😄"
    else:             return "🤑"
