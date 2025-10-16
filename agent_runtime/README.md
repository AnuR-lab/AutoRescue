# AutoRescue Agent Runtime

AWS Bedrock AgentCore Runtime implementation using Strands framework for the AutoRescue Flight Assistant.

## Overview

This agent provides an AI-powered conversational interface for:
- **Flight Search**: Find available flights between airports
- **Disruption Management**: Analyze cancellations and find alternative flights

## Architecture

```
User Input
    ↓
AWS Bedrock AgentCore Runtime (Docker Container)
    ↓
AutoRescue Agent (Strands)
    ├── Bedrock Model (Claude Sonnet 4.5)
    ├── MCP Gateway Client (OAuth2)
    │   ├── search-flights tool
    │   └── analyze-disruption tool
    └── Custom Tools
        └── current_time
```

## Components

### 1. Agent (`autorescue_agent.py`)

**Key Features:**
- Built with `strands-agents` framework
- Uses `BedrockModel` for Claude Sonnet 4.5
- Connects to AgentCore Gateway via MCP protocol
- OAuth2 authentication with Cognito
- Professional system prompt for flight assistance

**Tools Available:**
1. **current_time**: Returns current date/time
2. **search-flights___searchFlights**: Search for flight offers
3. **analyze-disruption___analyzeDisruption**: Analyze disruptions and find alternatives

**Environment Variables:**
- `GATEWAY_URL`: AgentCore Gateway MCP endpoint
- `ACCESS_TOKEN`: OAuth2 bearer token from Cognito
- `BEDROCK_MODEL_ID`: Bedrock model to use (default: claude-sonnet-4-5-20250929-v1:0)

### 2. Dockerfile

Containerizes the agent for deployment to AWS:
- Base image: `python:3.12-slim`
- Installs dependencies from `requirements.txt`
- Exposes port 8080
- Runs via BedrockAgentCoreApp

### 3. Deployment Script (`deploy_agent_runtime.py`)

Automates deployment process:
1. Creates ECR repository
2. Builds and pushes Docker image
3. Creates IAM execution role
4. Provides configuration for AgentCore Runtime creation

### 4. Local Testing (`test_agent_local.py`)

Tests agent locally before deployment:
- Fetches OAuth2 token from Cognito
- Initializes agent with gateway connection
- Runs 3 test scenarios:
  - Flight search (JFK → LAX)
  - Disruption analysis (AA123 canceled)
  - General conversation

## Quick Start

###  Prerequisites

```bash
# Install Python dependencies
pip install bedrock-agentcore strands-agents boto3 requests

# Configure AWS credentials
aws configure
```

### Local Testing

**⚠️ Note**: Local testing requires AWS credentials configured in `~/.aws/credentials`. If using temporary credentials (e.g., from `assume`), the agent will initialize successfully but model invocations may fail with "Unable to locate credentials". This is expected behavior for local testing only.

```bash
# Activate virtual environment
source venv/bin/activate

# Test the agent locally
python scripts/test_agent_local.py
```

**Expected Output:**
```
✅ Agent initialized successfully
   Tools loaded: 3
   Tool names: [current_time, search-flights, analyze-disruption]
   
✅ Connected to gateway
✅ OAuth2 token obtained
```

**When deployed to AgentCore Runtime**, the IAM execution role will handle credentials automatically - no credential issues will occur in production.

### Deployment to AWS

```bash
# Run deployment script
python scripts/deploy_agent_runtime.py
```

**What it does:**
1. ✅ Creates ECR repository: `autorescue-agent`
2. ✅ Builds Docker image
3. ✅ Pushes image to ECR
4. ✅ Creates IAM role: `AutoRescueAgentRuntimeRole`
5. 📝 Outputs configuration for manual runtime creation

## Manual Runtime Creation

After running the deployment script, create the AgentCore Runtime:

### Using AWS Console

1. Navigate to **AWS Bedrock → AgentCore → Runtimes**
2. Click **Create Runtime**
3. Configure:
   - **Name**: `autorescue-agent`
   - **Description**: Flight booking and disruption management assistant
   - **Container image**: `<ACCOUNT>.dkr.ecr.us-east-1.amazonaws.com/autorescue-agent:latest`
   - **Execution role**: `AutoRescueAgentRuntimeRole`
   
4. **Environment variables**:
   ```
   GATEWAY_URL=https://autorescue-gateway-7ildpiqiqm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp
   ACCESS_TOKEN=<Get from Cognito OAuth2>
   BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
   ```

