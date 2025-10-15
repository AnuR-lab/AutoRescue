#!/bin/bash
# Prerequisites setup script for AutoRescue Flight Assistant
# Sets up SSM parameters and initial infrastructure

set -e

echo "🚀 Setting up AutoRescue Flight Assistant Prerequisites..."
echo ""

# Configuration
PROJECT_NAME="autorescue"
REGION=${AWS_REGION:-us-east-1}

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Configuration:${NC}"
echo "  Project: $PROJECT_NAME"
echo "  Region: $REGION"
echo ""

# Function to create SSM parameter
create_ssm_param() {
    local param_name=$1
    local param_value=$2
    local param_desc=$3
    
    echo -e "${YELLOW}Creating SSM Parameter:${NC} $param_name"
    
    aws ssm put-parameter \
        --name "$param_name" \
        --value "$param_value" \
        --type "String" \
        --description "$param_desc" \
        --overwrite \
        --region "$REGION" \
        --tags "Key=Project,Value=AutoRescue" "Key=Environment,Value=Production" \
        > /dev/null 2>&1 || true
        
    echo -e "${GREEN}✓${NC} Created: $param_name"
}

# Create base SSM parameters
echo -e "${BLUE}Step 1: Creating base SSM parameters...${NC}"

create_ssm_param \
    "/app/$PROJECT_NAME/project/name" \
    "$PROJECT_NAME" \
    "Project name for AutoRescue"

create_ssm_param \
    "/app/$PROJECT_NAME/project/region" \
    "$REGION" \
    "AWS region for deployment"

create_ssm_param \
    "/app/$PROJECT_NAME/amadeus/api_base_url" \
    "https://test.api.amadeus.com" \
    "Amadeus API base URL (test environment)"

echo ""

# Prompt for Amadeus credentials
echo -e "${BLUE}Step 2: Configuring Amadeus API credentials...${NC}"
echo ""

read -p "Enter Amadeus Client ID (press Enter for default): " AMADEUS_CLIENT_ID
AMADEUS_CLIENT_ID=${AMADEUS_CLIENT_ID:-EAiOKtslVsY8vTxyT17QoXqdvyl9s67z}

read -p "Enter Amadeus Client Secret (press Enter for default): " AMADEUS_CLIENT_SECRET
AMADEUS_CLIENT_SECRET=${AMADEUS_CLIENT_SECRET:-leeAu7flsoGFTmYp}

create_ssm_param \
    "/app/$PROJECT_NAME/amadeus/client_id" \
    "$AMADEUS_CLIENT_ID" \
    "Amadeus API Client ID"

create_ssm_param \
    "/app/$PROJECT_NAME/amadeus/client_secret" \
    "$AMADEUS_CLIENT_SECRET" \
    "Amadeus API Client Secret"

echo ""

# Create IAM role for AgentCore runtime
echo -e "${BLUE}Step 3: Creating IAM role for AgentCore runtime...${NC}"

ROLE_NAME="${PROJECT_NAME}-agentcore-runtime-role"
TRUST_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
)

# Create role if it doesn't exist
if ! aws iam get-role --role-name "$ROLE_NAME" > /dev/null 2>&1; then
    echo "$TRUST_POLICY" > /tmp/trust-policy.json
    
    ROLE_ARN=$(aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file:///tmp/trust-policy.json \
        --description "Runtime role for AutoRescue AgentCore" \
        --tags "Key=Project,Value=AutoRescue" \
        --query 'Role.Arn' \
        --output text)
    
    # Attach policies
    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    
    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess"
    
    # Inline policy for Bedrock
    INLINE_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    }
  ]
}
EOF
)
    
    echo "$INLINE_POLICY" > /tmp/bedrock-policy.json
    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name "BedrockAccess" \
        --policy-document file:///tmp/bedrock-policy.json
    
    rm /tmp/trust-policy.json /tmp/bedrock-policy.json
    
    echo -e "${GREEN}✓${NC} Created IAM role: $ROLE_NAME"
else
    ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)
    echo -e "${GREEN}✓${NC} Using existing IAM role: $ROLE_NAME"
fi

# Store role ARN in SSM
create_ssm_param \
    "/app/$PROJECT_NAME/agentcore/runtime_iam_role" \
    "$ROLE_ARN" \
    "IAM role ARN for AgentCore runtime"

echo ""
echo -e "${GREEN}✅ Prerequisites setup complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Create AgentCore Gateway: python scripts/agentcore_gateway.py create --name ${PROJECT_NAME}-gw"
echo "  2. Setup Cognito: python scripts/cognito_credentials_provider.py create --name ${PROJECT_NAME}-gateways"
echo "  3. Create Memory: python scripts/agentcore_memory.py create --name ${PROJECT_NAME}"
echo "  4. Configure Agent: agentcore configure --entrypoint main.py -er $ROLE_ARN --name ${PROJECT_NAME}-flight-assistant"
echo ""
