import os
import decimal
import json


class Env:
    REGION = os.getenv("REGION")
    DATA_COLLECTION_BUCKET_NAME = os.getenv("DATA_COLLECTION_BUCKET_NAME")
    EXECUTION_ROLE_ARN = os.getenv("EXECUTION_ROLE_ARN")
    TASK_ROLE_ARN = os.getenv("TASK_ROLE_ARN")
    OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")
    COINBASE_API_KEY = os.environ.get("COINBASE_API_KEY")
    COINBASE_API_SECRET = os.environ.get("COINBASE_API_SECRET")
    ASSISTANT_API_KEY = os.environ.get("ASSISTANT_API_KEY")
    AUTH0_ASSISTANT_CLIENT_ID = os.environ.get("AUTH0_ASSISTANT_CLIENT_ID")
    AUTH0_ASSISTANT_CLIENT_SECRET = os.environ.get("AUTH0_ASSISTANT_CLIENT_SECRET")
    AUTH0_ASSISTANT_AUDIENCE = os.environ.get("AUTH0_ASSISTANT_AUDIENCE")
    CACHE_TABLE_NAME = os.environ.get("CACHE_TABLE_NAME")
    AUTH0_OAUTH_URL = os.environ.get("AUTH0_OAUTH_URL")
    SUBNET_IDS = (os.environ.get("SUBNET_IDS") or "").split(",")
    SGS_IDS = (os.environ.get("SGS_IDS", "") or "").split(",")
    NODE_GROUP_MIN_SIZE = int(os.environ.get("NODE_GROUP_MIN_SIZE") or 1)
    NODE_GROUP_MAX_SIZE = int(os.environ.get("NODE_GROUP_MAX_SIZE") or 2)
    NODE_GROUP_DESIRED_SIZE = int(os.environ.get("NODE_GROUP_DESIRED_SIZE") or 1)


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)


def multipart_upload(data_stream, bucket_name, most_recent_obj_key):
    """
    Uploads a file to S3 using multipart upload.
    :param data_stream: The data stream to upload.
    :param bucket_name: The name of the S3 bucket.
    :param most_recent_obj_key: The key for the object in S3.
    """
    # Example of multipart upload
    from boto3.s3.transfer import TransferConfig

    import boto3
    
    # Create a boto3 S3 client
    s3_client = boto3.client("s3")
    config = TransferConfig(multipart_threshold=5 * 1024 * 1024)  # 5 MB threshold
    s3_client.upload_fileobj(
        Fileobj=data_stream,
        Bucket=bucket_name,
        Key=most_recent_obj_key,
        Config=config,
    )