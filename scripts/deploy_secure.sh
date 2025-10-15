#!/bin/bash
#
# Deploy AutoRescue Agent with Secrets Manager Integration
# Works with AWS SSO credentials
#
set -e

echo "=================================================="
echo "AutoRescue Agent Deployment (Secure)"
echo "=================================================="
echo ""

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured"
    echo "Please run: aws sso login"
    exit 1
fi
echo "✓ AWS credentials configured"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install bedrock-agentcore-starter-toolkit
    echo "✓ Virtual environment created"
fi
echo ""

# Verify secrets exist
echo "Verifying secrets in AWS Secrets Manager..."
if aws secretsmanager get-secret-value --secret-id autorescue/cognito/credentials --region us-east-1 &> /dev/null; then
    echo "✓ Cognito credentials found"
else
    echo "❌ Cognito credentials not found in Secrets Manager"
    echo "Run: ./scripts/create_secrets.sh"
    exit 1
fi

if aws secretsmanager get-secret-value --secret-id autorescue/amadeus/credentials --region us-east-1 &> /dev/null; then
    echo "✓ Amadeus credentials found"
else
    echo "❌ Amadeus credentials not found in Secrets Manager"
    echo "Run: ./scripts/create_secrets.sh"
    exit 1
fi
echo ""

# Change to agent directory
cd "$(dirname "$0")/../agent_runtime" || {
    echo "❌ Failed to find agent_runtime directory"
    exit 1
}

# Deploy agent
echo "Deploying agent to AWS AgentCore Runtime..."
echo "(This will build and push Docker image, takes ~30 seconds)"
echo ""

export GATEWAY_URL="https://autorescue-gateway-7ildpiqiqm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
export BEDROCK_MODEL_ID="us.anthropic.claude-3-5-sonnet-20241022-v2:0"
export AWS_REGION="us-east-1"

agentcore launch

echo ""
echo "=================================================="
echo "✓ Deployment Complete!"
echo "=================================================="
echo ""
echo "Security improvements:"
echo "  ✓ Credentials stored in AWS Secrets Manager"
echo "  ✓ No hardcoded secrets in code or containers"
echo "  ✓ IAM role-based access to secrets"
echo ""
echo "Test the agent:"
echo "  agentcore invoke '{\"prompt\": \"Find flights from JFK to LAX\"}'"
echo ""
