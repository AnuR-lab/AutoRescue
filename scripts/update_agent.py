#!/usr/bin/env python3
"""
Update AgentCore Runtime
This script rebuilds and redeploys the agent using the agentcore CLI
"""
import subprocess
import sys
import os
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)
    print()

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"Running: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print()
        print(f"❌ Error: {description} failed")
        sys.exit(1)
    
    print()
    print(f"✅ {description} completed successfully")
    print()
    return result

def main():
    """Main function to update AgentCore runtime"""
    
    # Get directories
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    agent_dir = project_root / "agent_runtime"
    
    print_header("AgentCore Runtime Update")
    
    # Change to agent directory
    os.chdir(agent_dir)
    
    # Check if config exists
    config_file = agent_dir / ".bedrock_agentcore.yaml"
    if not config_file.exists():
        print(f"❌ Error: .bedrock_agentcore.yaml not found in {agent_dir}")
        print("Please ensure the agent is configured before running this script.")
        sys.exit(1)
    
    print("📋 Current Configuration:")
    print(f"   Working Directory: {agent_dir}")
    print(f"   Agent Config: .bedrock_agentcore.yaml")
    print()
    
    # Read config to get agent name
    import yaml
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
        agent_name = config.get('default_agent', 'autorescue_agent')
        agent_arn = config.get('agents', {}).get(agent_name, {}).get('bedrock_agentcore', {}).get('agent_arn', 'N/A')
    
    print(f"   Agent Name: {agent_name}")
    print(f"   Agent ARN: {agent_arn}")
    print()
    
    # Launch command handles build, push, and deploy
    print("� Updating AgentCore runtime (build → push → deploy)...")
    print()
    print("This will:")
    print("  1. Build the Docker image with latest code")
    print("  2. Push the image to ECR")
    print("  3. Update the runtime to use the new image")
    print()
    
    run_command(
        ["uv", "run", "agentcore", "launch"],
        "AgentCore runtime update"
    )
    
    # Success
    print_header("✅  AgentCore Runtime Updated Successfully!")
    
    print("The agent is now running with the latest code and Claude Sonnet 4.5 model.")
    print()
    print("🧪 Test the agent:")
    print(f'   cd {agent_dir}')
    print('   uv run agentcore invoke \'{"prompt": "Find me flights from JFK to LAX on October 23, 2025"}\'')
    print()
    print("📊 View logs:")
    print("   uv run agentcore logs --follow")
    print()
    print("🔍 Check status:")
    print("   uv run agentcore status")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Update cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
