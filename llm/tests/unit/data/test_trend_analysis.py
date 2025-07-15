import pytest

from consumer.trend_analysis import scheduler_handler

def test_trend_analysis():
    event = {
        "Records": [
            {
                "body": {
                    "correlation_id": "123",
                    "product_id": "123"
                }
            }
        ]
    }
    context = {}

    response = scheduler_handler(event, context)

    assert response["statusCode"] == 200