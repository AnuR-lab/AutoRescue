# AutoRescue Deployment Scripts

This directory contains scripts for deploying and managing the AutoRescue agent and Lambda functions.

## 📋 Available Scripts

### Agent Management

#### `update_agent.sh` / `update_agent.py`
**Purpose**: Update the AgentCore runtime with the latest code changes

**What it does**:
1. Builds the Docker image with your latest code
2. Pushes the image to AWS ECR
3. Updates the AgentCore runtime to use the new image

**Usage**:
```bash
# Using shell script
./scripts/update_agent.sh

# Or using Python script
python scripts/update_agent.py
```

**When to use**:
- After making changes to `agent_runtime/autorescue_agent.py`
- After updating the agent's system prompt
- After changing environment variables in `Dockerfile`
- After updating Python dependencies

---

### Lambda Functions

#### `deploy_lambdas.sh`
**Purpose**: Deploy Lambda functions to AWS

**What it does**:
1. Packages Lambda function code with dependencies
2. Creates deployment zip files
3. Updates Lambda functions in AWS

**Usage**:
```bash
./scripts/deploy_lambdas.sh
```

**When to use**:
- After making changes to Lambda function code
- After updating Lambda dependencies (requirements.txt)
- When deploying new Lambda functions

---

#### `test_search_flights.py`
**Purpose**: Test the SearchFlights Lambda function

**What it does**:
1. Invokes the Lambda function with test data
2. Validates the response
3. Displays flight search results

**Usage**:
```bash
python scripts/test_search_flights.py
```

**Sample output**:
```
✅ Flight search successful!
📊 Found 5 flights
🛫 Route: JFK → LAX
📅 Date: 2025-10-23

💰 Flight Options:
  1. $271.92 USD - Duration: PT13H52M
     Segment 1: JFK → BOS
       B61318 - PT1H17M
     Segment 2: BOS → LAX
       B6687 - PT6H17M
```

---

#### `test_agent_local.py`
**Purpose**: Test the agent locally before deployment

**What it does**:
1. Fetches OAuth2 token from Cognito
2. Initializes the agent with gateway connection
3. Runs test scenarios (flight search, disruption analysis)

**Usage**:
```bash
cd agent_runtime
python ../scripts/test_agent_local.py
```

**Note**: Requires Cognito credentials to be configured in environment or Secrets Manager.

---

### Utility Scripts

#### `create_agent_version.py`
**Purpose**: Create a new version of the AgentCore runtime

**What it does**:
- Forces creation of a new agent version
- Useful for ensuring the latest image is pulled

**Usage**:
```bash
cd agent_runtime
python ../scripts/create_agent_version.py
```

---

#### `force_runtime_restart.py`
**Purpose**: Force the AgentCore runtime to restart

**What it does**:
- Triggers CodeBuild to redeploy the runtime
- Forces the runtime to pull the latest Docker image from ECR

**Usage**:
```bash
python scripts/force_runtime_restart.py
```

---

## 🔄 Common Workflows

### Update Agent Code
```bash
# 1. Make changes to agent_runtime/autorescue_agent.py
# 2. Update the agent runtime
./scripts/update_agent.sh

# 3. Test the changes
cd agent_runtime
uv run agentcore invoke '{"prompt": "Find flights from JFK to LAX on October 23, 2025"}'
```

### Update Lambda Functions
```bash
# 1. Make changes to lambda_functions/search_flights/lambda_function.py
# 2. Deploy the Lambda
./scripts/deploy_lambdas.sh

# 3. Test the Lambda
python scripts/test_search_flights.py
```

### Full Deployment Pipeline
```bash
# 1. Deploy Lambda functions
./scripts/deploy_lambdas.sh

# 2. Update agent runtime
./scripts/update_agent.sh

# 3. Test end-to-end
cd agent_runtime
uv run agentcore invoke '{"prompt": "Find me flights from JFK to LAX on October 23, 2025"}'
```

---

## 🛠️ Prerequisites

### Required Tools
- **AWS CLI**: Configured with appropriate credentials
- **uv**: Python package manager (or pip)
- **Docker**: For building agent images
- **agentcore CLI**: Installed via `bedrock-agentcore-starter-toolkit`

### Installation
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install agentcore CLI and dependencies
uv pip install bedrock-agentcore-starter-toolkit

# Configure AWS credentials
aws configure
# Or use: assume <role-name>
```

---

## 📝 Environment Variables

Scripts use the following environment variables:

- `AWS_REGION`: AWS region (default: us-east-1)
- `AWS_PROFILE`: AWS profile to use
- `COGNITO_CLIENT_ID`: For local testing with Cognito
- `COGNITO_CLIENT_SECRET`: For local testing with Cognito

---

## 🐛 Troubleshooting

### "agentcore: command not found"
```bash
# Install the toolkit
uv pip install bedrock-agentcore-starter-toolkit

# Or add to your PATH if installed globally
export PATH="$HOME/.local/bin:$PATH"
```

### "Docker image build failed"
```bash
# Ensure Docker is running
docker ps

# Check Dockerfile syntax
cd agent_runtime
docker build -t test-build .
```

### "Lambda deployment failed"
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify Lambda function exists
aws lambda get-function --function-name AutoRescue-SearchFlights
```

### "Agent not picking up latest changes"
```bash
# Force runtime restart
./scripts/update_agent.sh

# Or use the force restart script
python scripts/force_runtime_restart.py
```

---

## 📚 Additional Resources

- [AgentCore Documentation](https://docs.aws.amazon.com/bedrock/agentcore/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Bedrock AgentCore Starter Toolkit](https://github.com/awslabs/bedrock-agentcore-starter-toolkit)

---

## 🔐 Security Notes

- Never commit AWS credentials to Git
- Use AWS Secrets Manager for sensitive data (Amadeus API keys, Cognito credentials)
- Use IAM roles with least privilege principles
- Keep dependencies updated for security patches

---

**Last Updated**: October 16, 2025
