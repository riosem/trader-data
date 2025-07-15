# train_xgboost_optimized.py - High-performance training script
import os
import time
import json
import boto3
import xgboost as xgb
import pandas as pd
import numpy as np
from sklearn.datasets import load_svmlight_file
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix
import joblib

def main():
    start_time = time.time()
    
    # Get configuration from environment
    bucket = os.environ['S3_BUCKET']
    s3_key = os.environ['S3_KEY']
    output_path = os.environ['OUTPUT_PATH']
    provider = os.environ['PROVIDER']
    product_id = os.environ['PRODUCT_ID']
    correlation_id = os.environ['CORRELATION_ID']
    
    print(f"🚀 Starting XGBoost training for {provider}/{product_id}")
    
    # Get hyperparameters from environment
    hyperparams = {
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
        'tree_method': 'hist',  # Faster training method
        'verbosity': 1,
        'n_jobs': -1,  # Use all CPU cores
        'random_state': 42,
    }
    
    print(f"📊 Hyperparameters: {json.dumps(hyperparams, indent=2)}")
    
    # Initialize S3 client
    s3_client = boto3.client('s3')
    
    # Download training data
    print("📥 Downloading training data...")
    train_local = 'train.libsvm'
    val_local = 'validation.libsvm'
    
    s3_client.download_file(bucket, f"{s3_key}/train/train.libsvm", train_local)
    s3_client.download_file(bucket, f"{s3_key}/validation/validation.libsvm", val_local)
    
    # Load data efficiently
    print("📊 Loading training data...")
    X_train, y_train = load_svmlight_file(train_local)
    X_val, y_val = load_svmlight_file(val_local)
    
    print(f"Training samples: {X_train.shape[0]}, Features: {X_train.shape[1]}")
    print(f"Validation samples: {X_val.shape[0]}")
    
    # Train XGBoost model with early stopping
    print("🔥 Training XGBoost model...")
    model = xgb.XGBClassifier(**hyperparams)
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        eval_names=['train', 'val'],
        verbose=True
    )
    
    training_time = time.time() - start_time
    print(f"✅ Training completed in {training_time:.2f} seconds")
    
    # Evaluate model
    print("📈 Evaluating model...")
    train_preds = model.predict_proba(X_train)[:, 1]
    val_preds = model.predict_proba(X_val)[:, 1]
    
    train_pred_binary = (train_preds > 0.5).astype(int)
    val_pred_binary = (val_preds > 0.5).astype(int)
    
    # Calculate metrics
    train_accuracy = accuracy_score(y_train, train_pred_binary)
    val_accuracy = accuracy_score(y_val, val_pred_binary)
    train_auc = roc_auc_score(y_train, train_preds)
    val_auc = roc_auc_score(y_val, val_preds)
    
    # Confusion matrix for validation set
    cm = confusion_matrix(y_val, val_pred_binary)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
    
    # Feature importance
    feature_importance = model.feature_importances_
    
    print("📊 Training Results:")
    print(f"  Train Accuracy: {train_accuracy:.4f}")
    print(f"  Validation Accuracy: {val_accuracy:.4f}")
    print(f"  Train AUC: {train_auc:.4f}")
    print(f"  Validation AUC: {val_auc:.4f}")
    print(f"  Best Iteration: {model.best_iteration}")
    print(f"  Confusion Matrix - TP: {tp}, TN: {tn}, FP: {fp}, FN: {fn}")
    
    # Save model
    print("💾 Saving model...")
    model_filename = 'xgb_model.joblib'
    joblib.dump(model, model_filename)
    
    # Upload model to S3
    model_s3_key = f"{s3_key}/trained_model/xgb_model.joblib"
    s3_client.upload_file(model_filename, bucket, model_s3_key)
    
    # Save training results
    results = {
        'provider': provider,
        'product_id': product_id,
        'correlation_id': correlation_id,
        'training_time_seconds': training_time,
        'train_accuracy': float(train_accuracy),
        'val_accuracy': float(val_accuracy),
        'train_auc': float(train_auc),
        'val_auc': float(val_auc),
        'confusion_matrix': {
            'true_positive': int(tp),
            'true_negative': int(tn),
            'false_positive': int(fp),
            'false_negative': int(fn)
        },
        'hyperparameters': hyperparams,
        'model_s3_path': f"s3://{bucket}/{model_s3_key}",
        'best_iteration': int(model.best_iteration),
        'feature_count': int(X_train.shape[1]),
        'training_samples': int(X_train.shape[0]),
        'validation_samples': int(X_val.shape[0])
    }
    
    # Save and upload results
    results_filename = 'training_results.json'
    with open(results_filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    results_s3_key = f"{s3_key}/trained_model/training_results.json"
    s3_client.upload_file(results_filename, bucket, results_s3_key)
    
    print(f"🎉 Training completed successfully!")
    print(f"📁 Model saved to: s3://{bucket}/{model_s3_key}")
    print(f"📊 Results saved to: s3://{bucket}/{results_s3_key}")

if __name__ == "__main__":
    main()
