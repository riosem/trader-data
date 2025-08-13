import csv
import boto3
import io
import os
import sys
import logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


ORDER_FEATURE_KEYS = [
    "average_filled_price",
    "filled_value",
    "outstanding_hold_amount",
    "total_fees",
    "total_value_after_fees",
    "number_of_fills",
    "fee",
    "filled_size",
]

CANDLE_FEATURE_KEYS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    # add more engineered features as needed
]


def csv_row_to_libsvm(row, feature_keys, label_col, label_map=None):
    label_val = row[label_col]
    if label_map:
        label = label_map.get(label_val, label_val)
    else:
        label = label_val
    features = (f"{i+1}:{row[key]}" for i, key in enumerate(feature_keys))
    return f"{label} " + " ".join(features)


def s3_csv_to_libsvm(s3_bucket, s3_csv_key, s3_libsvm_key, data_type="order"):
    if data_type == "order":
        feature_keys = ORDER_FEATURE_KEYS
        label_col = "side"
        label_map = {"BUY": 0, "SELL": 1}
    elif data_type == "candle":
        feature_keys = CANDLE_FEATURE_KEYS
        label_col = "trend"
        label_map = {"up": 1, "down": 0}
    else:
        raise ValueError("Unsupported data_type")

    s3 = boto3.client("s3")
    logger.info(f"Downloading CSV from s3://{s3_bucket}/{s3_csv_key}")
    csv_obj = s3.get_object(Bucket=s3_bucket, Key=s3_csv_key)
    csv_content = csv_obj['Body'].read().decode('utf-8')
    csvfile = io.StringIO(csv_content)
    reader = csv.DictReader(csvfile)

    def libsvm_line_generator():
        for row in reader:
            yield csv_row_to_libsvm(row, feature_keys, label_col, label_map)

    libsvm_buffer = io.StringIO()
    for libsvm_line in libsvm_line_generator():
        libsvm_buffer.write(libsvm_line + "\n")

    logger.info(f"Uploading libsvm to s3://{s3_bucket}/{s3_libsvm_key}")
    s3.put_object(Bucket=s3_bucket, Key=s3_libsvm_key, Body=libsvm_buffer.getvalue().encode("utf-8"))
    logger.info("Feature engineering complete.")


def main():
    try:
        s3_bucket = os.environ["S3_BUCKET"]
        s3_csv_key = os.environ["S3_CSV_KEY"]
        s3_libsvm_key = os.environ["S3_LIBSVM_KEY"]
        data_type = os.environ.get("DATA_TYPE", "order")
        s3_csv_to_libsvm(s3_bucket, s3_csv_key, s3_libsvm_key, data_type=data_type)
    except Exception as e:
        logger.error(f"Feature engineering failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()