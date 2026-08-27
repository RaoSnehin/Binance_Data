import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
import subprocess

PROCESSED_DATA_PATH = "hdfs://localhost:9000/data/crypto/processed/"

# Set Hadoop CLASSPATH so PyArrow can communicate with HDFS natively
try:
    classpath = subprocess.check_output(["hadoop", "classpath", "--glob"]).decode().strip()
    os.environ["CLASSPATH"] = classpath
except Exception:
    pass

st.set_page_config(page_title="Crypto Contagion & Safety Dashboard", layout="wide")

# ── Local cache directory ───────────────────────────────────────────────────
LOCAL_CACHE_DIR = "./data/dashboard_cache/"

def load_data():
    import shutil

    # ── Step 1: Try to refresh from HDFS (if available) ──────────────────────
    hdfs_available = False
    try:
        result = subprocess.run(
            ["hdfs", "dfs", "-ls", PROCESSED_DATA_PATH],
            capture_output=True, timeout=5
        )
        hdfs_available = result.returncode == 0
    except Exception:
        pass  # hdfs not installed or not reachable

    if hdfs_available:
        try:
            if os.path.exists(LOCAL_CACHE_DIR):
                shutil.rmtree(LOCAL_CACHE_DIR)
            os.makedirs(LOCAL_CACHE_DIR, exist_ok=True)
            for fname in ["scored_data.parquet", "contagion_matrix.csv",
                          "forecast_data.parquet", "signals_data.parquet"]:
                subprocess.run(
                    ["hdfs", "dfs", "-get", "-f",
                     os.path.join(PROCESSED_DATA_PATH, fname), LOCAL_CACHE_DIR],
                    check=False
                )
        except Exception:
            pass  # fall through to local cache

    # ── Step 2: Load from local cache (populated above or pre-existing) ───────
    try:
        os.makedirs(LOCAL_CACHE_DIR, exist_ok=True)
        df          = pd.read_parquet(os.path.join(LOCAL_CACHE_DIR, "scored_data.parquet"))
        corr_matrix = pd.read_csv(os.path.join(LOCAL_CACHE_DIR, "contagion_matrix.csv"), index_col=0)
        forecast    = pd.read_parquet(os.path.join(LOCAL_CACHE_DIR, "forecast_data.parquet"))

        signals_path = os.path.join(LOCAL_CACHE_DIR, "signals_data.parquet")
        signals = pd.read_parquet(signals_path) if os.path.exists(signals_path) else pd.DataFrame()

        # Deduplicate
        df       = df.drop_duplicates(subset=["symbol", "date"]).sort_values(["symbol", "date"])
        forecast = forecast.drop_duplicates(subset=["symbol", "date"]).sort_values(["symbol", "date"])
        if not signals.empty:
            signals = signals.drop_duplicates(subset=["symbol", "date"]).sort_values(["symbol", "date"])

        return df, corr_matrix, forecast, signals, None
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), str(e)


df, corr_matrix, forecast, signals, err_msg = load_data()

st.title("Multi-Asset Crypto Volatility Contagion & Safety")

if df.empty:
    st.warning("Processed data not found. Please run the PySpark pipeline (`python main.py`) first.")
    if err_msg:
        st.error(f"Error loading data: {err_msg}")
