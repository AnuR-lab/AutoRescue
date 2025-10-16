#!/bin/bash
# Deploy Lambda Functions to AWS

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LAMBDA_DIR="$PROJECT_ROOT/lambda_functions"

echo "🚀 Deploying Lambda Functions..."
echo "Project Root: $PROJECT_ROOT"

# Function to deploy a Lambda
deploy_lambda() {
    local function_name=$1
    local lambda_path=$2
    
    echo ""
    echo "📦 Deploying $function_name..."
    
    # Create temporary directory for packaging
    temp_dir=$(mktemp -d)
    
    # Copy Lambda function code
    cp -r "$lambda_path"/* "$temp_dir/"
    
    # Install dependencies if requirements.txt exists
    if [ -f "$lambda_path/requirements.txt" ]; then
        echo "📥 Installing dependencies..."
        uv pip install -r "$lambda_path/requirements.txt" --target "$temp_dir/" --quiet --no-cache || \
        pip3 install -r "$lambda_path/requirements.txt" -t "$temp_dir/" --quiet --no-cache-dir
    fi
    
    # Create deployment package
    cd "$temp_dir"
    zip -r function.zip . -x "*.pyc" -x "__pycache__/*" > /dev/null
    
    # Deploy to AWS
    aws lambda update-function-code \
        --function-name "$function_name" \
        --zip-file fileb://function.zip \
        --region us-east-1
    
    # Clean up
    rm -rf "$temp_dir"
    
    echo "✅ $function_name deployed successfully"
}

# Deploy each Lambda function
deploy_lambda "AutoRescue-SearchFlights" "$LAMBDA_DIR/search_flights"

echo ""
echo "🎉 Lambda function deployed successfully!"
