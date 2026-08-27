"""
CryptoSphere — Main Landing Page
A centralized crypto intelligence platform for investors, traders & learners.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ── Must be first Streamlit call ───────────────────────────────────────────
st.set_page_config(
    page_title="CryptoSphere — Crypto Intelligence Platform",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com",
        "About": "## CryptoSphere\nReal-time crypto analytics, news, education & portfolio tracking.",
    },
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.hero-title {
    font-size: 3.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 50%, #06B6D4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    line-height: 1.1;
    margin-bottom: 0.3rem;
}
.hero-sub {
    text-align: center;
    color: #94A3B8;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}
.stat-card {
    background: linear-gradient(135deg, rgba(124,58,237,0.15), rgba(59,130,246,0.10));
    border: 1px solid rgba(124,58,237,0.3);
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    text-align: center;
    transition: transform 0.2s;
}
.stat-card:hover { transform: translateY(-3px); }
.stat-label { color: #94A3B8; font-size: 0.78rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em; }
.stat-value { color: #E2E8F0; font-size: 1.6rem; font-weight: 700; }
.stat-change-pos { color: #22C55E; font-size: 0.85rem; }
.stat-change-neg { color: #EF4444; font-size: 0.85rem; }

.nav-card {
    background: rgba(19,19,43,0.8);
    border: 1px solid rgba(124,58,237,0.25);
    border-radius: 16px;
    padding: 1.4rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.25s ease;
    text-decoration: none;
    display: block;
}
.nav-card:hover {
    border-color: #7C3AED;
    background: rgba(124,58,237,0.12);
    transform: translateY(-4px);
    box-shadow: 0 8px 32px rgba(124,58,237,0.25);
}
.nav-icon { font-size: 2.2rem; display: block; margin-bottom: 0.5rem; }
.nav-title { color: #E2E8F0; font-weight: 600; font-size: 0.95rem; }
.nav-desc  { color: #64748B; font-size: 0.75rem; margin-top: 0.25rem; }

.ticker-row {
    display: flex;
    gap: 1.2rem;
    overflow-x: auto;
    padding: 0.6rem 0;
    scrollbar-width: none;
}
.ticker-item {
    background: rgba(19,19,43,0.9);
    border: 1px solid rgba(124,58,237,0.2);
    border-radius: 10px;
    padding: 0.5rem 1rem;
    white-space: nowrap;
    flex-shrink: 0;
    font-size: 0.88rem;
}
.ticker-coin  { color: #94A3B8; font-weight: 500; }
.ticker-price { color: #E2E8F0; font-weight: 700; margin: 0 0.4rem; }
.ticker-pos   { color: #22C55E; }
.ticker-neg   { color: #EF4444; }

.section-header {
    font-size: 1.3rem;
    font-weight: 700;
    color: #E2E8F0;
    border-left: 4px solid #7C3AED;
    padding-left: 0.8rem;
    margin: 1.5rem 0 1rem 0;
}
.fg-badge {
    display: inline-block;
    padding: 0.4rem 1.2rem;
    border-radius: 999px;
    font-weight: 700;
    font-size: 1rem;
}
.mover-up   { color: #22C55E; font-weight: 600; }
.mover-down { color: #EF4444; font-weight: 600; }

.footer {
    text-align: center;
    color: #334155;
    font-size: 0.75rem;
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid rgba(124,58,237,0.1);
}
</style>
""", unsafe_allow_html=True)

# ── Import data modules ────────────────────────────────────────────────────
try:
    from src.live_data import get_top_coins, get_global_stats
    from src.fear_greed import get_fear_greed, fear_greed_color, fear_greed_emoji
    LIVE_OK = True
except Exception:
    LIVE_OK = False

# ── Hero ───────────────────────────────────────────────────────────────────
st.markdown('<h1 class="hero-title">🌐 CryptoSphere</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">Your centralized crypto intelligence platform — '
    'Live markets · Breaking news · Education · Portfolio tracking · AI insights</p>',
    unsafe_allow_html=True
)

