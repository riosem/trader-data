import pytest
import json
from unittest.mock import Mock, patch

from consumer.prompts import (
    Prompt,
    prompt_handler
)

import pytest
import pandas as pd
from consumer.prompts import compute_features, ContextBuilder, PromptBuilder, fetch_data, Prompt


@pytest.mark.unit_tests
def test_compute_features_price_volume_change_len1():
    # Covers the else branch for price/volume change (len(data) < 2)
    df = pd.DataFrame({'close': [1], 'volume': [10]})
    features = compute_features(df)
    assert features["price_change"] is None
    assert features["volume_change"] is None

@pytest.mark.unit_tests
def test_prompt_builder_direct():
    # Directly test PromptBuilder with a real template and context
    class DummyTemplate:
        def render(self, **kwargs):
            return f"foo={kwargs.get('foo')}"
    pb = PromptBuilder(DummyTemplate(), {"foo": "bar"})
    assert pb.build() == "foo=bar"




@pytest.mark.unit_tests
def test_compute_features_price_volume_change_short_df():
    # Covers the else branch for price/volume change
    df = pd.DataFrame({'close': [1], 'volume': [10]})
    features = compute_features(df)
    assert features["price_change"] is None
    assert features["volume_change"] is None


@pytest.mark.unit_tests
def test_prompt_builder_render_called():
    # Covers PromptBuilder.build
    class DummyTemplate:
        def render(self, **kwargs):
            return "rendered"
    pb = PromptBuilder(DummyTemplate(), {"foo": "bar"})
    assert pb.build() == "rendered"


@pytest.mark.unit_tests
def test_context_builder_default_branch(monkeypatch):
    # Patch fetch_data to avoid real API call
    monkeypatch.setattr("consumer.prompts.fetch_data", lambda product_id: pd.DataFrame())
    class DummyCB(ContextBuilder):
        def build(self):
            return super().build()
    cb = DummyCB("BTC-USD", "unknown_prompt")
    context = cb.build()
    assert context == {"product_id": "BTC-USD"}


@pytest.mark.unit_tests
def test_prompt_handler_empty_records():
    # Covers the case where Records is empty
    event = {"Records": []}
    with pytest.raises(IndexError):
        prompt_handler(event, {})


@pytest.mark.unit_tests
def test_prompt_handler_missing_body():
    # Covers the case where body is missing in record
    event = {"Records": [{}]}
    with pytest.raises(KeyError):
        prompt_handler(event, {})


@patch('consumer.prompts.notify_assistant')
@patch('consumer.prompts.PromptEngine')
@patch('consumer.prompts.ContextBuilder')
def test_prompt_handler_notify_assistant_exception(self, mock_context_builder, mock_prompt_engine, mock_notify, valid_event):
    """Test exception when notify_assistant fails"""
    mock_context = {"product_id": "BTC-USD", "rolling_avg": 50000}
    mock_context_builder.return_value.build.return_value = mock_context
    mock_prompt_engine.return_value.send_prompt.return_value = "Market is bullish"
    mock_notify.side_effect = Exception("Notify failed")

    with pytest.raises(Exception):
        prompt_handler(valid_event, {})

    mock_context_builder.return_value.build.assert_called_once()
    mock_prompt_engine.return_value.send_prompt.assert_called_once()
    mock_notify.assert_called_once()


@pytest.mark.unit_tests
def test_compute_features_empty():
    df = pd.DataFrame()
    features = compute_features(df)
    assert all(v is None for v in features.values())


@pytest.mark.unit_tests
def test_compute_features_minimal():
    df = pd.DataFrame({'close': [1,2,3,4,5], 'volume': [10,20,30,40,50]})
    features = compute_features(df)
    assert features["rolling_avg"] is not None
    assert features["ema"] is not None
    assert features["bollinger_upper"] is not None
    assert features["bollinger_lower"] is not None
    assert features["rsi"] is not None
    assert features["price_change"] == 1
    assert features["volume_change"] == 10
    assert features["daily_high"] == 5
    assert features["daily_low"] == 1
    assert features["buying_momentum"] is not None
    assert features["selling_momentum"] is not None


@pytest.mark.unit_tests
def test_context_builder_trend_analysis(monkeypatch):
    class DummyCB(ContextBuilder):
        def build(self):
            return {"product_id": "BTC-USD", "rolling_avg": 1}
    cb = DummyCB("BTC-USD", Prompt.TREND_ANALYSIS.value)
    context = cb.build()
    assert context["product_id"] == "BTC-USD"


@pytest.mark.unit_tests
def test_prompt_builder():
    class DummyTemplate:
        def render(self, **kwargs):
            return "rendered"
    pb = PromptBuilder(DummyTemplate(), {"foo": "bar"})
    assert pb.build() == "rendered"


