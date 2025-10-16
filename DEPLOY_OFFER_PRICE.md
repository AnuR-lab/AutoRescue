# Deploying the Offer Price Lambda Function

## Overview

This guide explains how to deploy the new `AutoRescue-OfferPrice` Lambda function to AWS.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Access to AWS account (905418267822)
- Amadeus API credentials stored in AWS Secrets Manager

## Deployment Options

### Option 1: Deploy via CloudFormation Stack Update (Recommended)

If you already have the AutoRescue Lambda stack deployed:

```bash
# Navigate to project root
cd /Users/kiranbhagwat/sources/AutoRescue

# Update the existing CloudFormation stack
aws cloudformation update-stack \
  --stack-name AutoRescue-Lambdas \
  --template-body file://cloudformation-lambdas-only.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Monitor the update
aws cloudformation wait stack-update-complete \
  --stack-name AutoRescue-Lambdas \
  --region us-east-1

# Get the Lambda ARN
aws cloudformation describe-stacks \
  --stack-name AutoRescue-Lambdas \
  --query 'Stacks[0].Outputs[?OutputKey==`OfferPriceLambdaArn`].OutputValue' \
  --output text \
  --region us-east-1
```

### Option 2: Deploy Fresh Stack

If this is a new deployment:

```bash
# Create the CloudFormation stack
aws cloudformation create-stack \
  --stack-name AutoRescue-Lambdas \
  --template-body file://cloudformation-lambdas-only.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1 \
  --tags Key=Application,Value=AutoRescue Key=Environment,Value=Production

# Wait for stack creation
aws cloudformation wait stack-create-complete \
  --stack-name AutoRescue-Lambdas \
  --region us-east-1

# Get all Lambda ARNs
aws cloudformation describe-stacks \
  --stack-name AutoRescue-Lambdas \
  --query 'Stacks[0].Outputs' \
  --output table \
  --region us-east-1
```

### Option 3: Deploy Using Local Files (Development)

For development/testing with the actual Lambda code from `lambda_functions/offer_price/`:

```bash
# Navigate to the lambda function directory
cd lambda_functions/offer_price

# Install dependencies
pip install -r requirements.txt -t .

# Create deployment package
zip -r offer_price.zip . -x "*.pyc" -x "__pycache__/*"

# Create the Lambda function (if it doesn't exist)
aws lambda create-function \
  --function-name AutoRescue-OfferPrice \
  --runtime python3.12 \
  --role arn:aws:iam::905418267822:role/AutoRescue-OfferPrice-Role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://offer_price.zip \
  --timeout 30 \
  --memory-size 256 \
  --region us-east-1

# Or update existing function
aws lambda update-function-code \
  --function-name AutoRescue-OfferPrice \
  --zip-file fileb://offer_price.zip \
  --region us-east-1

# Clean up
rm offer_price.zip
```

## Post-Deployment Steps

### 1. Verify Lambda Deployment

```bash
# Check Lambda function exists
aws lambda get-function \
  --function-name AutoRescue-OfferPrice \
  --region us-east-1

# Check function configuration
aws lambda get-function-configuration \
  --function-name AutoRescue-OfferPrice \
  --region us-east-1
```

### 2. Test the Lambda Function

```bash
# Create test event
cat > test-event.json << 'EOF'
{
  "body": "{\"flight_offer\": {\"type\": \"flight-offer\", \"id\": \"1\", \"source\": \"GDS\", \"price\": {\"currency\": \"USD\", \"total\": \"350.00\"}}}"
}
EOF

# Invoke Lambda function
aws lambda invoke \
  --function-name AutoRescue-OfferPrice \
  --payload file://test-event.json \
  --region us-east-1 \
  response.json

# View response
cat response.json

# Clean up
rm test-event.json response.json
```

### 3. Add Lambda to AgentCore Gateway

After deployment, add the Lambda as a gateway target:

```bash
# Get the Lambda ARN
LAMBDA_ARN=$(aws lambda get-function \
  --function-name AutoRescue-OfferPrice \
  --query 'Configuration.FunctionArn' \
  --output text \
  --region us-east-1)

echo "Lambda ARN: $LAMBDA_ARN"

# Use the add_gateway_targets.py script
cd /Users/kiranbhagwat/sources/AutoRescue
python3 scripts/add_gateway_targets.py \
  --gateway-id <YOUR_GATEWAY_ID> \
  --lambda-arn $LAMBDA_ARN \
  --tool-name priceFlightOffer \
  --tool-definition mcp_tools/offer_price.json
```

### 4. Update Agent Runtime Configuration

Ensure the agent runtime knows about the new tool:

```bash
# Redeploy the agent runtime to pick up the new tool
# (This depends on your agent deployment method)
```

## Verification

### Test the Complete Workflow

1. **Search for flights** (using searchFlights tool)
2. **Select a flight** from results
3. **Price the flight** (using priceFlightOffer tool)

Example agent query:

```
"Search for flights from JFK to LAX on 2025-10-20, then price the cheapest option"
```

## Troubleshooting

### Issue: Lambda deployment fails

**Check IAM permissions:**

```bash
aws iam get-role --role-name AutoRescue-OfferPrice-Role
```

**Check if role exists:**
If not, the CloudFormation template will create it automatically.

### Issue: Lambda can't access Secrets Manager

**Verify secret exists:**

```bash
aws secretsmanager get-secret-value \
  --secret-id autorescue/amadeus/credentials \
  --region us-east-1
```

**Check IAM policy:**
The Lambda role should have `secretsmanager:GetSecretValue` permission.

### Issue: Lambda timeout or errors

**Check CloudWatch Logs:**

```bash
aws logs tail /aws/lambda/AutoRescue-OfferPrice \
  --follow \
  --region us-east-1
```

**Increase timeout if needed:**

```bash
aws lambda update-function-configuration \
  --function-name AutoRescue-OfferPrice \
  --timeout 60 \
  --region us-east-1
```

## Monitoring

### View Lambda Metrics

```bash
# View invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=AutoRescue-OfferPrice \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-east-1
```

### View Recent Logs

```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/AutoRescue-OfferPrice \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --region us-east-1
```

## Cost Estimates

- **Lambda execution:** ~$0.20 per 1M requests + compute time
- **Secrets Manager:** $0.40/month per secret + $0.05 per 10K API calls
- **CloudWatch Logs:** $0.50/GB ingested

Expected monthly cost for moderate usage: **< $5**

## Next Steps

1. ✅ Deploy Lambda function
2. ⏭️ Add to AgentCore Gateway
3. ⏭️ Test with agent runtime
4. ⏭️ Monitor logs and metrics
5. ⏭️ Update documentation with actual ARNs

## Quick Deploy Command

For a complete deployment:

```bash
cd /Users/kiranbhagwat/sources/AutoRescue
aws cloudformation update-stack \
  --stack-name AutoRescue-Lambdas \
  --template-body file://cloudformation-lambdas-only.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1 && \
aws cloudformation wait stack-update-complete \
  --stack-name AutoRescue-Lambdas \
  --region us-east-1 && \
echo "✅ Deployment complete!"
```

---

**Ready to deploy!** Choose the deployment option that best fits your needs.