# ── Live Ticker Bar ────────────────────────────────────────────────────────
if LIVE_OK:
    with st.spinner("Loading live prices…"):
        coins_df = get_top_coins(20)
        global_stats = get_global_stats()
        fg = get_fear_greed()

    ticker_html = '<div class="ticker-row">'
    for _, row in coins_df.head(15).iterrows():
        chg   = row.get("change_24h", 0) or 0
        price = row.get("price_usd", 0) or 0
        sym   = str(row.get("symbol", "")).upper()
        cls   = "ticker-pos" if chg >= 0 else "ticker-neg"
        arrow = "▲" if chg >= 0 else "▼"
        ticker_html += (
            f'<div class="ticker-item">'
            f'<span class="ticker-coin">{sym}</span>'
            f'<span class="ticker-price">${price:,.2f}</span>'
            f'<span class="{cls}">{arrow} {abs(chg):.2f}%</span>'
            f'</div>'
        )
    ticker_html += "</div>"
    st.markdown(ticker_html, unsafe_allow_html=True)
else:
    st.info("⚡ Live price ticker loading… Check internet connection.")
    coins_df     = pd.DataFrame()
    global_stats = {}
    fg           = {"value": 55, "label": "Greed"}

# ── Global Market Stats ────────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Global Market Snapshot</div>', unsafe_allow_html=True)

def fmt_large(n):
    if n >= 1e12: return f"${n/1e12:.2f}T"
    if n >= 1e9:  return f"${n/1e9:.2f}B"
    if n >= 1e6:  return f"${n/1e6:.2f}M"
    return f"${n:,.0f}"

c1, c2, c3, c4, c5 = st.columns(5)
mcap = global_stats.get("total_market_cap", 0)
vol  = global_stats.get("total_volume_24h", 0)
btcd = global_stats.get("btc_dominance", 0)
ethd = global_stats.get("eth_dominance", 0)
chg  = global_stats.get("market_cap_change_24h", 0)
ac   = global_stats.get("active_coins", 0)
fg_val = fg.get("value", 50)
fg_lbl = fg.get("label", "Neutral")

chg_cls = "stat-change-pos" if chg >= 0 else "stat-change-neg"

for col, label, val, sub in [
    (c1, "Total Market Cap",   fmt_large(mcap),  f'<span class="{chg_cls}">{"▲" if chg>=0 else "▼"} {abs(chg):.2f}% 24h</span>'),
    (c2, "24h Volume",         fmt_large(vol),   ""),
    (c3, "BTC Dominance",      f"{btcd:.1f}%",   ""),
    (c4, "Active Coins",       f"{ac:,}",         ""),
    (c5, "Fear & Greed",       f'{fear_greed_emoji(fg_val)} {fg_val}', f'<span style="color:{fear_greed_color(fg_val)}">{fg_lbl}</span>'),
]:
    col.markdown(
        f'<div class="stat-card"><div class="stat-label">{label}</div>'
        f'<div class="stat-value">{val}</div><div>{sub}</div></div>',
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Top Movers ─────────────────────────────────────────────────────────────
if not coins_df.empty and "change_24h" in coins_df.columns:
    st.markdown('<div class="section-header">🚀 Top Movers (24h)</div>', unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    sorted_df = coins_df.dropna(subset=["change_24h"]).sort_values("change_24h", ascending=False)
    top5  = sorted_df.head(5)
    bot5  = sorted_df.tail(5)

    with m1:
        st.markdown("**🟢 Top Gainers**")
        for _, r in top5.iterrows():
            sym = str(r.get("symbol","")).upper()
            p   = r.get("price_usd", 0) or 0
            c   = r.get("change_24h", 0) or 0
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:0.4rem 0;'
                f'border-bottom:1px solid rgba(124,58,237,0.1);">'
                f'<span style="color:#E2E8F0;font-weight:600">{sym}</span>'
                f'<span style="color:#94A3B8">${p:,.4g}</span>'
                f'<span class="mover-up">▲ {c:.2f}%</span></div>',
                unsafe_allow_html=True
            )
    with m2:
        st.markdown("**🔴 Top Losers**")
        for _, r in bot5[::-1].iterrows():
            sym = str(r.get("symbol","")).upper()
            p   = r.get("price_usd", 0) or 0
            c   = r.get("change_24h", 0) or 0
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:0.4rem 0;'
                f'border-bottom:1px solid rgba(239,68,68,0.1);">'
                f'<span style="color:#E2E8F0;font-weight:600">{sym}</span>'
                f'<span style="color:#94A3B8">${p:,.4g}</span>'
                f'<span class="mover-down">▼ {abs(c):.2f}%</span></div>',
                unsafe_allow_html=True
            )

