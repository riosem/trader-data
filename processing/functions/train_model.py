# train_model.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import RandomForestRegressor
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import RegressionEvaluator

import structlog
from utils.common import Env

structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
    )
logger = structlog.get_logger()

# Replace 'open', 'high', 'low', 'close', 'volume' with your actual feature columns
feature_cols = ["open", "high", "low", "close", "volume"]

try:
    spark = SparkSession.builder.appName("TrainPriceModel").getOrCreate()
except Exception as e:
    logger.error("Failed to create Spark session", exc_info=e)
    raise

# Load historical data from S3 or HDFS
try:
    df = spark.read.csv(f"s3://{Env.DATA_COLLECTION_BUCKET}/candlesticks-S.csv", header=True, inferSchema=True)
except Exception as e:
    logger.error("Failed to load data", exc_info=e)
    raise


# Feature engineering
try:
    data = df.withColumn("label", col("close"))
except Exception as e:
    logger.error("Failed to process data", exc_info=e)
    raise

# Drop rows with NaN or nulls in feature columns
try:
    df_clean = df.dropna(subset=feature_cols + ["label"])
except Exception as e:
    logger.error("Failed to clean data", exc_info=e)
    raise

# Split data
try:
    train, test = data.randomSplit([0.8, 0.2], seed=42)
except Exception as e:
    logger.error("Failed to split data", exc_info=e)
    raise

# Define assembler and model
try:
    assembler = VectorAssembler(inputCols=["open", "high", "low", "close", "volume"], outputCol="features")
except Exception as e:
    logger.error("Failed to create VectorAssembler", exc_info=e)
    raise

try:
    rf = RandomForestRegressor(featuresCol="features", labelCol="label")
except Exception as e:
    logger.error("Failed to create RandomForestRegressor", exc_info=e)
    raise

try:
    pipeline = Pipeline(stages=[assembler, rf])
except Exception as e:
    logger.error("Failed to create Pipeline", exc_info=e)
    raise

# Train model
try:
    model = pipeline.fit(train)
except Exception as e:
    logger.error("Failed to train model", exc_info=e)
    raise

# Evaluate
try:
    predictions = model.transform(test)
except Exception as e:
    logger.error("Failed to make predictions", exc_info=e)
    raise

try:
    evaluator = RegressionEvaluator(labelCol="label", predictionCol="prediction", metricName="rmse")
except Exception as e:
    logger.error("Failed to create RegressionEvaluator", exc_info=e)
    raise

try:
    rmse = evaluator.evaluate(predictions)
except Exception as e:
    logger.error("Failed to evaluate model", exc_info=e)
    raise
print(f"Test RMSE: {rmse}")

# Save model to S3 or HDFS
try:
    model.write().overwrite().save(f"s3://{Env.DATA_COLLECTION_BUCKET}/models/price_rf_model")
except Exception as e:
    logger.error("Failed to save model", exc_info=e)
    raise

try:
    spark.stop()
except Exception as e:
    logger.error("Failed to stop Spark session", exc_info=e)
    raise