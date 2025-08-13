FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    numpy==1.23.5 \
    scikit-learn==1.2.2 \
    joblib==1.2.0 \
    boto3==1.26.137 \
    fastapi==0.110.0 \
    uvicorn==0.29.0

# Copy all Python scripts in the tasks directory
COPY ./processing/tasks/*.py /app/
WORKDIR /app

# Default command (can be overridden at runtime)
CMD ["python", "train_scikit.py"]