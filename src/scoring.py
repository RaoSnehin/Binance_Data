from pyspark.sql import DataFrame
from pyspark.sql.functions import col, when

def calculate_safety_score(df: DataFrame) -> DataFrame:
    """
    Implement custom scoring algorithm: Safety = 30-Day Return / 30-Day Volatility.
    This acts as a proxy for the Sharpe Ratio. A higher score indicates higher safety/performance.
    """
    # Prevent division by zero if volatility is exactly 0
    df = df.withColumn(
        "safe_volatility", 
        when(col("volatility_30d") <= 0, 1e-9).otherwise(col("volatility_30d"))
    )
    
    df = df.withColumn(
        "safety_score",
        col("return_30d") / col("safe_volatility")
    )
    
    return df
