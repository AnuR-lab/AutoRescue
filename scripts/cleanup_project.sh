#!/bin/bash
#
# AutoRescue Project Cleanup Script
# This script removes redundant files and organizes the project
#

set -e

echo "🧹 AutoRescue Project Cleanup"
echo "========================================"
echo ""

# Change to project directory
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

# Create archive directory for safety
ARCHIVE_DIR=".archive/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ARCHIVE_DIR"

echo "📦 Creating archive at: $ARCHIVE_DIR"
echo ""

# Function to archive a file
archive_file() {
    local file="$1"
    if [ -f "$file" ] || [ -d "$file" ]; then
        echo "  📦 Archiving: $file"
        mkdir -p "$ARCHIVE_DIR/$(dirname "$file")"
        mv "$file" "$ARCHIVE_DIR/$file"
    fi
}

# Function to remove a file/directory
remove_file() {
    local file="$1"
    if [ -f "$file" ] || [ -d "$file" ]; then
        echo "  🗑️  Removing: $file"
        rm -rf "$file"
    fi
}

echo "🗂️  Phase 1: Archiving redundant documentation..."
echo ""

# Archive redundant documentation
archive_file "AGENT_RUNTIME_INTEGRATION.md"
archive_file "AWS_CREDENTIALS_FIX.md"
archive_file "CLOUDFORMATION_DEPLOY.md"
archive_file "CLOUDFORMATION_DEPLOYMENT.md"
archive_file "CLOUDFORMATION_SECURITY_NOTE.md"
archive_file "DEPENDENCIES.md"
archive_file "DEPLOY.md"
archive_file "GATEWAY_TEST_RESULTS.md"
archive_file "LAMBDA_LOGGING_UPDATE.md"
archive_file "LAMBDA_WORKING.md"
archive_file "NEXT_STEPS.md"
archive_file "QUICK_REFERENCE.md"
archive_file "SECRETS_MANAGER_FIX.md"
archive_file "SECRETS_MANAGER_TEST_RESULTS.md"
archive_file "SECURITY_COMPLETE.md"
archive_file "SECURITY_REMEDIATION.md"
archive_file "SECURITY_REMEDIATION_SUMMARY.md"
archive_file "TESTING.md"
archive_file "UV_SETUP.md"

echo ""
echo "🗂️  Phase 2: Archiving obsolete CloudFormation templates..."
echo ""

archive_file "cloudformation.yaml"
archive_file "cloudformation-lambdas-only.yaml"
archive_file "cloudformation-lambdas-only-backup.yaml"

echo ""
echo "🗂️  Phase 3: Archiving obsolete scripts..."
echo ""

archive_file "scripts/add_gateway_targets.py"
archive_file "scripts/apply_iam_policies.sh"
archive_file "scripts/cleanup_lambdas.sh"
archive_file "scripts/create_agentcore_gateway.py"
archive_file "scripts/create_secrets.sh"
archive_file "scripts/deploy_agent_runtime.py"
archive_file "scripts/deploy_cloudformation.sh"
archive_file "scripts/deploy_lambdas.sh"
archive_file "scripts/deploy_secure.sh"
archive_file "scripts/deploy_simplified.sh"
archive_file "scripts/deploy_with_agentcore_cli.py"
archive_file "scripts/deploy_with_agentcore_cli.sh"
archive_file "scripts/runtime_test.py"
archive_file "scripts/test_deployed_agent.py"
archive_file "scripts/test_gateway.py"
archive_file "scripts/test_lambdas.sh"
archive_file "scripts/test_secrets.py"
archive_file "scripts/update_lambdas.sh"

echo ""
echo "🗂️  Phase 4: Removing auto-generated files..."
echo ""

remove_file "scripts/__pycache__"
remove_file "agent_runtime/__pycache__"
remove_file "agent_runtime/.bedrock_agentcore"
remove_file "scripts/venv"
remove_file "venv"

echo ""
echo "🗂️  Phase 5: Archiving other obsolete files..."
echo ""

archive_file "dev-requirements.txt"
archive_file "FlightOffersSearch_v2_Version_2.8_swagger_specification.json"
archive_file "iam_policies"
archive_file ".cognito_user_pool_id"
archive_file "CLEANUP_PLAN.md"  # Archive the plan itself

# Check if mcp_tools is empty or not used
if [ -d "mcp_tools" ]; then
    if [ -z "$(ls -A mcp_tools)" ]; then
        echo "  🗑️  Removing empty: mcp_tools/"
        rm -rf "mcp_tools"
    else
        echo "  ⚠️  mcp_tools/ not empty - keeping for now"
    fi
fi

# Check if main.py is used
if [ -f "main.py" ]; then
    echo "  ⚠️  main.py exists - verify if still needed"
fi

echo ""
echo "✅ Cleanup Complete!"
echo ""
echo "📊 Summary:"
echo "  - Archived files moved to: $ARCHIVE_DIR"
echo "  - Auto-generated files removed"
echo "  - Project structure simplified"
echo ""
echo "📝 Next Steps:"
echo "  1. Review the archive directory"
echo "  2. Update README.md with consolidated documentation"
echo "  3. Commit the cleaned-up project"
echo ""
echo "🔍 To restore archived files:"
echo "  cp -r $ARCHIVE_DIR/path/to/file ."
echo ""
echo "🗑️  To permanently delete the archive:"
echo "  rm -rf .archive/"
echo ""
