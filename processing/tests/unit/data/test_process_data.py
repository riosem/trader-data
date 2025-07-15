import pytest
import json

from functions.data.collection.processing import process_data


@pytest.mark.unit_tests
def test_process_data_no_files(buy_order, sell_order):
    # test function
    assert process_data(
        "COINBASE", "BTC-USD", [buy_order, sell_order], "correlation-id"
    ) == {"body": '"Data collection handled successfully"', "statusCode": 200}


@pytest.mark.unit_tests
def test_process_data_existing_files(buy_order, sell_order, add_s3_object):
    libsvm_data = "1 1:0.123 2:0.456 3:0.789\n"
    add_s3_object("COINBASE/BTC-USD/train/2024-12-05-14-01-07.libsvm", libsvm_data)
    assert process_data(
        "COINBASE", "BTC-USD", [buy_order, sell_order], "correlation-id"
    ) == {"body": '"Data collection handled successfully"', "statusCode": 200}


@pytest.mark.unit_tests
def test_process_data_existing_files_over_1mb(
    buy_order, sell_order, add_s3_object_over_1mb
):
    assert process_data(
        "COINBASE", "BTC-USD", [buy_order, sell_order], "correlation-id"
    ) == {"body": '"Data collection handled successfully"', "statusCode": 200}


@pytest.mark.unit_tests
def test_process_data_random_key_validation(monkeypatch, buy_order, sell_order):
    import random

    monkeypatch.setattr(random, "randint", lambda x, y: 10)  # Number less than 33
    assert process_data(
        "COINBASE", "BTC-USD", [buy_order, sell_order], "correlation-id"
    ) == {"body": '"Data collection handled successfully"', "statusCode": 200}


@pytest.mark.unit_tests
def test_process_data_random_train(monkeypatch, buy_order, sell_order):
    import random

    monkeypatch.setattr(random, "randint", lambda x, y: 35)  # Number less than 33
    assert process_data(
        "COINBASE", "BTC-USD", [buy_order, sell_order], "correlation-id"
    ) == {"body": '"Data collection handled successfully"', "statusCode": 200}
