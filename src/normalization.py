from pyspark.sql import DataFrame
from pyspark.sql.functions import col

def normalize_to_usd(df: DataFrame) -> DataFrame:
    """
    Convert all assets (BTC, ETH, Altcoins) to USD using a self-join logic.
    Assumes USDT pairs approximate USD value.
    Priority: USDT pairs are always preferred; BTC-converted pairs fill the gaps.
    """
    # Identify USD/Stablecoin pairs vs non-USD pairs
    usd_pairs = df.filter(col("symbol").endswith("USDT"))
    non_usd_pairs = df.filter(~col("symbol").endswith("USDT"))

    # Extract BTCUSDT to use as a bridge for BTC-denominated pairs
    btc_usd = usd_pairs.filter(col("symbol") == "BTCUSDT").select(
        col("date"),
        col("close").alias("btc_usd_price")
    )

    # Standardize the USD pairs natively (PREFERRED over BTC-converted)
    standard_usd = usd_pairs \
        .withColumn("close_usd", col("close").cast("double")) \
        .withColumn("volume_usd", col("volume").cast("double"))

    # Only convert non-USD symbols that do NOT already have a USDT pair.
    # This prevents symbols like ETH appearing twice (ETHUSDT + ETHBTC both converting to USD).
    usdt_symbols = usd_pairs.select("symbol").distinct()
    non_usd_only = non_usd_pairs.join(usdt_symbols, on="symbol", how="left_anti")

    converted_non_usd = non_usd_only.join(btc_usd, on="date", how="inner") \
        .withColumn("close_usd", col("close") * col("btc_usd_price")) \
        .withColumn("volume_usd", col("volume") * col("btc_usd_price"))

    # Combine back, keeping only required columns
    cols_to_keep = ["date", "symbol", "close", "volume", "close_usd", "volume_usd"]

    final_df = standard_usd.select(*cols_to_keep).union(
        converted_non_usd.select(*cols_to_keep)
    )

    # Final safety dedup: one row per (symbol, date) pair
    final_df = final_df.dropDuplicates(["symbol", "date"])

    return final_df
