from pyspark.sql import DataFrame, Window
from pyspark.sql.functions import stddev_samp, avg
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.stat import Correlation
import pandas as pd

def calculate_volatility(df: DataFrame) -> DataFrame:
    """
    Calculate 7-day and 30-day rolling volatility.
    """
    window_7d = Window.partitionBy("symbol").orderBy("date").rowsBetween(-6, 0)
    window_30d = Window.partitionBy("symbol").orderBy("date").rowsBetween(-29, 0)
    
    df = df.withColumn("volatility_7d", stddev_samp("close_usd").over(window_7d))
    df = df.withColumn("volatility_30d", stddev_samp("close_usd").over(window_30d))
    
    # Calculate 30-day average volume for safety scoring
    df = df.withColumn("avg_volume_30d", avg("volume_usd").over(window_30d))
    
    return df

def build_contagion_matrix(df: DataFrame) -> pd.DataFrame:
    """
    Build a Pearson correlation matrix to identify assets with high crash correlation.
    """
    # Pivot dataset so dates are rows and symbols are columns
    pivot_df = df.groupBy("date").pivot("symbol").avg("close_usd").na.fill(0)
    
    symbols = [c for c in pivot_df.columns if c != "date"]
    
    # Assemble feature vector
    assembler = VectorAssembler(inputCols=symbols, outputCol="features")
    vector_df = assembler.transform(pivot_df).select("features")
    
    # Compute correlation
    matrix = Correlation.corr(vector_df, "features", "pearson").collect()[0][0]
    
    # Return as Pandas DataFrame for easy downstream serialization/plotting
    corr_df = pd.DataFrame(matrix.toArray(), index=symbols, columns=symbols)
    return corr_df
