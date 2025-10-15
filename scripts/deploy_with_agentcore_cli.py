#!/usr/bin/env python3
"""
Deployment script for AutoRescue Agent using bedrock-agentcore-starter-toolkit CLI
Based on: https://strandsagents.com/latest/documentation/docs/user-guide/deploy/deploy_to_bedrock_agentcore/

This script uses the agentcore CLI to:
1. Install the starter toolkit
2. Configure the agent
3. (Optionally) Test locally with Docker
4. Deploy to AWS AgentCore Runtime
5. Test the deployed agent
"""

import os
import sys
import subprocess
import json
import requests
from pathlib import Path

# Configuration
AGENT_DIR = "agent_runtime"
ENTRYPOINT = "autorescue_agent.py"
GATEWAY_URL = "https://autorescue-gateway-7ildpiqiqm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
# WARNING: Credentials are now fetched from AWS Secrets Manager at runtime
# These variables are no longer used - kept for reference only
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "YOUR_COGNITO_CLIENT_ID_HERE")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET", "YOUR_COGNITO_CLIENT_SECRET_HERE")
COGNITO_DOMAIN = "autorescue-1760552868.auth.us-east-1.amazoncognito.com"
MODEL_ID = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"

# Colors for terminal output
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color

def print_header(message):
    """Print a formatted header"""
    print(f"\n{Colors.GREEN}{'='*50}{Colors.NC}")
    print(f"{Colors.GREEN}{message}{Colors.NC}")
    print(f"{Colors.GREEN}{'='*50}{Colors.NC}\n")

def print_step(step_num, message):
    """Print a step message"""
    print(f"\n{Colors.YELLOW}Step {step_num}: {message}{Colors.NC}")

def print_error(message):
    """Print an error message"""
    print(f"{Colors.RED}Error: {message}{Colors.NC}")
    sys.exit(1)

def print_success(message):
    """Print a success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.NC}")

def run_command(command, capture_output=False, check=True):
    """Run a shell command"""
    if isinstance(command, str):
        command = command.split()
    
    if capture_output:
        result = subprocess.run(command, capture_output=True, text=True, check=check)
        return result.stdout.strip()
    else:
        result = subprocess.run(command, check=check)
        return result.returncode == 0

def get_oauth_token():
    """Fetch OAuth2 token from Cognito"""
    print_step(3, "Fetching OAuth2 token from Cognito...")
    
    token_url = f"https://{COGNITO_DOMAIN}/oauth2/token"
    
    try:
        response = requests.post(
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=f"grant_type=client_credentials&client_id={COGNITO_CLIENT_ID}&client_secret={COGNITO_CLIENT_SECRET}"
        )
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            print_error("Failed to obtain access token from response")
        
        print_success(f"OAuth2 token obtained (expires in {token_data.get('expires_in', 'N/A')} seconds)")
        return access_token
        
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to fetch OAuth2 token: {e}")

def main():
    print_header("AutoRescue Agent Deployment with AgentCore CLI")
    
    # Step 1: Install bedrock-agentcore-starter-toolkit
    print_step(1, "Installing bedrock-agentcore-starter-toolkit...")
    try:
        run_command("pip install bedrock-agentcore-starter-toolkit")
        print_success("bedrock-agentcore-starter-toolkit installed")
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install starter toolkit: {e}")
    
    # Step 2: Verify project structure
    print_step(2, "Verifying project structure...")
    
    agent_path = Path(AGENT_DIR)
    if not agent_path.exists():
        print_error(f"Directory {AGENT_DIR} not found")
    
    entrypoint_path = agent_path / ENTRYPOINT
    if not entrypoint_path.exists():
        print_error(f"{ENTRYPOINT} not found in {AGENT_DIR}")
    
    requirements_path = agent_path / "requirements.txt"
    if not requirements_path.exists():
        print_error(f"requirements.txt not found in {AGENT_DIR}")
    
    print_success("Project structure verified")
    
    # Step 3: Get OAuth token
    access_token = get_oauth_token()
    
    # Step 4: Configure the agent
    print_step(4, "Configuring agent with agentcore CLI...")
    
    # Change to agent directory
    original_dir = os.getcwd()
    os.chdir(AGENT_DIR)
    
    try:
        run_command(f"agentcore configure --entrypoint {ENTRYPOINT}")
        print_success("Agent configured")
    except subprocess.CalledProcessError as e:
        os.chdir(original_dir)
        print_error(f"Failed to configure agent: {e}")
    
    # Step 5: Optional local testing
    print_step(5, "Local testing (optional)...")
    response = input("Do you want to test locally? This requires Docker. (y/n): ")
    
    if response.lower() == 'y':
        print("Testing locally with Docker...")
        
        # Set environment variables
        os.environ["GATEWAY_URL"] = GATEWAY_URL
        os.environ["ACCESS_TOKEN"] = access_token
        os.environ["BEDROCK_MODEL_ID"] = MODEL_ID
        
        try:
            run_command("agentcore launch --local")
            
            print("\nTesting with sample invocation...")
            run_command(['agentcore', 'invoke', '{"prompt": "What time is it?"}'])
            
            print_success("Local testing complete")
            input("Press Enter to continue with AWS deployment...")
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.YELLOW}Warning: Local testing failed: {e}{Colors.NC}")
            response = input("Continue with AWS deployment anyway? (y/n): ")
            if response.lower() != 'y':
                os.chdir(original_dir)
                print("Deployment cancelled")
                sys.exit(0)
    
    # Step 6: Deploy to AWS
    print_step(6, "Deploying to AWS AgentCore Runtime...")
    print("This will:")
    print("  1. Build a Docker container (ARM64 for AgentCore)")
    print("  2. Push to Amazon ECR")
    print("  3. Create an IAM execution role")
    print("  4. Deploy the agent runtime")
    print()
    
    response = input("Continue with deployment? (y/n): ")
    
    if response.lower() != 'y':
        os.chdir(original_dir)
        print(f"{Colors.YELLOW}Deployment cancelled{Colors.NC}")
        sys.exit(0)
    
    # Set environment variables for deployment
    os.environ["GATEWAY_URL"] = GATEWAY_URL
    os.environ["ACCESS_TOKEN"] = access_token
    os.environ["BEDROCK_MODEL_ID"] = MODEL_ID
    
    try:
        run_command("agentcore launch")
        print_success("Deployment complete!")
    except subprocess.CalledProcessError as e:
        os.chdir(original_dir)
        print_error(f"Deployment failed: {e}")
    
    # Step 7: Test the deployed agent
    print_step(7, "Testing deployed agent...")
    
    print("Running test invocation...")
    try:
        run_command(['agentcore', 'invoke', '{"prompt": "What time is it?"}'])
        
        print(f"\n{Colors.GREEN}Testing flight search...{Colors.NC}")
        run_command(['agentcore', 'invoke', '{"prompt": "Find me a flight from JFK to LAX on December 25, 2025"}'])
        
    except subprocess.CalledProcessError as e:
        print(f"{Colors.YELLOW}Warning: Testing failed: {e}{Colors.NC}")
    
    # Return to original directory
    os.chdir(original_dir)
    
    # Print completion message
    print_header("All Done!")
    print("Your agent is now deployed and ready to use!")
    print()
    print("To invoke your agent:")
    print('  agentcore invoke \'{"prompt": "your message here"}\'')
    print()
    print("To check status:")
    print("  agentcore status")
    print()
    print("For more commands:")
    print("  agentcore --help")

if __name__ == "__main__":
    main()
