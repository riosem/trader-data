# predict_model.py
from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel

spark = SparkSession.builder.appName("PredictPrice").getOrCreate()

# Load new/unseen data
df = spark.read.csv("s3://your-bucket/new_candles.csv", header=True, inferSchema=True)

# Load trained model
model = PipelineModel.load("s3://your-bucket/models/price_rf_model")

# Predict
predictions = model.transform(df)
predictions.select("timestamp", "prediction").write.csv("s3://your-bucket/predictions/future_prices.csv", header=True)

spark.stop()