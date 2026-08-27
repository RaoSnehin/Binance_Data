"""
CryptoSphere — Chatbot Helper Module
Calls the Gemini API via direct HTTPS REST requests (no SDK).
This avoids all import namespace conflicts with google-api-python-client.

Design principle: TRUTHFULNESS FIRST.
- Real prices from CoinGecko are injected into every prompt.
- A strict system prompt prevents the model from fabricating any market data.
- If live data is unavailable, the bot says so explicitly.
"""

import streamlit as st
import requests
import json
from datetime import datetime


# ── Constants ─────────────────────────────────────────────────────────────────

COINGECKO_BASE   = "https://api.coingecko.com/api/v3"
FG_API           = "https://api.alternative.me/fng/?limit=1"
GEMINI_BASE      = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_MODEL     = "models/gemini-flash-latest"
GEMINI_TIMEOUT   = 40   # seconds — Gemini can be slow with large system prompts


CRYPTOSPHERE_KNOWLEDGE = """
## CryptoSphere Platform Knowledge Base

### What is CryptoSphere?
CryptoSphere is a centralized crypto intelligence platform for investors, traders, and learners.
Built with Streamlit, Python, PySpark, and scikit-learn. Uses CoinGecko for live prices,
Alternative.me for Fear & Greed Index, CryptoPanic for news, and YouTube for educational videos.

### Pages / Features:
1. **🏠 Home** — Live ticker bar (top 15 coins), Global Market Snapshot (total market cap,
   24h volume, BTC dominance, active coins, Fear & Greed), Top Movers (top 5 gainers/losers),
   Market Heatmap (treemap of top 30 coins colored by 24h change).

2. **📊 Live Market** — Full leaderboard of top 200 coins, treemap heatmap, price history
   chart (1d/7d/30d/90d) for any selected coin with volume bars.

3. **🌊 Contagion Lab** — PySpark-powered analytics pipeline showing:
   - Volatility analysis (30-day rolling std dev)
   - ML buy/sell signals (Gradient Boosting Classifier on 13 technical indicators)
   - Correlation heatmap between coins (contagion matrix)
   Requires running `python main.py` first to generate the pipeline data cache.

4. **📰 News Hub** — Live crypto news from CryptoPanic API and RSS feeds.
   Each article has a sentiment badge (bullish/bearish/neutral).

5. **🎬 Video Center** — Curated crypto education videos from YouTube.

6. **🎓 Crypto Academy** — Glossary, concept cards (DeFi, NFTs, Layer-2, etc.),
   how-to guides, and a 10-question quiz.

7. **💼 Virtual Portfolio Tracker** — Simulate a crypto portfolio:
   - Add any coin with your quantity and buy price
   - See live P&L updated every 60 seconds from CoinGecko
   - Formula: P&L ($) = (Live Price − Buy Price) × Quantity
   - Allocation pie chart and P&L bar chart by position
   - Summary: Total Invested, Current Value, Total P&L ($), P&L (%), # Positions
   - Export to CSV; Clear Portfolio button
   - SESSION ONLY: data resets on page refresh — no permanent storage, no real money

8. **🔮 Forecast & AI** —
   - Fear & Greed gauge with 10-day history (from Alternative.me)
   - Bitcoin halving countdown (next: April 2028, block 1,050,000 → 1.5625 BTC reward)
   - AI Analyst verdicts (rule-based: safety score + volatility + F&G)
   - 365-day quantile price forecast: 3 scenarios (p10 pessimistic / p50 expected / p90 optimistic)
     using Gradient Boosting Quantile Regression (MMQR methodology)
   Requires running `python main.py` first.

9. **🤖 Ask CryptoSphere** — AI chatbot (this page). Powered by Google Gemini.
   Answers platform questions, crypto concepts, uses live market data for truthful prices.

### Technical Stack:
- Frontend: Streamlit, Plotly
- Data pipeline: PySpark (local Spark session)
- ML: scikit-learn Gradient Boosting Classifier + Quantile Regressor
- APIs: CoinGecko (prices), Alternative.me (Fear & Greed), CryptoPanic (news), YouTube
- All API keys are optional — graceful fallbacks exist

### Data truthfulness:
Prices refresh every 60 seconds from CoinGecko. Fear & Greed refreshes hourly from Alternative.me.
This platform is for EDUCATIONAL and DEMONSTRATION purposes ONLY. NOT financial advice.
"""

