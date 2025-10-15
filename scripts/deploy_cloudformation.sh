#!/bin/bash

# AutoRescue CloudFormation Deployment Script
# This script deploys Lambda functions with AWS Secrets Manager integration

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="autorescue-lambdas"
TEMPLATE_FILE="cloudformation-lambdas-only.yaml"
REGION="${AWS_REGION:-us-east-1}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    AutoRescue CloudFormation Deployment Script            ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Step 1: Validate AWS credentials
echo -e "${YELLOW}[1/6] Validating AWS credentials...${NC}"
if ! aws sts get-caller-identity &>/dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Please run 'aws configure' or 'assume'.${NC}"
    exit 1
fi
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account: ${ACCOUNT_ID}${NC}"
echo ""

# Step 2: Check for existing stack
echo -e "${YELLOW}[2/6] Checking for existing CloudFormation stack...${NC}"
if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &>/dev/null; then
    echo -e "${BLUE}📦 Stack '$STACK_NAME' already exists.${NC}"
    read -p "Do you want to delete and recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}🗑️  Deleting existing stack...${NC}"
        aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION"
        echo -e "${BLUE}⏳ Waiting for stack deletion to complete...${NC}"
        aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION"
        echo -e "${GREEN}✅ Stack deleted successfully${NC}"
    else
        echo -e "${YELLOW}📝 Updating existing stack instead...${NC}"
        UPDATE_STACK=true
    fi
else
    echo -e "${GREEN}✅ No existing stack found. Will create new stack.${NC}"
    UPDATE_STACK=false
fi
echo ""

# Step 3: Check for existing Lambda functions (if not using stack)
echo -e "${YELLOW}[3/6] Checking for existing Lambda functions...${NC}"
EXISTING_LAMBDAS=$(aws lambda list-functions --region "$REGION" \
    --query 'Functions[?starts_with(FunctionName, `AutoRescue`)].FunctionName' \
    --output text)

if [ -n "$EXISTING_LAMBDAS" ]; then
    echo -e "${BLUE}📋 Found existing Lambda functions:${NC}"
    echo "$EXISTING_LAMBDAS" | tr '\t' '\n' | sed 's/^/   - /'
    
    read -p "Delete these Lambda functions? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for func in $EXISTING_LAMBDAS; do
            echo -e "${YELLOW}   Deleting $func...${NC}"
            aws lambda delete-function --function-name "$func" --region "$REGION" || true
        done
        echo -e "${GREEN}✅ Lambda functions deleted${NC}"
    fi
else
    echo -e "${GREEN}✅ No standalone Lambda functions found${NC}"
fi
echo ""

# Step 4: Check for existing IAM roles (if not using stack)
echo -e "${YELLOW}[4/6] Checking for existing IAM roles...${NC}"
EXISTING_ROLES=$(aws iam list-roles \
    --query 'Roles[?starts_with(RoleName, `AutoRescue`)].RoleName' \
    --output text)

if [ -n "$EXISTING_ROLES" ]; then
    echo -e "${BLUE}📋 Found existing IAM roles:${NC}"
    echo "$EXISTING_ROLES" | tr '\t' '\n' | sed 's/^/   - /'
    
    read -p "Delete these IAM roles? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for role in $EXISTING_ROLES; do
            echo -e "${YELLOW}   Processing role: $role${NC}"
            
            # Detach managed policies
            ATTACHED_POLICIES=$(aws iam list-attached-role-policies --role-name "$role" \
                --query 'AttachedPolicies[*].PolicyArn' --output text 2>/dev/null || echo "")
            for policy in $ATTACHED_POLICIES; do
                echo -e "${YELLOW}     Detaching policy: $policy${NC}"
                aws iam detach-role-policy --role-name "$role" --policy-arn "$policy" || true
            done
            
            # Delete inline policies
            INLINE_POLICIES=$(aws iam list-role-policies --role-name "$role" \
                --query 'PolicyNames[*]' --output text 2>/dev/null || echo "")
            for policy in $INLINE_POLICIES; do
                echo -e "${YELLOW}     Deleting inline policy: $policy${NC}"
                aws iam delete-role-policy --role-name "$role" --policy-name "$policy" || true
            done
            
            # Delete the role
            echo -e "${YELLOW}     Deleting role: $role${NC}"
            aws iam delete-role --role-name "$role" || true
        done
        echo -e "${GREEN}✅ IAM roles cleaned up${NC}"
    fi
