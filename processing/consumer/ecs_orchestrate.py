import json
import boto3

from utils.logger import logger as log
from utils.common import Env


def register_task(provider, product_id, correlation_id):
    logger = log.bind(
        correlation_id=correlation_id,
        provider=provider,
        product_id=product_id,
        operation="register_task",
    )

    ecs_client = boto3.client("ecs", region_name=Env.REGION)

    try:
        response = ecs_client.register_task_definition(
            family=f"{Env.SERVICE}-task-family",
            networkMode="awsvpc",
            containerDefinitions=[
                {
                    "name": Env.CONTAINER_NAME,
                    "image": Env.CONTAINER_IMAGE_URI,
                    "memory": Env.MEMORY,
                    "cpu": Env.CPU,
                    "essential": True,
                    "portMappings": [
                        {
                            "containerPort": Env.CONTAINER_PORT,
                            "hostPort": Env.HOST_PORT,
                        }
                    ],
                    "environment": [
                        {"name": "PROVIDER", "value": provider},
                        {"name": "PRODUCT_ID", "value": product_id},
                        {"name": "CORRELATION_ID", "value": correlation_id},
                        {"name": "ACTION", "value": "TRAIN"}
                    ],
                }
            ],
            requiresCompatibilities=["FARGATE"],
            executionRoleArn=Env.EXECUTION_ROLE_ARN,
            taskRoleArn=Env.TASK_ROLE_ARN,
        )
        logger.info("TASK_REGISTERED", response=response)
    except Exception as e:
        logger.error(
            "ERROR_REGISTERING_TASK",
            message=str(e),
            container_name=Env.CONTAINER_NAME,
            container_image_uri=Env.CONTAINER_IMAGE_URI,
            memory=Env.MEMORY,
            cpu=Env.CPU,
            port_mappings=Env.CONTAINER_PORT,
            host_port=Env.HOST_PORT,
        )
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)}),
        }

    try:
        response = ecs_client.update_service(
            cluster=Env.CLUSTER,
            service=Env.SERVICE,
            desiredCount=1,
        )
        logger.info("SERVICE_UPDATED", response=response)
    except Exception as e:
        logger.error(
            "ERROR_UPDATING_SERVICE",
            message=str(e),
            cluster=Env.CLUSTER,
            service=Env.SERVICE,
        )
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)}),
        }

    logger.info("TASK_HANDLER_SUCCESSFUL", message="Task handler successful")

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Task handler successful"}),
    }


def deregister_task(provider, product_id, correlation_id):
    logger = log.bind(
        correlation_id=correlation_id,
        provider=provider,
        product_id=product_id,
        operation="deregister_task",
    )

    ecs_client = boto3.client("ecs", region_name=Env.REGION)

    try:
        response = ecs_client.deregister_task_definition(
            taskDefinition=f"{Env.SERVICE}-task-family"
        )
        logger.info("TASK_DEREGISTERED", response=response)
    except Exception as e:
        logger.error(
            "ERROR_DEREGISTERING_TASK",
            message=str(e),
            task_definition=f"{Env.SERVICE}-task-family",
        )
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)}),
        }

    try:
        response = ecs_client.update_service(
            cluster=Env.CLUSTER,
            service=Env.SERVICE,
            desiredCount=0,
        )
        logger.info("SERVICE_UPDATED", response=response)
    except Exception as e:
        logger.error(
            "ERROR_UPDATING_SERVICE",
            message=str(e),
            cluster=Env.CLUSTER,
            service=Env.SERVICE,
        )
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)}),
        }

    logger.info("TASK_HANDLER_SUCCESSFUL", message="Task handler successful")

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Task handler successful"}),
    }


def sqs_record_handler(event, context):
    """
    This function is triggered by SQS messages to register or deregister ECS tasks.
    It determines the operation based on the message content.
    """
    logger = log.bind(operation="sqs_record_handler")

    for record in event.get("Records", []):
        body = json.loads(record.get("body", "{}"))
        operation = body.get("operation")
        provider = body.get("provider")
        product_id = body.get("product_id")
        correlation_id = body.get("correlation_id")
        action = body.get("action")

        if operation == "register":
            return register_task(provider, product_id, correlation_id, action=action)
        elif operation == "deregister":
            return deregister_task(provider, product_id, correlation_id)
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