from pyspark.sql import DataFrame, Window
from pyspark.sql.functions import stddev_samp, avg, col, lag, when
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.stat import Correlation
import pandas as pd
import math

def calculate_volatility(df: DataFrame) -> DataFrame:
    """
    Calculate 7-day and 30-day rolling volatility based on percentage returns.
    """
    # 1. Calculate Daily Returns
    window_prev = Window.partitionBy("symbol").orderBy("date")
    df = df.withColumn("prev_close_usd", lag("close_usd", 1).over(window_prev))
    
    # Avoid division by zero
    df = df.withColumn(
        "daily_return",
        when(col("prev_close_usd") == 0, 0)
        .otherwise((col("close_usd") - col("prev_close_usd")) / col("prev_close_usd"))
    )
    
    # If no prev close, return is 0
    df = df.fillna({"daily_return": 0.0})

    # 2. Calculate rolling standard deviation of daily returns
    window_7d = Window.partitionBy("symbol").orderBy("date").rowsBetween(-6, 0)
    window_30d = Window.partitionBy("symbol").orderBy("date").rowsBetween(-29, 0)
    
    # Annualize volatility by multiplying by sqrt(365)
    annualization_factor = math.sqrt(365)
    
    df = df.withColumn("volatility_7d", stddev_samp("daily_return").over(window_7d) * annualization_factor)
    df = df.withColumn("volatility_30d", stddev_samp("daily_return").over(window_30d) * annualization_factor)
    
    # Fill null volatilities at the start of series
    df = df.fillna({"volatility_7d": 0.0, "volatility_30d": 0.0})
    
    # 3. Calculate 30-day exact return for the Sharpe Ratio
    df = df.withColumn("close_usd_30d_ago", lag("close_usd", 30).over(window_prev))
    df = df.withColumn(
        "return_30d",
        when(col("close_usd_30d_ago") == 0, 0)
        .when(col("close_usd_30d_ago").isNull(), 0)
        .otherwise((col("close_usd") - col("close_usd_30d_ago")) / col("close_usd_30d_ago"))
    )
    df = df.fillna({"return_30d": 0.0})
    
    # 4. Calculate 30-day average volume for safety scoring
    df = df.withColumn("avg_volume_30d", avg("volume_usd").over(window_30d))
    
    return df

def build_contagion_matrix(df: DataFrame) -> pd.DataFrame:
    """
    Build a Pearson correlation matrix on daily returns to identify assets with high crash correlation.
    """
    # Ensure daily_return exists, if not fill it
    if "daily_return" not in df.columns:
        df = calculate_volatility(df)

    # ── Rolling 30-day window ──────────────────────────────────────────
    from pyspark.sql.functions import max as spark_max
    import datetime
    
    max_date_row = df.select(spark_max("date")).collect()
    if max_date_row and max_date_row[0][0]:
        max_date = max_date_row[0][0]
        if isinstance(max_date, str):
            max_date = datetime.datetime.strptime(max_date, "%Y-%m-%d").date()
        elif isinstance(max_date, datetime.datetime):
            max_date = max_date.date()
        thirty_days_ago = max_date - datetime.timedelta(days=30)
        df = df.filter(col("date") >= thirty_days_ago)
        
    # Pivot dataset so dates are rows and symbols are columns using daily_return
    pivot_df = df.groupBy("date").pivot("symbol").avg("daily_return").na.fill(0)
    
    symbols = [c for c in pivot_df.columns if c != "date"]
    
    # Assemble feature vector
    assembler = VectorAssembler(inputCols=symbols, outputCol="features")
    vector_df = assembler.transform(pivot_df).select("features")
    
    # Compute correlation
    matrix = Correlation.corr(vector_df, "features", "pearson").collect()[0][0]
    
    # Return as Pandas DataFrame for easy downstream serialization/plotting
    corr_df = pd.DataFrame(matrix.toArray(), index=symbols, columns=symbols)
    return corr_df
