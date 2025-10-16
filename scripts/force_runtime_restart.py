#!/usr/bin/env python3
"""
Force AgentCore runtime to restart and pick up the latest Docker image
by triggering a configuration update via CodeBuild
"""
import subprocess
import time

print("=" * 60)
print("  Force AgentCore Runtime Restart")
print("=" * 60)
print()
print("This will trigger CodeBuild to redeploy the runtime,")
print("forcing it to pull the latest Docker image from ECR.")
print()

# The trick: We'll trigger CodeBuild again with the same source
# This forces the runtime to restart with the fresh image

print("🔄 Triggering CodeBuild to force runtime restart...")
print()

result = subprocess.run([
    'python', 'scripts/deploy_agent_update.py'
], capture_output=False)

if result.returncode == 0:
    print()
    print("=" * 60)
    print("✅  Runtime restart triggered successfully!")
    print("=" * 60)
    print()
    print("The agent runtime will restart with the latest image.")
    print("Wait a few seconds, then test again.")
else:
    print()
    print("❌  Failed to trigger restart")
    exit(1)
