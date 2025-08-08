import os
import time
import boto3
import json
import pandas as pd

from enum import Enum

from utils.logger import logger
from utils.api_client import notify_assistant
from utils.common import Env
from coinbase.rest import RESTClient
from datetime import datetime, timedelta
from utils.model_client import get_llm_manager
from consumer.templates import PROMPT_REGISTRY




# Feature engineering module
def compute_features(data):
    """
    Calculate rolling average, EMA, RSI, Bollinger Bands, price/volume change,
    daily high/low, and momentum features from the input DataFrame.
    Assumes 'close' and 'volume' columns exist and are floats.
    """
    features = {}

    if data.empty or len(data) < 5:
        # Not enough data for most calculations
        return {
            "rolling_avg": None,
            "ema": None,
            "rsi": None,
            "bollinger_upper": None,
            "bollinger_lower": None,
            "price_change": None,
            "volume_change": None,
            "daily_high": None,
            "daily_low": None,
            "buying_momentum": None,
            "selling_momentum": None,
        }

    # 5-period rolling average
    features["rolling_avg"] = data['close'].rolling(window=5).mean().iloc[-1]

    # Exponential Moving Average (EMA)
    features["ema"] = data['close'].ewm(span=5, adjust=False).mean().iloc[-1]

    # Bollinger Bands (5-period window)
    std = data['close'].rolling(window=5).std().iloc[-1]
    features["bollinger_upper"] = features["rolling_avg"] + (2 * std)
    features["bollinger_lower"] = features["rolling_avg"] - (2 * std)

    # RSI calculation (14-period typical)
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14, min_periods=1).mean().iloc[-1]
    avg_loss = loss.rolling(window=14, min_periods=1).mean().iloc[-1]
    rs = avg_gain / avg_loss if avg_loss != 0 else float('nan')
    features["rsi"] = 100 - (100 / (1 + rs))

    # Price and volume change (last two points)
    if len(data) >= 2:
        features["price_change"] = data['close'].iloc[-1] - data['close'].iloc[-2]
        features["volume_change"] = data['volume'].iloc[-1] - data['volume'].iloc[-2]
    else:
        features["price_change"] = None
        features["volume_change"] = None

    # Daily high and low
    features["daily_high"] = data['close'].max()
    features["daily_low"] = data['close'].min()

    # Simple momentum calculation (can be customized)
    features["buying_momentum"] = gain.sum()
    features["selling_momentum"] = loss.sum()

    return features


def fetch_data(product_id):
        """ Fetch stock data from Yahoo Finance """
        _now = datetime.now()
        one_day_ago = _now - timedelta(days=1)
        # convert to unix timestamp
        one_day_ago = int(one_day_ago.timestamp())
        _now = int(_now.timestamp())
        coinbase_client = RESTClient(Env.COINBASE_API_KEY, Env.COINBASE_API_SECRET)
        coinbase_data = coinbase_client.get_candles(product_id, start=one_day_ago, end=_now, granularity=2)
        coinbase_data = [candle.to_dict() for candle in coinbase_data["candles"]]
        return pd.DataFrame(coinbase_data)


class Prompt(Enum):
    """ Enum to define different prompts """
    TREND_ANALYSIS = "trend_analysis"


class ContextBuilder:
    """Generic context builder for any prompt type."""
    def __init__(self, product_id, prompt_type):
        self.product_id = product_id
        self.prompt_type = prompt_type

    def build(self):
        data = fetch_data(self.product_id)
        if self.prompt_type == Prompt.TREND_ANALYSIS.value:
            features = compute_features(data)
            return {"product_id": self.product_id, **features}
        # Add more prompt types here as needed
        return {"product_id": self.product_id}


class PromptBuilder:
    def __init__(self, template, context):
        self.template = template
        self.context = context

    def build(self):
        return self.template.render(**self.context)


class PromptEngine:
    def __init__(self, llm_manager):
        self.llm_manager = llm_manager

    def render_prompt(self, prompt_type, context):
        template = PROMPT_REGISTRY[prompt_type]
        builder = PromptBuilder(template, context)
        return builder.build()

    def send_prompt(self, prompt_type, context, model="default_bedrock"):
        prompt_text = self.render_prompt(prompt_type, context)
        # Log prompt, context, and metadata
        logger.info("LLM_PROMPT_SENT", prompt_type=prompt_type, prompt=prompt_text, context=context)
        response = self.llm_manager.generate_response(model, prompt_text)
        # Log response
        logger.info("LLM_RESPONSE_RECEIVED", response=response)
        return response



def prompt_handler(event, context):
    """Process and analyze data based on the scheduler and prompt type."""
    record = event["Records"][0] or {}
    body = json.loads(record["body"])

    correlation_id = body.get("correlation_id")
    product_id = body.get("product_id")
    prompt_type = body.get("prompt")
    logger.info(f"Processing data for product: {product_id}")
    if not correlation_id:
        logger.error("Correlation ID is required")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Correlation ID is required"})
        }

    if prompt_type not in PROMPT_REGISTRY:
        logger.error("Unsupported prompt type")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Unsupported prompt type"})
        }
    if not product_id:
        logger.error("Product ID is required")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Product ID is required"})
        }

    # Build context and generate insights
    context_builder = ContextBuilder(product_id, prompt_type)
    prompt_context = context_builder.build()
    prompt_engine = PromptEngine(get_llm_manager())

    try:
        insights_summary = prompt_engine.send_prompt(prompt_type, prompt_context)
    except Exception as e:
        logger.error(
            "LLM_ANALYSIS_EXCEPTION",
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

    logger.info("LLM_INSIGHTS_COMPLETED", message=insights_summary)

    return {
        "statusCode": 200
    }
