#!/bin/bash
# Deployment script for AutoRescue Agent using bedrock-agentcore-starter-toolkit CLI
# Based on: https://strandsagents.com/latest/documentation/docs/user-guide/deploy/deploy_to_bedrock_agentcore/

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AGENT_DIR="agent_runtime"
ENTRYPOINT="autorescue_agent.py"
GATEWAY_URL="https://autorescue-gateway-7ildpiqiqm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
COGNITO_CLIENT_ID="5ptprke4sq904kc6kv067d4mjo"
COGNITO_CLIENT_SECRET="1k7ajt3pg59q2ef1oa9g449jteomhik63qod7e9vpckl0flnnp0r"
COGNITO_DOMAIN="autorescue-1760552868.auth.us-east-1.amazoncognito.com"
MODEL_ID="us.anthropic.claude-3-5-sonnet-20241022-v2:0"

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}AutoRescue Agent Deployment with AgentCore CLI${NC}"
echo -e "${GREEN}============================================${NC}"

# Step 1: Install bedrock-agentcore-starter-toolkit
echo -e "\n${YELLOW}Step 1: Installing bedrock-agentcore-starter-toolkit...${NC}"
pip install bedrock-agentcore-starter-toolkit

# Step 2: Verify project structure
echo -e "\n${YELLOW}Step 2: Verifying project structure...${NC}"
cd "$AGENT_DIR"

if [ ! -f "$ENTRYPOINT" ]; then
    echo -e "${RED}Error: $ENTRYPOINT not found in $AGENT_DIR${NC}"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: requirements.txt not found in $AGENT_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Project structure verified${NC}"

# Step 3: Fetch OAuth2 token for gateway access
echo -e "\n${YELLOW}Step 3: Fetching OAuth2 token from Cognito...${NC}"
TOKEN_RESPONSE=$(curl -s -X POST "https://$COGNITO_DOMAIN/oauth2/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -u "$COGNITO_CLIENT_ID:$COGNITO_CLIENT_SECRET" \
    -d "grant_type=client_credentials&scope=invoke")

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

if [ -z "$ACCESS_TOKEN" ]; then
    echo -e "${RED}Error: Failed to obtain OAuth2 token${NC}"
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ OAuth2 token obtained successfully${NC}"

# Step 4: Configure the agent
echo -e "\n${YELLOW}Step 4: Configuring agent with agentcore CLI...${NC}"
agentcore configure --entrypoint "$ENTRYPOINT"

echo -e "${GREEN}✓ Agent configured${NC}"

# Step 5: Test locally (optional - requires Docker)
echo -e "\n${YELLOW}Step 5: Local testing (optional)...${NC}"
read -p "Do you want to test locally? This requires Docker. (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Testing locally with Docker..."
    export GATEWAY_URL="$GATEWAY_URL"
    export ACCESS_TOKEN="$ACCESS_TOKEN"
    export BEDROCK_MODEL_ID="$MODEL_ID"
    
    agentcore launch --local
    
    echo -e "\n${YELLOW}Testing with sample invocation...${NC}"
    agentcore invoke '{"prompt": "What time is it?"}'
    
    echo -e "\n${GREEN}Local testing complete. Press any key to continue with AWS deployment...${NC}"
    read -n 1 -s
fi

# Step 6: Deploy to AWS
echo -e "\n${YELLOW}Step 6: Deploying to AWS AgentCore Runtime...${NC}"
echo "This will:"
echo "  1. Build a Docker container (ARM64 for AgentCore)"
echo "  2. Push to Amazon ECR"
echo "  3. Create an IAM execution role"
echo "  4. Deploy the agent runtime"
echo ""
read -p "Continue with deployment? (y/n): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled${NC}"
    exit 0
fi

# Set environment variables for deployment
export GATEWAY_URL="$GATEWAY_URL"
export ACCESS_TOKEN="$ACCESS_TOKEN"
export BEDROCK_MODEL_ID="$MODEL_ID"

agentcore launch

echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}============================================${NC}"

# Step 7: Test the deployed agent
echo -e "\n${YELLOW}Step 7: Testing deployed agent...${NC}"
echo "Running test invocation..."

agentcore invoke '{"prompt": "What time is it?"}'

echo -e "\n${GREEN}Testing flight search...${NC}"
agentcore invoke '{"prompt": "Find me a flight from JFK to LAX on December 25, 2025"}'

echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}All Done!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Your agent is now deployed and ready to use!"
echo ""
echo "To invoke your agent:"
echo "  agentcore invoke '{\"prompt\": \"your message here\"}'"
echo ""
echo "To check status:"
echo "  agentcore status"
echo ""
echo "For more commands:"
echo "  agentcore --help"
