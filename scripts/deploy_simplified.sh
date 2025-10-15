#!/bin/bash
#
# Simplified deployment using agentcore CLI with AWS credentials passed through
# 
set -e

echo "=================================================="
echo "AutoRescue Agent Deployment"
echo "=================================================="

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✓ Virtual environment created and activated"
fi
echo ""

# Install bedrock-agentcore-starter-toolkit if not already installed
echo "Installing bedrock-agentcore-starter-toolkit..."
pip install bedrock-agentcore-starter-toolkit
echo "✓ bedrock-agentcore-starter-toolkit installed"
echo ""

# Check for AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo ""
    echo "⚠️  AWS credentials not found in environment variables"
    echo "Please run 'assume' to get AWS credentials first, then run this script again"
    echo ""
    echo "Alternatively, export your AWS credentials:"
    echo "  export AWS_ACCESS_KEY_ID=..."
    echo "  export AWS_SECRET_ACCESS_KEY=..."
    echo "  export AWS_SESSION_TOKEN=..."
    exit 1
fi

echo "✓ AWS credentials found"
echo ""

# Change to agent directory
cd agent_runtime

# Run agentcore configure with AWS credentials
echo "Step 1: Configuring agent..."
echo "This will ask you some questions about your agent configuration."
echo ""

AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
AWS_SESSION_TOKEN="$AWS_SESSION_TOKEN" \
AWS_REGION="${AWS_REGION:-us-east-1}" \
agentcore configure --entrypoint autorescue_agent.py

echo ""
echo "Step 2: Deploying to AWS..."
echo "This will build the Docker image and deploy to AWS AgentCore Runtime."
echo ""

# Set environment variables for the agent
export GATEWAY_URL="https://autorescue-gateway-7ildpiqiqm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
export BEDROCK_MODEL_ID="us.anthropic.claude-3-5-sonnet-20241022-v2:0"

# Note: OAuth credentials are now fetched from AWS Secrets Manager at runtime
# The agent's IAM role has been granted secretsmanager:GetSecretValue permission
echo "✓ Agent will fetch OAuth credentials from AWS Secrets Manager"
echo ""

# Deploy with AWS credentials
AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
AWS_SESSION_TOKEN="$AWS_SESSION_TOKEN" \
AWS_REGION="${AWS_REGION:-us-east-1}" \
GATEWAY_URL="$GATEWAY_URL" \
BEDROCK_MODEL_ID="$BEDROCK_MODEL_ID" \
agentcore launch

echo ""
echo "=================================================="
echo "Deployment Complete!"
echo "=================================================="
echo ""
echo "To test your agent:"
echo "  agentcore invoke '{\"prompt\": \"What time is it?\"}'"
echo ""
echo "To check status:"
echo "  agentcore status"
