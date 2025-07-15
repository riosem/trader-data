package main

import (
    "context"
    "encoding/json"
    "fmt"
    "os"
    "strings"
    "time"
    
    "github.com/aws/aws-sdk-go-v2/aws"
    "github.com/aws/aws-sdk-go-v2/config"
    "github.com/aws/aws-sdk-go-v2/service/batch"
    "github.com/aws/aws-sdk-go-v2/service/batch/types"
    "github.com/aws/aws-sdk-go-v2/service/s3"
    "github.com/aws/aws-sdk-go-v2/service/sqs"
    sqstypes "github.com/aws/aws-sdk-go-v2/service/sqs/types"
)

type MLTrainer struct {
    batchClient *batch.Client
    sqsClient   *sqs.Client
    bucket      string
    region      string
    jobQueue    string
    jobDef      string
}

type TrainingRequest struct {
    Provider      string            `json:"provider"`
    ProductID     string            `json:"product_id"`
    CorrelationID string            `json:"correlation_id"`
    Action        string            `json:"action"`
    Hyperparams   map[string]string `json:"hyperparameters,omitempty"`
}

type TrainingResult struct {
    Provider        string    `json:"provider"`
    ProductID       string    `json:"product_id"`
    CorrelationID   string    `json:"correlation_id"`
    Status          string    `json:"status"`
    ModelPath       string    `json:"model_path"`
    TrainingTimeMs  int64     `json:"training_time_ms"`
    Accuracy        float64   `json:"accuracy,omitempty"`
    JobID           string    `json:"job_id"`
}

func main() {
    // Load AWS config
    cfg, err := config.LoadDefaultConfig(context.Background())
    if err != nil {
        fmt.Printf("Error loading AWS config: %v\n", err)
        os.Exit(1)
    }

    trainer := &MLTrainer{
        bucket:   os.Getenv("DATA_COLLECTION_BUCKET_NAME"),
        region:   os.Getenv("REGION"),
        jobQueue: "trader-ml-training-queue",
        jobDef:   "trader-xgb-training-job",
    }
    
    // Initialize AWS clients
    trainer.batchClient = batch.NewFromConfig(cfg)
    trainer.sqsClient = sqs.NewFromConfig(cfg)
    
    // Get action from environment
    action := os.Getenv("ACTION")
    provider := os.Getenv("PROVIDER")
    productID := os.Getenv("PRODUCT_ID")
    correlationID := os.Getenv("CORRELATION_ID")
    
    ctx := context.Background()
    
    switch action {
    case "train":
        if err := trainer.TrainModel(ctx, provider, productID, correlationID); err != nil {
            fmt.Printf("Training failed: %v\n", err)
            os.Exit(1)
        }
    case "predict":
        predictionService := &PredictionService{
            s3Client: s3.NewFromConfig(cfg),
            bucket:   trainer.bucket,
        }
        if _, err := predictionService.GeneratePrediction(ctx, provider, productID, correlationID); err != nil {
            fmt.Printf("Prediction failed: %v\n", err)
            os.Exit(1)
        }
    default:
        fmt.Printf("Unknown action: %s\n", action)
        os.Exit(1)
    }
}