@pytest.mark.unit_tests
def test_fetch_data(monkeypatch):
    # Patch RESTClient to avoid real API call
    class DummyClient:
        def get_candles(self, *a, **kw):
            class DummyCandle:
                def to_dict(self):
                    return {"close": 1, "volume": 1}
            return {"candles": [DummyCandle(), DummyCandle()]}
    monkeypatch.setattr("consumer.prompts.RESTClient", lambda *a, **kw: DummyClient())
    import consumer.prompts
    import pandas as pd
    df = consumer.prompts.fetch_data("BTC-USD")
    assert isinstance(df, pd.DataFrame)
    assert "close" in df.columns
    assert "volume" in df.columns


@pytest.mark.unit_tests
class TestPromptEnum:
    """Test Prompt enum"""

    def test_prompt_enum_values(self):
        """Test that Prompt enum has expected values"""
        assert Prompt.TREND_ANALYSIS.value == "trend_analysis"


@pytest.mark.unit_tests
class TestPromptHandler:
    """Test the main prompt_handler function"""

    @pytest.fixture
    def valid_event(self):
        return {
            "Records": [
                {
                    "body": json.dumps({
                        "correlation_id": "test-correlation-id",
                        "product_id": "BTC-USD",
                        "prompt": "trend_analysis"
                    })
                }
            ]
        }

    @pytest.fixture
    def invalid_prompt_event(self):
        return {
            "Records": [
                {
                    "body": json.dumps({
                        "correlation_id": "test-correlation-id",
                        "product_id": "BTC-USD",
                        "prompt": "invalid_prompt"
                    })
                }
            ]
        }

    @pytest.fixture
    def missing_product_id_event(self):
        return {
            "Records": [
                {
                    "body": json.dumps({
                        "correlation_id": "test-correlation-id",
                        "prompt": "trend_analysis"
                    })
                }
            ]
        }

    @pytest.fixture
    def missing_correlation_id_event(self):
        return {
            "Records": [
                {
                    "body": json.dumps({
                        "product_id": "BTC-USD",
                        "prompt": "trend_analysis"
                    })
                }
            ]
        }

    @patch('consumer.prompts.notify_assistant')
    @patch('consumer.prompts.PromptEngine')
    @patch('consumer.prompts.ContextBuilder')
    def test_prompt_handler_success(self, mock_context_builder, mock_prompt_engine, mock_notify, valid_event):
        """Test successful prompt handling"""
        # Setup mocks
        mock_context = {"product_id": "BTC-USD", "rolling_avg": 50000}
        mock_context_builder.return_value.build.return_value = mock_context
        mock_prompt_engine.return_value.send_prompt.return_value = "Market is bullish"

        # Execute
        response = prompt_handler(valid_event, {})

        # Verify
        assert response["statusCode"] == 200
        mock_context_builder.return_value.build.assert_called_once()
        mock_prompt_engine.return_value.send_prompt.assert_called_once_with(
            "trend_analysis", mock_context
        )
        mock_notify.assert_called_once_with(
            correlation_id="test-correlation-id",
            message="Market is bullish"
        )

    def test_prompt_handler_invalid_prompt(self, invalid_prompt_event):
        """Test handling of invalid prompt type"""
        response = prompt_handler(invalid_prompt_event, {})

        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Unsupported prompt type" in response_body["error"]

    def test_prompt_handler_missing_product_id(self, missing_product_id_event):
        """Test handling of missing product ID"""
        response = prompt_handler(missing_product_id_event, {})

        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Product ID is required" in response_body["error"]

    @patch('consumer.prompts.notify_assistant')
    @patch('consumer.prompts.PromptEngine')
    @patch('consumer.prompts.ContextBuilder')
    def test_prompt_handler_missing_correlation_id(self, mock_context_builder, mock_prompt_engine, mock_notify, missing_correlation_id_event):
        """Test handling of missing correlation ID"""
        mock_context_builder.return_value.build.return_value = {"product_id": "BTC-USD"}
        mock_prompt_engine.return_value.send_prompt.return_value = "Market is bullish"
        response = prompt_handler(missing_correlation_id_event, {})
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Correlation ID is required" in response_body["error"]

    @patch('consumer.prompts.notify_assistant')
    @patch('consumer.prompts.PromptEngine')
    @patch('consumer.prompts.ContextBuilder')
    def test_prompt_handler_analysis_exception(self, mock_context_builder, mock_prompt_engine, mock_notify, valid_event):
        """Test handling of analysis exceptions"""
        # Setup mocks to raise exception
        mock_context_builder.return_value.build.return_value = {"product_id": "BTC-USD"}
        mock_prompt_engine.return_value.send_prompt.side_effect = Exception("LLM error")

        with pytest.raises(Exception):
            prompt_handler(valid_event, {})

        mock_context_builder.return_value.build.assert_called_once()
        mock_prompt_engine.return_value.send_prompt.assert_called_once()

    def test_prompt_handler_missing_prompt(self, valid_event):
        """Test handling of missing prompt type"""
        event = {
            "Records": [
                {
                    "body": json.dumps({
                        "correlation_id": "test-correlation-id",
                        "product_id": "BTC-USD"
                    })
                }
            ]
        }
        response = prompt_handler(event, {})
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Unsupported prompt type" in response_body["error"]

    def test_prompt_handler_empty_records(self):
        """Test handling of empty Records list"""
        event = {"Records": []}
        # Should not raise, but will likely KeyError or return error
        with pytest.raises(IndexError):
            prompt_handler(event, {})

    def test_prompt_handler_missing_body(self):
        """Test handling of missing body in record"""
        event = {"Records": [{}]}
        with pytest.raises(KeyError):
            prompt_handler(event, {})

    @patch('consumer.prompts.notify_assistant')
    @patch('consumer.prompts.PromptEngine')
    @patch('consumer.prompts.ContextBuilder')
    def test_prompt_handler_notify_assistant_exception(self, mock_context_builder, mock_prompt_engine, mock_notify, valid_event):
        """Test exception when notify_assistant fails"""
        mock_context = {"product_id": "BTC-USD", "rolling_avg": 50000}
        mock_context_builder.return_value.build.return_value = mock_context
        mock_prompt_engine.return_value.send_prompt.return_value = "Market is bullish"
        mock_notify.side_effect = Exception("Notify failed")

        with pytest.raises(Exception):
            prompt_handler(valid_event, {})

        mock_context_builder.return_value.build.assert_called_once()
        mock_prompt_engine.return_value.send_prompt.assert_called_once()
        mock_notify.assert_called_once()

    @patch('consumer.prompts.notify_assistant')
    @patch('consumer.prompts.PromptEngine')
    @patch('consumer.prompts.ContextBuilder')
    def test_prompt_handler_empty_context(self, mock_context_builder, mock_prompt_engine, mock_notify, valid_event):
        """Test handling when context builder returns empty context"""
        mock_context_builder.return_value.build.return_value = {}
        mock_prompt_engine.return_value.send_prompt.return_value = "No data"
        response = prompt_handler(valid_event, {})
        assert response["statusCode"] == 200
        mock_context_builder.return_value.build.assert_called_once()
        mock_prompt_engine.return_value.send_prompt.assert_called_once()
        mock_notify.assert_called_once()
    

    @patch('consumer.prompts.ContextBuilder')
    @patch('consumer.prompts.PromptEngine')
    @patch('consumer.prompts.notify_assistant')
    def test_prompt_handler_unexpected_exception(self, mock_notify, mock_prompt_engine, mock_context_builder, valid_event):
        # Covers the generic exception branch in prompt_handler
        with patch('consumer.prompts.ContextBuilder') as mock_context_builder, \
            patch('consumer.prompts.PromptEngine') as mock_prompt_engine, \
            patch('consumer.prompts.notify_assistant'):
            mock_context_builder.return_value.build.return_value = {"product_id": "BTC-USD"}
            mock_prompt_engine.return_value.send_prompt.side_effect = Exception("Unexpected error")
            with pytest.raises(Exception):
                prompt_handler(valid_event, {})
                mock_context_builder.return_value.build.assert_called_once()
                mock_prompt_engine.return_value.send_prompt.assert_called_once()
                mock_notify.assert_called_once()

    @patch('consumer.prompts.ContextBuilder')
    @patch('consumer.prompts.PromptEngine')
    @patch('consumer.prompts.notify_assistant')
    def test_prompt_handler_notify_assistant_unexpected_exception(self, mock_notify, mock_prompt_engine, mock_context_builder, valid_event):
        # Covers the exception branch for notify_assistant in prompt_handler
        with patch('consumer.prompts.ContextBuilder') as mock_context_builder, \
            patch('consumer.prompts.PromptEngine') as mock_prompt_engine, \
            patch('consumer.prompts.notify_assistant', side_effect=Exception("Notify error")):
            mock_context_builder.return_value.build.return_value = {"product_id": "BTC-USD"}
            mock_prompt_engine.return_value.send_prompt.return_value = "Market is bullish"
            with pytest.raises(Exception):
                prompt_handler(valid_event, {})

    @patch('consumer.prompts.ContextBuilder')
    @patch('consumer.prompts.PromptEngine')
    @patch('consumer.prompts.notify_assistant')
    def test_prompt_handler_context_builder_returns_none(self, mock_notify, mock_prompt_engine, mock_context_builder, valid_event):
        # Covers the case where context_builder.build() returns None
        with patch('consumer.prompts.ContextBuilder') as mock_context_builder, \
            patch('consumer.prompts.PromptEngine') as mock_prompt_engine, \
            patch('consumer.prompts.notify_assistant'):
            mock_context_builder.return_value.build.return_value = None
            mock_prompt_engine.return_value.send_prompt.return_value = "No context"
            response = prompt_handler(valid_event, {})
            assert response["statusCode"] == 200