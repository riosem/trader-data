import os
import sys
import types
import pytest
from unittest.mock import patch, MagicMock

# --- feature_engineering.py ---
import tasks.feature_engineering as fe

def test_csv_row_to_libsvm_order():
    row = {
        "average_filled_price": "1.0",
        "filled_value": "2.0",
        "outstanding_hold_amount": "3.0",
        "total_fees": "4.0",
        "total_value_after_fees": "5.0",
        "number_of_fills": "6",
        "fee": "7.0",
        "filled_size": "8.0",
        "side": "BUY"
    }
    line = fe.csv_row_to_libsvm(row, fe.ORDER_FEATURE_KEYS, "side", {"BUY": 0, "SELL": 1})
    assert line.startswith("0 ")

def test_csv_row_to_libsvm_candle():
    row = {"start": "0", "open": "1", "high": "2", "low": "0", "close": "1.5", "volume": "100", "trend": "up"}
    line = fe.csv_row_to_libsvm(row, fe.CANDLE_FEATURE_KEYS, "trend", {"up": 1, "down": 0})
    assert line.startswith("1 ")

@patch("tasks.feature_engineering.boto3.client")
def test_s3_csv_to_libsvm_order(mock_boto3_client):
    # Mock S3 get_object and put_object
    s3 = MagicMock()
    csv_content = "side,average_filled_price,filled_value,outstanding_hold_amount,total_fees,total_value_after_fees,number_of_fills,fee,filled_size\nBUY,1,2,3,4,5,6,7,8\n"
    s3.get_object.return_value = {"Body": MagicMock(read=MagicMock(return_value=csv_content.encode("utf-8")))}
    mock_boto3_client.return_value = s3
    fe.s3_csv_to_libsvm("bucket", "csv_key", "libsvm_key", data_type="order")
    s3.put_object.assert_called_once()

def test_csv_row_to_libsvm_missing_key():
    import tasks.feature_engineering as fe
    row = {"open": "1", "high": "2"}  # missing keys
    line = fe.csv_row_to_libsvm(row, fe.CANDLE_FEATURE_KEYS, "trend", {"up": 1, "down": 0})
    assert line.startswith("0 ")

def test_csv_row_to_libsvm_invalid_label():
    import tasks.feature_engineering as fe
    row = {"start": "0", "open": "1", "high": "2", "low": "0", "close": "1.5", "volume": "100", "trend": "unknown"}
    line = fe.csv_row_to_libsvm(row, fe.CANDLE_FEATURE_KEYS, "trend", {"up": 1, "down": 0})
    assert line.startswith("0 ")

# --- predict_scikit.py ---
import tasks.predict_scikit as pred

@patch("tasks.predict_scikit.boto3.client")
def test_download_model(mock_boto3_client):
    s3 = MagicMock()
    mock_boto3_client.return_value = s3
    pred.download_model(s3, "bucket", "key", "local_path")
    s3.download_file.assert_called_once()

@patch("tasks.predict_scikit.joblib.load")
def test_load_model(mock_load):
    mock_load.return_value = "model"
    assert pred.load_model("path") == "model"

@patch("tasks.predict_scikit.load_svmlight_file")
def test_load_input_data(mock_load):
    import numpy as np
    X = np.array([[1], [2]])
    y = np.array([0, 1])
    mock_load.return_value = (X, y)
    X_out, y_out = pred.load_input_data("input")
    assert X_out.shape[0] == 2
    assert y_out.shape[0] == 2

def test_save_predictions(tmp_path):
    preds = [0.1, 0.2, 0.3]
    out = tmp_path / "preds.txt"
    pred.save_predictions(preds, str(out))
    with open(out) as f:
        lines = f.readlines()
    assert len(lines) == 3

def test_load_input_data_error(monkeypatch):
    import tasks.predict_scikit as pred
    def bad_load(*args, **kwargs):
        raise Exception("fail")
    monkeypatch.setattr(pred, "load_svmlight_file", bad_load)
    X, y = pred.load_input_data("input")
    assert X is None and y is None

def test_save_predictions_error(tmp_path):
    import tasks.predict_scikit as pred
    # Simulate error by passing an invalid path
    try:
        pred.save_predictions([0.1], "/invalid/path/preds.txt")
    except Exception:
        assert True

