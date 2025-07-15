package main

import (
    "context"
    "encoding/json"
    "fmt"
    "os"
    "testing"
    "time"

    "github.com/aws/aws-sdk-go-v2/aws"
    "github.com/aws/aws-sdk-go-v2/service/batch"
    "github.com/aws/aws-sdk-go-v2/service/batch/types"
    "github.com/aws/aws-sdk-go-v2/service/sqs"
    sqstypes "github.com/aws/aws-sdk-go-v2/service/sqs/types"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
)

// MockBatchClient for testing Batch operations
type MockBatchClient struct {
    mock.Mock
}

func (m *MockBatchClient) SubmitJob(ctx context.Context, input *batch.SubmitJobInput, opts ...func(*batch.Options)) (*batch.SubmitJobOutput, error) {
    args := m.Called(ctx, input)
    return args.Get(0).(*batch.SubmitJobOutput), args.Error(1)
}

func (m *MockBatchClient) DescribeJobs(ctx context.Context, input *batch.DescribeJobsInput, opts ...func(*batch.Options)) (*batch.DescribeJobsOutput, error) {
    args := m.Called(ctx, input)
    return args.Get(0).(*batch.DescribeJobsOutput), args.Error(1)
}

// MockSQSClient for testing SQS operations
type MockSQSClient struct {
    mock.Mock
}

func (m *MockSQSClient) SendMessage(ctx context.Context, input *sqs.SendMessageInput, opts ...func(*sqs.Options)) (*sqs.SendMessageOutput, error) {
    args := m.Called(ctx, input)
    return args.Get(0).(*sqs.SendMessageOutput), args.Error(1)
}

// MockMLTrainer for testing
type MockMLTrainer struct {
    *MLTrainer
    batchClient *MockBatchClient
    sqsClient   *MockSQSClient
}

func NewMockMLTrainer() *MockMLTrainer {
    mockBatch := &MockBatchClient{}
    mockSQS := &MockSQSClient{}
    return &MockMLTrainer{
        MLTrainer: &MLTrainer{
            bucket:   "test-bucket",
            region:   "us-east-2",
            jobQueue: "test-queue",
            jobDef:   "test-job-def",
        },
        batchClient: mockBatch,
        sqsClient:   mockSQS,
    }
}

func TestMLTrainer_TrainModel_Success(t *testing.T) {
    tests := []struct {
        name          string
        provider      string
        productID     string
        correlationID string
        expectError   bool
    }{
        {
            name:          "successful_training_coinbase_btc",
            provider:      "COINBASE",
            productID:     "BTC-USD",
            correlationID: "test-123",
            expectError:   false,
        },
        {
            name:          "successful_training_binance_eth",
            provider:      "BINANCE",
            productID:     "ETH-USD",
            correlationID: "test-456",
            expectError:   false,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Setup
            os.Setenv("DEREGISTER_TASK_QUEUE_URL", "https://sqs.us-east-2.amazonaws.com/123456789/test-queue")
            defer os.Unsetenv("DEREGISTER_TASK_QUEUE_URL")

            mockTrainer := NewMockMLTrainer()
            mockTrainer.MLTrainer.batchClient = mockTrainer.batchClient
            mockTrainer.MLTrainer.sqsClient = mockTrainer.sqsClient

            // Mock successful job submission
            mockTrainer.batchClient.On("SubmitJob", mock.Anything, mock.AnythingOfType("*batch.SubmitJobInput")).Return(
                &batch.SubmitJobOutput{
                    JobId: aws.String("job-123"),
                }, nil)

            // Mock job completion check
            mockTrainer.batchClient.On("DescribeJobs", mock.Anything, mock.AnythingOfType("*batch.DescribeJobsInput")).Return(
                &batch.DescribeJobsOutput{
                    Jobs: []types.JobDetail{
                        {
                            JobId:     aws.String("job-123"),
                            JobStatus: types.JobStatusSucceeded,
                        },
                    },
                }, nil)

            // Mock SQS message sending
            mockTrainer.sqsClient.On("SendMessage", mock.Anything, mock.AnythingOfType("*sqs.SendMessageInput")).Return(
                &sqs.SendMessageOutput{
                    MessageId: aws.String("msg-123"),
                }, nil)

            // Test
            ctx := context.Background()
            err := mockTrainer.MLTrainer.TrainModel(ctx, tt.provider, tt.productID, tt.correlationID)

            // Assertions
            if tt.expectError {
                assert.Error(t, err)
            } else {
                assert.NoError(t, err)
            }

            mockTrainer.batchClient.AssertExpectations(t)
            mockTrainer.sqsClient.AssertExpectations(t)
        })
    }
}

