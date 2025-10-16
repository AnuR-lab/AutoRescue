#!/bin/bash
# Update AgentCore Runtime
# This script rebuilds and redeploys the agent using the agentcore CLI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
AGENT_DIR="$PROJECT_ROOT/agent_runtime"

echo "=" | tr '=' '-' | head -c 60
echo ""
echo "  AgentCore Runtime Update"
echo "=" | tr '=' '-' | head -c 60
echo ""

cd "$AGENT_DIR"

# Check if .bedrock_agentcore.yaml exists
if [ ! -f ".bedrock_agentcore.yaml" ]; then
    echo "❌ Error: .bedrock_agentcore.yaml not found in $AGENT_DIR"
    echo "Please run this script from the agent_runtime directory or ensure configuration exists."
    exit 1
fi

echo "📋 Current Configuration:"
echo "   Working Directory: $AGENT_DIR"
echo "   Agent Config: .bedrock_agentcore.yaml"
echo ""

# Launch command handles build, push, and deploy
echo "🚀 Updating AgentCore runtime (build → push → deploy)..."
echo ""
echo "This will:"
echo "  1. Build the Docker image with latest code"
echo "  2. Push the image to ECR"
echo "  3. Update the runtime to use the new image"
echo ""
echo "Running: agentcore launch"
echo ""
uv run agentcore launch

echo ""
echo "=" | tr '=' '-' | head -c 60
echo ""
echo "✅  AgentCore Runtime Updated Successfully!"
echo "=" | tr '=' '-' | head -c 60
echo ""
echo "The agent is now running with the latest code and Claude Sonnet 4.5 model."
echo ""
echo "🧪 Test the agent:"
echo "   cd $AGENT_DIR"
echo "   uv run agentcore invoke '{\"prompt\": \"Find me flights from JFK to LAX on October 23, 2025\"}'"
echo ""
echo "📊 View logs:"
echo "   uv run agentcore logs --follow"
echo ""