else
    echo -e "${GREEN}✅ No standalone IAM roles found${NC}"
fi
echo ""

# Step 5: Validate CloudFormation template
echo -e "${YELLOW}[5/6] Validating CloudFormation template...${NC}"
if ! aws cloudformation validate-template \
    --template-body file://"$TEMPLATE_FILE" \
    --region "$REGION" &>/dev/null; then
    echo -e "${RED}❌ Template validation failed!${NC}"
    aws cloudformation validate-template \
        --template-body file://"$TEMPLATE_FILE" \
        --region "$REGION"
    exit 1
fi
echo -e "${GREEN}✅ Template is valid${NC}"
echo ""

# Step 6: Deploy CloudFormation stack
echo -e "${YELLOW}[6/6] Deploying CloudFormation stack...${NC}"
echo -e "${BLUE}Stack Name: $STACK_NAME${NC}"
echo -e "${BLUE}Region: $REGION${NC}"
echo -e "${BLUE}Template: $TEMPLATE_FILE${NC}"
echo ""

if [ "$UPDATE_STACK" = true ]; then
    echo -e "${YELLOW}📝 Updating stack...${NC}"
    aws cloudformation update-stack \
        --stack-name "$STACK_NAME" \
        --template-body file://"$TEMPLATE_FILE" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$REGION"
    
    echo -e "${BLUE}⏳ Waiting for stack update to complete...${NC}"
    aws cloudformation wait stack-update-complete \
        --stack-name "$STACK_NAME" \
        --region "$REGION"
else
    echo -e "${YELLOW}🚀 Creating new stack...${NC}"
    STACK_ID=$(aws cloudformation create-stack \
        --stack-name "$STACK_NAME" \
        --template-body file://"$TEMPLATE_FILE" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$REGION" \
        --query 'StackId' \
        --output text)
    
    echo -e "${GREEN}✅ Stack creation initiated: $STACK_ID${NC}"
    echo -e "${BLUE}⏳ Waiting for stack creation to complete (this may take a few minutes)...${NC}"
    
    aws cloudformation wait stack-create-complete \
        --stack-name "$STACK_NAME" \
        --region "$REGION"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           🎉 Deployment Successful! 🎉                     ║${NC}"
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Display stack outputs
echo -e "${BLUE}📊 Stack Outputs:${NC}"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

echo ""
echo -e "${BLUE}📋 Stack Resources:${NC}"
aws cloudformation describe-stack-resources \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'StackResources[?ResourceType==`AWS::Lambda::Function` || ResourceType==`AWS::IAM::Role`].[LogicalResourceId,ResourceType,ResourceStatus]' \
    --output table

echo ""
echo -e "${BLUE}🔍 Lambda Function Details:${NC}"
LAMBDA_FUNCTIONS=$(aws cloudformation describe-stack-resources \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'StackResources[?ResourceType==`AWS::Lambda::Function`].PhysicalResourceId' \
    --output text)

for func in $LAMBDA_FUNCTIONS; do
    echo -e "${GREEN}  ✓ $func${NC}"
    FUNC_ARN=$(aws lambda get-function --function-name "$func" --region "$REGION" \
        --query 'Configuration.FunctionArn' --output text)
    echo -e "${BLUE}    ARN: $FUNC_ARN${NC}"
done

echo ""
echo -e "${YELLOW}💡 Next Steps:${NC}"
echo -e "   1. Test the Lambda functions with the agent"
echo -e "   2. Check CloudWatch logs for execution details"
echo -e "   3. Monitor Secrets Manager access in CloudTrail"
echo ""
echo -e "${BLUE}🔗 Useful Commands:${NC}"
echo -e "   View stack:   aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION"
echo -e "   Delete stack: aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION"
echo -e "   View logs:    aws logs tail /aws/lambda/AutoRescue-SearchFlights --follow"
echo ""
