# Deployment Guide

This document explains how to set up and deploy the trader-data services to AWS.

## Prerequisites

1. **AWS Account**: You need an AWS account with appropriate permissions
2. **AWS CLI**: Install and configure the AWS CLI
3. **Serverless Framework**: Install the Serverless Framework (`npm install -g serverless`)
4. **Python 3.10**: Required Python version
5. **Node.js**: For Serverless Framework dependencies
6. **Docker**: For building container images

## Required AWS Resources

Before deploying, ensure you have the following AWS resources set up:

### 1. S3 Buckets
- Data collection bucket for storing collected market data
- Deployment bucket for Serverless Framework artifacts

### 2. IAM Roles
The application requires several IAM roles with appropriate permissions:

- **Lambda Execution Roles**: For each service (processing, llm, collection)
  - Example ARN format: `arn:aws:iam::YOUR_ACCOUNT_ID:role/SERVICE_NAME-role-blue-STAGE-REGION`
- **ECS Task Execution Role**: For ECS task execution
  - Example ARN format: `arn:aws:iam::YOUR_ACCOUNT_ID:role/task-execution-role-blue-STAGE-REGION`
- **ECS Task Role**: For ECS task permissions
  - Example ARN format: `arn:aws:iam::YOUR_ACCOUNT_ID:role/task-role-blue-STAGE-REGION`

### 3. VPC and Networking
- VPC with appropriate subnets (both public and private)
- Security groups for ECS tasks and Lambda functions
- NAT Gateway or VPC endpoints for private subnet internet access

### 4. Container Registry
- ECR repository for storing Docker images
- Example repository: `YOUR_ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPOSITORY_NAME`

### 5. DynamoDB Table
- Cache table for OAuth token storage
- Configured through SSM parameters

## Environment Variables and Secrets

### AWS Systems Manager Parameter Store
Store the following sensitive values in AWS SSM Parameter Store:

#### Development Environment (`/trader/dev/`)
- `/trader/dev/data/collection_bucket` - S3 bucket name for data collection
- `/trader/dev/subnet_ids` - VPC subnet ID for ECS tasks
- `/trader/dev/ec2_key_pair` - EC2 key pair name for ECS clusters
- `/trader/dev/ollama/api_key` - Ollama API key
- `/trader/dev/provider/api_key` - Data provider API key
- `/trader/dev/provider/api_url` - Data provider API URL
- `/trader/dev/coinbase/cdp/dev/api_key` - Coinbase API key
- `/trader/dev/coinbase/cdp/dev/api_secret` - Coinbase API secret
- `/trader/dev/auth0/assistant/client_id` - Auth0 client ID
- `/trader/dev/auth0/assistant/client_secret` - Auth0 client secret
- `/trader/dev/assistant/api_url` - Assistant API URL (used as audience)
- `/trader/dev/auth0/oauth_url` - Auth0 OAuth URL
- `/trader/dev/assistant/api_key` - Assistant API key
- `/trader/dev/authorizer/cache_table_name` - DynamoDB cache table name

#### Production Environment (`/trader/prod/`)
- Same parameters as dev but under `/trader/prod/` prefix

### Configuration Files

Before deployment, you need to update the following configuration values:

#### 1. Update `processing/serverless.yml`
Replace these hardcoded values with parameterized versions:

- **Security Group ID**: Currently `sg-xxxxxxxxxxxxx`
- **Subnet ID**: Currently `subnet-xxxxxxxxxxxx`
- **AWS Account ID**: Currently `12345678901` in IAM role ARNs
- **Docker Image**: Currently `USER/TAGNAME:TAGVERSION`

#### 2. Subnet and Security Group Configuration
You'll need to provide:
- Security group ID for ECS tasks
- Subnet ID for ECS task networking
- These should be added as parameters or environment variables

## External Service Setup

### 1. Data Provider API
1. Set up your market data provider (e.g., Alpha Vantage, IEX Cloud, etc.)
2. Obtain API credentials
3. Store credentials in AWS SSM Parameter Store

### 2. Coinbase Advanced Trade API (Optional)
1. Create a Coinbase Advanced Trade account
2. Generate API credentials
3. Store the API key and secret in AWS SSM Parameter Store

### 3. Auth0 Setup
1. Create an Auth0 account and application
2. Configure OAuth settings and API audience
3. Store client credentials in AWS SSM Parameter Store

