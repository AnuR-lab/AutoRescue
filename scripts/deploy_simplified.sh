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

# Get OAuth token
echo "Fetching OAuth2 token..."
TOKEN_RESPONSE=$(curl -s -X POST "https://autorescue-1760552868.auth.us-east-1.amazoncognito.com/oauth2/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=client_credentials&client_id=5ptprke4sq904kc6kv067d4mjo&client_secret=1k7ajt3pg59q2ef1oa9g449jteomhik63qod7e9vpckl0flnnp0r")

export ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Failed to obtain OAuth2 token"
    exit 1
fi

echo "✓ OAuth2 token obtained"
echo ""

# Deploy with AWS credentials
AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
AWS_SESSION_TOKEN="$AWS_SESSION_TOKEN" \
AWS_REGION="${AWS_REGION:-us-east-1}" \
GATEWAY_URL="$GATEWAY_URL" \
ACCESS_TOKEN="$ACCESS_TOKEN" \
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
