# import handler file
import pytest


@pytest.fixture
def event():
    return {"Records": [{"body": '{"s3_target_key": "data.csv"}'}]}
