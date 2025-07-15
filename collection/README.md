# Collection Pipeline

This directory contains the AWS Lambda serverless functions, utilities, and tests for the data collection component of the trading platform.

## Structure

```
serverless/collection/
├── functions/                # Lambda function source code
│   ├── consumer/             # Data collection handlers
│   │   ├── candle_stick.py   # Handles candlestick data ingestion (CSV format)
│   │   ├── handler.py        # Main Lambda handler for SQS events
│   │   └── position.py       # Handles position/order data ingestion (libsvm format)
│   └── utils/                # Shared utilities
│       ├── api_client.py     # Assistant API client
│       ├── common.py         # Environment and S3 helpers
│       ├── exceptions.py     # Custom exceptions
│       ├── logger.py         # Structlog logger config
│       ├── oauth.py          # OAuth token management and caching
│       └── sqs.py            # SQS message helpers
├── tests/                    # Unit and functional tests
│   ├── unit/                 # Unit tests for data and train modules
│   └── functional/           # (empty) Placeholder for functional tests
├── requirements.txt          # Python dependencies (compiled)
├── requirements.in           # Python dependencies (source)
├── requirements-dev.txt      # Dev dependencies (compiled)
├── requirements-dev.in       # Dev dependencies (source)
├── package.json              # Node.js dependencies for Serverless plugins
├── serverless.yml            # Serverless Framework deployment config
├── slsenvs.yml               # Environment variable mappings for dev/prod
├── pytest.ini                # Pytest configuration and test env vars
├── .coveragerc               # Coverage.py config
├── .python-version           # Python version pin
```

## Key Components

- **Lambda Functions:**  
  - `handler.py`: Main entrypoint for SQS-triggered data collection.
  - `candle_stick.py`: Handles candlestick data, saves as CSV to S3.
  - `position.py`: Handles position/order data, saves as libsvm to S3.

- **Utilities:**  
  - Logging, OAuth token caching, SQS helpers, and environment management.

- **Testing:**  
  - Unit tests for data processing and training logic using pytest and moto for AWS mocking.

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
- `COINBASE_API_KEY` / `COINBASE_API_SECRET`
- `AUTH0_ASSISTANT_CLIENT_ID` / `AUTH0_ASSISTANT_CLIENT_SECRET`
- `AUTH0_ASSISTANT_AUDIENCE`
- `ASSISTANT_API_KEY`
- `AUTH0_OAUTH_URL`
- `CACHE_TABLE_NAME`

## Testing

- Uses `pytest` and `moto` for AWS mocking.
- Test data and fixtures are in `tests/unit/data/` and `tests/unit/train/`.

## Notes

- Candlestick data is stored in CSV format in S3.
- Position/order data is stored in libsvm format in S3.
- Logging is handled with `structlog` and outputs JSON for easy ingestion.

---
```# Collection

This directory contains the AWS Lambda serverless functions, utilities, and tests for the data collection component of the trading platform.

## Structure

```
serverless/collection/
├── functions/                # Lambda function source code
│   ├── consumer/             # Data collection handlers
│   │   ├── candle_stick.py   # Handles candlestick data ingestion (CSV format)
│   │   ├── handler.py        # Main Lambda handler for SQS events
│   │   └── position.py       # Handles position/order data ingestion (libsvm format)
│   └── utils/                # Shared utilities
│       ├── api_client.py     # Assistant API client
│       ├── common.py         # Environment and S3 helpers
│       ├── exceptions.py     # Custom exceptions
│       ├── logger.py         # Structlog logger config
│       ├── oauth.py          # OAuth token management and caching
│       └── sqs.py            # SQS message helpers
├── tests/                    # Unit and functional tests
│   ├── unit/                 # Unit tests for data and train modules
│   └── functional/           # (empty) Placeholder for functional tests
├── requirements.txt          # Python dependencies (compiled)
├── requirements.in           # Python dependencies (source)
├── requirements-dev.txt      # Dev dependencies (compiled)
├── requirements-dev.in       # Dev dependencies (source)
├── package.json              # Node.js dependencies for Serverless plugins
├── serverless.yml            # Serverless Framework deployment config
├── slsenvs.yml               # Environment variable mappings for dev/prod
├── pytest.ini                # Pytest configuration and test env vars
├── .coveragerc               # Coverage.py config
├── .python-version           # Python version pin
```

## Key Components

- **Lambda Functions:**  
  - `handler.py`: Main entrypoint for SQS-triggered data collection.
  - `candle_stick.py`: Handles candlestick data, saves as CSV to S3.
  - `position.py`: Handles position/order data, saves as libsvm to S3.

- **Utilities:**  
  - Logging, OAuth token caching, SQS helpers, and environment management.

- **Testing:**  
  - Unit tests for data processing and training logic using pytest and moto for AWS mocking.

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
- `COINBASE_API_KEY` / `COINBASE_API_SECRET`
- `AUTH0_ASSISTANT_CLIENT_ID` / `AUTH0_ASSISTANT_CLIENT_SECRET`
- `AUTH0_ASSISTANT_AUDIENCE`
- `ASSISTANT_API_KEY`
- `AUTH0_OAUTH_URL`
- `CACHE_TABLE_NAME`

## Testing

- Uses `pytest` and `moto` for AWS mocking.
- Test data and fixtures are in `tests/unit/data/` and `tests/unit/train/`.

## Notes

- Candlestick data is stored in CSV format in S3.
- Position/order data is stored in libsvm format in S3.
- Logging is handled with `structlog` and outputs JSON for easy ingestion.

---
