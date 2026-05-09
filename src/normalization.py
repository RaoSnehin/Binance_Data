from pyspark.sql import DataFrame
from pyspark.sql.functions import col

def normalize_to_usd(df: DataFrame) -> DataFrame:
    """
    Convert all assets (BTC, ETH, Altcoins) to USD using a self-join logic.
    Assumes USDT pairs approximate USD value.
    """
    # Identify USD/Stablecoin pairs vs non-USD pairs
    usd_pairs = df.filter(col("symbol").endswith("USDT"))
    non_usd_pairs = df.filter(~col("symbol").endswith("USDT"))
    
    # Extract BTCUSDT to use as a bridge for BTC-denominated pairs
    btc_usd = usd_pairs.filter(col("symbol") == "BTCUSDT").select(
        col("date"),
        col("close").alias("btc_usd_price")
    )
    
    # Self-join to convert non-USD pairs
    # E.g., ETHBTC close * BTCUSDT close = ETH in USD
    converted_non_usd = non_usd_pairs.join(btc_usd, on="date", how="inner") \
        .withColumn("close_usd", col("close") * col("btc_usd_price")) \
        .withColumn("volume_usd", col("volume") * col("btc_usd_price"))
    
    # Standardize the USD pairs natively
    standard_usd = usd_pairs.withColumn("close_usd", col("close").cast("double")) \
        .withColumn("volume_usd", col("volume").cast("double"))
    
    # Combine back
    cols_to_keep = ["date", "symbol", "close", "volume", "close_usd", "volume_usd"]
    
    final_df = standard_usd.select(*cols_to_keep).union(
        converted_non_usd.select(*cols_to_keep)
    )
    
    return final_df
