from pyspark.sql import DataFrame
from pyspark.ml.regression import LinearRegression
from pyspark.ml.feature import VectorAssembler
from pyspark.sql.functions import col, row_number, max as f_max, explode, sequence, lit, date_add
from pyspark.sql import Window

def forecast_trend(df: DataFrame) -> DataFrame:
    """
    Use Spark MLlib to create a 365-day price trend projection.
    Uses Linear Regression trained on time index.
    """
    window = Window.partitionBy("symbol").orderBy("date")
    df = df.withColumn("time_index", row_number().over(window))
    
    assembler = VectorAssembler(inputCols=["time_index"], outputCol="features")
    
    # Drop rows without targets to fit the model
    df_features = assembler.transform(df.na.drop(subset=["close_usd"]))
    
    lr = LinearRegression(featuresCol="features", labelCol="close_usd", predictionCol="predicted_close")
    lr_model = lr.fit(df_features)
    
    # Get the last date and time index per symbol to project forward
    max_dates = df.groupBy("symbol").agg(
        f_max("date").alias("last_date"),
        f_max("time_index").alias("last_time_index")
    )
    
    # Generate 365 future days for each symbol
    future_df = max_dates.withColumn(
        "future_days", 
        explode(sequence(lit(1), lit(365)))
    ).withColumn(
        "date", date_add(col("last_date"), col("future_days"))
    ).withColumn(
        "time_index", col("last_time_index") + col("future_days")
    ).select("symbol", "date", "time_index")
    
    future_features = assembler.transform(future_df)
    
    # Make predictions
    predictions = lr_model.transform(future_features)
    
    return predictions.select("symbol", "date", "predicted_close")
