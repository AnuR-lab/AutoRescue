# Lambda-Based Architecture Deployment Guide

## Overview

AutoRescue now uses **AWS Lambda functions as separate tool targets**, matching the AWS Bedrock AgentCore Gateway architecture. This provides:

- ✅ Independent scaling per tool
- ✅ Better security isolation
- ✅ Easier testing and debugging
- ✅ Follows AWS best practices

## Architecture

```
Customer → AgentCore Runtime (Agent) → AgentCore Gateway → Lambda Functions → Amadeus API
                                      ↓                    ↓
                                  OAuth 2.0         AWS Lambda Targets:
                                  (Cognito)         1. AutoRescue-SearchFlights
                                                   2. AutoRescue-AnalyzeDisruption
```

## Lambda Functions

### 1. AutoRescue-SearchFlights
- **Purpose**: Search for flight offers
- **Handler**: `lambda_function.lambda_handler`
- **Runtime**: Python 3.12
- **Timeout**: 30 seconds
- **Memory**: 256 MB
- **API**: Amadeus Flight Offers Search API

### 2. AutoRescue-AnalyzeDisruption
- **Purpose**: Analyze flight disruptions and provide rebooking recommendations
- **Handler**: `lambda_function.lambda_handler`
- **Runtime**: Python 3.12
- **Timeout**: 30 seconds
- **Memory**: 256 MB
- **API**: Amadeus Flight Offers Search API (multi-date search)

## Deployment Steps

### Step 1: Deploy Lambda Functions

```bash
# Deploy both Lambda functions with dependencies
./scripts/deploy_lambdas.sh
```

This script will:
1. Create IAM role `AutoRescueLambdaExecutionRole` if needed
2. Package Python dependencies for each Lambda
3. Deploy/update both Lambda functions
4. Configure environment variables (Amadeus credentials)

**Expected Output:**
```
=== AutoRescue Lambda Functions Deployment ===

✓ IAM role 'AutoRescueLambdaExecutionRole' already exists
Role ARN: arn:aws:iam::123456789012:role/AutoRescueLambdaExecutionRole

Deploying AutoRescue-SearchFlights...
  Installing dependencies...
  Package size: 2.3M
  ✓ Created function: AutoRescue-SearchFlights
  ARN: arn:aws:lambda:us-east-1:123456789012:function:AutoRescue-SearchFlights

Deploying AutoRescue-AnalyzeDisruption...
  Installing dependencies...
  Package size: 2.3M
  ✓ Created function: AutoRescue-AnalyzeDisruption
  ARN: arn:aws:lambda:us-east-1:123456789012:function:AutoRescue-AnalyzeDisruption

=== Deployment Complete ===
```

### Step 2: Create AgentCore Gateway

```bash
# Gateway will automatically discover and register Lambda functions
python scripts/agentcore_gateway.py create --name autorescue-gw
```

This will:
1. Discover deployed Lambda functions
2. Create OpenAPI specification with Lambda integrations
3. Register Lambda ARNs as tool targets
4. Store configuration in SSM Parameter Store

**Expected Output:**
```
🚀 Creating AgentCore Gateway: autorescue-gw
✓ Found Lambda: AutoRescue-SearchFlights
✓ Found Lambda: AutoRescue-AnalyzeDisruption
✅ Gateway configuration created: gateway.config
   Gateway Name: autorescue-gw
   API Endpoints: 2
   Lambda Targets:
     - search-flights → arn:aws:lambda:us-east-1:123456789012:function:AutoRescue-SearchFlights
     - analyze-disruption → arn:aws:lambda:us-east-1:123456789012:function:AutoRescue-AnalyzeDisruption
```

### Step 3: Setup Cognito Authentication

```bash
# Create Cognito user pool and app client
python scripts/cognito_credentials_provider.py create --name autorescue-gateways
```

### Step 4: Create AgentCore Memory

```bash
# Create memory store for conversation context
python scripts/agentcore_memory.py create --name autorescue
```

### Step 5: Configure Agent

```bash
# Configure AgentCore agent with Lambda-backed tools
agentcore configure \
  --entrypoint main.py \
  --execution-role <LAMBDA_EXECUTION_ROLE_ARN> \
  --name autorescue-flight-assistant \
  --model us.anthropic.claude-3-5-sonnet-20241022-v2:0
```

### Step 6: Launch Agent

```bash
# Launch the agent
agentcore launch
```

## Testing Lambda Functions

### Test Search Flights Lambda

```bash
aws lambda invoke \
  --function-name AutoRescue-SearchFlights \
  --payload '{
    "origin": "JFK",
    "destination": "LAX",
    "departure_date": "2025-12-15",
    "adults": 1,
    "max_results": 5
  }' \
  --region us-east-1 \
  response.json

cat response.json | jq
```

### Test Analyze Disruption Lambda

```bash
aws lambda invoke \
  --function-name AutoRescue-AnalyzeDisruption \
  --payload '{
    "original_flight": "AA123",
    "origin": "JFK",
    "destination": "LAX",
    "original_date": "2025-12-15",
    "disruption_reason": "cancellation"
  }' \
  --region us-east-1 \
  response.json

cat response.json | jq
```