### 4. Ollama API (for LLM service)
1. Set up Ollama service (self-hosted or cloud)
2. Configure API access
3. Store API credentials in SSM Parameter Store

## Deployment Steps

### 1. Install Dependencies
```bash
# For each service (processing, llm, collection)
cd processing/  # or llm/ or collection/
pip install -r requirements.txt
pip install -r requirements-dev.txt
npm install
```

### 2. Set Up Environment Variables (Optional)
Create environment variables for easier deployment:
```bash
# Copy the example environment file and customize it
cp .env.example .env.local

# Edit .env.local with your actual values
export AWS_REGION=us-east-2
export AWS_ACCOUNT_ID=123456789012
export DEPLOYMENT_BUCKET=my-serverless-deployment-bucket
export SECURITY_GROUP_ID=sg-0123456789abcdef0
export SUBNET_ID=subnet-0123456789abcdef0

# Source the environment variables
source .env.local
```

### 3. Build and Push Docker Image (for processing service)
```bash
cd processing/
docker build -t TAGNAME -f task/Dockerfile .

# Tag and push to your ECR repository (replace with your actual values)
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker tag TAGNAME:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/TAGNAME:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/TAGNAME:latest
```

### 4. Deploy Services
```bash
# Deploy data collection service
cd collection/
sls deploy --stage dev --param="deployment-bucket=$DEPLOYMENT_BUCKET"

# Deploy LLM service
cd ../llm/
sls deploy --stage dev --param="deployment-bucket=$DEPLOYMENT_BUCKET"

# Deploy processing service
cd ../processing/
sls deploy --stage dev \
  --param="deployment-bucket=$DEPLOYMENT_BUCKET" \
  --param="security-group-id=$SECURITY_GROUP_ID" \
  --param="subnet-id=$SUBNET_ID" \
  --param="container-image=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/TAGNAME:latest"
```

### 5. Verify Deployment
After deployment, verify that all services are working:
```bash
# Check CloudWatch logs for any errors
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/trader-data"

# Test individual functions (optional)
sls invoke -f collection --stage dev
```

## Parameter Examples

The CLI commands above use example parameter values. Replace these with your actual values:

### Example Parameters Used:
- **AWS Account ID**: `123456789012` (replace with your 12-digit AWS account ID)
- **Security Group ID**: `sg-0123456789abcdef0` (replace with your VPC security group)
- **Subnet ID**: `subnet-0123456789abcdef0` (replace with your VPC subnet)
- **Deployment Bucket**: `my-serverless-deployment-bucket` (replace with your S3 bucket)
- **ECR Image URI**: `123456789012.dkr.ecr.us-east-2.amazonaws.com/TAGNAME:latest`

### Finding Your AWS Resources:
To find the correct values for your deployment:

```bash
# Get your AWS Account ID
aws sts get-caller-identity --query Account --output text

# List your VPCs
aws ec2 describe-vpcs --query 'Vpcs[*].[VpcId,Tags[?Key==`Name`].Value|[0]]' --output table

# List subnets in a VPC
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-XXXXXXXXX" --query 'Subnets[*].[SubnetId,AvailabilityZone,CidrBlock]' --output table

# List security groups
aws ec2 describe-security-groups --query 'SecurityGroups[*].[GroupId,GroupName,Description]' --output table
```

### Network Configuration:
- Update security groups to allow appropriate access
- Ensure subnets have proper routing for external API access

## Testing

Run the test suite for each service:

```bash
# In each service directory
pytest
```

## Monitoring and Logging

- CloudWatch logs are automatically created for all Lambda functions
- Log retention is set to 7 days (configurable)
- ECS tasks log to CloudWatch under `/ecs/trader-data-train-STAGE`

## Security Considerations

- All sensitive data is stored in AWS SSM Parameter Store
- No hardcoded credentials in source code
- IAM roles follow principle of least privilege
- VPC configuration provides network isolation
- Security groups restrict access to necessary ports only

## Cost Optimization

- Use appropriate ECS task sizes based on workload
- Configure auto-scaling for ECS services
- Monitor CloudWatch costs and set up billing alerts
- Use Spot instances for non-critical batch processing

## Troubleshooting

### Common Issues:

