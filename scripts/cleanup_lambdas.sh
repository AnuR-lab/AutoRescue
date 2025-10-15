#!/bin/bash
#
# Cleanup existing Lambda functions and IAM roles before CloudFormation deployment
#
set -e

echo "=========================================="
echo "AutoRescue Lambda Cleanup Script"
echo "=========================================="
echo ""

# Function names
SEARCH_FLIGHTS_LAMBDA="AutoRescue-SearchFlights"
ANALYZE_DISRUPTION_LAMBDA="AutoRescue-AnalyzeDisruption"

# IAM Role names (from the original deployment script)
SEARCH_FLIGHTS_ROLE="AutoRescue-SearchFlights-Role"
ANALYZE_DISRUPTION_ROLE="AutoRescue-AnalyzeDisruption-Role"

echo "Step 1: Deleting Lambda Functions..."
echo "--------------------------------------"

# Delete Search Flights Lambda
if aws lambda get-function --function-name "$SEARCH_FLIGHTS_LAMBDA" 2>/dev/null; then
    echo "Deleting $SEARCH_FLIGHTS_LAMBDA..."
    aws lambda delete-function --function-name "$SEARCH_FLIGHTS_LAMBDA"
    echo "✓ Deleted $SEARCH_FLIGHTS_LAMBDA"
else
    echo "○ $SEARCH_FLIGHTS_LAMBDA not found (already deleted)"
fi

# Delete Analyze Disruption Lambda
if aws lambda get-function --function-name "$ANALYZE_DISRUPTION_LAMBDA" 2>/dev/null; then
    echo "Deleting $ANALYZE_DISRUPTION_LAMBDA..."
    aws lambda delete-function --function-name "$ANALYZE_DISRUPTION_LAMBDA"
    echo "✓ Deleted $ANALYZE_DISRUPTION_LAMBDA"
else
    echo "○ $ANALYZE_DISRUPTION_LAMBDA not found (already deleted)"
fi

echo ""
echo "Step 2: Deleting IAM Roles..."
echo "--------------------------------------"

# Function to delete IAM role
delete_iam_role() {
    local ROLE_NAME=$1
    
    if aws iam get-role --role-name "$ROLE_NAME" 2>/dev/null; then
        echo "Detaching policies from $ROLE_NAME..."
        
        # Detach managed policies
        ATTACHED_POLICIES=$(aws iam list-attached-role-policies --role-name "$ROLE_NAME" --query 'AttachedPolicies[].PolicyArn' --output text)
        for POLICY_ARN in $ATTACHED_POLICIES; do
            echo "  Detaching $POLICY_ARN..."
            aws iam detach-role-policy --role-name "$ROLE_NAME" --policy-arn "$POLICY_ARN"
        done
        
        # Delete inline policies
        INLINE_POLICIES=$(aws iam list-role-policies --role-name "$ROLE_NAME" --query 'PolicyNames[]' --output text)
        for POLICY_NAME in $INLINE_POLICIES; do
            echo "  Deleting inline policy $POLICY_NAME..."
            aws iam delete-role-policy --role-name "$ROLE_NAME" --policy-name "$POLICY_NAME"
        done
        
        echo "Deleting role $ROLE_NAME..."
        aws iam delete-role --role-name "$ROLE_NAME"
        echo "✓ Deleted $ROLE_NAME"
    else
        echo "○ $ROLE_NAME not found (already deleted)"
    fi
}

# Delete roles
delete_iam_role "$SEARCH_FLIGHTS_ROLE"
delete_iam_role "$ANALYZE_DISRUPTION_ROLE"

echo ""
echo "Step 3: Deleting CloudWatch Log Groups..."
echo "--------------------------------------"

# Delete log groups
LOG_GROUPS=(
    "/aws/lambda/$SEARCH_FLIGHTS_LAMBDA"
    "/aws/lambda/$ANALYZE_DISRUPTION_LAMBDA"
)

for LOG_GROUP in "${LOG_GROUPS[@]}"; do
    if aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" 2>/dev/null | grep -q "$LOG_GROUP"; then
        echo "Deleting log group $LOG_GROUP..."
        aws logs delete-log-group --log-group-name "$LOG_GROUP"
        echo "✓ Deleted $LOG_GROUP"
    else
        echo "○ $LOG_GROUP not found (already deleted)"
    fi
done

echo ""
echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
echo ""
echo "You can now deploy the CloudFormation stack:"
echo ""
echo "  aws cloudformation create-stack \\"
echo "    --stack-name autorescue-stack \\"
echo "    --template-body file://cloudformation.yaml \\"
echo "    --capabilities CAPABILITY_NAMED_IAM"
echo ""