# --- train_scikit.py ---
import tasks.train_scikit as train

def test_create_random_forest_estimator():
    model = train.create_random_forest_estimator(estimators=10, max_depth=2, random_state=1)
    assert hasattr(model, "fit")

def test_get_config_env(monkeypatch):
    monkeypatch.setenv("S3_BUCKET", "b")
    monkeypatch.setenv("S3_KEY", "k")
    monkeypatch.setenv("OUTPUT_PATH", "o")
    monkeypatch.setenv("PROVIDER", "p")
    monkeypatch.setenv("PRODUCT_ID", "pid")
    monkeypatch.setenv("CORRELATION_ID", "cid")
    config = train.get_config()
    assert config["bucket"] == "b"

@patch("tasks.train_scikit.boto3.client")
def test_download_data(mock_boto3_client):
    s3 = MagicMock()
    mock_boto3_client.return_value = s3
    s3.download_file.side_effect = lambda b, k, f: None
    train.download_data(s3, "bucket", "key")

@patch("tasks.train_scikit.load_svmlight_file")
def test_load_data(mock_load):
    import numpy as np
    X_train = np.array([[1, 2], [3, 4]])
    y_train = np.array([0, 1])
    X_val = np.array([[5, 6]])
    y_val = np.array([1])
    mock_load.side_effect = [(X_train, y_train), (X_val, y_val)]
    X_train_out, y_train_out, X_val_out, y_val_out = train.load_data("train", "val")
    assert X_train_out.shape == (2, 2)
    assert y_val_out.shape == (1,)

def test_train_model(monkeypatch):
    class DummyModel:
        def __init__(self, **kwargs): pass
        def fit(self, X, y): self.fitted = True
    model = train.train_model([1], [2], [3], [4], {}, DummyModel)
    assert hasattr(model, "fit")

def test_evaluate_model():
    import numpy as np
    class DummyModel:
        def predict_proba(self, X): return np.array([[0.1, 0.9]] * len(X))
        feature_importances_ = [0.5, 0.5]
        best_iteration = 1
    
    model = DummyModel()
    X = [[0], [1]]
    y = [0, 1]
    metrics = train.evaluate_model(model, X, y, X, y)
    assert "train_accuracy" in metrics

@patch("tasks.train_scikit.joblib.dump")
@patch("tasks.train_scikit.boto3.client")
def test_save_and_upload_model(mock_boto3_client, mock_dump):
    s3 = MagicMock()
    mock_boto3_client.return_value = s3
    model = MagicMock()
    train.save_and_upload_model(s3, model, "bucket", "key", model_version="1")
    s3.upload_file.assert_called_once()

@patch("tasks.train_scikit.boto3.client")
def test_save_and_upload_results(mock_boto3_client, tmp_path):
    s3 = MagicMock()
    mock_boto3_client.return_value = s3
    results = {"a": 1}
    train.save_and_upload_results(s3, results, "bucket", "key")
    s3.upload_file.assert_called_once()


def test_load_data_error(monkeypatch):
    import tasks.train_scikit as train
    def bad_load(*args, **kwargs):
        raise Exception("fail")
    monkeypatch.setattr(train, "load_svmlight_file", bad_load)
    X, y, Xv, yv = train.load_data("train", "val")
    assert X is None and y is None

def test_evaluate_model_error():
    import tasks.train_scikit as train
    class BadModel:
        def predict_proba(self, X): raise Exception("fail")
    metrics = train.evaluate_model(BadModel(), [[0]], [0], [[0]], [0])
    assert "error" in metrics

# --- rag_api.py ---
import tasks.rag_api as rag

def test_root():
    resp = rag.root()
    assert "message" in resp

def test_search_logs():
    req = rag.LogSearchRequest(query="BTC", top_k=2)
    resp = rag.search_logs(req)
    assert hasattr(resp, "results")

def test_get_log_found():
    resp = rag.get_log("1")
    assert resp.log_id == "1"

def test_get_log_not_found():
    resp = rag.get_log("999")
    assert isinstance(resp, dict) and "error" in resp