from pyspark.sql import DataFrame
from pyspark.sql.functions import col, coalesce, lit

def calculate_safety_score(df: DataFrame) -> DataFrame:
    """
    Implement custom scoring algorithm: Safety = Volatility / Volume.
    Using 30-day metrics. A lower score indicates higher safety.
    """
    # Prevent division by zero
    df = df.withColumn("safe_volume", coalesce(col("avg_volume_30d"), lit(1.0)))
    
    df = df.withColumn(
        "safety_score",
        col("volatility_30d") / (col("safe_volume") + 1e-9)
    )
    
    return df