func TestMLTrainer_TrainModel_BatchSubmitJobFailure(t *testing.T) {
    // Setup
    mockTrainer := NewMockMLTrainer()
    mockTrainer.MLTrainer.batchClient = mockTrainer.batchClient

    // Mock failed job submission
    mockTrainer.batchClient.On("SubmitJob", mock.Anything, mock.AnythingOfType("*batch.SubmitJobInput")).Return(
        (*batch.SubmitJobOutput)(nil), fmt.Errorf("batch service unavailable"))

    // Test
    ctx := context.Background()
    err := mockTrainer.MLTrainer.TrainModel(ctx, "COINBASE", "BTC-USD", "test-123")

    // Assertions
    assert.Error(t, err)
    assert.Contains(t, err.Error(), "failed to submit training job")
    mockTrainer.batchClient.AssertExpectations(t)
}

func TestMLTrainer_TrainModel_JobFailure(t *testing.T) {
    // Setup
    mockTrainer := NewMockMLTrainer()
    mockTrainer.MLTrainer.batchClient = mockTrainer.batchClient

    // Mock successful job submission
    mockTrainer.batchClient.On("SubmitJob", mock.Anything, mock.AnythingOfType("*batch.SubmitJobInput")).Return(
        &batch.SubmitJobOutput{
            JobId: aws.String("job-123"),
        }, nil)

    // Mock job failure
    mockTrainer.batchClient.On("DescribeJobs", mock.Anything, mock.AnythingOfType("*batch.DescribeJobsInput")).Return(
        &batch.DescribeJobsOutput{
            Jobs: []types.JobDetail{
                {
                    JobId:        aws.String("job-123"),
                    JobStatus:    types.JobStatusFailed,
                    StatusReason: aws.String("Container failed with exit code 1"),
                },
            },
        }, nil)

    // Test
    ctx := context.Background()
    err := mockTrainer.MLTrainer.TrainModel(ctx, "COINBASE", "BTC-USD", "test-123")

    // Assertions
    assert.Error(t, err)
    assert.Contains(t, err.Error(), "training job failed")
    assert.Contains(t, err.Error(), "Container failed with exit code 1")
    mockTrainer.batchClient.AssertExpectations(t)
}

func TestMLTrainer_waitForJobCompletion_Success(t *testing.T) {
    // Setup
    mockTrainer := NewMockMLTrainer()
    mockTrainer.MLTrainer.batchClient = mockTrainer.batchClient

    // Mock successful job completion
    mockTrainer.batchClient.On("DescribeJobs", mock.Anything, mock.AnythingOfType("*batch.DescribeJobsInput")).Return(
        &batch.DescribeJobsOutput{
            Jobs: []types.JobDetail{
                {
                    JobId:     aws.String("job-123"),
                    JobStatus: types.JobStatusSucceeded,
                },
            },
        }, nil)

    // Test
    ctx := context.Background()
    err := mockTrainer.MLTrainer.waitForJobCompletion(ctx, "job-123", "test-job")

    // Assertions
    assert.NoError(t, err)
    mockTrainer.batchClient.AssertExpectations(t)
}

