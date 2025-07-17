import os
import time
import boto3
import json
import pandas as pd


from utils.logger import logger
from utils.api_client import notify_assistant
from utils.common import Env
from coinbase.rest import RESTClient
from datetime import datetime, timedelta
from utils.model_client import get_llm_manager


# Global variables to store rolling data
class TrendAnalysis:
    """ Class to handle the analysis of stock data """
    data = pd.DataFrame()
    rolling_window = pd.DataFrame()
    daily_high = float('-inf')
    daily_low = float('inf')
    buying_momentum = 0
    selling_momentum = 0

    def __init__(self, product_id):
        self.product_id = product_id
        self.llm_manager = get_llm_manager()

    def fecth_data(self):
        """ Fetch stock data from Yahoo Finance """
        _now = datetime.now()
        one_day_ago = _now - timedelta(days=1)
        # convert to unix timestamp
        one_day_ago = int(one_day_ago.timestamp())
        _now = int(_now.timestamp())
        coinbase_client = RESTClient(Env.COINBASE_API_KEY, Env.COINBASE_API_SECRET)
        coinbase_data = coinbase_client.get_candles(self.product_id, start=one_day_ago, end=_now, granularity=2)
        coinbase_data = [candle.to_dict() for candle in coinbase_data["candles"]]
        self.data = pd.DataFrame(coinbase_data)
        logger.info("Successfully retreived data from Coinbase API")

    def process_stock_update(self):
        """ Process a new stock update"""
        if self.data.empty:
            logger.info("No data to process")
            return

        self.data['close'] = self.data['close'].astype('float')
        self.data['volume'] = self.data['volume'].astype('float')

        # if not data.empty and not dow_data.empty:
        # Simulate receiving a new data point for AAPL and Dow Jones
        update = self.data.iloc[0].to_frame().T
        # dow_update = dow_data.iloc[0].to_frame().T
        self.data = self.data.iloc[1:]  # Remove the processed row
        # dow_data = dow_data.iloc[1:]

        # Append the new data points to the rolling windows and make sure close column has been converted to float
        self.rolling_window = pd.concat([self.rolling_window, self.data], ignore_index=False)

        # dow_rolling_window = pd.concat([dow_rolling_window, dow_update], ignore_index=False)

        # Update daily high and low
        self.daily_high = max(self.daily_high, float(update['close'].values[0]))
        self.daily_low = min(self.daily_low, float(update['close'].values[0]))

        # Calculate momentum
        if len(self.rolling_window) >= 2:
            last_index = len(self.rolling_window) - 1
            self.price_change = float(update['close'].values[0]) - self.rolling_window['close'].iloc[last_index]
            self.volume_change = float(update['volume'].values[0]) - self.rolling_window['volume'].iloc[last_index]
            if self.price_change > 0 and self.volume_change > 0:
                self.buying_momentum += self.price_change
            else:
                self.selling_momentum += abs(self.price_change)

        logger.info("Successfully processed stock update")

    def get_natural_language_insights(
        self, rolling_avg, ema, rsi, bollinger_upper, bollinger_lower,
        price_change, volume_change, daily_high, daily_low, 
        buying_momentum, selling_momentum
    ):
        """ Get natural language insights from the LLM """
        prompt = f"""
        You are a professional stock broker. {self.product_id} stock has a 5-minute rolling average of {rolling_avg:.2f}.
        The Exponential Moving Average (EMA) is {ema:.2f}, and the Relative Strength Index (RSI) is {rsi:.2f}.
        The Bollinger Bands are set with an upper band of {bollinger_upper:.2f} and a lower band of {bollinger_lower:.2f}.
        The price has changed by {price_change:.2f}, and the volume has shifted by {volume_change}.
        Today's high was {daily_high:.2f} and low was {daily_low:.2f}.
        The buying momentum is {buying_momentum:.2f} and selling momentum is {selling_momentum:.2f}.
        Based on this data, provide insights into the current stock trend and the general market sentiment.
        The insights should not be longer than 100 words, should not have an introduction, 
        and should include the name of the stock.
        """

        return self.llm_manager.generate_response(
            "default_bedrock", 
            prompt,
            temperature=0.7,
            max_tokens=150
        )

    def calculate_insights(self):
        """ Calculate insights based on the stock data """
        if len(self.rolling_window) < 5:
            logger.info(f"Not enough data points to calculate insights, window length: {len(self.rolling_window)}")
            logger.info(self.rolling_window)
            return

        # 5-minute rolling average
        rolling_avg = self.rolling_window['close'].rolling(window=5).mean().iloc[-1]
        
        # Exponential Moving Average (EMA)
        ema = self.rolling_window['close'].ewm(span=5, adjust=False).mean().iloc[-1]
        
        # Bollinger Bands (using a 5-period window)
        std = self.rolling_window['close'].rolling(window=5).std().iloc[-1]
        bollinger_upper = rolling_avg + (2 * std)
        bollinger_lower = rolling_avg - (2 * std)

        # RSI calculation
        delta = self.rolling_window['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14, min_periods=1).mean().iloc[-1]
        avg_loss = loss.rolling(window=14, min_periods=1).mean().iloc[-1]
        rs = avg_gain / avg_loss if avg_loss != 0 else float('nan')
        rsi = 100 - (100 / (1 + rs))

        # Calculate Relative Strength Index (RSI) if there are enough periods (14 is typical)
        delta = self.rolling_window['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14, min_periods=1).mean().iloc[-1]
        avg_loss = loss.rolling(window=14, min_periods=1).mean().iloc[-1]
        rs = avg_gain / avg_loss if avg_loss != 0 else float('nan')
        rsi = 100 - (100 / (1 + rs))

        # # Calculate Dow Jones index rolling average
        # dow_rolling_avg = dow_window['close'].rolling(window=5).mean().iloc[-1]
        
        # market_open_duration = get_market_open_duration(window)
        # if int(market_open_duration) % 5 == 0:  # Trigger LLM every 5 minutes
            
        # get_natural_language_insights(
        #     rolling_avg, ema, rsi, bollinger_upper, bollinger_lower,
        #     price_change, volume_change, dow_rolling_avg, market_open_duration, 
        #     dow_price_change, dow_volume_change, daily_high, daily_low, 
        #     buying_momentum, selling_momentum, timestamp
        # )

        return self.get_natural_language_insights(
            rolling_avg,
            ema,
            rsi,
            bollinger_upper,
            bollinger_lower,
            self.price_change,
            self.volume_change,
            self.daily_high,
            self.daily_low,
            self.buying_momentum,
            self.selling_momentum
        )


def scheduler_handler(event, context):
    """ Here we will process, analysis any data based on the scheduler"""
    record = event["Records"][0] or {}

    body = json.loads(record["body"])

    correlation_id = body.get("correlation_id")
    product_id = body.get("product_id")
    logger.info(f"Processing data for product: {product_id}")

    # For now we will analysis candle stick data for past 24 hours
    process = TrendAnalysis(product_id)
    process.fecth_data()
    process.process_stock_update()

    try:
        insights_summary = process.calculate_insights()
    except Exception as e:
        logger.error(
            "OLLAMA_ANALYSIS_EXCEPTION",
            message="Could not calculate insights",
            error=str(e)
        )
        raise e

    try:
        notify_assistant(correlation_id=correlation_id, message=insights_summary)
    except Exception as e:
        logger.error(
            "NOTIFY_ASSISTANT_MESSAGE_EXCEPTION",
            message="Could not send message to assistant",
            error=str(e)
        )
        raise e

    logger.info("OLLAMA_INSIGHTS_COMPLETED", message=insights_summary)

    return {
        "statusCode": 200
    }