1. **Network Connectivity**: Ensure subnets have proper routing and NAT Gateway access
2. **IAM Permissions**: Verify all roles have necessary permissions for AWS services
3. **Parameter Store**: Ensure all required SSM parameters are set
4. **Container Issues**: Check ECR permissions and image availability
5. **Docker Build Failures**: Ensure Docker daemon is running and you have sufficient disk space
6. **ECR Authentication**: Re-authenticate if you get "authentication required" errors

### Debugging Commands:
```bash
# Check CloudWatch logs for detailed error messages
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/trader-data"

# View specific function logs
sls logs -f FUNCTION_NAME --stage dev --tail

# Test individual functions
sls invoke -f FUNCTION_NAME --stage dev --data '{}'

# Check ECS task status
aws ecs list-tasks --cluster trader-data-cluster-dev

# Verify SSM parameter values
aws ssm get-parameter --name "/trader/dev/data/collection_bucket" --query "Parameter.Value" --output text

# Test Docker image locally
docker run --rm -it TAGNAME:latest /bin/bash
```

### Performance Optimization:
- Monitor Lambda function duration and memory usage in CloudWatch
- Optimize container image size by using multi-stage builds
- Use Lambda layers for common dependencies
- Configure appropriate timeout values for long-running tasks

### Security Best Practices:
- Regularly rotate API keys and access tokens
- Use VPC endpoints to avoid internet traffic where possible
- Enable CloudTrail for audit logging
- Implement least-privilege IAM policies
- Use encryption in transit and at rest for all data

## Advanced Deployment Patterns

### Multi-Environment Setup
For production deployments, consider setting up multiple environments:

```bash
# Development environment
sls deploy --stage dev --param="deployment-bucket=trader-dev-deployment"

# Staging environment  
sls deploy --stage staging --param="deployment-bucket=trader-staging-deployment"

# Production environment
sls deploy --stage prod --param="deployment-bucket=trader-prod-deployment"
```

### Blue-Green Deployment
For zero-downtime deployments:

```bash
# Deploy to blue environment
sls deploy --stage prod-blue --param="deployment-bucket=trader-prod-deployment"

# Test blue environment
# Switch traffic from green to blue
# Remove green environment when confident
sls remove --stage prod-green --param="deployment-bucket=trader-prod-deployment"
```

### Automated CI/CD Pipeline
Example GitHub Actions workflow for automated deployment:

```yaml
name: Deploy Services
on:
  push:
    branches: [main]
    
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Deploy Collection Service
        run: |
          cd collection/
          npm install
          pip install -r requirements.txt
          sls deploy --stage prod
      
      - name: Deploy Processing Service  
        run: |
          cd processing/
          npm install
          pip install -r requirements.txt
          sls deploy --stage prod
```

## Monitoring and Maintenance

### CloudWatch Dashboards
Create custom dashboards to monitor:
- Lambda function invocations, errors, and duration
- ECS task CPU and memory utilization
- S3 bucket metrics and costs
- DynamoDB read/write capacity units

### Automated Backup and Recovery
- Configure S3 versioning and lifecycle policies
- Set up DynamoDB point-in-time recovery
- Create automated snapshots of critical data
- Test disaster recovery procedures regularly

### Cost Management
- Set up AWS Budget alerts for unexpected costs
- Use AWS Cost Explorer to analyze spending patterns
- Implement resource tagging for cost allocation
- Consider Reserved Instances for predictable workloads

## Additional Resources

### Useful AWS CLI Commands
```bash
# Monitor Lambda function metrics
aws logs filter-log-events --log-group-name "/aws/lambda/trader-data-collection-dev"

# Check ECS service status
aws ecs describe-services --cluster trader-data-cluster-dev --services trader-data-service-dev

# List all resources with specific tags
aws resourcegroupstaggingapi get-resources --tag-filters Key=app_name,Values=TAGNAME-dev

# Check SSM parameter values
aws ssm get-parameters-by-path --path "/trader/dev" --recursive --with-decryption
```

### Learning Resources
- [AWS Serverless Application Model (SAM)](https://aws.amazon.com/serverless/sam/)
- [Serverless Framework Documentation](https://www.serverless.com/framework/docs/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [AWS Cost Optimization](https://aws.amazon.com/aws-cost-management/cost-optimization/)

---

For questions or issues with deployment, please:
1. Check the troubleshooting section above
2. Review the GitHub Issues for known problems
3. Create a new issue with detailed error logs
4. Follow the security guidelines when sharing information
