#!/bin/bash
#
# Start AutoRescue Streamlit UI with AWS Credentials
#
# This script ensures AWS credentials are loaded before starting Streamlit
#

set -e

echo "🚀 Starting AutoRescue Streamlit UI"
echo "======================================"

# Change to project directory
cd "$(dirname "$0")/.."

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo ""
    echo "⚠️  AWS credentials not found!"
    echo ""
    echo "Please configure AWS credentials first:"
    echo "  1. Run: assume SBPOC11AdministratorAccess"
    echo "  2. Or run: aws configure"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Get AWS account info
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "unknown")
AWS_REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")

echo ""
echo "✅ AWS Credentials Found"
echo "   Account: $AWS_ACCOUNT"
echo "   Region: $AWS_REGION"
echo ""

# Check if UV is available
if command -v uv &> /dev/null; then
    echo "🚀 Starting Streamlit with UV..."
    echo ""
    uv run streamlit run app.py
else
    echo "🚀 Starting Streamlit with Python virtual environment..."
    echo ""
    source .venv/bin/activate
    streamlit run app.py
fi
