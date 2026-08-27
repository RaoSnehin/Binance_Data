"""
CryptoSphere — Page 2: Contagion Lab
Original PySpark pipeline analytics: volatility, safety scores,
contagion matrix, ML buy/sell signals, and forecasts.
"""
import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
import subprocess

st.set_page_config(page_title="Contagion Lab · CryptoSphere", page_icon="🌊", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-title { font-size:2rem; font-weight:800; background: linear-gradient(135deg,#7C3AED,#06B6D4);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
</style>
""", unsafe_allow_html=True)

st.markdown('<span class="page-title">🌊 Contagion Lab</span>', unsafe_allow_html=True)
st.caption("PySpark-powered analytics — volatility, safety scoring, cross-asset correlation & ML signals")

import os
LOCAL_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "dashboard_cache")

@st.cache_data(ttl=600, show_spinner=False)
def load_pipeline_data():
    try:
        df          = pd.read_parquet(os.path.join(LOCAL_CACHE_DIR, "scored_data.parquet"))
        corr_matrix = pd.read_csv(os.path.join(LOCAL_CACHE_DIR, "contagion_matrix.csv"), index_col=0)
        forecast    = pd.read_parquet(os.path.join(LOCAL_CACHE_DIR, "forecast_data.parquet"))
        signals_path = os.path.join(LOCAL_CACHE_DIR, "signals_data.parquet")
        signals = pd.read_parquet(signals_path) if os.path.exists(signals_path) else pd.DataFrame()
        df       = df.drop_duplicates(subset=["symbol","date"]).sort_values(["symbol","date"])
        forecast = forecast.drop_duplicates(subset=["symbol","date"]).sort_values(["symbol","date"])
        if not signals.empty:
            signals = signals.drop_duplicates(subset=["symbol","date"]).sort_values(["symbol","date"])
        return df, corr_matrix, forecast, signals, None
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), str(e)

with st.spinner("Loading pipeline data…"):
    df, corr_matrix, forecast, signals, err = load_pipeline_data()

if df.empty:
    st.warning("📦 Pipeline data not found. Run `python main.py` to generate it.")
    if err:
        st.error(f"Details: {err}")
    st.stop()

df["date"]       = pd.to_datetime(df["date"])
forecast["date"] = pd.to_datetime(forecast["date"])
if not signals.empty:
    signals["date"] = pd.to_datetime(signals["date"])

symbols = sorted(df["symbol"].dropna().unique().tolist())
latest_date = df["date"].max()

# ── Staleness Warning ──────────────────────────────────────────────────────
from datetime import datetime as dt_cls
days_stale = (pd.Timestamp(dt_cls.now()) - latest_date).days
if days_stale > 3:
    st.warning(f"⚠️ Data is **{days_stale} days old** (latest: {latest_date.date()}). Re-run `python main.py` to refresh.")

# ── 1. Comparative Price & Volatility ─────────────────────────────────────
st.header("1. Comparative Price & Volatility Trend")
c1, c2 = st.columns(2)
with c1: coin1 = st.selectbox("Coin 1", symbols, index=0)
with c2: coin2 = st.selectbox("Coin 2", symbols, index=min(1, len(symbols)-1))

compare_df = df[df["symbol"].isin([coin1, coin2])]
fig_p = px.line(compare_df, x="date", y="close_usd", color="symbol",
                title="USD Price Trend",
                color_discrete_sequence=["#7C3AED","#06B6D4"])
fig_p.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#94A3B8"),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
st.plotly_chart(fig_p, use_container_width=True)

if "volatility_30d" in df.columns:
    fig_v = px.line(compare_df, x="date", y="volatility_30d", color="symbol",
                    title="30-Day Rolling Volatility",
                    color_discrete_sequence=["#7C3AED","#06B6D4"])
    fig_v.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#94A3B8"),
                        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
    st.plotly_chart(fig_v, use_container_width=True)

# ── 2. Safety Leaderboard ─────────────────────────────────────────────────
st.header("2. Top 10 Safest Coins (by Sharpe Ratio)")
st.markdown("**Safety Score ≈ Sharpe Ratio** = 30d Return / 30d Volatility. Higher = better risk-adjusted return.")

latest_df  = df[df["date"] == latest_date]
top_10     = latest_df.sort_values("safety_score", ascending=False).head(10)
disp_cols  = [c for c in ["symbol","close_usd","volatility_30d","return_30d","safety_score"] if c in top_10.columns]
top_10_d   = top_10[disp_cols].copy()
top_10_d.columns = [{"symbol":"Symbol","close_usd":"Price (USD)","volatility_30d":"30d Vol",
                     "return_30d":"30d Return","safety_score":"Safety (Sharpe)"}.get(c,c)
                    for c in top_10_d.columns]
st.dataframe(top_10_d.reset_index(drop=True), use_container_width=True)

# ── 3. Contagion Matrix ────────────────────────────────────────────────────
st.header("3. Contagion Matrix (Pearson Correlation)")
st.markdown("Correlation among highest-volume assets. Values near **1.0** = crash/pump together (contagion risk).")

latest_unique = latest_df.drop_duplicates(subset=["symbol"])
total_days = df["date"].nunique()
coverage = df.groupby("symbol")["date"].count().reset_index()
coverage.columns = ["symbol","n_days"]
coverage = coverage[coverage["n_days"] >= 0.9 * total_days]
eligible = latest_unique[latest_unique["symbol"].isin(coverage["symbol"])]

if "avg_volume_30d" in eligible.columns:
    top_vol = eligible.sort_values("avg_volume_30d", ascending=False).head(30)["symbol"].tolist()
else:
    top_vol = eligible["symbol"].head(30).tolist()

valid_coins = [c for c in top_vol if c in corr_matrix.columns]
if valid_coins:
    sub_matrix = corr_matrix.loc[valid_coins, valid_coins]
    fig_corr = px.imshow(sub_matrix, text_auto=False, aspect="auto",
                         title="Correlation Matrix (Top Volume Coins)",
                         color_continuous_scale="Blues")
    fig_corr.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8"))
    st.plotly_chart(fig_corr, use_container_width=True)
else:
    st.info("Not enough data to build contagion matrix.")

# ── 4. ML Signals ─────────────────────────────────────────────────────────
st.header("4. Buy / Sell / Hold Signals (ML Gradient Boosting)")
st.markdown(
    "**16-feature Gradient Boosting Classifier** with balanced class weights.  \n"
    "🟢 **UP** (top 30% return) | 🔴 **DOWN** (bottom 30%) | ⚪ **NEUTRAL** (middle 40%)"
)

if signals.empty:
    st.info("Signal data not found. Run `python main.py` to generate.")
else:
    latest_sig_date = signals["date"].max()
    latest_sigs = (signals[signals["date"] == latest_sig_date]
                   .drop_duplicates(subset=["symbol"])
                   .sort_values("prob_up", ascending=False))

    def sig_icon(s):
        return "🟢 UP" if s == "UP" else ("🔴 DOWN" if s == "DOWN" else "⚪ NEUTRAL")
    latest_sigs["Signal"] = latest_sigs["signal"].apply(sig_icon)

    n_up = (latest_sigs["signal"] == "UP").sum()
    n_dn = (latest_sigs["signal"] == "DOWN").sum()
    n_ne = (latest_sigs["signal"] == "NEUTRAL").sum()
    cs1, cs2, cs3 = st.columns(3)
    cs1.metric("🟢 BUY Signals",  n_up)
    cs2.metric("🔴 SELL Signals", n_dn)
    cs3.metric("⚪ HOLD Signals", n_ne)

    for pct_col in ["prob_up","prob_down","prob_neutral"]:
        if pct_col in latest_sigs.columns:
            latest_sigs[pct_col.replace("prob_","Prob ").title()+" %"] = (latest_sigs[pct_col]*100).round(1)

    show_cols = ["symbol","Signal"] + [c for c in latest_sigs.columns if "Prob" in c and "%" in c]
    st.dataframe(latest_sigs[show_cols].rename(columns={"symbol":"Coin"}).reset_index(drop=True),
                 use_container_width=True)

    st.subheader("Signal History for Selected Coin")
    sig_coin = st.selectbox("Select coin", sorted(signals["symbol"].unique().tolist()), key="sig_coin")
    coin_sig = signals[signals["symbol"] == sig_coin].sort_values("date")
    fig_sig  = go.Figure()
    if "prob_up" in coin_sig.columns:
        fig_sig.add_trace(go.Scatter(x=coin_sig["date"], y=coin_sig["prob_up"],
                                     name="Prob UP", fill="tozeroy", line=dict(color="#22C55E",width=1.5)))
    if "prob_down" in coin_sig.columns:
        fig_sig.add_trace(go.Scatter(x=coin_sig["date"], y=coin_sig["prob_down"],
                                     name="Prob DOWN", fill="tozeroy", line=dict(color="#EF4444",width=1.5)))
    fig_sig.update_layout(
        title=f"Buy/Sell Probability — {sig_coin}",
        xaxis_title="Date", yaxis_title="Probability",
        yaxis=dict(range=[0,1]),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94A3B8"),
    )
    st.plotly_chart(fig_sig, use_container_width=True)
