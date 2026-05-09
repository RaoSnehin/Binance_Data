import streamlit as st
import pandas as pd
import os
import plotly.express as px

import subprocess

PROCESSED_DATA_PATH = "hdfs://localhost:9000/data/crypto/processed/"

# Set Hadoop CLASSPATH so PyArrow can communicate with HDFS natively
try:
    classpath = subprocess.check_output(["hadoop", "classpath", "--glob"]).decode().strip()
    os.environ["CLASSPATH"] = classpath
except Exception:
    pass

st.set_page_config(page_title="Crypto Contagion & Safety Dashboard", layout="wide")

# Set up a local cache directory
LOCAL_CACHE_DIR = "./data/dashboard_cache/"
os.makedirs(LOCAL_CACHE_DIR, exist_ok=True)

# Removed cache temporarily to force reload
def load_data():
    try:
        # Download from HDFS to local cache to bypass PyArrow libjvm issues on macOS
        import subprocess
        subprocess.run(["hdfs", "dfs", "-get", "-f", os.path.join(PROCESSED_DATA_PATH, "scored_data.parquet"), LOCAL_CACHE_DIR], check=False)
        subprocess.run(["hdfs", "dfs", "-get", "-f", os.path.join(PROCESSED_DATA_PATH, "contagion_matrix.csv"), LOCAL_CACHE_DIR], check=False)
        subprocess.run(["hdfs", "dfs", "-get", "-f", os.path.join(PROCESSED_DATA_PATH, "forecast_data.parquet"), LOCAL_CACHE_DIR], check=False)
        
        df = pd.read_parquet(os.path.join(LOCAL_CACHE_DIR, "scored_data.parquet"))
        corr_matrix = pd.read_csv(os.path.join(LOCAL_CACHE_DIR, "contagion_matrix.csv"), index_col=0)
        forecast = pd.read_parquet(os.path.join(LOCAL_CACHE_DIR, "forecast_data.parquet"))
        
        return df, corr_matrix, forecast, None
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), str(e)

df, corr_matrix, forecast, err_msg = load_data()

st.title("Multi-Asset Crypto Volatility Contagion & Safety")

if df.empty:
    st.warning("Processed data not found. Please run the PySpark pipeline (`python main.py`) first.")
    if err_msg:
        st.error(f"Error loading data: {err_msg}")
else:
    df['date'] = pd.to_datetime(df['date'])
    forecast['date'] = pd.to_datetime(forecast['date'])
    
    symbols = sorted(df["symbol"].dropna().unique().tolist())
    
    st.sidebar.header("Navigation Controls")
    
    # 1. Comparative Trend
    st.header("1. Comparative Price & Volatility Trend")
    col1, col2 = st.columns(2)
    with col1:
        coin1 = st.selectbox("Select Coin 1", symbols, index=min(0, len(symbols)-1))
    with col2:
        coin2 = st.selectbox("Select Coin 2", symbols, index=min(1, len(symbols)-1))
        
    compare_df = df[df["symbol"].isin([coin1, coin2])]
    
    fig_price = px.line(compare_df, x="date", y="close_usd", color="symbol", title="USD Price Trend")
    st.plotly_chart(fig_price, use_container_width=True)
    
    fig_vol = px.line(compare_df, x="date", y="volatility_30d", color="symbol", title="30-Day Rolling Volatility")
    st.plotly_chart(fig_vol, use_container_width=True)
    
    # 2. Safety Leaderboard
    st.header("2. Top 10 Safest Coins")
    st.markdown("Based on `Safety = Volatility / Volume`. A lower score implies higher safety.")
    
    latest_date = df['date'].max()
    latest_df = df[df['date'] == latest_date]
    top_10 = latest_df.sort_values("safety_score", ascending=True).head(10)
    
    st.dataframe(top_10[["symbol", "close_usd", "volatility_30d", "avg_volume_30d", "safety_score"]].reset_index(drop=True))
    
    # 3. Contagion Matrix
    st.header("3. Contagion Matrix (Pearson Correlation)")
    st.markdown("Crash correlation among the highest volume assets.")
    
    # Filter matrix to top 30 to keep UI responsive
    top_volume_coins = latest_df.sort_values("avg_volume_30d", ascending=False).head(30)["symbol"].tolist()
    valid_coins = [c for c in top_volume_coins if c in corr_matrix.columns]
    sub_matrix = corr_matrix.loc[valid_coins, valid_coins]
    
    fig_corr = px.imshow(sub_matrix, text_auto=False, aspect="auto", title="Correlation Matrix (Top Volume Coins)")
    st.plotly_chart(fig_corr, use_container_width=True)
    
    # 4. Forecasting
    st.header("4. 365-Day Trend Projection")
    forecast_coin = st.selectbox("Select Coin for Projection", symbols, key="forecast_coin")
    f_df = forecast[forecast["symbol"] == forecast_coin]
    
    fig_forecast = px.line(f_df, x="date", y="predicted_close", title=f"365-Day Trend Projection for {forecast_coin}")
    st.plotly_chart(fig_forecast, use_container_width=True)
