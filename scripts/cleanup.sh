#!/bin/bash
# Cleanup script for AutoRescue resources

set -e

PROJECT_NAME="autorescue"
REGION=${AWS_REGION:-us-east-1}

echo "🧹 Cleaning up AutoRescue resources..."
echo ""

# Confirm cleanup
read -p "This will delete all AutoRescue resources. Continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

# Delete Cognito provider
echo "1. Deleting Cognito credentials provider..."
python scripts/cognito_credentials_provider.py delete --confirm || true

# Delete Memory
echo "2. Deleting AgentCore memory..."
python scripts/agentcore_memory.py delete --confirm || true

# Delete Gateway
echo "3. Deleting AgentCore gateway..."
python scripts/agentcore_gateway.py delete --confirm || true

# Delete SSM parameters
echo "4. Deleting SSM parameters..."
PARAMS=$(aws ssm get-parameters-by-path \
    --path "/app/$PROJECT_NAME" \
    --recursive \
    --region "$REGION" \
    --query 'Parameters[*].Name' \
    --output text)

for param in $PARAMS; do
    echo "  Deleting: $param"
    aws ssm delete-parameter --name "$param" --region "$REGION" || true
done

# Delete IAM role
ROLE_NAME="${PROJECT_NAME}-agentcore-runtime-role"
echo "5. Deleting IAM role: $ROLE_NAME..."
aws iam detach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" || true
aws iam detach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess" || true
aws iam delete-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-name "BedrockAccess" || true
aws iam delete-role --role-name "$ROLE_NAME" || true

# Delete config files
echo "6. Deleting local config files..."
rm -f .agentcore.yaml
rm -f .bedrock_agentcore.yaml
rm -f gateway.config

echo ""
echo "✅ Cleanup complete!"
