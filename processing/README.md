# Data Processing Service

This directory contains the AWS Lambda serverless functions, orchestration scripts, utilities, and tests for the data processing component of the trading platform.

## Structure

```
serverless/processing/
├── consumer/                # Orchestration handlers for ECS
│   ├── ecs_orchestrate.py   # ECS cluster orchestration and SQS handler
├── functions/               # Data processing and ML functions
│   ├── candle_stick_patterns.py # Candlestick pattern detection logic
│   ├── train_model.py           # PySpark model training script
│   ├── predict_model.py         # PySpark model prediction script
├── task/                    # Containerized training and prediction scripts
│   ├── app.py               # Entrypoint for container
│   ├── train.py             # SageMaker training logic
│   ├── predict.py           # SageMaker prediction logic
│   ├── Dockerfile           # Dockerfile for containerized ML tasks
│   └── .dockerignore        # Docker ignore file
├── tests/                   # Unit and functional tests
│   ├── unit/                # Unit tests for data and ML logic
│   └── functional/          # (empty) Placeholder for functional tests
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

- **Orchestration:**  
  - `consumer/ecs_orchestrate.py`: Handles ECS cluster operations and SQS events.

- **Data Processing & ML:**  
  - `functions/candle_stick_patterns.py`: Implements candlestick pattern detection.
  - `functions/train_model.py`: Trains a PySpark RandomForest model on historical data.
  - `functions/predict_model.py`: Loads a trained model and generates predictions.
  - `task/train.py` & `task/predict.py`: SageMaker-based training and prediction for containerized ML workflows.

- **Utilities:**  
  - Logging, OAuth token caching, SQS helpers, and environment management.

- **Testing:**  
  - Unit tests for data processing and ML logic using pytest and moto for AWS mocking.

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

### Run containerized ML tasks

Build and run the Docker container for local or ECS training:

```sh
docker build -t task -f task/Dockerfile .
docker run --env-file .env task
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
- ECS cluster and service configuration

## Notes

- Candlestick pattern detection is implemented in `functions/candle_stick_patterns.py`.
- Logging is handled with `structlog` and outputs JSON for easy ingestion.
- Test data and fixtures are in `tests/unit/`.

---

For more details on orchestration and ML workflows, see the code and comments in the