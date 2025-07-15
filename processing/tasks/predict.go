// predict.go - High-performance prediction service
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "github.com/aws/aws-sdk-go-v2/service/s3"
    "io"
    "os"
    "os/exec"
    "strings"
)

type PredictionService struct {
    s3Client *s3.Client
    bucket   string
}

type PredictionResult struct {
    Provider        string            `json:"provider"`
    ProductID       string            `json:"product_id"`
    CorrelationID   string            `json:"correlation_id"`
    Predictions     []float64         `json:"predictions"`
    Accuracy        float64           `json:"accuracy"`
    AUC            float64           `json:"auc"`
    ConfusionMatrix map[string]int    `json:"confusion_matrix"`
    SampleCount     int               `json:"sample_count"`
}

func (ps *PredictionService) GeneratePrediction(ctx context.Context, provider, productID, correlationID string) (*PredictionResult, error) {
    s3Key := fmt.Sprintf("%s/%s", provider, productID)
    
    // Download model and validation data
    modelPath := "xgb_model.joblib"
    validationPath := "validation.libsvm"
    
    if err := ps.downloadFromS3(ctx, fmt.Sprintf("%s/trained_model/xgb_model.joblib", s3Key), modelPath); err != nil {
        return nil, fmt.Errorf("failed to download model: %w", err)
    }
    
    if err := ps.downloadFromS3(ctx, fmt.Sprintf("%s/validation/validation.libsvm", s3Key), validationPath); err != nil {
        return nil, fmt.Errorf("failed to download validation data: %w", err)
    }
    
    // Run Python prediction script (optimized for speed)
    pythonScript := `
import joblib
import numpy as np
from sklearn.datasets import load_svmlight_file
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix
import json
import sys

# Load model and data
model = joblib.load('xgb_model.joblib')
X_val, y_val = load_svmlight_file('validation.libsvm')

# Generate predictions
predictions = model.predict_proba(X_val)[:, 1]
predictions_binary = (predictions > 0.5).astype(int)

# Calculate metrics
accuracy = accuracy_score(y_val, predictions_binary)
auc = roc_auc_score(y_val, predictions)
cm = confusion_matrix(y_val, predictions_binary)
tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)

# Output results
result = {
    'predictions': predictions.tolist(),
    'accuracy': float(accuracy),
    'auc': float(auc),
    'confusion_matrix': {
        'true_positive': int(tp),
        'true_negative': int(tn), 
        'false_positive': int(fp),
        'false_negative': int(fn)
    },
    'sample_count': len(predictions)
}

print(json.dumps(result))
`
    
    // Execute Python script
    cmd := exec.CommandContext(ctx, "python3", "-c", pythonScript)
    output, err := cmd.Output()
    if err != nil {
        return nil, fmt.Errorf("prediction script failed: %w", err)
    }
    
    // Parse results
    var scriptResult struct {
        Predictions     []float64         `json:"predictions"`
        Accuracy        float64           `json:"accuracy"`
        AUC            float64           `json:"auc"`
        ConfusionMatrix map[string]int    `json:"confusion_matrix"`
        SampleCount     int               `json:"sample_count"`
    }
    
    if err := json.Unmarshal(output, &scriptResult); err != nil {
        return nil, fmt.Errorf("failed to parse prediction results: %w", err)
    }
    
    result := &PredictionResult{
        Provider:        provider,
        ProductID:       productID,
        CorrelationID:   correlationID,
        Predictions:     scriptResult.Predictions,
        Accuracy:        scriptResult.Accuracy,
        AUC:            scriptResult.AUC,
        ConfusionMatrix: scriptResult.ConfusionMatrix,
        SampleCount:     scriptResult.SampleCount,
    }
    
    // Save results to S3
    resultsPath := fmt.Sprintf("%s/predictions/prediction_results.json", s3Key)
    if err := ps.uploadResults(ctx, result, resultsPath); err != nil {
        fmt.Printf("⚠️  Failed to upload results: %v\n", err)
    }
    
    fmt.Printf("✅ Prediction completed for %s/%s - Accuracy: %.4f, AUC: %.4f\n", 
        provider, productID, result.Accuracy, result.AUC)
    
    return result, nil
}

func (ps *PredictionService) downloadFromS3(ctx context.Context, s3Key, localPath string) error {
    result, err := ps.s3Client.GetObject(ctx, &s3.GetObjectInput{
        Bucket: aws.String(ps.bucket),
        Key:    aws.String(s3Key),
    })
    if err != nil {
        return err
    }
    defer result.Body.Close()
    
    file, err := os.Create(localPath)
    if err != nil {
        return err
    }
    defer file.Close()
    
    _, err = io.Copy(file, result.Body)
    return err
}

func (ps *PredictionService) uploadResults(ctx context.Context, result *PredictionResult, s3Key string) error {
    data, err := json.MarshalIndent(result, "", "  ")
    if err != nil {
        return err
    }
    
    _, err = ps.s3Client.PutObject(ctx, &s3.PutObjectInput{
        Bucket: aws.String(ps.bucket),
        Key:    aws.String(s3Key),
        Body:   strings.NewReader(string(data)),
        ContentType: aws.String("application/json"),
    })
    
    return err
}