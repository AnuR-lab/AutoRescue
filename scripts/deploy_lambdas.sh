#!/bin/bash
#
# Deploy Lambda Functions for AutoRescue Tools
# This script packages and deploys both Lambda functions
#

set -e

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
LAMBDA_ROLE_NAME="AutoRescueLambdaExecutionRole"
PROJECT_ROOT=$(pwd)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== AutoRescue Lambda Functions Deployment ===${NC}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check if role exists, create if not
echo -e "${YELLOW}Checking IAM role...${NC}"
if aws iam get-role --role-name "$LAMBDA_ROLE_NAME" --region "$AWS_REGION" 2>/dev/null; then
    echo "✓ IAM role '$LAMBDA_ROLE_NAME' already exists"
    ROLE_ARN=$(aws iam get-role --role-name "$LAMBDA_ROLE_NAME" --query 'Role.Arn' --output text --region "$AWS_REGION")
else
    echo "Creating IAM role '$LAMBDA_ROLE_NAME'..."
    
    # Create trust policy
    cat > /tmp/lambda-trust-policy.json <<EOF
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

    ROLE_ARN=$(aws iam create-role \
        --role-name "$LAMBDA_ROLE_NAME" \
        --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
        --query 'Role.Arn' \
        --output text \
        --region "$AWS_REGION")
    
    # Attach basic Lambda execution policy
    aws iam attach-role-policy \
        --role-name "$LAMBDA_ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" \
        --region "$AWS_REGION"
    
    # Attach SSM read policy for reading parameters
    aws iam attach-role-policy \
        --role-name "$LAMBDA_ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess" \
        --region "$AWS_REGION"
    
    echo "✓ Created IAM role: $ROLE_ARN"
    echo "Waiting 10 seconds for role propagation..."
    sleep 10
fi

echo ""
echo "Role ARN: $ROLE_ARN"
echo ""

# Function to deploy a Lambda
deploy_lambda() {
    local FUNCTION_NAME=$1
    local LAMBDA_DIR=$2
    local DESCRIPTION=$3
    
    echo -e "${YELLOW}Deploying $FUNCTION_NAME...${NC}"
    
    # Create deployment package
    cd "$PROJECT_ROOT/lambda_functions/$LAMBDA_DIR"
    
    # Create a clean directory for packaging
    rm -rf package
    mkdir -p package
    
    # Install dependencies
    if [ -f requirements.txt ]; then
        echo "  Installing dependencies..."
        pip3 install -r requirements.txt -t package/ --quiet --upgrade
    fi
    
    # Copy Lambda function
    cp lambda_function.py package/
    
    # Create ZIP file
    cd package
    zip -r ../deployment.zip . > /dev/null
    cd ..
    
    echo "  Package size: $(du -h deployment.zip | cut -f1)"
    
    # Set environment variables for Lambda (use credentials from hardcoded values)
    ENV_VARS="Variables={AMADEUS_CLIENT_ID=EAiOKtslVsY8vTxyT17QoXqdvyl9s67z,AMADEUS_CLIENT_SECRET=leeAu7flsoGFTmYp}"
    
    # Check if function exists
    if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$AWS_REGION" 2>/dev/null; then
        echo "  Updating existing function..."
        aws lambda update-function-code \
            --function-name "$FUNCTION_NAME" \
            --zip-file fileb://deployment.zip \
            --region "$AWS_REGION" > /dev/null
        
        # Update configuration
        aws lambda update-function-configuration \
            --function-name "$FUNCTION_NAME" \
            --timeout 30 \
            --memory-size 256 \
            --environment "$ENV_VARS" \
            --region "$AWS_REGION" > /dev/null
        
        echo -e "  ${GREEN}✓ Updated function: $FUNCTION_NAME${NC}"
    else
        echo "  Creating new function..."
        aws lambda create-function \
            --function-name "$FUNCTION_NAME" \
            --runtime python3.12 \
            --role "$ROLE_ARN" \
            --handler lambda_function.lambda_handler \
            --zip-file fileb://deployment.zip \
            --description "$DESCRIPTION" \
            --timeout 30 \
            --memory-size 256 \
            --environment "$ENV_VARS" \
            --region "$AWS_REGION" > /dev/null
        
        echo -e "  ${GREEN}✓ Created function: $FUNCTION_NAME${NC}"
    fi
    
    # Get function ARN
    FUNCTION_ARN=$(aws lambda get-function \
        --function-name "$FUNCTION_NAME" \
        --query 'Configuration.FunctionArn' \
        --output text \
        --region "$AWS_REGION")
    
    echo "  ARN: $FUNCTION_ARN"
    
    # Cleanup
    rm -rf package deployment.zip
    
    cd "$PROJECT_ROOT"
    echo ""
}

# Deploy both Lambda functions
deploy_lambda "AutoRescue-SearchFlights" "search_flights" "Search for flight offers using Amadeus API"
deploy_lambda "AutoRescue-AnalyzeDisruption" "analyze_disruption" "Analyze flight disruptions and provide recommendations"

echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Lambda Functions Deployed:"
echo "  1. AutoRescue-SearchFlights"
echo "  2. AutoRescue-AnalyzeDisruption"
echo ""
echo "Next Steps:"
echo "  1. Update AgentCore Gateway to use these Lambda functions as tool targets"
echo "  2. Run: python scripts/agentcore_gateway.py update"
echo ""
