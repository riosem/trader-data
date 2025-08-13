import json
import boto3

from functions.utils.logger import logger as log
from functions.consumer import position
from functions.consumer import candle_stick
from functions.utils.common import Env


def data_collection_handler(event, context):
    record = event["Records"][0] or {}
    if not record:
        log.error("No record found in the event")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "No record found in the event"}),
        }

    body = json.loads(record.get("body", "{}"))
    if not body:
        logger.error("No body found in the record")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "No body found in the record"}),
        }

    # msg_attributes = record.get("messageAttributes", {})
    provider = body.get("provider")
    product_id = body.get("product_id")
    correlation_id = body.get("correlation_id")

    logger = log.bind(
        correlation_id=correlation_id,
        provider=provider,
        product_id=product_id,
        operation="data_collection",
    )

    if not provider or not product_id or not correlation_id:
        logger.error("Missing required attributes in the message", record=record)
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Missing required attributes in the message"}
            ),
        }

    data_collection_type = body.get("data_collection_type") or "POSITION"

    # Call the appropriate data collection function based on the type
    if data_collection_type == "historical":
        candle_stick_data = body.get("candle_sticks", [])
        data_to_collect = candle_stick_data

        data_collection_func = candle_stick.collect_data
    elif data_collection_type == "POSITION":
        entry_positions = body.get("entry_positions", [])
        exit_positions = body.get("exit_positions", [])
        positions = entry_positions + exit_positions
        data_to_collect = positions
        data_collection_func = position.collect_data
    else:
        logger.error(
            "Unsupported data collection type",
            data_collection_type=data_collection_type,
        )
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"message": "Unsupported data collection type"}
            ),
        }

    try:
        data_collection_func(provider, product_id, data_to_collect, correlation_id)
    except Exception as e:
        logger.info("DATA_COLLECTION_ERROR", message=str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)}),
        }

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Data collection handler"}),
    }
