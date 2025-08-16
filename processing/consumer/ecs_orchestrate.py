import json
import boto3
import os
from utils.logger import logger as log
from utils.common import Env
from datetime import datetime, date


ECS_CLIENT = boto3.client("ecs", region_name=os.getenv("REGION"))


TASK_DEFINITIONS = {
    "data_processing": "ecs-task-def-data-processing.json.template",
}


def clean_for_json(obj):
    """Recursively convert non-serializable objects (like datetime) to strings."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(clean_for_json(v) for v in obj)
    else:
        return obj


def json_dumps_safe(obj):
    """Serialize obj to JSON, converting datetime objects to strings."""
    return json.dumps(clean_for_json(obj), default=str)


def run_task(cluster, task_type, task_def_arn, overrides=None):
    """Run a task of the given type."""
    log.info("RUN_TASK", cluster=cluster, task_type=task_type, task_def_arn=task_def_arn)
    try:
        run_response = ECS_CLIENT.run_task(
            cluster=cluster,
            taskDefinition=task_def_arn,
            overrides=overrides or {},
            launchType="FARGATE",
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": [os.getenv("SUBNET_ID")],
                    "assignPublicIp": "ENABLED"
                }
            }
        )
        return clean_for_json(run_response)
    except Exception as e:
        log.error("RUN_TASK_ERROR", cluster=cluster, task_type=task_type, error=str(e))
        return {
            "statusCode": 500,
            "body": json_dumps_safe({"message": f"Error running task: {str(e)}"}),
        }


def build_env_vars(module, s3_bucket, **kwargs):
    """Builds the environment variables for the ECS task."""
    if module == "feature_engineering.py":
        return [
            {"name": "S3_BUCKET", "value": s3_bucket},
            {"name": "S3_CSV_KEY", "value": kwargs.get("s3_csv_key")},
            {"name": "S3_LIBSVM_KEY", "value": kwargs.get("s3_libsvm_key")},
            {"name": "DATA_TYPE", "value": kwargs.get("data_type")}
        ]
    elif module == "train_scikit.py":
        return [
            {"name": "S3_BUCKET", "value": s3_bucket},
            {"name": "S3_KEY", "value": kwargs.get("s3_key")},
        ]
    elif module == "predict_scikit.py":
        return [
            {"name": "S3_BUCKET", "value": s3_bucket},
            {"name": "S3_KEY", "value": kwargs.get("s3_key")},
        ]


def stop_task(cluster, task_arn, correlation_id=None):
    """
    Stops a running ECS task.
    """
    logger = log.bind(
        operation="stop_task",
        cluster=cluster,
        task_arn=task_arn,
        correlation_id=correlation_id,
    )
    ecs_client = boto3.client("ecs", region_name=Env.REGION)
    try:
        response = ecs_client.stop_task(
            cluster=cluster,
            task=task_arn,
            reason="Stopped by orchestrator"
        )
        logger.info("TASK_STOPPED", response=response)
        return {
            "statusCode": 200,
            "body": json_dumps_safe({"message": "Task stopped successfully", "response": response}),
        }
    except Exception as e:
        logger.error(
            "ERROR_STOPPING_TASK",
            message=str(e),
            cluster=cluster,
            task_arn=task_arn,
        )
        return {
            "statusCode": 500,
            "body": json_dumps_safe({"message": str(e)}),
        }

def sqs_record_handler(event, context):
    """
    This function is triggered by SQS messages to register or deregister ECS tasks.
    It determines the operation based on the message content.
    """
    logger = log.bind(operation="sqs_record_handler")

    for record in event.get("Records", []):
        body = json.loads(record.get("body", "{}"))
        provider = body.get("provider")
        product_id = body.get("product_id")
        correlation_id = body.get("correlation_id")
        operation = body.get("operation")
        cluster = body.get("cluster")
        task_type = body.get("task_type")
        task_def_arn = body.get("task_def_arn")

        APP = body.get("APP") or os.environ.get("APP")
        MODULE = body.get("MODULE") or "feature_engineering.py"
        s3_bucket = body.get("S3_BUCKET")
        s3_csv_key = body.get("S3_CSV_KEY")
        s3_libsvm_key = body.get("S3_LIBSVM_KEY")
        data_type = body.get("DATA_TYPE")
        # CPU = body.get("CPU") or os.environ.get("CPU", "256")
        # MEMORY = body.get("MEMORY") or os.environ.get("MEMORY", "512")

        env_vars = build_env_vars(
            MODULE, 
            s3_bucket, 
            s3_csv_key=s3_csv_key, 
            s3_libsvm_key=s3_libsvm_key, 
            data_type=data_type, 
            s3_key=f"{provider}/{product_id}"
        )
        container_overrides = {
            "containerOverrides": [
                {
                    "name": f"{APP}-container",
                    "command": [
                        'python',
                        '-u',
                        MODULE,
                        '--provider', provider,
                        '--product-id', product_id,
                        '--correlation-id', correlation_id,
                        '--s3-bucket', s3_bucket,
                        '--s3-csv-key', s3_csv_key,
                        '--s3-libsvm-key', s3_libsvm_key,
                        '--data-type', data_type,
                        # '--cpu', CPU,
                    ],
                    "environment": [
                        {
                            "name": "PROVIDER",
                            "value": provider
                        },
                        {
                            "name": "PRODUCT_ID",
                            "value": product_id
                        },
                        {
                            "name": "CORRELATION_ID",
                            "value": correlation_id
                        },
                        {
                            "name": "S3_BUCKET",
                            "value": s3_bucket
                        }
                    ] + env_vars
                },
            ]
        }

        logger.info("PROCESSING_RECORD", record=record)
        if operation == "run":
            result = run_task(cluster, task_type, task_def_arn, overrides=container_overrides)
            if isinstance(result, dict) and "body" in result:
                result["body"] = json_dumps_safe(json.loads(result["body"]))
            return result
        elif operation == "stop":
            return stop_task(cluster, task_type, task_def_arn)
        else:
            logger.error("UNKNOWN_OPERATION", message=f"Unknown operation: {operation}")
            return {
                "statusCode": 400,
                "body": json_dumps_safe({"message": "Unknown operation"}),
            }
    
    return {
        "statusCode": 200,
        "body": json_dumps_safe({"message": "No records to process"}),
    }