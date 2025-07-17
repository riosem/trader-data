import pytest
import json
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from enum import Enum

from consumer.prompts import (
    Prompt,
    TrendAnalysis,
    prompt_handler
)


class TestPromptEnum:
    """Test Prompt enum"""
    
    def test_prompt_enum_values(self):
        """Test that Prompt enum has expected values"""
        assert Prompt.TREND_ANALYSIS.value == "trend_analysis"


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
    @patch('consumer.prompts.TrendAnalysis')
    def test_prompt_handler_success(self, mock_trend_analysis_class, mock_notify, valid_event):
        """Test successful prompt handling"""
        # Setup mocks
        mock_process = Mock()
        mock_process.calculate_insights.return_value = "Market is bullish"
        mock_trend_analysis_class.return_value = mock_process
        
        # Execute
        response = prompt_handler(valid_event, {})
        
        # Verify
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert response_body["message"] == "Successfully processed prompt"
        
        mock_trend_analysis_class.assert_called_once_with("BTC-USD")
        mock_process.fecth_data.assert_called_once()
        mock_process.process_stock_update.assert_called_once()
        mock_process.calculate_insights.assert_called_once()
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

    def test_prompt_handler_missing_correlation_id(self, missing_correlation_id_event):
        """Test handling of missing correlation ID"""
        response = prompt_handler(missing_correlation_id_event, {})
        
        assert response["statusCode"] == 400
        response_body = json.loads(response["body"])
        assert "Correlation ID is required" in response_body["error"]
    
    @patch('consumer.prompts.notify_assistant')
    @patch('consumer.prompts.TrendAnalysis')
    def test_prompt_handler_analysis_exception(self, mock_trend_analysis_class, mock_notify, valid_event):
        """Test handling of analysis exceptions"""
        # Setup mocks to raise exception
        mock_process = Mock()
        mock_process.fecth_data.side_effect = Exception("Data fetch failed")
        mock_trend_analysis_class.return_value = mock_process
        
        # Execute
        response = prompt_handler(valid_event, {})
        
        # Verify error response
        assert response["statusCode"] == 500
        response_body = json.loads(response["body"])
        assert "Internal server error" in response_body["error"]


