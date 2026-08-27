"""
CryptoSphere — Page 3: News Hub
Aggregates crypto news from CryptoPanic API + RSS feeds.
Filterable by sentiment and currency.
"""
import streamlit as st
import time

st.set_page_config(page_title="News Hub · CryptoSphere", page_icon="📰", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-title { font-size:2rem; font-weight:800;
  background: linear-gradient(135deg,#7C3AED,#EC4899);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.news-card {
  background: rgba(19,19,43,0.9);
  border: 1px solid rgba(124,58,237,0.2);
  border-radius: 14px;
  padding: 1.1rem 1.3rem;
  margin-bottom: 0.9rem;
  transition: all 0.2s;
}
.news-card:hover { border-color: #7C3AED; transform: translateX(4px); }
.news-title { color: #E2E8F0; font-weight: 600; font-size: 0.95rem; line-height: 1.4; }
.news-meta  { color: #64748B; font-size: 0.75rem; margin-top: 0.4rem; }
.badge { display:inline-block; padding:0.15rem 0.55rem; border-radius:999px; font-size:0.72rem; font-weight:600; margin-right:0.3rem; }
.badge-bull { background:rgba(34,197,94,0.15);  color:#22C55E; }
.badge-bear { background:rgba(239,68,68,0.15);  color:#EF4444; }
.badge-neut { background:rgba(148,163,184,0.15);color:#94A3B8; }
.badge-hot  { background:rgba(251,146,60,0.2);  color:#FB923C; }
.badge-curr { background:rgba(59,130,246,0.15); color:#60A5FA; }
.source-tag { color:#7C3AED; font-weight:500; }
.divider-line { border:none; border-top:1px solid rgba(124,58,237,0.1); margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

from src.news_feed import get_crypto_news

st.markdown('<span class="page-title">📰 Crypto News Hub</span>', unsafe_allow_html=True)
st.caption("Aggregated from CryptoPanic, CoinDesk, CoinTelegraph & Decrypt · Updates every 5 minutes")

# ── Filters ────────────────────────────────────────────────────────────────
col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
with col_f1:
    sentiment_filter = st.selectbox(
        "Filter by sentiment / type",
        ["All News", "🔥 Hot", "📈 Bullish", "📉 Bearish", "⚡ Rising"],
        index=0
    )
with col_f2:
    currency_filter = st.text_input("Filter by coin (e.g. BTC, ETH)", placeholder="Leave blank for all")
with col_f3:
    st.markdown("<br>", unsafe_allow_html=True)
    n_articles = st.selectbox("Show", [15, 25, 40], index=0)

filter_map = {
    "All News": "hot",
    "🔥 Hot": "hot",
    "📈 Bullish": "bullish",
    "📉 Bearish": "bearish",
    "⚡ Rising": "rising",
}
api_filter = filter_map.get(sentiment_filter, "hot")

with st.spinner("Fetching latest crypto news…"):
    articles = get_crypto_news(
        filter_type=api_filter,
        currency=currency_filter.strip().upper() if currency_filter else "",
        limit=n_articles,
    )

if not articles:
    st.warning("No articles loaded. Check your internet connection or try removing the currency filter.")
    st.stop()

# ── Sentiment Stats ────────────────────────────────────────────────────────
bull_count = sum(1 for a in articles if a.get("sentiment") == "bullish")
bear_count = sum(1 for a in articles if a.get("sentiment") == "bearish")
neut_count = len(articles) - bull_count - bear_count
hot_count  = sum(1 for a in articles if a.get("is_hot"))

ms1, ms2, ms3, ms4 = st.columns(4)
ms1.metric("📰 Total Articles", len(articles))
ms2.metric("📈 Bullish",  bull_count)
ms3.metric("📉 Bearish",  bear_count)
ms4.metric("🔥 Hot",      hot_count)

st.markdown("<br>", unsafe_allow_html=True)

# ── Article Render ─────────────────────────────────────────────────────────
for art in articles:
    sent  = art.get("sentiment", "neutral")
    sent_cls  = {"bullish":"badge-bull","bearish":"badge-bear","neutral":"badge-neut"}.get(sent,"badge-neut")
    sent_icon = {"bullish":"📈","bearish":"📉","neutral":"⚪"}.get(sent,"⚪")
    sent_lbl  = {"bullish":"Bullish","bearish":"Bearish","neutral":"Neutral"}.get(sent,"Neutral")

    currs = art.get("currencies", [])
    curr_badges = " ".join(f'<span class="badge badge-curr">{c}</span>' for c in currs[:4])
    hot_badge   = '<span class="badge badge-hot">🔥 HOT</span>' if art.get("is_hot") else ""

    url   = art.get("url","#")
    title = art.get("title","")
    src   = art.get("source","")
    ts    = art.get("published_at","")

    st.markdown(f"""
    <div class="news-card">
      <div class="news-title">
        <a href="{url}" target="_blank" style="color:#E2E8F0;text-decoration:none;">{title}</a>
      </div>
      <hr class="divider-line"/>
      <div class="news-meta">
        <span class="source-tag">🔗 {src}</span> &nbsp;·&nbsp; {ts}
        &nbsp;&nbsp;
        <span class="badge {sent_cls}">{sent_icon} {sent_lbl}</span>
        {hot_badge}
        {curr_badges}
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.caption("💡 Tip: Add your CryptoPanic API key in `.streamlit/secrets.toml` for richer sentiment data.")
