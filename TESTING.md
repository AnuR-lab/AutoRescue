# Runtime Testing Guide

This document explains how to test the AutoRescue agent runtime.

## Prerequisites

1. **AWS Credentials**: Ensure your AWS credentials are configured with access to:
   - Bedrock AgentCore
   - AWS Secrets Manager (for retrieving the runtime ARN)
2. **Environment Variables**: Optional - configure for local development overrides

## Architecture: Secrets Management

The AutoRescue project uses **AWS Secrets Manager** to securely store sensitive configuration like the Agent Runtime ARN. This provides:

- ✅ **Centralized secrets management**
- ✅ **No secrets in version control**
- ✅ **Easy rotation and updates**
- ✅ **Access control via IAM policies**
- ✅ **Automatic retrieval in production**

### How It Works

1. **Priority Order**: The application checks for secrets in this order:
   - Environment variables (`.env` file) - for local development override
   - AWS Secrets Manager - production/default

2. **Automatic Fallback**: If not found locally, automatically retrieves from AWS Secrets Manager

3. **Caching**: Secrets are cached in memory to minimize API calls

## Setup

### Option 1: Use AWS Secrets Manager (Recommended for Production)

The Agent Runtime ARN is already stored in AWS Secrets Manager. No local configuration needed!

```bash
# Just run the test - it will automatically fetch from Secrets Manager
python3 scripts/runtime_test.py
```

### Option 2: Local Development Override

For local development, you can override with environment variables:

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit `.env` and uncomment the `AGENT_RUNTIME_ARN` line:

```bash
# Uncomment this line for local override:
AGENT_RUNTIME_ARN=arn:aws:bedrock-agentcore:us-east-1:YOUR_ACCOUNT_ID:runtime/YOUR_RUNTIME_NAME
```

**Note:** The `.env` file is gitignored and never committed.

## Managing Secrets in AWS Secrets Manager

Use the provided management script to interact with secrets:

### List All Secrets

```bash
python3 scripts/manage_secrets.py list
```

### View a Secret

```bash
python3 scripts/manage_secrets.py get autorescue/agent-runtime-arn
```

### Update a Secret

```bash
python3 scripts/manage_secrets.py update autorescue/agent-runtime-arn \
  --arn "arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:runtime/NAME"
```

### Create a New Secret

```bash
python3 scripts/manage_secrets.py create autorescue/my-new-secret \
  --arn "arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:runtime/NAME" \
  --description "Description of the secret"
```

### Delete a Secret

```bash
python3 scripts/manage_secrets.py delete autorescue/agent-runtime-arn
```

## Running Tests

### Runtime Test

Test the agent runtime with a sample flight search query:

```bash
python3 scripts/runtime_test.py
```

This will:

1. Try to load `AGENT_RUNTIME_ARN` from `.env` (if exists)
2. If not found, automatically retrieve from AWS Secrets Manager
3. Connect to the Bedrock AgentCore runtime
4. Send a test query for flight search
5. Display the agent's response

### Expected Output

```
✓ Successfully retrieved ARN from AWS Secrets Manager
Agent Response: {
  "response": "Flight search results...",
  "model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
  "gateway": "https://your-gateway.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
}
```

Or with local override:

```
✓ Using AGENT_RUNTIME_ARN from environment variable
Agent Response: {...}
```

## Environment Variables Reference

| Variable            | Description                       | Required | Default              | Source                        |
| ------------------- | --------------------------------- | -------- | -------------------- | ----------------------------- |
| `AGENT_RUNTIME_ARN` | ARN of the deployed agent runtime | No\*     | From Secrets Manager | AWS Secrets Manager or `.env` |
| `AWS_REGION`        | AWS region for Bedrock            | No       | `us-east-1`          | `.env`                        |
| `GATEWAY_URL`       | MCP Gateway URL                   | No       | From deployment      | `.env`                        |
| `ACCESS_TOKEN`      | OAuth2 access token               | No       | Fetched dynamically  | `.env`                        |
| `BEDROCK_MODEL_ID`  | Bedrock model identifier          | No       | Claude 3.5 Sonnet    | `.env`                        |

\* Not required if using AWS Secrets Manager (recommended)

## Troubleshooting

### Error: "Failed to retrieve AGENT_RUNTIME_ARN"

**Cause:** Secret not found in AWS Secrets Manager and not in environment.

**Solution:**

```bash
# Check if the secret exists
python3 scripts/manage_secrets.py list

# If it doesn't exist, create it
python3 scripts/manage_secrets.py create autorescue/agent-runtime-arn \
  --arn "arn:aws:bedrock-agentcore:us-east-1:YOUR_ACCOUNT:runtime/YOUR_NAME"
```

### Error: "AccessDeniedException" for Secrets Manager

**Cause:** IAM permissions missing for Secrets Manager.

**Solution:** Add the following IAM policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:autorescue/*"
    }
  ]
}
```

### Error: "AccessDeniedException" for Bedrock

**Solution:** Check your AWS credentials:

```bash
aws sts get-caller-identity
```

### Error: "The security token included in the request is expired"

**Solution:** Refresh your AWS credentials:

```bash
aws sso login
# or
aws configure
```

## Security Best Practices

### Production

1. ✅ Store all secrets in AWS Secrets Manager
2. ✅ Use IAM roles with least privilege access
3. ✅ Enable CloudTrail for audit logging
4. ✅ Rotate secrets regularly (use Lambda for automation)
5. ✅ Use KMS for encryption at rest

### Development

1. ✅ Use `.env` file for local overrides only
2. ✅ Never commit `.env` file to version control
3. ✅ Use environment-specific configurations
4. ✅ Clear secrets cache when testing updates

### Git Security

```bash
# Verify .env is gitignored
git status

# The .env file should NOT appear in untracked files
```

## Secrets Management CLI Reference

### List Secrets

```bash
python3 scripts/manage_secrets.py list [--region REGION]
```

### Get Secret

```bash
python3 scripts/manage_secrets.py get SECRET_NAME [--region REGION]
```

### Create Secret

```bash
python3 scripts/manage_secrets.py create SECRET_NAME \
  --arn ARN_VALUE \
  [--description "Description"] \
  [--region REGION]
```

### Update Secret

```bash
python3 scripts/manage_secrets.py update SECRET_NAME \
  --arn NEW_ARN_VALUE \
  [--region REGION]
```

### Delete Secret

```bash
python3 scripts/manage_secrets.py delete SECRET_NAME \
  [--force] \
  [--region REGION]
```

## Additional Resources

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
- [AWS Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/)
- [Python-dotenv Documentation](https://pypi.org/project/python-dotenv/)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