5. Click **Create**

### Using AWS CLI

```bash
# Create runtime (example - adjust based on actual API)
aws bedrock-agentcore-control create-runtime \
  --runtime-name autorescue-agent \
  --description "AutoRescue Flight Assistant" \
  --image-uri <ACCOUNT>.dkr.ecr.us-east-1.amazonaws.com/autorescue-agent:latest \
  --execution-role-arn arn:aws:iam::<ACCOUNT>:role/AutoRescueAgentRuntimeRole \
  --environment-variables \
    GATEWAY_URL=https://autorescue-gateway-7ildpiqiqm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp \
    ACCESS_TOKEN=<token> \
    BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0 \
  --region us-east-1
```

## Testing the Deployed Agent

### Invoke via SDK

```python
import boto3
import json

agentcore = boto3.client('bedrock-agentcore-runtime', region_name='us-east-1')

response = agentcore.invoke_agent(
    runtimeId='autorescue-agent',
    payload={
        'prompt': 'Find me flights from JFK to LAX on November 15, 2025'
    }
)

print(json.loads(response['body'].read()))
```

### Expected Response

```json
{
  "response": "I found 3 available flights from JFK to LAX on November 15, 2025:\n\n1. JetBlue B6 623\n   - Departs: 9:00 AM\n   - Arrives: 12:19 PM\n   - Duration: 6h 19m\n   - Price: $123.44 USD\n\n2. JetBlue B6 323\n   - Departs: 10:00 AM\n   - Arrives: 1:19 PM\n   - Duration: 6h 19m\n   - Price: $123.44 USD\n\n3. JetBlue B6 723\n   - Departs: 2:00 PM\n   - Arrives: 5:19 PM\n   - Duration: 6h 19m\n   - Price: $123.44 USD\n\nWould you like to book one of these flights?",
  "model": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "gateway": "https://autorescue-gateway-7ildpiqiqm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
}
```

## System Prompt

The agent uses a comprehensive system prompt that:
- Defines its role as AutoRescue flight assistant
- Lists available capabilities (search, disruptions)
- Provides guidelines for professional interaction
- Explains tool usage and parameters
- Emphasizes empathy for disrupted passengers

## Dependencies

```
bedrock-agentcore    # AgentCore Runtime framework
strands-agents      # Strands agent framework
boto3==1.40.52       # AWS SDK
requests==2.32.5     # HTTP client
```

## Configuration

### Gateway Configuration
- **Gateway ID**: `autorescue-gateway-7ildpiqiqm`
- **Gateway URL**: `https://autorescue-gateway-7ildpiqiqm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp`
- **Authentication**: OAuth2 Client Credentials (Cognito)

### Cognito OAuth2
- **Credentials**: Stored in AWS Secrets Manager (`autorescue/cognito/credentials`)
- **Token URL**: `https://autorescue-1760552868.auth.us-east-1.amazoncognito.com/oauth2/token`
- **Grant Type**: `client_credentials`
- **Scopes**: `autorescue-api/flights.read`, `flights.search`, `disruptions.analyze`

### Model Configuration
- **Default Model**: `us.anthropic.claude-sonnet-4-5-20250929-v1:0`
- **Region**: `us-east-1`

## Troubleshooting

### Agent initialization fails
- Verify AWS credentials are configured
- Check `ACCESS_TOKEN` environment variable
- Ensure gateway URL is correct

### Gateway connection fails
- Verify gateway is in READY status
- Check OAuth token hasn't expired (1-hour TTL)
- Confirm network connectivity to gateway

### Tool calls fail
- Verify gateway targets are in READY status
- Check Lambda functions are deployed
- Review Lambda execution role permissions

### Model invocation fails
- Confirm Bedrock model access in region
- Verify execution role has Bedrock permissions
- Check model ID is correct

## Next Steps

1. ✅ **Agent Runtime Created**: Agent is containerized and ready
2. ⏸️  **Deploy to AgentCore**: Create runtime in AWS Console/CLI
3. ⏸️  **Test in Production**: Invoke agent via SDK/API
4. ⏸️  **Add Monitoring**: CloudWatch logs and metrics
5. ⏸️  **Build Frontend**: Streamlit/React UI for user interaction

## Resources

- [AWS Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Strands Agents Framework](https://github.com/anthropics/strands)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [AutoRescue Gateway](../GATEWAY_TEST_RESULTS.md)
- [Deployment Guide](../DEPLOY.md)
