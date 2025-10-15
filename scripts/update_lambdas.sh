#!/bin/bash

# Deploy Lambda Functions with Enhanced Logging
# This script packages and updates existing Lambda functions

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    AutoRescue Lambda Functions Deployment                 ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo ""

REGION="${AWS_REGION:-us-east-1}"

# Validate AWS credentials
echo -e "${YELLOW}[0/4] Validating AWS credentials...${NC}"
if ! aws sts get-caller-identity &>/dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Please run 'assume' first.${NC}"
    exit 1
fi
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account: ${ACCOUNT_ID}${NC}"
echo ""

# Step 1: Package Search Flights Lambda
echo -e "${YELLOW}[1/4] Packaging SearchFlights Lambda with dependencies...${NC}"
cd lambda_functions/search_flights
if [ -f lambda_package.zip ]; then
    rm lambda_package.zip
fi
# Create temporary directory for packaging
mkdir -p package
# Install dependencies
pip install -q requests boto3 -t package/ --no-cache-dir
# Copy lambda function as index.py
cp lambda_function.py package/index.py
# Create ZIP from package directory
cd package
zip -qr ../lambda_package.zip .
cd ..
# Cleanup
rm -rf package
echo -e "${GREEN}✅ Package created: search_flights/lambda_package.zip (with dependencies)${NC}"
cd ../..
echo ""

# Step 2: Package Analyze Disruption Lambda
echo -e "${YELLOW}[2/4] Packaging AnalyzeDisruption Lambda with dependencies...${NC}"
cd lambda_functions/analyze_disruption
if [ -f lambda_package.zip ]; then
    rm lambda_package.zip
fi
# Create temporary directory for packaging
mkdir -p package
# Install dependencies
pip install -q requests boto3 -t package/ --no-cache-dir
# Copy lambda function as index.py
cp lambda_function.py package/index.py
# Create ZIP from package directory
cd package
zip -qr ../lambda_package.zip .
cd ..
# Cleanup
rm -rf package
echo -e "${GREEN}✅ Package created: analyze_disruption/lambda_package.zip (with dependencies)${NC}"
cd ../..
echo ""

# Step 3: Update SearchFlights Lambda
echo -e "${YELLOW}[3/4] Updating AutoRescue-SearchFlights Lambda...${NC}"
aws lambda update-function-code \
    --function-name AutoRescue-SearchFlights \
    --zip-file fileb://lambda_functions/search_flights/lambda_package.zip \
    --region $REGION \
    --output json > /tmp/update-search-flights.json

SEARCH_VERSION=$(jq -r '.Version' /tmp/update-search-flights.json)
echo -e "${GREEN}✅ Updated SearchFlights Lambda (Version: $SEARCH_VERSION)${NC}"
echo ""

# Step 4: Update AnalyzeDisruption Lambda
echo -e "${YELLOW}[4/4] Updating AutoRescue-AnalyzeDisruption Lambda...${NC}"
aws lambda update-function-code \
    --function-name AutoRescue-AnalyzeDisruption \
    --zip-file fileb://lambda_functions/analyze_disruption/lambda_package.zip \
    --region $REGION \
    --output json > /tmp/update-analyze-disruption.json

ANALYZE_VERSION=$(jq -r '.Version' /tmp/update-analyze-disruption.json)
echo -e "${GREEN}✅ Updated AnalyzeDisruption Lambda (Version: $ANALYZE_VERSION)${NC}"
echo ""

# Cleanup
echo -e "${YELLOW}Cleaning up temporary files...${NC}"
rm -f lambda_functions/search_flights/lambda_package.zip
rm -f lambda_functions/analyze_disruption/lambda_package.zip
echo ""

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           🎉 Lambda Functions Updated! 🎉                  ║${NC}"
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo ""

echo -e "${BLUE}📊 Function Details:${NC}"
echo -e "${GREEN}  ✓ AutoRescue-SearchFlights (Version: $SEARCH_VERSION)${NC}"
echo -e "${GREEN}  ✓ AutoRescue-AnalyzeDisruption (Version: $ANALYZE_VERSION)${NC}"
echo ""

echo -e "${YELLOW}💡 Next Steps:${NC}"
echo -e "   1. Test the Lambda functions with enhanced logging"
echo -e "   2. Check CloudWatch logs: aws logs tail /aws/lambda/AutoRescue-SearchFlights --follow"
echo -e "   3. Invoke agent: agentcore invoke '{\"prompt\": \"Search flights\"}'"
echo ""

echo -e "${BLUE}🔗 Useful Commands:${NC}"
echo -e "   View logs:        aws logs tail /aws/lambda/AutoRescue-SearchFlights --follow --region $REGION"
echo -e "   Test SearchFlights: aws lambda invoke --function-name AutoRescue-SearchFlights --payload '{\"body\":\"{}\"}' output.json"
echo ""
