#!/bin/bash
# Apply Secrets Manager IAM policies to Lambda execution roles

set -e

POLICY_FILE="iam_policies/secrets_manager_policy.json"
AGENTCORE_RUNTIME_ROLE="AmazonBedrockAgentCoreSDKRuntime-us-east-1-c76824e496"

echo "==============================================="
echo "Applying Secrets Manager Permissions"
echo "==============================================="
echo

# Check if policy file exists
if [ ! -f "$POLICY_FILE" ]; then
    echo "❌ Policy file not found: $POLICY_FILE"
    exit 1
fi

echo "✓ Policy file found: $POLICY_FILE"
echo

# Function to attach inline policy to a role
attach_policy() {
    local role_name=$1
    local policy_name="AutoRescueSecretsManagerAccess"
    
    echo "Attaching policy to role: $role_name"
    
    # Check if role exists
    if aws iam get-role --role-name "$role_name" > /dev/null 2>&1; then
        # Attach inline policy
        aws iam put-role-policy \
            --role-name "$role_name" \
            --policy-name "$policy_name" \
            --policy-document "file://$POLICY_FILE"
        
        echo "✓ Policy attached to $role_name"
    else
        echo "⚠️  Role not found: $role_name (skipping)"
    fi
    echo
}

# Attach policy to AgentCore Runtime role
echo "Attaching to AgentCore Runtime role..."
attach_policy "$AGENTCORE_RUNTIME_ROLE"

echo "==============================================="
echo "✓ IAM policies applied successfully!"
echo "==============================================="
echo
echo "Note: Lambda function roles will be created by CloudFormation"
echo "and will include Secrets Manager permissions automatically."
echo
echo "Next steps:"
echo "  1. Redeploy agent runtime: cd agent_runtime && agentcore launch"
echo "  2. Test agent: agentcore invoke '{\"prompt\": \"test\"}'"
echo
