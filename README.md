# trader-data

## Project Overview:

 Modular platform for collecting, processing, and analyzing trading data using serverless AWS infrastructure, and LLMs. It demonstrates cloud-native design, scalable ML workflows, and modern DevOps practices.

## 🚀 Quick Start

For deployment instructions, environment setup, and configuration details, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Repository Structure

```
trader-data/
├── collection/             # Data collection serverless functions
│   ├── handler.py          # Lambda handlers for data collection
│   ├── serverless.yml      # Serverless deployment configuration
│   ├── slsenvs.yml         # Environment variables
│   └── requirements.txt    # Python dependencies
├── llm/                    # LLM integration serverless functions  
│   ├── serverless.yml      # Serverless deployment configuration
│   ├── slsenvs.yml         # Environment variables
│   └── requirements.txt    # Python dependencies
├── processing/             # Data processing and ML serverless functions
│   ├── consumer/           # ECS orchestration handlers
│   ├── functions/          # Data processing and ML functions
│   ├── task/               # Containerized ML tasks
│   ├── tests/              # Unit and integration tests
│   ├── utils/              # Shared utilities
│   ├── serverless.yml      # Serverless deployment configuration
│   ├── slsenvs.yml         # Environment variables
│   └── Dockerfile          # Container image for ML tasks
├── .github/workflows/      # CI/CD GitHub Actions workflows
├── run                     # Project management and deployment script
├── DEPLOYMENT.md           # Detailed deployment guide
├── SECURITY.md             # Security policies and practices
└── README.md               # This documentation
```

## Key Components

- **Data Collection Service** (`collection/`): 
  - Serverless functions for collecting market data from various APIs
  - Automated data ingestion and storage to S3
  - Integration with external data providers

- **LLM Service** (`llm/`): 
  - Integration with Large Language Models (Ollama, OpenAI, etc.)
  - Natural language processing for market analysis
  - Chat interfaces for trading insights

- **Data Processing Service** (`processing/`):
  - Candlestick pattern detection and technical analysis
  - Machine learning model training and prediction
  - ECS-based containerized processing workflows
  - PySpark integration for large-scale data processing

- **Infrastructure**: 
  - Serverless AWS architecture with Lambda, ECS, S3, and DynamoDB
  - Infrastructure as Code with Serverless Framework
  - CI/CD pipelines with GitHub Actions

## Setup

### Prerequisites

