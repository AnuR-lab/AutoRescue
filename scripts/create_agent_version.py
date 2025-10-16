#!/usr/bin/env python3
"""
Create a new version of the AgentCore runtime to pick up the latest image
"""
import boto3
import json
import time

def create_new_agent_version():
    """Force creation of a new agent version"""
    
    # Read the agent configuration
    with open('agent_runtime/.bedrock_agentcore.yaml', 'r') as f:
        import yaml
        config = yaml.safe_load(f)
    
    agent_arn = config['agents']['autorescue_agent']['bedrock_agentcore']['agent_arn']
    agent_id = config['agents']['autorescue_agent']['bedrock_agentcore']['agent_id']
    
    print("=" * 60)
    print("  Creating New Agent Version")
    print("=" * 60)
    print(f"\nAgent ID: {agent_id}")
    print(f"Agent ARN: {agent_arn}")
    
    # The way to create a new version in AgentCore is to update the runtime
    # which will automatically create a new version
    
    # Since we can't directly call bedrock-agentcore API via boto3 yet,
    # we need to trigger a configuration update
    
    # Option 1: Update via bedrock-agentcore toolkit
    import subprocess
    
    try:
        print("\n📦 Triggering agent version creation...")
        result = subprocess.run(
            ['bedrock-agentcore', 'deploy', '--force'],
            cwd='agent_runtime',
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ New version created successfully!")
            print(result.stdout)
        else:
            print("❌ Failed to create version")
            print(result.stderr)
            
            # Alternative: The version will be created on next invocation
            print("\n💡 Note: The new image will be used on the next agent invocation.")
            print("   The agent runtime automatically picks up the latest ECR image.")
            
    except Exception as e:
        print(f"⚠️  Could not trigger version creation: {e}")
        print("\n💡 The agent will automatically use the latest image on next invocation.")
        print("   AgentCore runtimes pull the 'latest' tag from ECR.")

if __name__ == "__main__":
    try:
        create_new_agent_version()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
