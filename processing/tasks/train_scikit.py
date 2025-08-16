import os
import time
import json
import boto3
from sklearn.datasets import load_svmlight_file
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
import joblib
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


def create_random_forest_estimator(estimators=100, max_depth=5, random_state=42):
    """Creates a RandomForestClassifier model with the given hyperparameters."""
    return RandomForestClassifier(
        n_estimators=estimators,
        max_depth=max_depth,
        random_state=random_state
    )

def get_config():
    try:
        config = {
            "bucket": os.environ['S3_BUCKET'],
            "s3_key": os.environ['S3_KEY'],
            "provider": os.environ['PROVIDER'],
            "product_id": os.environ['PRODUCT_ID'],
            "correlation_id": os.environ['CORRELATION_ID'],
            "hyperparams": {
                'max_depth': int(os.environ.get('HYPERPARAM_MAX_DEPTH', '6')),
                'learning_rate': float(os.environ.get('HYPERPARAM_ETA', '0.1')),
                'gamma': float(os.environ.get('HYPERPARAM_GAMMA', '1')),
                'min_child_weight': int(os.environ.get('HYPERPARAM_MIN_CHILD_WEIGHT', '1')),
                'subsample': float(os.environ.get('HYPERPARAM_SUBSAMPLE', '0.8')),
                'colsample_bytree': float(os.environ.get('HYPERPARAM_COLSAMPLE_BYTREE', '0.8')),
                'objective': os.environ.get('HYPERPARAM_OBJECTIVE', 'binary:logistic'),
                'eval_metric': os.environ.get('HYPERPARAM_EVAL_METRIC', 'auc'),
                'n_estimators': int(os.environ.get('HYPERPARAM_NUM_ROUND', '100')),
                'early_stopping_rounds': int(os.environ.get('HYPERPARAM_EARLY_STOPPING', '10')),
                'tree_method': 'hist',
                'verbosity': 1,
                'n_jobs': -1,
                'random_state': 42,
            }
        }
        return config
    except KeyError as e:
        logger.error(f"Missing required environment variable: {e}")
        raise

def download_data(s3_client, bucket, s3_key):
    try:
        logger.info("📥 Downloading training data...")
        train_local = 'train.libsvm'
        val_local = 'validation.libsvm'
        s3_client.download_file(bucket, f"{s3_key}/train/train.libsvm", train_local)
        s3_client.download_file(bucket, f"{s3_key}/validation/validation.libsvm", val_local)
        return train_local, val_local
    except Exception as e:
        logger.error(f"Error downloading data from S3: {e}")
        raise

def load_data(train_local, val_local):
    try:
        logger.info("📊 Loading training data...")
        X_train, y_train = load_svmlight_file(train_local)
        X_val, y_val = load_svmlight_file(val_local)
        logger.info(f"Training samples: {X_train.shape[0]}, Features: {X_train.shape[1]}")
        logger.info(f"Validation samples: {X_val.shape[0]}")
        return X_train, y_train, X_val, y_val
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return None, None, None, None

def train_model(X_train, y_train, X_val, y_val, hyperparams, model_class):
    """
    Trains a model using the provided model_class (e.g., sklearn.ensemble.RandomForestClassifier, etc.)
    """
    try:
        logger.info(f"🔥 Training model: {model_class.__name__} ...")
        model = model_class(**hyperparams)
        # scikit-learn estimators do not use eval_set or eval_names
        model.fit(X_train, y_train)
        return model
    except Exception as e:
        logger.error(f"Error during model training: {e}")
        raise