func TestMLTrainer_waitForJobCompletion_JobNotFound(t *testing.T) {
    // Setup
    mockTrainer := NewMockMLTrainer()
    mockTrainer.MLTrainer.batchClient = mockTrainer.batchClient

    // Mock empty job list
    mockTrainer.batchClient.On("DescribeJobs", mock.Anything, mock.AnythingOfType("*batch.DescribeJobsInput")).Return(
        &batch.DescribeJobsOutput{
            Jobs: []types.JobDetail{},
        }, nil)

    // Test
    ctx := context.Background()
    err := mockTrainer.MLTrainer.waitForJobCompletion(ctx, "job-123", "test-job")

    // Assertions
    assert.Error(t, err)
    assert.Contains(t, err.Error(), "job job-123 not found")
    mockTrainer.batchClient.AssertExpectations(t)
}

func TestMLTrainer_waitForJobCompletion_ContextCancelled(t *testing.T) {
    // Setup
    mockTrainer := NewMockMLTrainer()
    ctx, cancel := context.WithCancel(context.Background())
    cancel() // Cancel immediately

    // Test
    err := mockTrainer.MLTrainer.waitForJobCompletion(ctx, "job-123", "test-job")

    // Assertions
    assert.Error(t, err)
    assert.Equal(t, context.Canceled, err)
}

func TestMLTrainer_sendCompletionMessage_Success(t *testing.T) {
    // Setup
    os.Setenv("DEREGISTER_TASK_QUEUE_URL", "https://sqs.us-east-2.amazonaws.com/123456789/test-queue")
    defer os.Unsetenv("DEREGISTER_TASK_QUEUE_URL")

    mockTrainer := NewMockMLTrainer()
    mockTrainer.MLTrainer.sqsClient = mockTrainer.sqsClient

    // Mock SQS message sending
    mockTrainer.sqsClient.On("SendMessage", mock.Anything, mock.AnythingOfType("*sqs.SendMessageInput")).Return(
        &sqs.SendMessageOutput{
            MessageId: aws.String("msg-123"),
        }, nil)

    // Test data
    result := TrainingResult{
        Provider:       "COINBASE",
        ProductID:      "BTC-USD",
        CorrelationID:  "test-123",
        Status:         "completed",
        ModelPath:      "s3://test-bucket/COINBASE/BTC-USD/trained_model",
        TrainingTimeMs: 30000,
        JobID:          "job-123",
    }

    // Test
    ctx := context.Background()
    err := mockTrainer.MLTrainer.sendCompletionMessage(ctx, result)

    // Assertions
    assert.NoError(t, err)
    mockTrainer.sqsClient.AssertExpectations(t)
}

func TestMLTrainer_sendCompletionMessage_NoQueueURL(t *testing.T) {
    // Setup - no queue URL set
    os.Unsetenv("DEREGISTER_TASK_QUEUE_URL")

    mockTrainer := NewMockMLTrainer()

    // Test data
    result := TrainingResult{
        Provider:      "COINBASE",
        ProductID:     "BTC-USD",
        CorrelationID: "test-123",
        Status:        "completed",
    }

    // Test
    ctx := context.Background()
    err := mockTrainer.MLTrainer.sendCompletionMessage(ctx, result)

    // Assertions - should not error when no queue URL is provided
    assert.NoError(t, err)
}

func TestMLTrainer_sendCompletionMessage_SQSFailure(t *testing.T) {
    // Setup
    os.Setenv("DEREGISTER_TASK_QUEUE_URL", "https://sqs.us-east-2.amazonaws.com/123456789/test-queue")
    defer os.Unsetenv("DEREGISTER_TASK_QUEUE_URL")

    mockTrainer := NewMockMLTrainer()
    mockTrainer.MLTrainer.sqsClient = mockTrainer.sqsClient

    // Mock SQS failure
    mockTrainer.sqsClient.On("SendMessage", mock.Anything, mock.AnythingOfType("*sqs.SendMessageInput")).Return(
        (*sqs.SendMessageOutput)(nil), fmt.Errorf("SQS service unavailable"))

    // Test data
    result := TrainingResult{
        Provider:      "COINBASE",
        ProductID:     "BTC-USD",
        CorrelationID: "test-123",
        Status:        "completed",
    }

    // Test
    ctx := context.Background()
    err := mockTrainer.MLTrainer.sendCompletionMessage(ctx, result)

    // Assertions
    assert.Error(t, err)
    assert.Contains(t, err.Error(), "failed to send SQS message")
    mockTrainer.sqsClient.AssertExpectations(t)
}

