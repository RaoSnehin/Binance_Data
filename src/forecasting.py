from pyspark.sql import DataFrame
import pandas as pd
import numpy as np

# ── Paper References ──────────────────────────────────────────────────────────
# p4 (Havidz et al., MMQR): Quantile regression predicts multiple percentiles
#   of the return distribution rather than just the mean. We implement this as
#   3 parallel GBM Quantile Regressors (p10/p50/p90) producing a "cone of
#   uncertainty" chart — pessimistic / expected / optimistic scenarios.
#   This is how central banks (RBI, Fed) present inflation forecasts.
# p1 (Sharma et al.): HistGradientBoosting is used for the median (p50) model.
# ──────────────────────────────────────────────────────────────────────────────


def forecast_trend(df: DataFrame) -> DataFrame:
    """
    Distributed Quantile Regression Forecasting — 3 scenarios per coin.

    Inspired by p4 (Havidz et al. MMQR): instead of a single point forecast,
    we train THREE quantile regressors on daily returns:
      - p10 (pessimistic):  10th percentile — the bear-case projection
      - p50 (expected):     50th percentile — the median / most-likely path
      - p90 (optimistic):   90th percentile — the bull-case projection

    The dashboard displays all three as a 'cone of uncertainty' —
    a shaded band between pessimistic and optimistic with expected in the middle.

    Features: 13 technical indicators (same as before).
    Returns: (symbol, date, predicted_p10, predicted_p50, predicted_p90)
    """
    df = df.na.drop(subset=["close_usd", "date"])
    # ensure columns exist
    from pyspark.sql.functions import lit
    if "volume_usd" not in df.columns:
        df = df.withColumn("volume_usd", lit(1.0))
    if "btc_return" not in df.columns:
        df = df.withColumn("btc_return", lit(0.0))

    def forecast_symbol(pdf: pd.DataFrame) -> pd.DataFrame:
        from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor
        import warnings
        warnings.filterwarnings("ignore")

        pdf = pdf.sort_values("date").reset_index(drop=True)
        if len(pdf) < 180:
            return pd.DataFrame(columns=[
                "symbol", "date", "predicted_p10", "predicted_p50",
                "predicted_p90", "predicted_close"])

        symbol = pdf["symbol"].iloc[0]
        prices = pdf["close_usd"].values.astype(float)
        volumes = pdf["volume_usd"].values.astype(float) if "volume_usd" in pdf.columns else np.ones(len(pdf))
        btc_returns = pdf["btc_return"].values.astype(float) if "btc_return" in pdf.columns else np.zeros(len(pdf))

        # ── Daily Returns ─────────────────────────────────────────────────
        returns = np.zeros(len(prices))
        returns[1:] = (prices[1:] - prices[:-1]) / (np.abs(prices[:-1]) + 1e-9)
        returns = np.clip(returns, -0.5, 5.0)

        def ema(arr, span):
            alpha = 2.0 / (span + 1)
            result = np.zeros(len(arr))
            result[0] = arr[0]
            for k in range(1, len(arr)):
                result[k] = alpha * arr[k] + (1 - alpha) * result[k - 1]
            return result

        ema12 = ema(returns, 12)
        ema26 = ema(returns, 26)
        macd  = ema12 - ema26

        WIN = 30
        feature_rows, targets = [], []

        for i in range(WIN, len(returns) - 1):
            r = returns
            lag1  = r[i];  lag2 = r[i-1]; lag3 = r[i-2]
            lag5  = r[i-4]; lag7 = r[i-6]; lag14 = r[i-13]
            mean7  = np.mean(r[i-6:i+1])
            mean14 = np.mean(r[i-13:i+1])
            vol7   = np.std(r[i-6:i+1])  + 1e-9
            vol14  = np.std(r[i-13:i+1]) + 1e-9
            macd_v = macd[i]
            deltas = r[max(0, i-13): i+1]
            gains  = deltas[deltas > 0]; losses = -deltas[deltas < 0]
            ag = gains.mean()  if len(gains)  > 0 else 0.0
            al = losses.mean() if len(losses) > 0 else 1e-9
            rsi = 100 - (100 / (1 + ag / al))
            price_mom = (prices[i] - prices[i - WIN]) / (prices[i - WIN] + 1e-9)
            avg_vol7  = np.mean(volumes[max(0, i-6):i+1]) + 1e-9
            vol_ratio = float(volumes[i]) / avg_vol7
            sma20  = np.mean(prices[max(0, i-19):i+1])
            std20  = np.std(prices[max(0, i-19):i+1])  + 1e-9
            bb_pos = (prices[i] - sma20) / (2.0 * std20)
            btc_lag1 = float(btc_returns[i-1]) if i > 0 else 0.0
            
            feature_rows.append([
                lag1, lag2, lag3, lag5, lag7, lag14,
                mean7, mean14, vol7, vol14, macd_v, rsi, price_mom,
                vol_ratio, bb_pos, btc_lag1
            ])
            targets.append(r[i + 1])

        X = np.array(feature_rows)
        y = np.array(targets)

        if len(X) < 30:
            return pd.DataFrame(columns=[
                "symbol", "date", "predicted_p10", "predicted_p50",
                "predicted_p90", "predicted_close"])

        split   = int(len(X) * 0.8)
        X_train = X[:split];  y_train = y[:split]

        # ── THREE Quantile Regressors (p4 — Havidz et al. MMQR approach) ──
        import os
        import joblib
        
        max_date_str = pd.to_datetime(pdf["date"]).max().strftime('%Y%m%d')
        cache_dir = "models_cache/forecasting"
        os.makedirs(cache_dir, exist_ok=True)
        p10_path = f"{cache_dir}/{symbol}_p10_{max_date_str}.joblib"
        p50_path = f"{cache_dir}/{symbol}_p50_{max_date_str}.joblib"
        p90_path = f"{cache_dir}/{symbol}_p90_{max_date_str}.joblib"
        
        if os.path.exists(p10_path) and os.path.exists(p50_path) and os.path.exists(p90_path):
            model_p10 = joblib.load(p10_path)
            model_p50 = joblib.load(p50_path)
            model_p90 = joblib.load(p90_path)
        else:
            model_p10 = GradientBoostingRegressor(
                loss="quantile", alpha=0.10,
                n_estimators=150, learning_rate=0.05, max_depth=3,
                subsample=0.8, random_state=42
            )
            model_p50 = GradientBoostingRegressor(
                loss="quantile", alpha=0.50,
                n_estimators=150, learning_rate=0.05, max_depth=3,
                subsample=0.8, random_state=42
            )
            model_p90 = GradientBoostingRegressor(
                loss="quantile", alpha=0.90,
                n_estimators=150, learning_rate=0.05, max_depth=3,
                subsample=0.8, random_state=42
            )

            model_p10.fit(X_train, y_train)
            model_p50.fit(X_train, y_train)
            model_p90.fit(X_train, y_train)
            
            joblib.dump(model_p10, p10_path)
            joblib.dump(model_p50, p50_path)
            joblib.dump(model_p90, p90_path)

        # ── Recursive 365-Day Return Forecast — 3 parallel paths ──────────
        price_hist  = list(prices[-WIN:])
        return_hist = list(returns[-WIN:])
        ema12_last  = float(ema12[-1])
        ema26_last  = float(ema26[-1])
        alpha12     = 2.0 / (12 + 1)
        alpha26     = 2.0 / (26 + 1)

        # 3 price chains: pessimistic / expected / optimistic
        chain_p10 = [prices[-1]]
        chain_p50 = [prices[-1]]
        chain_p90 = [prices[-1]]

        last_vol_ratio = float(volumes[-1]) / (np.mean(volumes[-7:]) + 1e-9)
        last_bb_pos    = (prices[-1] - np.mean(prices[-20:])) / (2 * np.std(prices[-20:]) + 1e-9)
        last_btc_lag1  = float(btc_returns[-1])

        for _ in range(365):
            rh = np.array(return_hist[-WIN:])
            ph = np.array(price_hist[-WIN:])

            lag1  = rh[-1]; lag2 = rh[-2]; lag3 = rh[-3]
            lag5  = rh[-5]; lag7 = rh[-7]
            lag14 = rh[-14] if len(rh) >= 14 else rh[0]
            mean7  = np.mean(rh[-7:])
            mean14 = np.mean(rh[-14:])
            vol7   = np.std(rh[-7:])  + 1e-9
            vol14  = np.std(rh[-14:]) + 1e-9
            macd_v = ema12_last - ema26_last
            deltas = rh[-14:]
            gains  = deltas[deltas > 0]; losses = -deltas[deltas < 0]
            ag = gains.mean()  if len(gains)  > 0 else 0.0
            al = losses.mean() if len(losses) > 0 else 1e-9
            rsi = 100 - (100 / (1 + ag / al))
            price_mom = (ph[-1] - ph[-WIN]) / (ph[-WIN] + 1e-9)

            feat = np.array([[lag1, lag2, lag3, lag5, lag7, lag14,
                              mean7, mean14, vol7, vol14, macd_v, rsi, price_mom,
                              last_vol_ratio, last_bb_pos, last_btc_lag1]])

            step_number = len(chain_p50) - 1
            decay       = np.exp(-step_number / 180)
            
            r50 = float(np.clip(model_p50.predict(feat)[0], -0.20, 0.20))
            raw_r10 = float(np.clip(model_p10.predict(feat)[0], -0.20, 0.20))
            raw_r90 = float(np.clip(model_p90.predict(feat)[0], -0.20, 0.20))

            r10 = r50 + (raw_r10 - r50) * decay
            r90 = r50 + (raw_r90 - r50) * decay

            r10 = min(r10, r50)
            r90 = max(r90, r50)

            chain_p10.append(max(chain_p10[-1] * (1 + r10), 1e-9))
            chain_p50.append(max(chain_p50[-1] * (1 + r50), 1e-9))
            chain_p90.append(max(chain_p90[-1] * (1 + r90), 1e-9))

            # Advance the shared state using the median return
            price_hist.append(chain_p50[-1]);  price_hist = price_hist[-WIN:]
            return_hist.append(r50);           return_hist = return_hist[-WIN:]
            ema12_last = alpha12 * r50 + (1 - alpha12) * ema12_last
            ema26_last = alpha26 * r50 + (1 - alpha26) * ema26_last

        last_date    = pd.to_datetime(pdf["date"].iloc[-1])
        future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=365)

        return pd.DataFrame({
            "symbol":          [symbol] * 365,
            "date":            future_dates.date,
            "predicted_p10":   chain_p10[1:],   # pessimistic
            "predicted_p50":   chain_p50[1:],   # expected (median)
            "predicted_p90":   chain_p90[1:],   # optimistic
            "predicted_close": chain_p50[1:],   # kept for backward compat
        })

    forecast_df = df.groupby("symbol").applyInPandas(
        forecast_symbol,
        schema=(
            "symbol string, date date, "
            "predicted_p10 double, predicted_p50 double, "
            "predicted_p90 double, predicted_close double"
        )
    )

    # Safety dedup
    from pyspark.sql import Window
    from pyspark.sql.functions import row_number
    w = Window.partitionBy("symbol", "date").orderBy("predicted_p50")
    forecast_df = forecast_df \
        .withColumn("_rn", row_number().over(w)) \
        .filter("_rn = 1") \
        .drop("_rn")

    return forecast_df