func (mt *MLTrainer) TrainModel(ctx context.Context, provider, productID, correlationID string) error {
    start := time.Now()
    
    s3Key := fmt.Sprintf("%s/%s", provider, productID)
    outputPath := fmt.Sprintf("s3://%s/%s/trained_model", mt.bucket, s3Key)
    
    // Define optimized hyperparameters for trading
    hyperparams := map[string]string{
        "max_depth":         "6",
        "eta":              "0.1",
        "gamma":            "1",
        "min_child_weight": "1",
        "subsample":        "0.8",
        "colsample_bytree": "0.8",
        "objective":        "binary:logistic",
        "eval_metric":      "auc",
        "num_round":        "100",
        "early_stopping":   "10",
        "tree_method":      "hist",
        "verbosity":        "1",
    }
    
    // Create job name with timestamp
    jobName := fmt.Sprintf("trader-xgb-%s-%s-%d", provider, productID, time.Now().Unix())
    
    // Environment variables for the training container
    envVars := []types.KeyValuePair{
        {Name: aws.String("S3_BUCKET"), Value: aws.String(mt.bucket)},
        {Name: aws.String("S3_KEY"), Value: aws.String(s3Key)},
        {Name: aws.String("OUTPUT_PATH"), Value: aws.String(outputPath)},
        {Name: aws.String("PROVIDER"), Value: aws.String(provider)},
        {Name: aws.String("PRODUCT_ID"), Value: aws.String(productID)},
        {Name: aws.String("CORRELATION_ID"), Value: aws.String(correlationID)},
        {Name: aws.String("AWS_DEFAULT_REGION"), Value: aws.String(mt.region)},
    }
    
    // Add hyperparameters as environment variables
    for k, v := range hyperparams {
        envVars = append(envVars, types.KeyValuePair{
            Name:  aws.String(fmt.Sprintf("HYPERPARAM_%s", strings.ToUpper(k))),
            Value: aws.String(v),
        })
    }
    
    // Submit training job to AWS Batch
    submitInput := &batch.SubmitJobInput{
        JobName:       aws.String(jobName),
        JobQueue:      aws.String(mt.jobQueue),
        JobDefinition: aws.String(mt.jobDef),
        ContainerOverrides: &types.ContainerOverrides{
            Environment: envVars,
            Memory:      aws.Int32(8192), // 8GB RAM
            Vcpus:       aws.Int32(4),    // 4 vCPUs
        },
        Tags: map[string]string{
            "Provider":      provider,
            "ProductID":     productID,
            "CorrelationID": correlationID,
            "JobType":       "xgboost-training",
            "Environment":   "dev",
        },
        Timeout: &types.JobTimeout{
            AttemptDurationSeconds: aws.Int32(1800), // 30 minutes max
        },
    }
    
    result, err := mt.batchClient.SubmitJob(ctx, submitInput)
    if err != nil {
        return fmt.Errorf("failed to submit training job: %w", err)
    }
    
    fmt.Printf("✅ Training job submitted: %s (Job ID: %s)\n", jobName, *result.JobId)
    
    // Wait for job completion
    if err := mt.waitForJobCompletion(ctx, *result.JobId, jobName); err != nil {
        return fmt.Errorf("training job failed: %w", err)
    }
    
    // Send completion message to SQS
    trainingResult := TrainingResult{
        Provider:       provider,
        ProductID:      productID,
        CorrelationID:  correlationID,
        Status:         "completed",
        ModelPath:      outputPath,
        TrainingTimeMs: time.Since(start).Milliseconds(),
        JobID:          *result.JobId,
    }
    
    return mt.sendCompletionMessage(ctx, trainingResult)
}

func (mt *MLTrainer) waitForJobCompletion(ctx context.Context, jobID, jobName string) error {
    ticker := time.NewTicker(30 * time.Second)
    defer ticker.Stop()
    
    timeout := time.After(45 * time.Minute)
    
    for {
        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-timeout:
            return fmt.Errorf("job %s timed out after 45 minutes", jobName)
        case <-ticker.C:
            describeInput := &batch.DescribeJobsInput{
                Jobs: []string{jobID},
            }
            
            result, err := mt.batchClient.DescribeJobs(ctx, describeInput)
            if err != nil {
                return fmt.Errorf("failed to describe job: %w", err)
            }
            
            if len(result.Jobs) == 0 {
                return fmt.Errorf("job %s not found", jobID)
            }
            
            job := result.Jobs[0]
            fmt.Printf("🔄 Job %s status: %s\n", jobName, job.JobStatus)
            
            switch job.JobStatus {
            case types.JobStatusSucceeded:
                fmt.Printf("✅ Training job %s completed successfully\n", jobName)
                return nil
            case types.JobStatusFailed:
                reason := "Unknown error"
                if job.StatusReason != nil {
                    reason = *job.StatusReason
                }
                return fmt.Errorf("training job %s failed: %s", jobName, reason)
            case types.JobStatusCancelled:
                return fmt.Errorf("training job %s was cancelled", jobName)
            }
        }
    }
}

func (mt *MLTrainer) sendCompletionMessage(ctx context.Context, result TrainingResult) error {
    queueURL := os.Getenv("DEREGISTER_TASK_QUEUE_URL")
    if queueURL == "" {
        fmt.Println("⚠️  No DEREGISTER_TASK_QUEUE_URL provided, skipping message")
        return nil
    }
    
    messageBody, err := json.Marshal(result)
    if err != nil {
        return fmt.Errorf("failed to marshal message: %w", err)
    }
    
    _, err = mt.sqsClient.SendMessage(ctx, &sqs.SendMessageInput{
        QueueUrl:    aws.String(queueURL),
        MessageBody: aws.String(string(messageBody)),
        MessageAttributes: map[string]sqstypes.MessageAttributeValue{
            "Provider": {
                DataType:    aws.String("String"),
                StringValue: aws.String(result.Provider),
            },
            "ProductID": {
                DataType:    aws.String("String"),
                StringValue: aws.String(result.ProductID),
            },
            "JobType": {
                DataType:    aws.String("String"),
                StringValue: aws.String("training_completion"),
            },
        },
    })
    
    if err != nil {
        return fmt.Errorf("failed to send SQS message: %w", err)
    }
    
    fmt.Printf("📨 Completion message sent to SQS for %s/%s\n", result.Provider, result.ProductID)
    return nil
}