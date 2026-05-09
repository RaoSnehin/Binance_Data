import os

# Base paths
BASE_PATH = "./spot/"
PROCESSED_DATA_PATH = "hdfs://localhost:9000/data/crypto/processed/"
MODELS_PATH = "hdfs://localhost:9000/data/crypto/models/"

# Spark configuration constants
SPARK_APP_NAME = "CryptoVolatilityPipeline"
SPARK_DRIVER_MEMORY = "4g"
SPARK_EXECUTOR_MEMORY = "4g"
SPARK_SHUFFLE_PARTITIONS = "10"