SYSTEM_PROMPT = f"""You are CryptoBot, a helpful and honest AI assistant inside the CryptoSphere platform.

## YOUR ROLE
Help users understand:
1. How to use the CryptoSphere platform and its features
2. General cryptocurrency concepts, technology, and history
3. Current market data — ONLY using the [LIVE MARKET CONTEXT] provided to you

## STRICT TRUTHFULNESS RULES (MUST FOLLOW):
1. NEVER fabricate, invent, or guess specific prices, market caps, or percentage changes.
2. For current prices/data, use ONLY the numbers in [LIVE MARKET CONTEXT].
3. If a user asks about a coin not in the context, say: "I don't have live data for that — please check the Live Market page."
4. If live data failed, say: "Live market data is temporarily unavailable — check the Live Market page directly."
5. You MAY freely explain how cryptocurrencies work, their history, technology, and concepts.
6. ALWAYS add a disclaimer for market-related questions: "⚠️ This is not financial advice."

## PLATFORM KNOWLEDGE
{CRYPTOSPHERE_KNOWLEDGE}

## RESPONSE STYLE
- Friendly, clear, and concise
- Use bullet points for complex answers
- Use emojis sparingly but effectively
- For platform questions, mention which page/feature to use
"""


# ── Live Data Fetching ─────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def get_live_context_for_prompt(top_n: int = 20) -> dict:
    """
    Fetch live market data to inject into the chatbot prompt.
    Uses CoinGecko + Alternative.me. Cached for 60 seconds.
    """
    ctx = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
        "prices": {},
        "global": {},
        "fear_greed": {},
        "available": False,
        "error": None,
    }

    headers = {"accept": "application/json"}
    try:
        key = st.secrets.get("COINGECKO_KEY", "")
        if key:
            headers["x-cg-demo-api-key"] = key
    except Exception:
        pass

    # Top coins
    try:
        r = requests.get(
            f"{COINGECKO_BASE}/coins/markets",
            headers=headers,
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": min(top_n, 50),
                "page": 1,
                "sparkline": False,
                "price_change_percentage": "24h",
            },
            timeout=8,
        )
        r.raise_for_status()
        for c in r.json():
            sym = c.get("symbol", "").upper()
            ctx["prices"][sym] = {
                "name": c.get("name", ""),
                "price_usd": c.get("current_price", 0),
                "change_24h": c.get("price_change_percentage_24h", 0),
                "market_cap": c.get("market_cap", 0),
                "volume_24h": c.get("total_volume", 0),
                "rank": c.get("market_cap_rank", 0),
            }
        ctx["available"] = True
    except Exception as e:
        ctx["error"] = str(e)

    # Global stats
    try:
        rg = requests.get(f"{COINGECKO_BASE}/global", headers=headers, timeout=6)
        rg.raise_for_status()
        d = rg.json().get("data", {})
        ctx["global"] = {
            "total_market_cap_usd": d.get("total_market_cap", {}).get("usd", 0),
            "total_volume_24h_usd": d.get("total_volume", {}).get("usd", 0),
            "btc_dominance_pct": d.get("market_cap_percentage", {}).get("btc", 0),
            "market_cap_change_24h_pct": d.get("market_cap_change_percentage_24h_usd", 0),
        }
    except Exception:
        pass

    # Fear & Greed
    try:
        rf = requests.get(FG_API, timeout=5)
        rf.raise_for_status()
        fg = rf.json().get("data", [{}])[0]
        ctx["fear_greed"] = {
            "value": int(fg.get("value", 50)),
            "label": fg.get("value_classification", "Neutral"),
        }
    except Exception:
        ctx["fear_greed"] = {"value": 50, "label": "Neutral"}

    return ctx


def build_live_context_block(ctx: dict) -> str:
    """Format live context dict into a readable text block for prompt injection."""
    if not ctx.get("available"):
        return "[LIVE MARKET CONTEXT: Unavailable. Do NOT provide specific prices — tell user to check Live Market page.]"

    def fmt(n):
        if n >= 1e12: return f"${n/1e12:.2f}T"
        if n >= 1e9:  return f"${n/1e9:.2f}B"
        return f"${n:,.0f}"

    lines = [f"[LIVE MARKET CONTEXT — {ctx['timestamp']} (CoinGecko, ~1 min delay)]"]

    fg = ctx.get("fear_greed", {})
    lines.append(f"Fear & Greed Index: {fg.get('value','?')}/100 — {fg.get('label','?')}")

    g = ctx.get("global", {})
    if g:
        chg  = g.get("market_cap_change_24h_pct", 0)
        sign = "+" if chg >= 0 else ""
        lines.append(f"Global Market Cap: {fmt(g.get('total_market_cap_usd',0))} ({sign}{chg:.2f}% 24h)")
        lines.append(f"24h Volume: {fmt(g.get('total_volume_24h_usd',0))}")
        lines.append(f"BTC Dominance: {g.get('btc_dominance_pct',0):.1f}%")

    lines.append("\nLive Coin Prices:")
    for sym, info in list(ctx["prices"].items())[:25]:
        p   = info.get("price_usd", 0)
        chg = info.get("change_24h", 0) or 0
        ps  = (f"${p:,.2f}" if p >= 1000 else f"${p:.4f}" if p >= 1 else f"${p:.6f}")
        sign = "+" if chg >= 0 else ""
        lines.append(f"  {sym} ({info.get('name','')}) = {ps} ({sign}{chg:.2f}% 24h)")

    return "\n".join(lines)


