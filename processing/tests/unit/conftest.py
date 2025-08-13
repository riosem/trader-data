import boto3
import pytest
import os

from utils.common import Env


@pytest.fixture()
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_REGION"] = Env.REGION
    os.environ["AWS_DEFAULT_REGION"] = Env.REGION


@pytest.fixture(autouse=True)
def mock_aws_sqs(aws_credentials):
    from moto import mock_aws

    with mock_aws():
        conn = boto3.client("sqs", Env.REGION)
        conn.create_queue(QueueName="train-queue")

        yield conn


@pytest.fixture(autouse=True)
def mock_aws_s3(aws_credentials):
    from moto import mock_aws

    with mock_aws():
        conn = boto3.client("s3", Env.REGION)
        conn.create_bucket(
            Bucket=Env.DATA_COLLECTION_BUCKET_NAME,
            CreateBucketConfiguration={"LocationConstraint": Env.REGION},
        )
        yield conn


@pytest.fixture(autouse=True)
def mock_aws_ecs(aws_credentials):
    from moto import mock_aws

    with mock_aws():
        conn = boto3.client("ecs", Env.REGION)
        conn.create_cluster(clusterName=Env.CLUSTER)
        conn.create_task_definition(
            family="task-definition",
            networkMode="bridge",
            containerDefinitions=[
                {
                    "name": "task-container",
                    "image": "task-image",
                    "memory": Env.MEMORY,
                    "cpu": Env.CPU,
                    "portMappings": [
                        {
                            "containerPort": Env.CONTAINER_PORT,
                            "hostPort": Env.HOST_PORT,
                        }
                    ],
                }
            ],
            executionRoleArn=Env.EXECUTION_ROLE_ARN,
            taskRoleArn=Env.TASK_ROLE_ARN,
        )
        conn.create_service(
            cluster=Env.CLUSTER,
            serviceName=Env.SERVICE,
            taskDefinition="task-definition",
            desiredCount=0,
        )
        yield conn


@pytest.fixture(autouse=True)
def aws_mock_sagemaker(aws_credentials):
    from moto import mock_aws

    with mock_aws():
        conn = boto3.client("sagemaker", Env.REGION)
        yield conn


@pytest.fixture
def add_s3_object(mock_aws_s3):
    s3_client = mock_aws_s3

    def _add_object(key, body):
        s3_client.put_object(Bucket=Env.DATA_COLLECTION_BUCKET_NAME, Key=key, Body=body)

    return _add_object


@pytest.fixture
def add_s3_object_over_1mb(add_s3_object):
    libsvm_data = "1 1:0.123 2:0.456 3:0.789\n"
    add_s3_object(
        "COINBASE/BTC-USD/train/2024-12-05-14-01-07.libsvm",
        libsvm_data * 1024 * 1024 * 2,
    )