def evaluate_model(model, X_train, y_train, X_val, y_val):
    try:
        logger.info("📈 Evaluating model...")
        train_preds = model.predict_proba(X_train)[:, 1]
        val_preds = model.predict_proba(X_val)[:, 1]
        train_pred_binary = (train_preds > 0.5).astype(int)
        val_pred_binary = (val_preds > 0.5).astype(int)
        train_accuracy = accuracy_score(y_train, train_pred_binary)
        val_accuracy = accuracy_score(y_val, val_pred_binary)
        train_auc = roc_auc_score(y_train, train_preds)
        val_auc = roc_auc_score(y_val, val_preds)
        cm = confusion_matrix(y_val, val_pred_binary)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
        feature_importance = model.feature_importances_
        logger.info("📊 Training Results:")
        logger.info(f"  Train Accuracy: {train_accuracy:.4f}")
        logger.info(f"  Validation Accuracy: {val_accuracy:.4f}")
        logger.info(f"  Train AUC: {train_auc:.4f}")
        logger.info(f"  Validation AUC: {val_auc:.4f}")
        logger.info(f"  Best Iteration: {model.best_iteration}")
        logger.info(f"  Confusion Matrix - TP: {tp}, TN: {tn}, FP: {fp}, FN: {fn}")
        return {
            "train_accuracy": train_accuracy,
            "val_accuracy": val_accuracy,
            "train_auc": train_auc,
            "val_auc": val_auc,
            "confusion_matrix": {"true_positive": int(tp), "true_negative": int(tn), "false_positive": int(fp), "false_negative": int(fn)},
            "feature_importance": feature_importance,
            "best_iteration": int(model.best_iteration),
        }
    except Exception as e:
        logger.error(f"Error during model evaluation: {e}")
        return {"error": str(e)}

def save_and_upload_model(s3_client, model, bucket, s3_key, model_version=None):
    try:
        logger.info("Saving model...")
        version_str = f"_v{model_version}" if model_version else ""
        model_filename = f"xgb_model{version_str}.joblib"
        joblib.dump(model, model_filename)
        model_s3_key = f"{s3_key}/trained_model/xgb_model{version_str}.joblib"
        s3_client.upload_file(model_filename, bucket, model_s3_key)
        return model_s3_key
    except Exception as e:
        logger.error(f"Error saving/uploading model: {e}")
        raise

def save_and_upload_results(s3_client, results, bucket, s3_key):
    try:
        results_filename = 'training_results.json'
        with open(results_filename, 'w') as f:
            json.dump(results, f, indent=2)
        results_s3_key = f"{s3_key}/trained_model/training_results.json"
        s3_client.upload_file(results_filename, bucket, results_s3_key)
        return results_s3_key
    except Exception as e:
        logger.error(f"Error saving/uploading results: {e}")
        raise

def main():
    try:
        start_time = time.time()
        config = get_config()
        model_version = os.environ.get('MODEL_VERSION')
        logger.info(f"🚀 Starting training for {config['provider']}/{config['product_id']}")
        logger.info(f"📊 Hyperparameters: {json.dumps(config['hyperparams'], indent=2)}")
        s3_client = boto3.client('s3')
        train_local, val_local = download_data(s3_client, config['bucket'], config['s3_key'])
        X_train, y_train, X_val, y_val = load_data(train_local, val_local)

        estimator = create_random_forest_estimator(
            estimators=config['hyperparams'].get('n_estimators', 100),
            max_depth=config['hyperparams'].get('max_depth', 5),
            random_state=config['hyperparams'].get('random_state', 42)
        )

        model = train_model(X_train, y_train, X_val, y_val, config['hyperparams'], estimator)
        training_time = time.time() - start_time
        metrics = evaluate_model(model, X_train, y_train, X_val, y_val)
        model_s3_key = save_and_upload_model(s3_client, model, config['bucket'], config['s3_key'], model_version=model_version)
        results = {
            'provider': config['provider'],
            'product_id': config['product_id'],
            'correlation_id': config['correlation_id'],
            'training_time_seconds': training_time,
            'train_accuracy': float(metrics['train_accuracy']),
            'val_accuracy': float(metrics['val_accuracy']),
            'train_auc': float(metrics['train_auc']),
            'val_auc': float(metrics['val_auc']),
            'confusion_matrix': metrics['confusion_matrix'],
            'hyperparameters': config['hyperparams'],
            'model_s3_path': f"s3://{config['bucket']}/{model_s3_key}",
            'best_iteration': metrics['best_iteration'],
            'feature_count': int(X_train.shape[1]),
            'training_samples': int(X_train.shape[0]),
            'validation_samples': int(X_val.shape[0])
        }
        results_s3_key = save_and_upload_results(s3_client, results, config['bucket'], config['s3_key'])
        logger.info(f"🎉 Training completed successfully!")
        logger.info(f"📁 Model saved to: s3://{config['bucket']}/{model_s3_key}")
        logger.info(f"📊 Results saved to: s3://{config['bucket']}/{results_s3_key}")
    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
