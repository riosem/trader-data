FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    xgboost==1.7.4 \
    pandas==1.5.3 \
    numpy==1.24.3 \
    boto3==1.26.137 \
    scikit-learn==1.2.2 \
    joblib==1.2.0

COPY ./processing/tasks/train_xgboost_optimized.py /app/
WORKDIR /app

ENTRYPOINT ["python", "train_xgboost_optimized.py"]
