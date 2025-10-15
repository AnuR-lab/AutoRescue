#!/bin/bash
# List all SSM parameters for AutoRescue project

PROJECT_NAME="autorescue"
REGION=${AWS_REGION:-us-east-1}

echo "📋 AutoRescue SSM Parameters"
echo "=============================="
echo ""

aws ssm get-parameters-by-path \
    --path "/app/$PROJECT_NAME" \
    --recursive \
    --region "$REGION" \
    --query 'Parameters[*].[Name,Value]' \
    --output table

echo ""
echo "💡 Use these values when configuring AgentCore runtime"