# ── Gemini REST API ────────────────────────────────────────────────────────────

def _build_gemini_payload(user_message: str, chat_history: list, live_ctx: dict) -> dict:
    """Build the JSON payload for the Gemini generateContent endpoint."""
    ctx_block = build_live_context_block(live_ctx)

    # Build multi-turn contents list
    contents = []
    for msg in chat_history[:-1]:   # prior turns (exclude current user msg)
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    # Current user message — inject live context
    full_user_text = f"{ctx_block}\n\nUser question: {user_message}"
    contents.append({"role": "user", "parts": [{"text": full_user_text}]})

    return {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1024,
            "candidateCount": 1,
        },
    }


def _parse_gemini_response(data: dict) -> str:
    """Extract text from a Gemini REST API response dict."""
    try:
        candidates = data.get("candidates", [])
        if not candidates:
            return "I couldn't generate a response. The model returned no candidates."
        content = candidates[0].get("content", {})
        parts   = content.get("parts", [])
        text    = "".join(p.get("text", "") for p in parts).strip()
        if not text:
            finish = candidates[0].get("finishReason", "UNKNOWN")
            return f"The model returned an empty response (reason: {finish}). Please try rephrasing your question."
        return text
    except Exception as e:
        return f"Error parsing response: {e}"


def get_gemini_response(
    user_message: str,
    chat_history: list,
    api_key: str,
    live_ctx: dict,
) -> str:
    """
    Call Gemini REST API and return the full response text.
    No SDK — pure requests. Zero import conflicts.
    """
    if not api_key or not api_key.strip():
        return (
            "🔑 **No Gemini API key configured.**\n\n"
            "To enable the AI chatbot:\n"
            "1. Get a free key at https://aistudio.google.com/app/apikey\n"
            "2. Enter it in the sidebar, or add `GEMINI_KEY = \"your-key\"` to `.streamlit/secrets.toml`\n\n"
            "The rest of CryptoSphere works without a key — only this chatbot requires one."
        )

    url     = f"{GEMINI_BASE}/{GEMINI_MODEL}:generateContent?key={api_key.strip()}"
    payload = _build_gemini_payload(user_message, chat_history, live_ctx)

    try:
        r = requests.post(url, json=payload, timeout=GEMINI_TIMEOUT)
        if r.status_code == 400:
            return f"❌ Bad request (400). Check your API key format.\nDetails: {r.text[:200]}"
        if r.status_code == 403:
            return "❌ API key rejected (403 Forbidden). Please check your key at https://aistudio.google.com/app/apikey"
        if r.status_code == 429:
            return "⏳ Gemini rate limit reached (429). Please wait a moment and try again."
        if r.status_code != 200:
            return f"❌ Gemini API error ({r.status_code}): {r.text[:300]}"
        return _parse_gemini_response(r.json())

    except requests.exceptions.Timeout:
        return (
            "⏳ Gemini API timed out after 40 seconds. "
            "This can happen with slow network connections to Google's servers. "
            "Please try again in a moment."
        )
    except requests.exceptions.ConnectionError:
        return (
            "🌐 Cannot connect to Gemini API. "
            "Please check your internet connection and try again."
        )
    except Exception as e:
        return f"❌ Unexpected error: {e}"


def stream_gemini_response(
    user_message: str,
    chat_history: list,
    api_key: str,
    live_ctx: dict,
):
    """
    Generator that yields the full response text (non-streaming for reliability).
    We simulate streaming by yielding the full response at once.
    True SSE streaming via requests is complex — this keeps it simple and robust.
    """
    response = get_gemini_response(user_message, chat_history, api_key, live_ctx)
    # Yield in ~50-char chunks to simulate a streaming effect in the UI
    chunk_size = 50
    for i in range(0, len(response), chunk_size):
        yield response[i:i + chunk_size]
