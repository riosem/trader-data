# trader-data-llm

This directory contains the AWS Lambda serverless functions, utilities, and configuration for the LLM (Large Language Model) integration component of the trading platform.

## Structure

```
llm/
├── consumer/                # Lambda function source code for LLM (e.g., prompts.py)
│   ├── prompts.py           # Module for handling llm prompting
├── tests/                   # Unit and functional tests
│   ├── unit/                # Unit tests for LLM and data processing
│   └── functional/          # Functional tests for LLM integration
├── utils/                   # Shared utilities
│   ├── api_client.py        # Assistant API client and notification logic
│   ├── common.py            # Environment and S3 helpers
│   ├── exceptions.py        # Custom exceptions
│   ├── logger.py            # Structlog logger config
│   ├── oauth.py             # OAuth token management and caching
│   └── sqs.py               # SQS message helpers
├── requirements.txt         # Python dependencies (compiled)
├── requirements.in          # Python dependencies (source)
├── requirements-dev.txt     # Dev dependencies (compiled)
├── requirements-dev.in      # Dev dependencies (source)
├── package.json             # Node.js dependencies for Serverless plugins
├── serverless.yml           # Serverless Framework deployment config
├── slsenvs.yml              # Environment variable mappings for dev/prod
├── pytest.ini               # Pytest configuration and test env vars
├── .coveragerc              # Coverage.py config
├── .python-version          # Python version pin
└── README.md                # This documentation
```

## Key Components

- **Lambda Functions:**  
  - `consumer/prompts.py`: Handles LLM-based analysis of trading data and generates natural language insights.

- **Utilities:**  
  - Logging, OAuth token caching, SQS helpers, and environment management.

- **Testing:**  
  - Unit and functional tests for LLM integration and data processing using pytest and moto for AWS mocking.

- **Deployment:**  
  - Managed via the Serverless Framework (`serverless.yml`), with environment-specific variables in `slsenvs.yml`.

## Usage

### Install dependencies

```sh
pip install -r requirements.txt
pip install -r requirements-dev.txt  # for development/testing
```

### Run tests

```sh
pytest
```

### Deploy to AWS

```sh
sls deploy --stage dev
```

## Environment Variables

Environment variables are managed via `slsenvs.yml` and injected by the Serverless Framework.  
Key variables include:

- `DATA_COLLECTION_BUCKET_NAME`
- `OLLAMA_API_KEY`
- `COINBASE_API_KEY` / `COINBASE_API_SECRET`
- `AUTH0_ASSISTANT_CLIENT_ID` / `AUTH0_ASSISTANT_CLIENT_SECRET`
- `AUTH0_ASSISTANT_AUDIENCE`
- `ASSISTANT_API_KEY`
- `AUTH0_OAUTH_URL`
- `CACHE_TABLE_NAME`
- ECS cluster and node configuration

## Prompting and LLM Integration

The LLM integration is designed to process prompts for advanced trading analytics and insights. The main Lambda handler (`consumer/prompts.py`) receives prompt requests (typically via SQS), fetches relevant trading data, and uses an LLM (such as AWS Bedrock or Ollama) to generate natural language insights.

### Prompt Workflow

1. **Event Trigger:**  
   An SQS message or API event triggers the Lambda function with a payload containing a `prompt` type (e.g., `"trend_analysis"`), `product_id`, and `correlation_id`.

2. **Data Fetching:**  
   The handler fetches recent trading data (e.g., candlestick data) for the specified product.

3. **Feature Calculation:**  
   The handler computes technical indicators (rolling averages, EMA, RSI, Bollinger Bands, etc.) and market features.

4. **Prompt Construction:**  
   A detailed prompt is constructed for the LLM, including all relevant statistics and context.

5. **LLM Call:**  
   The prompt is sent to the configured LLM provider (AWS Bedrock, Ollama, etc.) using the `LLMManager` abstraction in `utils/model_client.py`.

6. **Insight Generation:**  
   The LLM returns a concise, human-readable summary or insight, which is then sent as a notification (e.g., to a Discord assistant or other channel).

### Example Prompt Payload

```json
{
  "correlation_id": "abc-123",
  "product_id": "BTC-USD",
  "prompt": "trend_analysis"
}
```

### Example LLM Prompt (auto-generated)

```
You are a professional stock broker. BTC-USD stock has a 5-minute rolling average of 50000.00.
The Exponential Moving Average (EMA) is 50100.00, and the Relative Strength Index (RSI) is 65.00.
The Bollinger Bands are set with an upper band of 51000.00 and a lower band of 49000.00.
The price has changed by 500.00, and the volume has shifted by 100.00.
Today's high was 51500.00 and low was 49500.00.
The buying momentum is 1000.00 and selling momentum is 500.00.
Based on this data, provide insights into the current stock trend and the general market sentiment.
The insights should not be longer than 100 words, should not have an introduction, and should include the name of the stock.
```

### Supported Prompts

- `trend_analysis`: Generates a technical and natural language summary of recent trading activity for a given product.

To add new prompt types, extend the `Prompt` enum and implement the corresponding handler logic in `consumer/prompts.py`.

## Testing

- Uses `pytest` and `moto` for AWS mocking.
- Test data and fixtures are in `tests/unit/`.

---