"""
CryptoSphere — Page 7: Forecast & AI Insights
ML-based price projections, Fear & Greed gauge, AI Analyst verdicts, Bitcoin halving countdown.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import datetime, timezone

st.set_page_config(page_title="Forecast & AI · CryptoSphere", page_icon="🔮", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-title { font-size:2rem; font-weight:800;
  background: linear-gradient(135deg,#A855F7,#EC4899);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.ai-card {
  background: rgba(19,19,43,0.95);
  border: 1px solid rgba(168,85,247,0.3);
  border-radius: 16px;
  padding: 1.4rem 1.6rem;
  margin-bottom: 1rem;
}
.ai-header { color:#A855F7; font-weight:700; font-size:0.85rem; text-transform:uppercase;
  letter-spacing:0.1em; margin-bottom:0.6rem; }
.verdict { font-size:1rem; color:#E2E8F0; font-weight:500; line-height:1.7; }
.signal-up   { color:#22C55E; font-weight:700; }
.signal-down { color:#EF4444; font-weight:700; }
.signal-hold { color:#EAB308; font-weight:700; }
.halving-card {
  background: linear-gradient(135deg,rgba(251,146,60,0.1),rgba(239,68,68,0.08));
  border: 1px solid rgba(251,146,60,0.3);
  border-radius: 16px; padding: 1.4rem 1.6rem; text-align:center;
}
.halving-num { font-size:2.4rem; font-weight:800; color:#FB923C; }
.halving-sub { color:#94A3B8; font-size:0.85rem; }
</style>
""", unsafe_allow_html=True)

from src.fear_greed import get_fear_greed, fear_greed_color, fear_greed_emoji

st.markdown('<span class="page-title">🔮 Forecast & AI Insights</span>', unsafe_allow_html=True)
st.caption("ML-based quantile forecasts · Fear & Greed index · AI analyst verdicts · Bitcoin cycle metrics")

# ── Load pipeline data ─────────────────────────────────────────────────────
LOCAL_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "dashboard_cache")

@st.cache_data(ttl=600, show_spinner=False)
def load_forecast_data():
    try:
        df       = pd.read_parquet(os.path.join(LOCAL_CACHE_DIR, "scored_data.parquet"))
        forecast = pd.read_parquet(os.path.join(LOCAL_CACHE_DIR, "forecast_data.parquet"))
        df       = df.drop_duplicates(subset=["symbol","date"]).sort_values(["symbol","date"])
        forecast = forecast.drop_duplicates(subset=["symbol","date"]).sort_values(["symbol","date"])
        df["date"]       = pd.to_datetime(df["date"])
        forecast["date"] = pd.to_datetime(forecast["date"])
        signals_path = os.path.join(LOCAL_CACHE_DIR, "signals_data.parquet")
        signals = pd.read_parquet(signals_path) if os.path.exists(signals_path) else pd.DataFrame()
        if not signals.empty:
            signals = signals.drop_duplicates(subset=["symbol","date"]).sort_values(["symbol","date"])
            signals["date"] = pd.to_datetime(signals["date"])
        return df, forecast, signals, None
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), str(e)

with st.spinner("Loading analytics data…"):
    df, forecast, signals, err = load_forecast_data()
    fg = get_fear_greed()

has_pipeline = not df.empty

# ── Layout: Fear & Greed + Halving ────────────────────────────────────────
col_fg, col_hv = st.columns([3, 2])

