import boto3
import json

from ulid import ULID
from utils.common import DecimalEncoder


def send_message_to_queue(
    queue_url: str, message_body: dict, msg_group_id=str(ULID()), msg_attrs={}
):
    sqs = boto3.client("sqs", "us-east-2")

    options = {
        "QueueUrl": queue_url,
        "MessageBody": json.dumps(message_body, cls=DecimalEncoder),
        # "MessageGroupId": msg_group_id,
        # "MessageDeduplicationId": str(ULID()),
        "MessageAttributes": msg_attrs,
    }

    if queue_url.endswith("fifo"):
        options["MessageGroupId"] = msg_group_id
        options["MessageDeduplicationId"] = str(ULID())

    sqs.send_message(**options)