func TestTrainingRequest_JSON(t *testing.T) {
    // Test JSON marshaling/unmarshaling
    req := TrainingRequest{
        Provider:      "COINBASE",
        ProductID:     "BTC-USD",
        CorrelationID: "test-123",
        Action:        "train",
        Hyperparams: map[string]string{
            "max_depth": "6",
            "eta":       "0.1",
        },
    }

    // Marshal to JSON
    data, err := json.Marshal(req)
    assert.NoError(t, err)

    // Unmarshal from JSON
    var decoded TrainingRequest
    err = json.Unmarshal(data, &decoded)
    assert.NoError(t, err)

    // Verify
    assert.Equal(t, req.Provider, decoded.Provider)
    assert.Equal(t, req.ProductID, decoded.ProductID)
    assert.Equal(t, req.CorrelationID, decoded.CorrelationID)
    assert.Equal(t, req.Action, decoded.Action)
    assert.Equal(t, req.Hyperparams, decoded.Hyperparams)
}

func TestTrainingResult_JSON(t *testing.T) {
    // Test JSON marshaling/unmarshaling
    result := TrainingResult{
        Provider:       "COINBASE",
        ProductID:      "BTC-USD",
        CorrelationID:  "test-123",
        Status:         "completed",
        ModelPath:      "s3://bucket/model",
        TrainingTimeMs: 30000,
        Accuracy:       0.85,
        JobID:          "job-123",
    }

    // Marshal to JSON
    data, err := json.Marshal(result)
    assert.NoError(t, err)

    // Unmarshal from JSON
    var decoded TrainingResult
    err = json.Unmarshal(data, &decoded)
    assert.NoError(t, err)

    // Verify
    assert.Equal(t, result.Provider, decoded.Provider)
    assert.Equal(t, result.ProductID, decoded.ProductID)
    assert.Equal(t, result.Status, decoded.Status)
    assert.Equal(t, result.ModelPath, decoded.ModelPath)
    assert.Equal(t, result.TrainingTimeMs, decoded.TrainingTimeMs)
    assert.Equal(t, result.Accuracy, decoded.Accuracy)
    assert.Equal(t, result.JobID, decoded.JobID)
}

// Benchmark tests for performance validation
func BenchmarkMLTrainer_TrainModel(b *testing.B) {
    mockTrainer := NewMockMLTrainer()
    mockTrainer.MLTrainer.batchClient = mockTrainer.batchClient
    mockTrainer.MLTrainer.sqsClient = mockTrainer.sqsClient

    // Setup mocks
    mockTrainer.batchClient.On("SubmitJob", mock.Anything, mock.AnythingOfType("*batch.SubmitJobInput")).Return(
        &batch.SubmitJobOutput{JobId: aws.String("job-123")}, nil)
    mockTrainer.batchClient.On("DescribeJobs", mock.Anything, mock.AnythingOfType("*batch.DescribeJobsInput")).Return(
        &batch.DescribeJobsOutput{
            Jobs: []types.JobDetail{{JobId: aws.String("job-123"), JobStatus: types.JobStatusSucceeded}},
        }, nil)
    mockTrainer.sqsClient.On("SendMessage", mock.Anything, mock.AnythingOfType("*sqs.SendMessageInput")).Return(
        &sqs.SendMessageOutput{MessageId: aws.String("msg-123")}, nil)

    ctx := context.Background()

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        mockTrainer.MLTrainer.TrainModel(ctx, "COINBASE", "BTC-USD", "test-123")
    }
}