import os
import boto3
import joblib
import logging
import sys
import json
from sklearn.datasets import load_svmlight_file

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

def download_model(s3_client, bucket, model_s3_key, local_path):
    try:
        logger.info(f"Downloading model from s3://{bucket}/{model_s3_key} ...")
        s3_client.download_file(bucket, model_s3_key, local_path)
        logger.info("Model downloaded.")
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        raise

def load_model(local_path):
    try:
        logger.info(f"Loading model from {local_path} ...")
        model = joblib.load(local_path)
        logger.info("Model loaded.")
        return model
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise

def load_input_data(input_path):
    try:
        X, y = load_svmlight_file(input_path)
        logger.info(f"Loaded {X.shape[0]} samples.")
        return X, y
    except Exception as e:
        logger.error(f"Error loading input data: {e}")
        return None, None

def save_predictions(preds, output_path):
    try:
        logger.info(f"Saving predictions to {output_path} ...")
        with open(output_path, "w") as f:
            for p in preds:
                f.write(f"{p}\n")
        logger.info("Predictions saved.")
    except Exception as e:
        logger.error(f"Error saving predictions: {e}")
        raise

def main():
    try:
        # Environment/config
        bucket = os.environ['S3_BUCKET']
        model_s3_key = os.environ['MODEL_S3_KEY']  # e.g. "my/path/to/model.joblib"
        input_data_path = os.environ.get('INPUT_DATA_PATH', 'predict.libsvm')
        output_path = os.environ.get('OUTPUT_PATH', 'predictions.txt')

        s3_client = boto3.client('s3')
        local_model_path = "model.joblib"

        # Download model from S3
        download_model(s3_client, bucket, model_s3_key, local_model_path)

        # Load model
        model = load_model(local_model_path)

        # Load input data
        X, y = load_input_data(input_data_path)

        # Make predictions
        logger.info("Making predictions ...")
        if hasattr(model, "predict_proba"):
            preds = model.predict_proba(X)[:, 1]
        else:
            preds = model.predict(X)
        save_predictions(preds, output_path)
        logger.info("Prediction complete!")

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()