## Lambda Function Structure

Each Lambda function follows this structure:

```
lambda_functions/
├── search_flights/
│   ├── lambda_function.py      # Main handler
│   ├── requirements.txt        # Dependencies
│   └── deployment.zip          # (generated during deployment)
└── analyze_disruption/
    ├── lambda_function.py      # Main handler
    ├── requirements.txt        # Dependencies
    └── deployment.zip          # (generated during deployment)
```

## Environment Variables

Both Lambda functions use:

- `AMADEUS_CLIENT_ID`: Amadeus API client ID (from SSM or env)
- `AMADEUS_CLIENT_SECRET`: Amadeus API client secret (from SSM or env)

## IAM Permissions

The `AutoRescueLambdaExecutionRole` has:

1. **Basic Lambda Execution** (`AWSLambdaBasicExecutionRole`)
   - CloudWatch Logs write permissions
   
2. **SSM Read Access** (`AmazonSSMReadOnlyAccess`)
   - Read configuration parameters
   
3. **VPC Access** (if needed)
   - EC2 network interface management

## Monitoring

### CloudWatch Logs

Each Lambda function logs to:
- `/aws/lambda/AutoRescue-SearchFlights`
- `/aws/lambda/AutoRescue-AnalyzeDisruption`

View logs:
```bash
# Search Flights logs
aws logs tail /aws/lambda/AutoRescue-SearchFlights --follow

# Analyze Disruption logs
aws logs tail /aws/lambda/AutoRescue-AnalyzeDisruption --follow
```

### CloudWatch Metrics

Monitor Lambda metrics:
- Invocations
- Duration
- Errors
- Throttles
- Concurrent executions

## Updating Lambda Functions

### Update Function Code

```bash
# Re-run deployment script
./scripts/deploy_lambdas.sh
```

### Update Function Configuration

```bash
# Update timeout
aws lambda update-function-configuration \
  --function-name AutoRescue-SearchFlights \
  --timeout 60 \
  --region us-east-1

# Update memory
aws lambda update-function-configuration \
  --function-name AutoRescue-SearchFlights \
  --memory-size 512 \
  --region us-east-1
```

## Troubleshooting

### Lambda Not Found Error

**Error**: `Lambda functions not found. Please deploy them first`

**Solution**:
```bash
./scripts/deploy_lambdas.sh
```

### Amadeus API Authentication Error

**Error**: `401 Unauthorized from Amadeus API`

**Solution**:
```bash
# Update environment variables
aws lambda update-function-configuration \
  --function-name AutoRescue-SearchFlights \
  --environment "Variables={AMADEUS_CLIENT_ID=your_id,AMADEUS_CLIENT_SECRET=your_secret}" \
  --region us-east-1
```

### Timeout Error

**Error**: `Task timed out after 30.00 seconds`

**Solution**:
```bash
# Increase timeout to 60 seconds
aws lambda update-function-configuration \
  --function-name AutoRescue-SearchFlights \
  --timeout 60 \
  --region us-east-1
```

### Package Too Large Error

**Error**: `Deployment package size exceeds limit`

**Solution**:
1. Use Lambda Layers for dependencies
2. Remove unnecessary packages
3. Use S3 for deployment packages

## Cost Optimization

### Lambda Pricing
- **Free Tier**: 1M requests/month + 400,000 GB-seconds compute
- **After Free Tier**: 
  - $0.20 per 1M requests
  - $0.0000166667 per GB-second

### Optimization Tips
1. **Right-size memory**: Start with 256 MB, monitor and adjust
2. **Cache tokens**: Both functions cache Amadeus OAuth tokens (1500s)
3. **Set appropriate timeouts**: 30 seconds is usually sufficient
4. **Use provisioned concurrency** only if needed for latency

## Security Best Practices

1. **Credentials Management**
   - Store Amadeus credentials in AWS Secrets Manager or SSM Parameter Store
   - Never hardcode credentials in Lambda code
   - Use IAM roles for AWS service access

2. **Network Security**
   - Deploy Lambda in VPC if accessing private resources
   - Use security groups to restrict outbound traffic
   - Enable VPC endpoints for AWS services

3. **Function Security**
   - Enable AWS X-Ray for tracing
   - Set resource-based policies to control who can invoke
   - Enable CloudTrail logging

## Next Steps

After successful deployment:

1. **Test the complete flow**:
   ```bash
   # Test via AgentCore
   agentcore test --query "Find flights from JFK to LAX on December 15"
   ```

2. **Monitor performance**:
   - Check CloudWatch dashboards
   - Review Lambda metrics
   - Analyze costs in Cost Explorer

3. **Scale as needed**:
   - Adjust Lambda memory/timeout
   - Configure auto-scaling for AgentCore
   - Set up alarms for errors

## Additional Resources

- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [AgentCore Gateway Documentation](https://docs.aws.amazon.com/bedrock/agentcore/)
- [Amadeus API Documentation](https://developers.amadeus.com/)
