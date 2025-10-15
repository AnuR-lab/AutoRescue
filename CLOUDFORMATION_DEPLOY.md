# AutoRescue CloudFormation Deployment Guide

This guide explains how to deploy AutoRescue infrastructure using AWS CloudFormation.

## Overview

The CloudFormation template (`cloudformation.yaml`) deploys:
- **2 Lambda Functions**: Search Flights and Analyze Disruption
- **IAM Roles**: For Lambda execution with CloudWatch logging
- **CloudWatch Log Groups**: For Lambda function logs
- **EC2 Instance** (Optional): For Streamlit UI

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. AWS account with permissions to create:
   - Lambda functions
   - IAM roles
   - EC2 instances
   - CloudWatch log groups

## Deployment Options

### Option 1: Deploy via AWS CLI

#### Basic Deployment (Lambdas only)

```bash
aws cloudformation create-stack \
  --stack-name autorescue-stack \
  --template-body file://cloudformation.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters \
    ParameterKey=AmadeusClientID,ParameterValue=YOUR_AMADEUS_CLIENT_ID \
    ParameterKey=AmadeusClientSecret,ParameterValue=YOUR_AMADEUS_CLIENT_SECRET
```

#### Full Deployment (Lambdas + EC2)

```bash
aws cloudformation create-stack \
  --stack-name autorescue-stack \
  --template-body file://cloudformation.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters \
    ParameterKey=AmadeusClientID,ParameterValue=YOUR_AMADEUS_CLIENT_ID \
    ParameterKey=AmadeusClientSecret,ParameterValue=YOUR_AMADEUS_CLIENT_SECRET \
    ParameterKey=KeyName,ParameterValue=your-ec2-key-pair \
    ParameterKey=InstanceType,ParameterValue=t2.small
```

### Option 2: Deploy via AWS Console

1. **Open CloudFormation Console**
   - Go to: https://console.aws.amazon.com/cloudformation/

2. **Create Stack**
   - Click "Create stack" → "With new resources (standard)"
   - Choose "Upload a template file"
   - Upload `cloudformation.yaml`
   - Click "Next"

3. **Specify Stack Details**
   - **Stack name**: `autorescue-stack`
   - **Parameters**:
     - `AmadeusClientID`: Your Amadeus API client ID
     - `AmadeusClientSecret`: Your Amadeus API client secret
     - `KeyName`: (Optional) Your EC2 key pair name
     - `InstanceType`: (Optional) EC2 instance size

4. **Configure Stack Options**
   - Add tags if desired
   - Click "Next"

5. **Review**
   - Check "I acknowledge that AWS CloudFormation might create IAM resources with custom names"
   - Click "Create stack"

6. **Monitor Progress**
   - Watch the "Events" tab for progress
   - Wait for status: `CREATE_COMPLETE`

## Parameters

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `AmadeusClientID` | [DEPRECATED] Amadeus API Client ID - Now in Secrets Manager | PLACEHOLDER | No |
| `AmadeusClientSecret` | [DEPRECATED] Amadeus API Client Secret - Now in Secrets Manager | PLACEHOLDER | No |
| `KeyName` | EC2 Key Pair for SSH access | (empty) | No |
| `InstanceType` | EC2 instance type | t2.micro | No |

## Stack Outputs

After successful deployment, the stack provides these outputs:

### Lambda Outputs
- `SearchFlightsLambdaArn`: ARN of the Search Flights function
- `SearchFlightsLambdaName`: Name of the Search Flights function
- `AnalyzeDisruptionLambdaArn`: ARN of the Analyze Disruption function
- `AnalyzeDisruptionLambdaName`: Name of the Analyze Disruption function

### EC2 Outputs (if deployed)
- `InstanceId`: EC2 instance ID
- `PublicIP`: Public IP address
- `StreamlitURL`: URL to access Streamlit UI
- `SSHCommand`: SSH command to connect to instance

### Retrieve Outputs via CLI

```bash
aws cloudformation describe-stacks \
  --stack-name autorescue-stack \
  --query 'Stacks[0].Outputs'
```

## Post-Deployment Steps

### 1. Test Lambda Functions

#### Test Search Flights Lambda

```bash
aws lambda invoke \
  --function-name AutoRescue-SearchFlights \
  --payload '{"origin":"JFK","destination":"LAX","departureDate":"2025-12-25","adults":1}' \
  response.json

cat response.json
```