else:
    df["date"]       = pd.to_datetime(df["date"])
    forecast["date"] = pd.to_datetime(forecast["date"])
    if not signals.empty:
        signals["date"] = pd.to_datetime(signals["date"])

    # ── Staleness Warning ──────────────────────────────────────────
    from datetime import datetime
    data_cutoff = df["date"].max()
    days_stale  = (pd.Timestamp(datetime.now()) - data_cutoff).days
    if days_stale > 3:
        st.warning(
            f"⚠️ **Data is {days_stale} days old** (latest: {data_cutoff.date()}). "
            "Signals and forecasts may not reflect current market conditions. "
            "Re-run `python main.py` to refresh."
        )

    symbols = sorted(df["symbol"].dropna().unique().tolist())

    st.sidebar.header("Navigation Controls")

    # ── Section 1: Comparative Price & Volatility ───────────────────────────
    st.header("1. Comparative Price & Volatility Trend")
    col1, col2 = st.columns(2)
    with col1:
        coin1 = st.selectbox("Select Coin 1", symbols, index=min(0, len(symbols)-1))
    with col2:
        coin2 = st.selectbox("Select Coin 2", symbols, index=min(1, len(symbols)-1))

    df = df.drop_duplicates(subset=["symbol", "date"]).sort_values(["symbol", "date"])
    compare_df = df[df["symbol"].isin([coin1, coin2])]

    fig_price = px.line(compare_df, x="date", y="close_usd", color="symbol",
                        title="USD Price Trend")
    st.plotly_chart(fig_price, use_container_width=True)

    fig_vol = px.line(compare_df, x="date", y="volatility_30d", color="symbol",
                      title="30-Day Rolling Volatility")
    st.plotly_chart(fig_vol, use_container_width=True)

    # ── Section 2: Safety Leaderboard ──────────────────────────────────────
    st.header("2. Top 10 Safest Coins")
    st.markdown("Based on `Safety ≈ Sharpe Ratio = 30d Return / 30d Volatility`. "
                "A **higher** score implies better risk-adjusted performance.")

    latest_date = df["date"].max()
    latest_df   = df[df["date"] == latest_date]
    top_10      = latest_df.sort_values("safety_score", ascending=False).head(10)

    top_10_display = top_10[["symbol", "close_usd", "volatility_30d", "return_30d", "safety_score"]].copy()
    top_10_display.columns = ["Symbol", "Price (USD)", "30d Volatility", "30d Return", "Safety Score (Sharpe)"]
    st.dataframe(top_10_display.reset_index(drop=True), use_container_width=True)

    # ── Section 3: Contagion Matrix ─────────────────────────────────────────
    st.header("3. Contagion Matrix (Pearson Correlation)")
    st.markdown("Crash correlation among the highest-volume assets. "
                "Values near **1.0** = assets crash/pump together (contagion risk).")

    latest_unique_df = latest_df.drop_duplicates(subset=["symbol"])
    total_days = df["date"].nunique()
    coverage = df.groupby("symbol")["date"].count().reset_index()
    coverage.columns = ["symbol", "n_days"]
    coverage = coverage[coverage["n_days"] >= 0.9 * total_days]
    
    eligible = latest_unique_df[latest_unique_df["symbol"].isin(coverage["symbol"])]
    top_volume_coins = eligible.sort_values("avg_volume_30d", ascending=False).head(30)["symbol"].tolist()
    valid_coins      = [c for c in top_volume_coins if c in corr_matrix.columns]
    sub_matrix       = corr_matrix.loc[valid_coins, valid_coins]

    fig_corr = px.imshow(sub_matrix, text_auto=False, aspect="auto",
                         title="Correlation Matrix (Top Volume Coins)",
                         color_continuous_scale="Blues")
    st.plotly_chart(fig_corr, use_container_width=True)

    # ── Section 4: Buy / Sell / Hold Signals ────────────────────────────────
    st.header("4. Buy / Sell / Hold Signals (ML Classification Model)")
    st.markdown(
        "Signals generated by a **16-feature Gradient Boosting Classifier** "
        "with **balanced class weights** (SMOTE equivalent). "
        "Labels: 🟢 **UP** (top 30% return) | 🔴 **DOWN** (bottom 30%) | ⚪ **NEUTRAL** (middle 40%)\n\n"
        "⚠️ *Signals shown for test-set dates only (last 20% of each coin's history — leakage-free).*"
    )

    if signals.empty:
        st.info("Signal data not found. Run `python main.py` to generate classification signals.")
    else:
        # Latest signal per coin
        latest_sig_date = signals["date"].max()
        latest_signals  = (
            signals[signals["date"] == latest_sig_date]
            .drop_duplicates(subset=["symbol"])
            .sort_values("prob_up", ascending=False)
        )

        # Colour-coded signal column
        def signal_icon(s):
            return "🟢 UP" if s == "UP" else ("🔴 DOWN" if s == "DOWN" else "⚪ NEUTRAL")

        latest_signals["Signal"] = latest_signals["signal"].apply(signal_icon)
        latest_signals["Prob UP %"]      = (latest_signals["prob_up"]      * 100).round(1)
        latest_signals["Prob DOWN %"]    = (latest_signals["prob_down"]    * 100).round(1)
        latest_signals["Prob NEUTRAL %"] = (latest_signals["prob_neutral"] * 100).round(1)

        # Summary counts
        c1, c2, c3 = st.columns(3)
        n_up      = (latest_signals["signal"] == "UP").sum()
        n_down    = (latest_signals["signal"] == "DOWN").sum()
        n_neutral = (latest_signals["signal"] == "NEUTRAL").sum()
        c1.metric("🟢 BUY Signals",  n_up)
        c2.metric("🔴 SELL Signals", n_down)
        c3.metric("⚪ HOLD Signals", n_neutral)

        sig_display = latest_signals[[
            "symbol", "Signal", "Prob UP %", "Prob DOWN %", "Prob NEUTRAL %"
        ]].rename(columns={"symbol": "Coin"}).reset_index(drop=True)
        st.dataframe(sig_display, use_container_width=True)

        # Signal chart for selected coin over time
        st.subheader("Signal History for Selected Coin")
        sig_coins     = sorted(signals["symbol"].unique().tolist())
        selected_coin = st.selectbox("Select Coin for Signal History", sig_coins, key="sig_coin")
        coin_sig      = signals[signals["symbol"] == selected_coin].sort_values("date")

        fig_sig = go.Figure()
        fig_sig.add_trace(go.Scatter(
            x=coin_sig["date"], y=coin_sig["prob_up"],
            name="Prob UP", fill="tozeroy", line=dict(color="green", width=1.5)
        ))
        fig_sig.add_trace(go.Scatter(
            x=coin_sig["date"], y=coin_sig["prob_down"],
            name="Prob DOWN", fill="tozeroy", line=dict(color="red", width=1.5)
        ))
        fig_sig.update_layout(
            title=f"Buy/Sell Probability over Time — {selected_coin}",
            xaxis_title="Date", yaxis_title="Probability",
            yaxis=dict(range=[0, 1])
        )
        st.plotly_chart(fig_sig, use_container_width=True)

    # ── Section 5: 365-Day Trend Projection (Quantile Cone of Uncertainty) ─
    st.header("5. 365-Day Trend Projection")
    st.markdown(
        "**3-scenario quantile forecast** inspired by *Havidz et al. (p4) MMQR* — "
        "each scenario is a separate quantile regression model trained on daily returns:\n\n"
        "- 🟢 **Optimistic (p90)**: 90th-percentile path — bull case\n"
        "- 🔵 **Expected (p50 median)**: most-likely central path\n"
        "- 🔴 **Pessimistic (p10)**: 10th-percentile path — bear case\n\n"
        "The shaded band shows the **cone of uncertainty** (p10–p90 range)."
    )
    st.info(
        "📌 **Reliability guide:** p50 (expected) is most accurate within 0–30 days. "
        "The p10/p90 band widens beyond 60 days and should be read as *directional scenarios*, "
        "not price targets. Do not use as financial advice."
    )
    forecast_coin = st.selectbox("Select Coin for Projection", symbols, key="forecast_coin")
    f_df = forecast[forecast["symbol"] == forecast_coin].drop_duplicates(subset=["date"]).sort_values("date")

    if f_df.empty:
        st.info("No forecast data available. Run `python main.py` to generate forecasts.")
    else:
        fig_forecast = go.Figure()

        # Shaded cone between p10 and p90
        if "predicted_p90" in f_df.columns and "predicted_p10" in f_df.columns:
            fig_forecast.add_trace(go.Scatter(
                x=pd.concat([f_df["date"], f_df["date"][::-1]]),
                y=pd.concat([f_df["predicted_p90"], f_df["predicted_p10"][::-1]]),
                fill="toself", fillcolor="rgba(59,130,246,0.12)",
                line=dict(color="rgba(0,0,0,0)"),
                name="Uncertainty Band (p10–p90)", showlegend=True
            ))
            fig_forecast.add_trace(go.Scatter(
                x=f_df["date"], y=f_df["predicted_p90"],
                name="Optimistic (p90)", line=dict(color="green", width=1.5, dash="dot")
            ))
            fig_forecast.add_trace(go.Scatter(
                x=f_df["date"], y=f_df["predicted_p10"],
                name="Pessimistic (p10)", line=dict(color="red", width=1.5, dash="dot")
            ))

        col_y = "predicted_p50" if "predicted_p50" in f_df.columns else "predicted_close"
        fig_forecast.add_trace(go.Scatter(
            x=f_df["date"], y=f_df[col_y],
            name="Expected / Median (p50)", line=dict(color="royalblue", width=2.5)
        ))

        fig_forecast.update_layout(
            title=f"365-Day Quantile Forecast — {forecast_coin}",
            xaxis_title="Date", yaxis_title="Price (USD)",
            legend=dict(orientation="h", y=-0.2),
            hovermode="x unified"
        )
        st.plotly_chart(fig_forecast, use_container_width=True)