- Python 3.10+
- Docker (for local development and deployment)
- AWS CLI (for deploying serverless functions)
- [Serverless Framework](https://www.serverless.com/) (for Lambda deployment)

### Installation

1. **Clone the repository:**
    ```sh
    git clone https://github.com/yourusername/trader-data.git
    cd trader-data
    ```

2. **Install dependencies for each service:**
    ```sh
    # Data collection service
    cd collection/
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    npm install
    cd ..

    # LLM service
    cd llm/
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    npm install
    cd ..

    # Processing service
    cd processing/
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    npm install
    cd ..
    ```

3. **Set up environment variables:**
    ```sh
    cp .env.example .env.local
    # Edit .env.local with your AWS account details
    source .env.local
    ```

4. **Configure AWS credentials:**
    ```sh
    aws configure
    # or export AWS credentials as environment variables
    ```

## Usage

### Local Development

**Run tests for each service:**
```sh
# Test collection service
cd collection/
pytest

# Test LLM service
cd ../llm/
pytest

# Test processing service
cd ../processing/
pytest
```

**Build and test Docker containers:**
```sh
cd processing/
docker build -t TAGNAME -f task/Dockerfile .
docker run --env-file .env.local TAGNAME
```

### Deployment

**Deploy individual services:**
```sh
# Using the run script (sets up dependencies automatically)
ENV=dev REGION=us-east-2 DEPLOYMENT_BUCKET=my-bucket ./run deploy-service collection
ENV=dev REGION=us-east-2 DEPLOYMENT_BUCKET=my-bucket ./run deploy-service llm
ENV=dev REGION=us-east-2 DEPLOYMENT_BUCKET=my-bucket ./run deploy-service processing

# Or deploy manually with serverless
cd collection/
sls deploy --stage dev --param="deployment-bucket=my-deployment-bucket"
```

**Deploy all services:**
```sh
# Deploy everything (see DEPLOYMENT.md for detailed instructions)
./scripts/deploy-all.sh dev
```

## Features

### 📊 Data Collection & Processing
- **Multi-source Data Ingestion**: Collect market data from various APIs (Coinbase, etc.)
- **Real-time Processing**: Stream processing capabilities for live market data
- **Technical Analysis**: Candlestick pattern detection and technical indicators
- **Data Storage**: Efficient S3-based data lake with partitioned storage

### 🤖 Machine Learning & AI
- **ML Model Training**: Automated model training with PySpark on ECS
- **Prediction Services**: Real-time prediction APIs for trading signals
- **LLM Integration**: Natural language interface for market analysis
- **Pattern Recognition**: Advanced algorithmic pattern detection

### ☁️ Cloud-Native Architecture
- **Serverless Functions**: AWS Lambda for scalable event-driven processing
- **Container Orchestration**: ECS for ML training and batch processing
- **Infrastructure as Code**: Serverless Framework deployment
- **Auto-scaling**: Dynamic scaling based on demand

### 🔒 Security & Compliance
- **Secrets Management**: AWS SSM Parameter Store for sensitive data
- **IAM Integration**: Fine-grained access control
- **Encryption**: Data encryption in transit and at rest
- **Audit Logging**: Comprehensive logging for compliance

## Key Services

### Data Collection Service (`collection/`)
- Automated market data collection from external APIs
- Configurable data sources and collection intervals
- Error handling and retry mechanisms
- Data validation and cleansing

### LLM Service (`llm/`)
- Integration with Ollama, OpenAI, and other LLM providers
- Natural language queries for market data
- Automated report generation
- Chat interfaces for trading insights

### Processing Service (`processing/`)
- Candlestick pattern detection and analysis
- Machine learning model training and inference
- Large-scale data processing with PySpark
- ECS-based containerized workflows

## About the Author

This project provides a comprehensive data collection and processing system for financial market analysis.  
Key skills demonstrated:
- Cloud architecture (AWS Lambda, S3, ECS)
- Python (PySpark, Pandas)
- Machine Learning (feature engineering, model training)
- DevOps (CI/CD, Docker, Serverless Framework, Terraform)
- LLM integration (Ollama, Hugging Face, OpenAI API)

## Future Enhancements

### 🔮 Planned Features

#### Data & Analytics
- **Real-time Data Streaming**: Implement Kinesis Data Streams for live market data ingestion
- **Advanced Pattern Recognition**: Expand candlestick pattern detection with ML-based pattern discovery
- **Multi-Asset Support**: Extend beyond crypto to support stocks, forex, and commodities
- **Historical Data Warehouse**: Implement data lake architecture with partitioned historical data

#### Machine Learning & AI
- **Automated Model Training**: Scheduled retraining pipelines with performance monitoring
- **Ensemble Models**: Combine multiple ML models for improved prediction accuracy
- **Reinforcement Learning**: RL agents for dynamic trading strategy optimization
- **Sentiment Analysis**: Integration with news and social media sentiment data
- **Custom LLM Fine-tuning**: Fine-tune models on trading-specific datasets

#### Infrastructure & Scalability
- **Kubernetes Migration**: Transition from ECS to EKS for better container orchestration
- **Multi-Region Deployment**: Global deployment for reduced latency and high availability
- **Auto-Scaling**: Dynamic scaling based on market volatility and data volume
- **Cost Optimization**: Implement Spot instances and reserved capacity for cost reduction

#### Security & Compliance
- **Zero-Trust Architecture**: Enhanced security with service mesh and mTLS
- **Audit Logging**: Comprehensive audit trails for all trading decisions
- **Compliance Reporting**: Automated compliance reports for regulatory requirements
- **Encryption at Rest**: End-to-end encryption for all sensitive data

#### Monitoring & Observability
- **Distributed Tracing**: OpenTelemetry integration for request tracing
- **Custom Metrics**: Business-specific metrics and alerting
- **Performance Analytics**: Latency and throughput optimization
- **Health Checks**: Comprehensive health monitoring with automatic recovery

### 🤝 Contributing

We welcome contributions! Areas where help is needed:
- **Documentation**: Improve setup guides and API documentation
- **Testing**: Expand test coverage and add integration tests
- **Performance**: Optimize data processing and ML inference
- **Features**: Implement any of the planned enhancements above
