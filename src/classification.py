from pyspark.sql import DataFrame
import pandas as pd
import numpy as np

# ── Paper References ──────────────────────────────────────────────────────────
# p3 (Dahiphale et al., CDFMR): CDF-based percentile thresholds replace fixed
#   ±1% cut-offs. Each coin's UP/DOWN threshold is its own 70th/30th return
#   percentile — so a volatile coin needs a bigger move to be labelled UP.
# p1 (Sharma et al.): HistGradientBoostingClassifier replaces GBM — faster,
#   native missing-value support, closer to XGBoost performance.
# ──────────────────────────────────────────────────────────────────────────────


def generate_signals(df: DataFrame, btc_return_df: DataFrame = None) -> DataFrame:
    """
    Per-coin BUY / SELL / HOLD signal generator using Gradient Boosting Classifier.

    Key improvements over the regressor:
    - Problem is now CLASSIFICATION (UP/DOWN/NEUTRAL labels) — SMOTE-equivalent
      class weighting is applicable and applied via compute_sample_weight('balanced').
    - 16 features: 13 price-based + volume_ratio_7d + Bollinger Band position + BTC return lag.
    - Label rule: return > +1% = UP | return < -1% = DOWN | else = NEUTRAL
    - Outputs: signal (UP/DOWN/NEUTRAL), prob_up, prob_down, prob_neutral per day.
    """
    df = df.na.drop(subset=["close_usd", "date"])

    # Join BTC return as a cross-asset feature if provided
    if btc_return_df is not None:
        df = df.join(btc_return_df, on="date", how="left").fillna({"btc_return": 0.0})
    else:
        from pyspark.sql.functions import lit
        df = df.withColumn("btc_return", lit(0.0))

    def classify_symbol(pdf: pd.DataFrame) -> pd.DataFrame:
        from sklearn.ensemble import GradientBoostingClassifier
        from sklearn.utils.class_weight import compute_sample_weight
        import warnings
        warnings.filterwarnings("ignore")

        pdf = pdf.sort_values("date").reset_index(drop=True)
        prices  = pdf["close_usd"].values.astype(float)

        # ── Quality Filters ───────────────────────────────────────────────
        if len(pdf) < 180:
            return pd.DataFrame(columns=[
                "symbol", "date", "signal", "prob_up", "prob_down", "prob_neutral"])

        # Exclude stablecoins (price barely moves — nothing to classify)
        cv = np.std(prices) / (np.mean(np.abs(prices)) + 1e-9)
        if cv < 0.10:
            return pd.DataFrame(columns=[
                "symbol", "date", "signal", "prob_up", "prob_down", "prob_neutral"])

        symbol      = pdf["symbol"].iloc[0]
        volumes     = pdf["volume_usd"].values.astype(float) if "volume_usd" in pdf.columns else np.ones(len(pdf))
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

        # ── CDF-based per-coin thresholds (p3 inspiration) ───────────────
        p30_threshold = float(np.percentile(returns[returns != 0], 30))
        p70_threshold = float(np.percentile(returns[returns != 0], 70))

        X_rows, labels, dates = [], [], []

        for i in range(WIN, len(returns) - 1):
            r = returns

            # ── Original 13 price features ────────────────────────────────
            lag1  = r[i];  lag2 = r[i-1]; lag3 = r[i-2]
            lag5  = r[i-4]; lag7 = r[i-6]; lag14 = r[i-13]
            mean7  = np.mean(r[i-6:i+1])
            mean14 = np.mean(r[i-13:i+1])
            vol7   = np.std(r[i-6:i+1])  + 1e-9
            vol14  = np.std(r[i-13:i+1]) + 1e-9
            macd_v = macd[i]
            deltas = r[max(0, i-13):i+1]
            gains  = deltas[deltas > 0]; losses = -deltas[deltas < 0]
            ag = gains.mean()  if len(gains)  > 0 else 0.0
            al = losses.mean() if len(losses) > 0 else 1e-9
            rsi = 100 - (100 / (1 + ag / al))
            price_mom = (prices[i] - prices[i-WIN]) / (prices[i-WIN] + 1e-9)

            # ── NEW Feature 14: Volume Ratio (surge detection) ────────────
            avg_vol7   = np.mean(volumes[max(0, i-6):i+1]) + 1e-9
            vol_ratio  = float(volumes[i]) / avg_vol7

            # ── NEW Feature 15: Bollinger Band Position ───────────────────
            sma20  = np.mean(prices[max(0, i-19):i+1])
            std20  = np.std(prices[max(0, i-19):i+1])  + 1e-9
            bb_pos = (prices[i] - sma20) / (2.0 * std20)   # +1 = upper band, -1 = lower

            # ── NEW Feature 16: BTC Return Lag-1 (cross-asset beta) ───────
            btc_lag1 = float(btc_returns[i - 1]) if i > 0 else 0.0

            X_rows.append([
                lag1, lag2, lag3, lag5, lag7, lag14,
                mean7, mean14, vol7, vol14, macd_v, rsi, price_mom,
                vol_ratio, bb_pos, btc_lag1
            ])

            # ── Label: CDF-inspired coin-specific percentile thresholds ────
            # Inspired by p3 (Dahiphale et al., CDFMR): instead of a fixed
            # ±1% threshold, use the 70th / 30th percentile of THIS coin's
            # own return distribution.  A volatile coin (e.g. PEPE) needs a
            # larger move to be labelled UP than a stable one (e.g. NEOUSDT).
            next_return = r[i + 1]
            if next_return > p70_threshold:
                labels.append("UP")
            elif next_return < p30_threshold:
                labels.append("DOWN")
            else:
                labels.append("NEUTRAL")

            dates.append(pdf["date"].iloc[i + 1])

        X = np.array(X_rows)
        y = np.array(labels)
        d = np.array(dates)

        if len(X) < 30 or len(np.unique(y)) < 2:
            return pd.DataFrame(columns=[
                "symbol", "date", "signal", "prob_up", "prob_down", "prob_neutral"])

        split   = int(len(X) * 0.8)
        X_train = X[:split];  y_train = y[:split]
        X_test  = X[split:]
        d_test  = d[split:]

        # ── HistGradientBoostingClassifier (p1 — Sharma et al. recommendation) ─
        import os
        import joblib
        from sklearn.ensemble import HistGradientBoostingClassifier
        
        max_date_str = pd.to_datetime(pdf["date"]).max().strftime('%Y%m%d')
        cache_dir = "models_cache/classification"
        os.makedirs(cache_dir, exist_ok=True)
        model_path = f"{cache_dir}/{symbol}_{max_date_str}.joblib"
        
        if os.path.exists(model_path):
            model = joblib.load(model_path)
        else:
            model = HistGradientBoostingClassifier(
                max_iter=200, learning_rate=0.05, max_depth=4,
                min_samples_leaf=10, class_weight="balanced", random_state=42
            )
            model.fit(X_train, y_train)
            joblib.dump(model, model_path)

        # Predict signals + probabilities ONLY on test set (unseen data) for dashboard
        signals  = model.predict(X_test)
        proba    = model.predict_proba(X_test)
        classes  = list(model.classes_)

        def col_or_zero(name):
            return proba[:, classes.index(name)] if name in classes else np.zeros(len(X_test))

        return pd.DataFrame({
            "symbol":       [symbol] * len(X_test),
            "date":         d_test,
            "signal":       signals,
            "prob_up":      col_or_zero("UP"),
            "prob_down":    col_or_zero("DOWN"),
            "prob_neutral": col_or_zero("NEUTRAL"),
        })

    signals_df = df.groupby("symbol").applyInPandas(
        classify_symbol,
        schema=(
            "symbol string, date date, signal string, "
            "prob_up double, prob_down double, prob_neutral double"
        )
    )

    # Dedup: keep one signal per (symbol, date)
    from pyspark.sql.functions import row_number
    from pyspark.sql import Window
    w = Window.partitionBy("symbol", "date").orderBy("prob_up")
    signals_df = signals_df \
        .withColumn("_rn", row_number().over(w)) \
        .filter("_rn = 1") \
        .drop("_rn")

    return signals_df
