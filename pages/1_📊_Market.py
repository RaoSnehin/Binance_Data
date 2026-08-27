"""
CryptoSphere — Page 1: Live Market Dashboard
Real-time prices, treemap heatmap, volume leaders, sparklines.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Live Market · CryptoSphere", page_icon="📊", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-title { font-size:2rem; font-weight:800; background: linear-gradient(135deg,#7C3AED,#3B82F6);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.metric-card { background:rgba(19,19,43,0.9); border:1px solid rgba(124,58,237,0.25);
  border-radius:14px; padding:1rem 1.2rem; }
.coin-row { display:flex; align-items:center; gap:0.8rem; padding:0.5rem 0;
  border-bottom:1px solid rgba(255,255,255,0.05); }
.badge-pos { background:rgba(34,197,94,0.15); color:#22C55E; border-radius:6px;
  padding:0.15rem 0.5rem; font-size:0.8rem; font-weight:600; }
.badge-neg { background:rgba(239,68,68,0.15); color:#EF4444; border-radius:6px;
  padding:0.15rem 0.5rem; font-size:0.8rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

from src.live_data import get_top_coins, get_global_stats, get_coin_history

st.markdown('<span class="page-title">📊 Live Market Dashboard</span>', unsafe_allow_html=True)
st.caption("Auto-refreshes every 60 seconds · Data from CoinGecko")

# ── Controls ───────────────────────────────────────────────────────────────
col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2,2,1])
with col_ctrl1:
    n_coins = st.slider("Number of coins to display", 10, 100, 50, step=10)
with col_ctrl2:
    sort_by = st.selectbox("Sort by", ["Market Cap (↓)", "24h Change (↓)", "24h Change (↑)", "Volume (↓)"])
with col_ctrl3:
    st.markdown("<br>", unsafe_allow_html=True)
    refresh = st.button("🔄 Refresh", use_container_width=True)

if refresh:
    st.cache_data.clear()

# ── Load data ──────────────────────────────────────────────────────────────
with st.spinner("Fetching live market data…"):
    df = get_top_coins(n_coins)

if df.empty:
    st.warning("Could not load live data. Check your internet connection.")
    st.stop()

# Apply sort
sort_map = {
    "Market Cap (↓)":   ("market_cap",   False),
    "24h Change (↓)":   ("change_24h",   False),
    "24h Change (↑)":   ("change_24h",   True),
    "Volume (↓)":       ("volume_24h",   False),
}
scol, sasc = sort_map[sort_by]
if scol in df.columns:
    df = df.sort_values(scol, ascending=sasc, na_position="last").reset_index(drop=True)

# ── Global stats ───────────────────────────────────────────────────────────
gs = get_global_stats()
def fmt(n):
    if n >= 1e12: return f"${n/1e12:.2f}T"
    if n >= 1e9:  return f"${n/1e9:.2f}B"
    return f"${n:,.0f}"

g1,g2,g3,g4 = st.columns(4)
g1.metric("Total Market Cap",   fmt(gs.get("total_market_cap",0)),   f"{gs.get('market_cap_change_24h',0):+.2f}%")
g2.metric("24h Volume",         fmt(gs.get("total_volume_24h",0)))
g3.metric("BTC Dominance",      f"{gs.get('btc_dominance',0):.1f}%")
g4.metric("Active Cryptocurrencies", f"{gs.get('active_coins',0):,}")

st.divider()

# ── Market Heatmap ─────────────────────────────────────────────────────────
st.subheader("🗺️ Market Heatmap")
hmap_df = df.dropna(subset=["market_cap","change_24h"]).copy()
hmap_df["label"] = hmap_df.apply(
    lambda r: f"{str(r.get('symbol','')).upper()}<br>{r.get('change_24h',0):+.2f}%", axis=1
)
fig_hmap = go.Figure(go.Treemap(
    labels=hmap_df["label"],
    parents=[""] * len(hmap_df),
    values=hmap_df["market_cap"],
    marker=dict(
        colors=hmap_df["change_24h"],
        colorscale=[[0,"#7F1D1D"],[0.35,"#B91C1C"],[0.48,"#1E293B"],
                    [0.52,"#1E293B"],[0.65,"#15803D"],[1,"#052E16"]],
        cmid=0, showscale=True,
        colorbar=dict(title="24h %", tickfont=dict(color="#94A3B8")),
    ),
    textfont=dict(color="white", size=12),
    hovertemplate="<b>%{label}</b><br>Market Cap: $%{value:,.0f}<extra></extra>",
))
fig_hmap.update_layout(
    height=420, margin=dict(t=5,b=5,l=5,r=5),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_hmap, use_container_width=True)

# ── Price Table ────────────────────────────────────────────────────────────
st.subheader("📋 Full Coin Leaderboard")

display_cols = ["rank","name","symbol","price_usd","change_1h","change_24h","change_7d","volume_24h","market_cap"]
available = [c for c in display_cols if c in df.columns]
table_df = df[available].copy()

rename_map = {
    "rank":"#", "name":"Coin","symbol":"Ticker",
    "price_usd":"Price (USD)","change_1h":"1h %","change_24h":"24h %","change_7d":"7d %",
    "volume_24h":"Volume 24h","market_cap":"Market Cap",
}
table_df = table_df.rename(columns={k:v for k,v in rename_map.items() if k in table_df})
table_df["Ticker"] = table_df["Ticker"].str.upper()

# Format numbers
for col in ["Price (USD)"]:
    if col in table_df: table_df[col] = table_df[col].apply(lambda x: f"${x:,.4g}" if pd.notna(x) else "-")
for col in ["Volume 24h","Market Cap"]:
    if col in table_df: table_df[col] = table_df[col].apply(lambda x: fmt(x) if pd.notna(x) else "-")
for col in ["1h %","24h %","7d %"]:
    if col in table_df: table_df[col] = table_df[col].apply(
        lambda x: f"▲ {x:.2f}%" if (pd.notna(x) and x>=0) else (f"▼ {abs(x):.2f}%" if pd.notna(x) else "-"))

st.dataframe(table_df.reset_index(drop=True), use_container_width=True, height=420)

# ── Individual Coin Chart ──────────────────────────────────────────────────
st.divider()
st.subheader("📈 Individual Coin Price Chart")
coin_options = list(df["name"].dropna().unique()) if "name" in df.columns else ["bitcoin"]
selected_name = st.selectbox("Select coin", coin_options, index=0)

row = df[df["name"] == selected_name].iloc[0] if not df[df["name"]==selected_name].empty else None
if row is not None:
    coin_id = row.get("coin_id", selected_name.lower().replace(" ","-"))
    days    = st.radio("Time range", [7, 30, 90, 365], horizontal=True, format_func=lambda d: f"{d}D")

    symbol  = str(row.get("symbol", "")).upper()
    hist    = get_coin_history(coin_id, days, symbol=symbol)
    if not hist.empty:
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=hist["date"], y=hist["price"],
            mode="lines",
            fill="tozeroy",
            fillcolor="rgba(124,58,237,0.08)",
            line=dict(color="#7C3AED", width=2),
            name="Price",
        ))
        fig_line.update_layout(
            title=f"{selected_name} — {days}D Price History",
            xaxis_title="Date", yaxis_title="Price (USD)",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            font=dict(color="#94A3B8"),
            height=380,
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Historical data unavailable for this coin.")