# ── Market Heatmap Mini ────────────────────────────────────────────────────
if not coins_df.empty and "market_cap" in coins_df.columns:
    st.markdown('<div class="section-header">🗺️ Market Heatmap (Top 30 by Market Cap)</div>', unsafe_allow_html=True)
    hmap_df = coins_df.dropna(subset=["market_cap", "change_24h"]).head(30).copy()
    hmap_df["label"] = hmap_df.apply(
        lambda r: f"{str(r.get('symbol','')).upper()}<br>{r.get('change_24h',0):+.2f}%", axis=1
    )
    fig_hmap = go.Figure(go.Treemap(
        labels=hmap_df["label"],
        parents=["" for _ in range(len(hmap_df))],
        values=hmap_df["market_cap"],
        marker=dict(
            colors=hmap_df["change_24h"],
            colorscale=[
                [0.0,  "#7F1D1D"],
                [0.35, "#991B1B"],
                [0.48, "#1E293B"],
                [0.52, "#1E293B"],
                [0.65, "#14532D"],
                [1.0,  "#15803D"],
            ],
            cmid=0,
            showscale=True,
            colorbar=dict(title="24h %", tickfont=dict(color="#94A3B8")),
        ),
        textfont=dict(color="white", size=13),
        hovertemplate="<b>%{label}</b><br>Market Cap: $%{value:,.0f}<extra></extra>",
    ))
    fig_hmap.update_layout(
        height=380,
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_hmap, use_container_width=True)

# ── Navigation Cards ───────────────────────────────────────────────────────
st.markdown('<div class="section-header">🧭 Explore CryptoSphere</div>', unsafe_allow_html=True)

nav_items = [
    ("📊", "Live Market",      "Real-time prices, heatmap & movers",       "pages/1_📊_Market.py"),
    ("🌊", "Contagion Lab",    "Volatility, ML signals & correlations",     "pages/2_🌊_Contagion.py"),
    ("📰", "News Hub",         "Live crypto news with sentiment filters",   "pages/3_📰_News.py"),
    ("🎬", "Video Center",     "Curated crypto educational videos",         "pages/4_🎬_Videos.py"),
    ("🎓", "Crypto Academy",   "Learn crypto from scratch + quiz",          "pages/5_🎓_Learn.py"),
    ("💼", "Portfolio",        "Virtual portfolio tracker with P&L",        "pages/6_💼_Portfolio.py"),
    ("🔮", "Forecast & AI",    "ML forecasts, Fear & Greed + AI analyst",   "pages/7_🔮_Forecast.py"),
    ("🤖", "Ask CryptoSphere", "AI chatbot with live market context",       "pages/8_🤖_Ask_CryptoSphere.py"),
]

cols = st.columns(4)  # 4-column grid handles up to 8 items (2 rows)
for i, (icon, title, desc, _path) in enumerate(nav_items):
    with cols[i % 4]:
        st.markdown(
            f'<div class="nav-card">'
            f'<span class="nav-icon">{icon}</span>'
            f'<div class="nav-title">{title}</div>'
            f'<div class="nav-desc">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        st.markdown("<div style='margin-bottom:0.8rem'></div>", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer">🌐 <b>CryptoSphere</b> · Built with Streamlit · '
    'Data: CoinGecko, Alternative.me, CryptoPanic · '
    '⚠️ Not financial advice · Use responsibly</div>',
    unsafe_allow_html=True
)
