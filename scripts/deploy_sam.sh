#!/bin/bash

# Deploy AutoRescue Lambda Functions using AWS SAM
# This script uses SAM to package and deploy Lambda functions with dependencies

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    AutoRescue SAM Deployment Script                       ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo ""

STACK_NAME="autorescue-lambdas"
TEMPLATE_FILE="template-sam.yaml"
REGION="${AWS_REGION:-us-east-1}"
S3_BUCKET="${SAM_BUCKET:-autorescue-lambda-deployment-${RANDOM}}"

# Step 1: Validate AWS credentials
echo -e "${YELLOW}[1/5] Validating AWS credentials...${NC}"
if ! aws sts get-caller-identity &>/dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Please run 'assume' first.${NC}"
    exit 1
fi
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account: ${ACCOUNT_ID}${NC}"
echo ""

# Step 2: Check if SAM CLI is installed
echo -e "${YELLOW}[2/5] Checking for AWS SAM CLI...${NC}"
if ! command -v sam &> /dev/null; then
    echo -e "${YELLOW}⚠️  SAM CLI not found. Using regular CloudFormation with manual packaging...${NC}"
    USE_SAM=false
else
    echo -e "${GREEN}✅ SAM CLI found${NC}"
    USE_SAM=true
fi
echo ""

if [ "$USE_SAM" = true ]; then
    # Step 3: Build with SAM
    echo -e "${YELLOW}[3/5] Building Lambda functions with SAM...${NC}"
    sam build --template-file "$TEMPLATE_FILE" --region "$REGION"
    echo -e "${GREEN}✅ Build complete${NC}"
    echo ""

    # Step 4: Check for existing stack
    echo -e "${YELLOW}[4/5] Checking for existing stack...${NC}"
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &>/dev/null; then
        echo -e "${BLUE}📦 Stack '$STACK_NAME' exists. Will update it.${NC}"
        DEPLOY_CMD="deploy"
    else
        echo -e "${GREEN}✅ No existing stack. Will create new one.${NC}"
        DEPLOY_CMD="deploy"
    fi
    echo ""

    # Step 5: Deploy with SAM
    echo -e "${YELLOW}[5/5] Deploying with SAM...${NC}"
    sam deploy \
        --template-file .aws-sam/build/template.yaml \
        --stack-name "$STACK_NAME" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$REGION" \
        --resolve-s3 \
        --no-confirm-changeset \
        --no-fail-on-empty-changeset

else
    # Manual packaging approach
    echo -e "${YELLOW}[3/5] Packaging Lambda functions manually...${NC}"
    
    # Package SearchFlights
    echo -e "${BLUE}  Packaging SearchFlights...${NC}"
    cd lambda_functions/search_flights
    if [ -d package ]; then rm -rf package; fi
    mkdir package
    pip install -q -r requirements.txt -t package/ --no-cache-dir
    cp index.py package/
    cd package
    zip -qr ../deployment-package.zip .
    cd ..
    rm -rf package
    echo -e "${GREEN}  ✓ SearchFlights packaged${NC}"
    cd ../..
    
    # Package AnalyzeDisruption
    echo -e "${BLUE}  Packaging AnalyzeDisruption...${NC}"
    cd lambda_functions/analyze_disruption
    if [ -d package ]; then rm -rf package; fi
    mkdir package
    pip install -q -r requirements.txt -t package/ --no-cache-dir
    cp index.py package/
    cd package
    zip -qr ../deployment-package.zip .
    cd ..
    rm -rf package
    echo -e "${GREEN}  ✓ AnalyzeDisruption packaged${NC}"
    cd ../..
    
    echo -e "${GREEN}✅ Packaging complete${NC}"
    echo ""

    # Step 4: Check for existing stack
    echo -e "${YELLOW}[4/5] Checking for existing stack...${NC}"
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &>/dev/null; then
        echo -e "${BLUE}📦 Stack exists. Updating Lambda code directly...${NC}"
        
        # Update Lambda functions
        echo -e "${BLUE}  Updating SearchFlights...${NC}"
        aws lambda update-function-code \
            --function-name AutoRescue-SearchFlights \
            --zip-file fileb://lambda_functions/search_flights/deployment-package.zip \
            --region "$REGION" > /dev/null
        echo -e "${GREEN}  ✓ SearchFlights updated${NC}"
        
        echo -e "${BLUE}  Updating AnalyzeDisruption...${NC}"
        aws lambda update-function-code \
            --function-name AutoRescue-AnalyzeDisruption \
            --zip-file fileb://lambda_functions/analyze_disruption/deployment-package.zip \
            --region "$REGION" > /dev/null
        echo -e "${GREEN}  ✓ AnalyzeDisruption updated${NC}"
        
        # Cleanup
        rm lambda_functions/search_flights/deployment-package.zip
        rm lambda_functions/analyze_disruption/deployment-package.zip
    else
        echo -e "${RED}❌ Stack doesn't exist. Please use SAM CLI or create stack first with CloudFormation template.${NC}"
        echo -e "${YELLOW}Install SAM CLI: brew install aws-sam-cli${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           🎉 Deployment Successful! 🎉                     ║${NC}"
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Display stack info
echo -e "${BLUE}📊 Lambda Functions:${NC}"
aws lambda list-functions --region "$REGION" \
    --query 'Functions[?starts_with(FunctionName, `AutoRescue`)].{Name:FunctionName,Runtime:Runtime,Modified:LastModified}' \
    --output table

echo ""
echo -e "${YELLOW}💡 Next Steps:${NC}"
echo -e "   1. Test with agent: agentcore invoke '{\"prompt\": \"Search flights\"}'"
echo -e "   2. View logs: aws logs tail /aws/lambda/AutoRescue-SearchFlights --follow"
echo ""
