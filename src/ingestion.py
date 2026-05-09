from pyspark.sql import DataFrame
from pyspark.sql.types import StructType, StructField, LongType, DoubleType, StringType
from pyspark.sql.functions import col, to_date, input_file_name, regexp_extract

def ingest_data(spark, base_path: str) -> DataFrame:
    """
    Ingest all CSV files recursively from the given base path.
    Uses recursiveFileLookup to crawl all folders.
    Applies standard Binance schema as the files do not have headers.
    """
    binance_schema = StructType([
        StructField("open_time", LongType(), True),
        StructField("open", DoubleType(), True),
        StructField("high", DoubleType(), True),
        StructField("low", DoubleType(), True),
        StructField("close", DoubleType(), True),
        StructField("volume", DoubleType(), True),
        StructField("close_time", LongType(), True),
        StructField("quote_asset_volume", DoubleType(), True),
        StructField("number_of_trades", LongType(), True),
        StructField("taker_buy_base_asset_volume", DoubleType(), True),
        StructField("taker_buy_quote_asset_volume", DoubleType(), True),
        StructField("ignore", StringType(), True)
    ])

    df = spark.read \
        .option("header", "false") \
        .schema(binance_schema) \
        .option("recursiveFileLookup", "true") \
        .csv(base_path)
    
    # Append the source file path to extract symbol
    df = df.withColumn("file_path", input_file_name())
    
    from pyspark.sql.functions import when
    
    # Extract symbol from filename. Binance pattern example: BTCUSDT-1d-2023-01.csv
    # This extracts the characters right before the first hyphen.
    df = df.withColumn("symbol", regexp_extract(col("file_path"), r"([^/]+)-(\d+[a-zA-Z])-", 1))
    
    # Convert timestamp to a date object. Handle both ms (13 digits) and us (16 digits)
    df = df.withColumn(
        "date", 
        to_date(
            when(col("open_time") > 1e14, (col("open_time") / 1000000))
            .otherwise(col("open_time") / 1000).cast("timestamp")
        )
    )
        
    return df

def deduplicate_data(df: DataFrame) -> DataFrame:
    """
    Remove overlapping date records between monthly and daily files.
    """
    # Drop duplicates prioritizing whatever row is read first 
    # (can be modified to order by path if daily/monthly distinction is in string)
    df_dedup = df.dropDuplicates(["symbol", "date"])
    return df_dedup
