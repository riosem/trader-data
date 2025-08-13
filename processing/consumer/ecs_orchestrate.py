import json
import boto3

from utils.logger import logger as log
from utils.common import Env


import boto3
import json
import os

ECS_CLIENT = boto3.client("ecs", region_name=os.getenv("REGION"))

# Define your task definition templates (could also load from files)
TASK_DEFINITIONS = {
    # "fastapi": "ecs-task-definition-fastapi.json.template",
    # "vector_search": "ecs-task-definition-vector-search.json.template",
    "data_processing": "ecs-task-def-data-processing.json.template",
}


def load_task_definition(template_path, params):
    """Load and render a task definition template with params."""
    with open(template_path) as f:
        template = f.read()
    for k, v in params.items():
        template = template.replace(f"${{{k}}}", str(v))
    return json.loads(template)


def register_task_definition(task_type, params):
    """Register a task definition for the given type."""
    template_path = TASK_DEFINITIONS[task_type]
    task_def = load_task_definition(template_path, params)
    response = ECS_CLIENT.register_task_definition(**task_def)
    return response


def run_task(cluster, task_type, params, overrides=None):
    """Run a task of the given type."""
    response = register_task_definition(task_type, params)
    task_def_arn = response["taskDefinition"]["taskDefinitionArn"]
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
    return run_response


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
            "body": json.dumps({"message": "Task stopped successfully", "response": response}),
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
            "body": json.dumps({"message": str(e)}),
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

        APP = body.get("APP") or os.environ.get("APP")
        MODULE = body.get("MODULE") or "feature_engineering.py"
        IMAGE = os.environ.get("IMAGE")
        EXECUTION_ROLE = os.environ.get("EXECUTION_ROLE")
        TASK_ROLE = os.environ.get("TASK_ROLE")
        CPU = body.get("CPU") or os.environ.get("CPU", "256")
        MEMORY = body.get("MEMORY") or os.environ.get("MEMORY", "512")
        params = {
            "APP": APP,
            "IMAGE": IMAGE,
            "MODULE": MODULE,
            "EXEC_ROLE_NAME": EXECUTION_ROLE,
            "TASK_ROLE_NAME": TASK_ROLE,
            "CPU": CPU,
            "MEMORY": MEMORY,
        }

        if operation == "run":
            # return run_task(provider, product_id, correlation_id, action=action)
            return run_task(cluster, task_type, params, overrides=body.get("overrides"))
        elif operation == "stop":
            # return stop_task(provider, product_id, correlation_id)
            return stop_task(cluster, task_type, params)
        else:
            logger.error("UNKNOWN_OPERATION", message=f"Unknown operation: {operation}")
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Unknown operation"}),
            }
    
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "No records to process"}),
    }