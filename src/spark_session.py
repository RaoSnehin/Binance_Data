from pyspark.sql import SparkSession
from src.config import SPARK_APP_NAME, SPARK_DRIVER_MEMORY, SPARK_EXECUTOR_MEMORY, SPARK_SHUFFLE_PARTITIONS

def get_spark_session(app_name=SPARK_APP_NAME):
    """
    Initialize and return a local Spark session optimized for a standard laptop.
    Hadoop compliance is maintained through Spark's DataFrame API which mimics 
    HDFS distributed processing logically.
    """
    spark = SparkSession.builder \
        .appName(app_name) \
        .master("local[*]") \
        .config("spark.driver.memory", SPARK_DRIVER_MEMORY) \
        .config("spark.executor.memory", SPARK_EXECUTOR_MEMORY) \
        .config("spark.sql.shuffle.partitions", SPARK_SHUFFLE_PARTITIONS) \
        .config("spark.driver.extraJavaOptions", "-Djava.security.manager=allow") \
        .config("spark.executor.extraJavaOptions", "-Djava.security.manager=allow") \
        .getOrCreate()
    
    return spark
