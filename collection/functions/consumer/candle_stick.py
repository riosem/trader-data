import boto3
import boto3.session
import json

import datetime
from functions.utils.logger import logger as log
from functions.utils.common import Env

SERVICE = "data_collection"

def read_object(key):
    """Reads an object from S3"""

    s3_client = boto3.client("s3")
    obj = s3_client.get_object(Bucket=Env.DATA_COLLECTION_BUCKET_NAME, Key=key)
    return obj["Body"].read().decode("utf-8")


def get_data_dir():
    return "historical"


def collect_data(provider, product_id, candle_sticks, correlation_id):
    """Handle candle stick data from s3 bucket and processes it"""
    OPERATION = "process_candles_stick_data"
    logger = log.bind(correlation_id=correlation_id, service=SERVICE, operation=OPERATION)

    feature_keys = [
        "start",
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]

    # we will save candle stick data in csv format
    csv_lines = []
    for candle_stick in candle_sticks:
        features = [str(candle_stick[key]) for key in feature_keys]
        csv_line = ",".join(features)
        csv_lines.append(csv_line)
    csv_data = "\n".join(csv_lines)
    # Check what files are already processed for this product
    dataset_directory = get_data_dir()
    s3_client = boto3.client("s3")
    s3_base_key = f"{provider}/{product_id}/{dataset_directory}"
    response = s3_client.list_objects_v2(
        Bucket=Env.DATA_COLLECTION_BUCKET_NAME, Prefix=s3_base_key
    )
    objects = response.get("Contents", [])
    time_stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    if not objects:
        # If there are no files we create a new file and add the record(s) we retrieved from queue
        new_file_key = f"{s3_base_key}/{time_stamp}.csv"
        s3_client.put_object(
            Bucket=Env.DATA_COLLECTION_BUCKET_NAME, Key=new_file_key, Body=csv_data
        )
        logger.info("CREATING_FIRST_FILE", message="No files found", key=s3_base_key)
        return {
            "statusCode": 200,
            "body": json.dumps("Data collection handled successfully"),
        }
    # Assuming the first object in list is the most recent file
    most_recent_obj_key = objects[0]["Key"]
    # Check the file size
    obj = s3_client.get_object(
        Bucket=Env.DATA_COLLECTION_BUCKET_NAME, Key=most_recent_obj_key
    )
    file_size = obj["ContentLength"]
    if file_size > 1000000:  # 1MB
        # If the file size is too big we create a new file and add the record(s) we retrieved from queue
        most_recent_obj_key = f"{s3_base_key}/{time_stamp}.csv"
        s3_client.put_object(
            Bucket=Env.DATA_COLLECTION_BUCKET_NAME, Key=most_recent_obj_key, Body=csv_data
        )
        logger.info(
            "FILE_SIZE_HAS_GROWN", message="File size is too big, creating new file"
        )
        return {
            "statusCode": 200,
            "body": json.dumps("Data collection handled successfully"),
        }
    data = read_object(most_recent_obj_key)
    data = data + "\n" + csv_data
    # If the file size is not too big we add the record to this file
    s3_client.put_object(
        Bucket=Env.DATA_COLLECTION_BUCKET_NAME, Key=most_recent_obj_key, Body=data
    )
    logger.info(
        "APPENDING_DATA",
        message="Data collection handled successfully",
        key=most_recent_obj_key,
    )
    return {
        "statusCode": 200,
        "body": json.dumps("Data collection handled successfully"),
    }