class TestTrendAnalysis:
    """Test TrendAnalysis class"""
    
    @pytest.fixture
    def trend_analysis(self):
        with patch('consumer.prompts.get_llm_manager'):
            return TrendAnalysis("BTC-USD")
    
    @patch('consumer.prompts.RESTClient')
    @patch('consumer.prompts.datetime')
    def test_fetch_data_success(self, mock_datetime, mock_rest_client_class, trend_analysis):
        """Test successful data fetching"""
        # Setup mocks
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        mock_client = Mock()
        mock_rest_client_class.return_value = mock_client
        
        # Mock candles data
        mock_candle = Mock()
        mock_candle.to_dict.return_value = {
            'close': '50000.0',
            'volume': '1000.0',
            'timestamp': 1704110400
        }
        mock_client.get_candles.return_value = {"candles": [mock_candle]}
        
        # Execute
        trend_analysis.fecth_data()
        
        # Verify
        assert not trend_analysis.data.empty
        assert len(trend_analysis.data) == 1
        mock_client.get_candles.assert_called_once()
    
    @patch('consumer.prompts.RESTClient')
    def test_fetch_data_api_exception(self, mock_rest_client_class, trend_analysis):
        """Test data fetching with API exception"""
        mock_client = Mock()
        mock_rest_client_class.return_value = mock_client
        mock_client.get_candles.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            trend_analysis.fecth_data()
    
    def test_process_stock_update_empty_data(self, trend_analysis):
        """Test processing with empty data"""
        trend_analysis.data = pd.DataFrame()
        
        trend_analysis.process_stock_update()
        
        # Should handle empty data gracefully
        assert trend_analysis.data.empty
    
    def test_process_stock_update_with_data(self, trend_analysis):
        """Test processing with actual data"""
        # Setup test data
        test_data = pd.DataFrame({
            'close': [50000.0, 51000.0, 49000.0, 52000.0, 48000.0],
            'volume': [1000.0, 1100.0, 900.0, 1200.0, 800.0],
            'timestamp': [1704110400, 1704110460, 1704110520, 1704110580, 1704110640]
        })
        trend_analysis.data = test_data
        
        # Execute
        trend_analysis.process_stock_update()
        
        # Verify data was processed
        assert not trend_analysis.rolling_window.empty
        assert trend_analysis.daily_high > 0
        assert trend_analysis.daily_low < float('inf')
        assert len(trend_analysis.rolling_window) == 5
    
    @patch('consumer.prompts.get_llm_manager')
    def test_get_natural_language_insights(self, mock_get_llm_manager, trend_analysis):
        """Test natural language insights generation"""
        # Setup mock
        mock_manager = Mock()
        mock_manager.generate_response.return_value = "BTC-USD shows bullish momentum"
        mock_get_llm_manager.return_value = mock_manager
        
        # Execute
        result = trend_analysis.get_natural_language_insights(
            rolling_avg=50000.0,
            ema=50100.0,
            rsi=65.0,
            bollinger_upper=51000.0,
            bollinger_lower=49000.0,
            price_change=500.0,
            volume_change=100.0,
            daily_high=51500.0,
            daily_low=49500.0,
            buying_momentum=1000.0,
            selling_momentum=500.0
        )
        
        # Verify
        assert result == "BTC-USD shows bullish momentum"
        mock_manager.generate_response.assert_called_once()
    
    def test_calculate_insights_insufficient_data(self, trend_analysis):
        """Test insights calculation with insufficient data"""
        # Setup insufficient data (less than 5 points needed for calculations)
        trend_analysis.rolling_window = pd.DataFrame({
            'close': [50000.0, 51000.0],
            'volume': [1000.0, 1100.0]
        })
        
        # Execute
        result = trend_analysis.calculate_insights()
        
        # Should return None for insufficient data
        assert result is None
    
    @patch('consumer.prompts.get_llm_manager')
    def test_calculate_insights_sufficient_data(self, mock_get_llm_manager, trend_analysis):
        """Test insights calculation with sufficient data"""
        # Setup sufficient data
        trend_analysis.rolling_window = pd.DataFrame({
            'close': [50000.0, 51000.0, 49000.0, 52000.0, 48000.0, 53000.0],
            'volume': [1000.0, 1100.0, 900.0, 1200.0, 800.0, 1300.0]
        })
        trend_analysis.price_change = 1000.0
        trend_analysis.volume_change = 100.0
        trend_analysis.daily_high = 53000.0
        trend_analysis.daily_low = 48000.0
        trend_analysis.buying_momentum = 2000.0
        trend_analysis.selling_momentum = 1000.0
        
        # Setup mock
        mock_manager = Mock()
        mock_manager.generate_response.return_value = "Market analysis complete"
        mock_get_llm_manager.return_value = mock_manager
        
        # Execute
        result = trend_analysis.calculate_insights()
        
        # Verify
        assert result == "Market analysis complete"
        mock_manager.generate_response.assert_called_once()

    @patch('consumer.prompts.get_llm_manager')
    def test_calculate_insights_llm_exception(self, mock_get_llm_manager, trend_analysis):
        """Test insights calculation with LLM exception"""
        # Setup sufficient data
        trend_analysis.rolling_window = pd.DataFrame({
            'close': [50000.0, 51000.0, 49000.0, 52000.0, 48000.0, 53000.0],
            'volume': [1000.0, 1100.0, 900.0, 1200.0, 800.0, 1300.0]
        })
        
        # Setup mock to raise exception
        mock_manager = Mock()
        mock_manager.generate_response.side_effect = Exception("LLM Error")
        mock_get_llm_manager.return_value = mock_manager
        
        # Execute and verify exception propagates
        with pytest.raises(Exception, match="LLM Error"):
            trend_analysis.calculate_insights()