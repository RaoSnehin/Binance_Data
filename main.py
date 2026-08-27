import os
from src.config import BASE_PATH, PROCESSED_DATA_PATH
from src.spark_session import get_spark_session
from src.ingestion import ingest_data, deduplicate_data
from src.normalization import normalize_to_usd
from src.analytics import calculate_volatility, build_contagion_matrix
from src.forecasting import forecast_trend
from src.scoring import calculate_safety_score
from src.classification import generate_signals

def main():
    print("Starting Multi-Asset Crypto Volatility & Safety Pipeline...")

    # 1. Spark Session Setup
    spark = get_spark_session()
    spark.sparkContext.setLogLevel("ERROR")

    # 2. Data Engineering: Ingestion & Deduplication
    print(f"Ingesting raw data from {BASE_PATH}...")
    raw_df   = ingest_data(spark, BASE_PATH)
    dedup_df = deduplicate_data(raw_df)

    # 3. Normalization
    print("Normalizing assets to USD...")
    usd_df = normalize_to_usd(dedup_df)

    # 4. Analytics: Volatility & Safety Scoring
    print("Calculating rolling volatility and safety scores...")
    analyzed_df = calculate_volatility(usd_df)
    scored_df   = calculate_safety_score(analyzed_df)

    os.makedirs(PROCESSED_DATA_PATH, exist_ok=True)

    # Persist the primary dataset as Parquet
    print("Saving processed multi-asset dataset...")
    scored_df.write.mode("overwrite").parquet(
        os.path.join(PROCESSED_DATA_PATH, "scored_data.parquet"))

    # 5. Contagion Matrix
    print("Building Contagion Matrix (Pearson Correlation)...")
    corr_matrix = build_contagion_matrix(scored_df)

    local_csv_path = "./contagion_matrix.csv"
    corr_matrix.to_csv(local_csv_path)

    print("Uploading contagion matrix to HDFS...")
    import subprocess
    subprocess.run(["hdfs", "dfs", "-rm", "-f",
                    os.path.join(PROCESSED_DATA_PATH, "contagion_matrix.csv")], check=False)
    subprocess.run(["hdfs", "dfs", "-put", local_csv_path, PROCESSED_DATA_PATH], check=True)

    # 6. ML Classification: BUY / SELL / HOLD Signals (16 features + class weights)
    print("Generating Buy/Sell/Hold signals via classification model...")

    # Extract BTC daily return as a cross-asset feature for all other coins
    from pyspark.sql.functions import col as F_col
    btc_return_df = scored_df \
        .filter(F_col("symbol") == "BTCUSDT") \
        .select(
            F_col("date"),
            F_col("daily_return").alias("btc_return")
        )

    signals_df = generate_signals(scored_df, btc_return_df=btc_return_df)
    signals_df.write.mode("overwrite").parquet(
        os.path.join(PROCESSED_DATA_PATH, "signals_data.parquet"))
    print(f"  Signals generated for {signals_df.select('symbol').distinct().count()} coins.")

    # 7. Forecasting (price trend projection for dashboard chart)
    print("Generating 365-day trend forecast...")
    forecast_df = forecast_trend(scored_df)
    forecast_df.write.mode("overwrite").parquet(
        os.path.join(PROCESSED_DATA_PATH, "forecast_data.parquet"))

    print("Pipeline execution completed successfully!")

if __name__ == "__main__":
    main()
