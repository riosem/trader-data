# trader-data-llm

This directory contains the AWS Lambda serverless functions, utilities, and configuration for the LLM (Large Language Model) integration component of the trading platform.

## Structure

```
serverless/llm/
├── consumer/                # Lambda function source code for LLM
│   └── ollama_analysis.py   # LLM-based analysis and insights handler
├── ollama/                  # Local Ollama model fine-tuning and inference environment
│   ├── Dockerfile           # Dockerfile for local Ollama environment
│   ├── main.py              # Fine-tuning and inference script for Llama models
│   ├── requirements.txt     # Python dependencies for Ollama
│   ├── README.md            # Ollama usage and troubleshooting
│   └── ...                  # Supporting files and data
├── tests/                   # Unit and functional tests
│   ├── unit/                # Unit tests for LLM and data processing
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

- **Lambda Functions:**  
  - `consumer/ollama_analysis.py`: Handles LLM-based analysis of trading data and generates natural language insights.

- **Ollama Local Environment:**  
  - `ollama/`: Scripts and Dockerfile for running and fine-tuning Llama models locally using Ollama and Hugging Face.

- **Utilities:**  
  - Logging, OAuth token caching, SQS helpers, and environment management.

- **Testing:**  
  - Unit tests for LLM integration and data processing using pytest and moto for AWS mocking.

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

### Ollama Local Fine-Tuning

See [`ollama/README.md`](ollama/README.md) for instructions on building and running the local Ollama environment for Llama model fine-tuning.

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

## Testing

- Uses `pytest` and `moto` for AWS mocking.
- Test data and fixtures are in `tests/unit/`.

## Notes

- LLM analysis is performed using OpenAI-compatible APIs and Hugging Face models.
- OAuth tokens are cached in DynamoDB for efficiency.
- Logging is handled with `structlog` and outputs JSON for easy ingestion.
- Local Ollama environment is for experimentation and not deployed to AWS.

---

For more details on Ollama usage and troubleshooting, see [`ollama/README.md`](ollama/README.md).
