import boto3
import json

from ulid import ulid
from utils.common import DecimalEncoder


def send_message_to_queue(
    queue_url: str, message_body: dict, msg_group_id=str(ulid()), msg_attrs={}
):
    sqs = boto3.client("sqs", "us-east-2")

    options = {
        "QueueUrl": queue_url,
        "MessageBody": json.dumps(message_body, cls=DecimalEncoder),
        # "MessageGroupId": msg_group_id,
        # "MessageDeduplicationId": str(ulid()),
        "MessageAttributes": msg_attrs,
    }

    if queue_url.endswith("fifo"):
        options["MessageGroupId"] = msg_group_id
        options["MessageDeduplicationId"] = str(ulid())

    sqs.send_message(**options)