#### Test Analyze Disruption Lambda

```bash
aws lambda invoke \
  --function-name AutoRescue-AnalyzeDisruption \
  --payload '{"flightNumber":"AA123","origin":"JFK","destination":"LAX","originalDate":"2025-11-15","disruptionType":"cancellation"}' \
  response.json

cat response.json
```

### 2. Create AgentCore Gateway

The Lambda functions are now deployed. Next, create the AgentCore Gateway and targets:

```bash
# Run the gateway setup script
python3 scripts/setup_gateway.py
```

Or manually create gateway targets pointing to:
- Search Flights Lambda: `AutoRescue-SearchFlights`
- Analyze Disruption Lambda: `AutoRescue-AnalyzeDisruption`

### 3. Deploy Agent Runtime

```bash
cd agent_runtime
agentcore launch
```

### 4. Access Streamlit UI (if deployed)

Get the Streamlit URL from stack outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name autorescue-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`StreamlitURL`].OutputValue' \
  --output text
```

## Updating the Stack

To update the stack with changes:

```bash
aws cloudformation update-stack \
  --stack-name autorescue-stack \
  --template-body file://cloudformation.yaml \
  --capabilities CAPABILITY_NAMED_IAM
```

## Deleting the Stack

To remove all resources:

```bash
aws cloudformation delete-stack --stack-name autorescue-stack
```

**Note**: This will delete:
- Both Lambda functions
- IAM roles
- CloudWatch log groups
- EC2 instance (if deployed)

The AgentCore Gateway and runtime must be deleted separately.

## Troubleshooting

### Stack Creation Failed

Check the CloudFormation events:

```bash
aws cloudformation describe-stack-events \
  --stack-name autorescue-stack \
  --max-items 20
```

### Lambda Function Not Working

Check CloudWatch logs:

```bash
# Search Flights logs
aws logs tail /aws/lambda/AutoRescue-SearchFlights --follow

# Analyze Disruption logs
aws logs tail /aws/lambda/AutoRescue-AnalyzeDisruption --follow
```

### IAM Permission Issues

Ensure your AWS user/role has these permissions:
- `cloudformation:*`
- `lambda:*`
- `iam:CreateRole`
- `iam:AttachRolePolicy`
- `logs:CreateLogGroup`
- `ec2:*` (if deploying EC2)

## Cost Estimation

### Lambda Costs
- **Free Tier**: 1M requests/month, 400,000 GB-seconds compute
- **After Free Tier**: $0.20 per 1M requests + $0.0000166667 per GB-second

### EC2 Costs (if deployed)
- **t2.micro**: ~$8.50/month (Free tier: 750 hours/month for first 12 months)
- **t2.small**: ~$17/month
- **t2.medium**: ~$34/month

### CloudWatch Logs
- **Free Tier**: 5GB ingestion, 5GB archive
- **After Free Tier**: $0.50 per GB ingested

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│           AWS CloudFormation Stack              │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────────────────────────────┐      │
│  │  Lambda Functions                    │      │
│  │  ├─ AutoRescue-SearchFlights        │      │
│  │  └─ AutoRescue-AnalyzeDisruption    │      │
│  └──────────────────────────────────────┘      │
│                    │                            │
│                    ↓                            │
│  ┌──────────────────────────────────────┐      │
│  │  IAM Roles                           │      │
│  │  ├─ SearchFlightsLambdaRole         │      │
│  │  └─ AnalyzeDisruptionLambdaRole     │      │
│  └──────────────────────────────────────┘      │
│                    │                            │
│                    ↓                            │
│  ┌──────────────────────────────────────┐      │
│  │  CloudWatch Log Groups               │      │
│  │  ├─ /aws/lambda/AutoRescue-*        │      │
│  └──────────────────────────────────────┘      │
│                                                 │
│  ┌──────────────────────────────────────┐      │
│  │  EC2 Instance (Optional)             │      │
│  │  └─ Streamlit UI Server              │      │
│  └──────────────────────────────────────┘      │
│                                                 │
└─────────────────────────────────────────────────┘
                    │
                    ↓
        ┌───────────────────────┐
        │   Amadeus Flight API  │
        └───────────────────────┘
```

## Additional Resources

- [AWS CloudFormation Documentation](https://docs.aws.amazon.com/cloudformation/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Amadeus for Developers](https://developers.amadeus.com/)
- [AutoRescue Deployment Guide](DEPLOY.md)
