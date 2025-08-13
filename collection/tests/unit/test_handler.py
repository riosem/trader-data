import pytest
from functions.consumer import candle_stick, position
from functions.utils import common

def test_get_data_dir(monkeypatch):
    monkeypatch.setenv("DATA_DIR", "/tmp/data")
    from functions.consumer.position import get_data_dir
    assert get_data_dir() == "/tmp/data"

def test_read_object(monkeypatch):
    # Mock S3 client and response
    class DummyS3:
        def get_object(self, Bucket, Key):
            return {"Body": DummyBody()}
    class DummyBody:
        def read(self):
            return b"test-content"
    monkeypatch.setattr("functions.consumer.position.boto3", type("Boto3", (), {"client": lambda *a, **k: DummyS3()})())
    from functions.consumer.position import read_object
    assert read_object("some/key") == b"test-content"

def test_collect_data():
    from functions.consumer.position import collect_data
    orders = [
        {
            "average_filled_price": 100,
            "filled_value": 200,
            "outstanding_hold_amount": 10,
            "total_fees": 2,
            "total_value_after_fees": 198,
            "number_of_fills": 1,
            "fee": 2,
            "filled_size": 2,
            "side": "BUY"
        }
    ]
    result = collect_data("provider", "BTC-USD", orders, "corr-id")
    assert isinstance(result, list)
    assert result[0]["side"] == "BUY"