with col_fg:
    st.subheader("😱 Crypto Fear & Greed Index")
    fg_val  = fg.get("value", 50)
    fg_lbl  = fg.get("label", "Neutral")
    fg_clr  = fear_greed_color(fg_val)
    fg_emj  = fear_greed_emoji(fg_val)

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=fg_val,
        title={"text": f"{fg_emj} {fg_lbl}", "font": {"color":"#E2E8F0","size":18}},
        gauge={
            "axis": {"range":[0,100], "tickcolor":"#94A3B8", "tickfont":{"color":"#94A3B8"}},
            "bar":  {"color": fg_clr, "thickness": 0.25},
            "bgcolor": "rgba(0,0,0,0)",
            "steps": [
                {"range":[0,20],  "color":"rgba(127,29,29,0.4)"},
                {"range":[20,40], "color":"rgba(153,27,27,0.3)"},
                {"range":[40,60], "color":"rgba(30,41,59,0.4)"},
                {"range":[60,80], "color":"rgba(20,83,45,0.3)"},
                {"range":[80,100],"color":"rgba(5,46,22,0.4)"},
            ],
            "threshold":{"line":{"color":fg_clr,"width":4},"thickness":0.75,"value":fg_val},
        },
        number={"font":{"color":"#E2E8F0","size":42}},
    ))
    fig_gauge.update_layout(
        height=300, margin=dict(t=30,b=10,l=30,r=30),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8"),
    )
    st.plotly_chart(fig_gauge, use_container_width=True)
    st.caption("Source: Alternative.me · Updates hourly · Scale: 0 = Extreme Fear → 100 = Extreme Greed")

    # F&G history bar
    history = fg.get("history", [])
    if len(history) > 1:
        hist_df = pd.DataFrame(history[::-1])
        fig_hist = go.Figure(go.Bar(
            x=[f"D-{i}" for i in range(len(hist_df)-1,-1,-1)],
            y=hist_df["value"],
            marker_color=[fear_greed_color(v) for v in hist_df["value"]],
            text=hist_df["label"],
            textposition="outside", textfont=dict(color="#94A3B8", size=10),
        ))
        fig_hist.update_layout(
            title="10-Day Fear & Greed History",
            height=240, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94A3B8"),
            yaxis=dict(range=[0,110], gridcolor="rgba(255,255,255,0.05)"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            showlegend=False, margin=dict(t=40,b=10),
        )
        st.plotly_chart(fig_hist, use_container_width=True)

with col_hv:
    st.subheader("₿ Bitcoin Halving Countdown")
    # Next halving est: April 2028 (block 1,050,000)
    # Using April 20, 2028 as estimate
    next_halving = datetime(2028, 4, 20, tzinfo=timezone.utc)
    now_utc      = datetime.now(timezone.utc)
    delta        = next_halving - now_utc
    days_left    = delta.days
    months_left  = round(days_left / 30.44)

    st.markdown(
        f'<div class="halving-card">'
        f'<div style="font-size:1rem;color:#94A3B8;margin-bottom:0.5rem">⏳ Next Bitcoin Halving</div>'
        f'<div class="halving-num">{days_left:,}</div>'
        f'<div class="halving-sub">days remaining (~{months_left} months)</div>'
        f'<div style="color:#64748B;font-size:0.75rem;margin-top:0.8rem">Estimated: April 2028 · Block 1,050,000</div>'
        f'<div style="color:#64748B;font-size:0.75rem;margin-top:0.3rem">Block reward will drop: 3.125 BTC → 1.5625 BTC</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader("📊 Halving History")
    halving_data = {
        "Event":        ["Genesis","Halving 1","Halving 2","Halving 3","Halving 4","Halving 5 (Est.)"],
        "Date":         ["Jan 2009","Nov 2012","Jul 2016","May 2020","Apr 2024","Apr 2028"],
        "Block Reward": ["50 BTC","25 BTC","12.5 BTC","6.25 BTC","3.125 BTC","1.5625 BTC"],
    }
    st.dataframe(pd.DataFrame(halving_data), use_container_width=True, hide_index=True)

st.divider()

# ── AI Analyst Verdicts ────────────────────────────────────────────────────
st.subheader("🤖 AI Analyst — Coin Verdicts")
st.caption("Rule-based commentary combining safety score, trend, volatility & Fear & Greed level")

def generate_verdict(symbol, row_data, fg_val):
    """Generate a plain-English analyst verdict for a coin."""
    safety   = row_data.get("safety_score", 0) or 0
    vol30    = row_data.get("volatility_30d", 0) or 0
    ret30    = row_data.get("return_30d", 0) or 0
    price    = row_data.get("close_usd", 0) or 0

    trend   = "📈 uptrend" if ret30 > 0 else "📉 downtrend"
    vol_lbl = "low" if vol30 < 0.03 else ("moderate" if vol30 < 0.07 else "high")
    fg_lbl  = "Extreme Fear" if fg_val < 20 else "Fear" if fg_val < 40 else "Neutral" if fg_val < 60 else "Greed" if fg_val < 80 else "Extreme Greed"

    if safety > 1.5 and ret30 > 0.1 and fg_val > 50:
        signal_txt = '<span class="signal-up">🟢 BULLISH</span>'
        summary    = f"Strong positive momentum with above-average risk-adjusted returns. Market sentiment ({fg_lbl}) supports continued upside. Consider accumulating on dips."
    elif safety < -1 or (ret30 < -0.15 and fg_val < 40):
        signal_txt = '<span class="signal-down">🔴 BEARISH</span>'
        summary    = f"Negative trend combined with {fg_lbl} market sentiment signals caution. High volatility ({vol_lbl}) increases downside risk. Consider reducing exposure."
    elif 40 <= fg_val <= 60 and abs(ret30) < 0.05:
        signal_txt = '<span class="signal-hold">🟡 NEUTRAL / HOLD</span>'
        summary    = f"Market in consolidation phase with mixed signals. {fg_lbl} sentiment and {vol_lbl} volatility suggest sideways action. Wait for a clearer directional signal."
    elif fg_val < 30 and safety > 0:
        signal_txt = '<span class="signal-up">🟢 CONTRARIAN BUY</span>'
        summary    = f"Extreme Fear often marks market bottoms. Despite pessimism, {symbol} maintains a positive safety score. Historically a favorable accumulation zone for long-term holders."
    else:
        signal_txt = '<span class="signal-hold">🟡 WATCH</span>'
        summary    = f"Mixed signals — {trend} with {vol_lbl} volatility in a {fg_lbl} environment. Monitor closely for a breakout or breakdown before committing capital."

    return signal_txt, summary, trend, vol_lbl, f"{ret30*100:+.1f}%", f"{safety:.2f}"

if has_pipeline:
    latest_date = df["date"].max()
    latest_df   = df[df["date"] == latest_date].drop_duplicates(subset=["symbol"])
    symbols     = sorted(latest_df["symbol"].dropna().unique().tolist())
    sel_coin    = st.selectbox("Select coin for AI analysis", symbols, key="ai_coin")
    row         = latest_df[latest_df["symbol"] == sel_coin]

    if not row.empty:
        r = row.iloc[0].to_dict()
        sig, summary, trend, vol_lbl, ret_str, safe_str = generate_verdict(sel_coin, r, fg_val)

        st.markdown(
            f'<div class="ai-card">'
            f'<div class="ai-header">🤖 AI Analyst · {sel_coin}</div>'
            f'<div style="margin-bottom:0.8rem">Signal: {sig}</div>'
            f'<div class="verdict">{summary}</div>'
            f'<div style="margin-top:1rem;color:#64748B;font-size:0.8rem">'
            f'30d Return: <b style="color:#E2E8F0">{ret_str}</b> &nbsp;·&nbsp; '
            f'Volatility: <b style="color:#E2E8F0">{vol_lbl}</b> &nbsp;·&nbsp; '
            f'Safety Score: <b style="color:#E2E8F0">{safe_str}</b> &nbsp;·&nbsp; '
            f'Market Sentiment: <b style="color:{fear_greed_color(fg_val)}">{fg_lbl} ({fg_val})</b>'
            f'</div></div>',
            unsafe_allow_html=True
        )
else:
    st.info("AI analysis requires pipeline data. Run `python main.py` first.")
    sel_coin = None

st.divider()

# ── 365-Day Quantile Forecast ──────────────────────────────────────────────
st.subheader("📈 365-Day Quantile Price Forecast")
st.markdown("""
**3-scenario quantile forecast** inspired by MMQR methodology:
- 🟢 **Optimistic (p90)** — bull case 90th-percentile path  
- 🔵 **Expected (p50 median)** — most-likely central path  
- 🔴 **Pessimistic (p10)** — bear case 10th-percentile path

The shaded band shows the **cone of uncertainty** (p10–p90 range).
""")
st.info("📌 p50 is most accurate within 0–30 days. The band widens beyond 60 days — read as directional scenarios, not price targets. Not financial advice.")

if has_pipeline and not forecast.empty:
    symbols      = sorted(forecast["symbol"].dropna().unique().tolist())
    fc_sel       = st.selectbox("Select coin for forecast", symbols, key="fc_coin")
    f_df         = forecast[forecast["symbol"] == fc_sel].drop_duplicates(subset=["date"]).sort_values("date")

    if not f_df.empty:
        fig_fc = go.Figure()
        if "predicted_p90" in f_df.columns and "predicted_p10" in f_df.columns:
            fig_fc.add_trace(go.Scatter(
                x=pd.concat([f_df["date"], f_df["date"][::-1]]),
                y=pd.concat([f_df["predicted_p90"], f_df["predicted_p10"][::-1]]),
                fill="toself", fillcolor="rgba(59,130,246,0.10)",
                line=dict(color="rgba(0,0,0,0)"),
                name="Uncertainty Band (p10–p90)", showlegend=True,
            ))
            fig_fc.add_trace(go.Scatter(
                x=f_df["date"], y=f_df["predicted_p90"],
                name="Optimistic (p90)", line=dict(color="#22C55E", width=1.5, dash="dot")
            ))
            fig_fc.add_trace(go.Scatter(
                x=f_df["date"], y=f_df["predicted_p10"],
                name="Pessimistic (p10)", line=dict(color="#EF4444", width=1.5, dash="dot")
            ))
        col_y = "predicted_p50" if "predicted_p50" in f_df.columns else "predicted_close"
        if col_y in f_df.columns:
            fig_fc.add_trace(go.Scatter(
                x=f_df["date"], y=f_df[col_y],
                name="Expected / Median (p50)", line=dict(color="#60A5FA", width=2.5)
            ))
        fig_fc.update_layout(
            title=f"365-Day Quantile Forecast — {fc_sel}",
            xaxis_title="Date", yaxis_title="Price (USD)",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94A3B8"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            legend=dict(orientation="h", y=-0.2),
            hovermode="x unified", height=450,
        )
        st.plotly_chart(fig_fc, use_container_width=True)
    else:
        st.info(f"No forecast data for {fc_sel}.")
else:
    st.info("Forecast data requires the PySpark pipeline. Run `python main.py` to generate forecasts.")
