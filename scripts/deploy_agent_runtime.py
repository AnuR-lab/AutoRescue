#!/usr/bin/env python3
"""
Deploy AutoRescue Agent to AWS Bedrock AgentCore Runtime
"""

import boto3
import os
import sys
import time
import subprocess
from datetime import datetime

# Configuration
REGION = "us-east-1"
RUNTIME_NAME = "autorescue-agent"
GATEWAY_ID = "autorescue-gateway-7ildpiqiqm"
GATEWAY_URL = f"https://{GATEWAY_ID}.gateway.bedrock-agentcore.{REGION}.amazonaws.com/mcp"

# ECR Repository
ECR_REPOSITORY = "autorescue-agent"
AWS_ACCOUNT_ID = boto3.client('sts').get_caller_identity()['Account']
ECR_URI = f"{AWS_ACCOUNT_ID}.dkr.ecr.{REGION}.amazonaws.com/{ECR_REPOSITORY}"

# Agent Runtime Configuration
RUNTIME_CONFIG = {
    "runtime_name": RUNTIME_NAME,
    "description": "AutoRescue Flight Booking and Disruption Management Assistant",
    "model_id": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "gateway_url": GATEWAY_URL,
}


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    print(f"   Command: {command}")
    
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Failed: {description}")
        print(f"   Error: {result.stderr}")
        return False
    
    print(f"✅ Success: {description}")
    if result.stdout:
        print(f"   Output: {result.stdout[:200]}")
    return True


def create_ecr_repository():
    """Create ECR repository if it doesn't exist"""
    print_section("Step 1: Create ECR Repository")
    
    ecr_client = boto3.client('ecr', region_name=REGION)
    
    try:
        response = ecr_client.describe_repositories(
            repositoryNames=[ECR_REPOSITORY]
        )
        print(f"✅ ECR repository already exists: {ECR_REPOSITORY}")
        print(f"   URI: {ECR_URI}")
        return True
    except ecr_client.exceptions.RepositoryNotFoundException:
        print(f"📦 Creating ECR repository: {ECR_REPOSITORY}")
        
        try:
            response = ecr_client.create_repository(
                repositoryName=ECR_REPOSITORY,
                imageScanningConfiguration={'scanOnPush': True},
                encryptionConfiguration={'encryptionType': 'AES256'}
            )
            print(f"✅ ECR repository created successfully")
            print(f"   URI: {ECR_URI}")
            return True
        except Exception as e:
            print(f"❌ Failed to create ECR repository: {str(e)}")
            return False


def build_and_push_docker_image():
    """Build and push Docker image to ECR"""
    print_section("Step 2: Build and Push Docker Image")
    
    # Change to agent_runtime directory
    os.chdir('agent_runtime')
    
    # Login to ECR
    login_command = f"aws ecr get-login-password --region {REGION} | docker login --username AWS --password-stdin {ECR_URI}"
    if not run_command(login_command, "Login to ECR"):
        return False
    
    # Build Docker image
    build_command = f"docker build -t {ECR_REPOSITORY}:latest ."
    if not run_command(build_command, "Build Docker image"):
        return False
    
    # Tag image
    tag_command = f"docker tag {ECR_REPOSITORY}:latest {ECR_URI}:latest"
    if not run_command(tag_command, "Tag Docker image"):
        return False
    
    # Push image
    push_command = f"docker push {ECR_URI}:latest"
    if not run_command(push_command, "Push Docker image to ECR"):
        return False
    
    # Return to parent directory
    os.chdir('..')
    
    return True


def create_iam_role():
    """Create IAM role for agent runtime"""
    print_section("Step 3: Create IAM Role for Agent Runtime")
    
    iam_client = boto3.client('iam')
    role_name = "AutoRescueAgentRuntimeRole"
    
    # Trust policy for AgentCore Runtime
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock-agentcore.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Check if role exists
    try:
        iam_client.get_role(RoleName=role_name)
        print(f"✅ IAM role already exists: {role_name}")
        role_arn = f"arn:aws:iam::{AWS_ACCOUNT_ID}:role/{role_name}"
    except iam_client.exceptions.NoSuchEntityException:
        print(f"🔐 Creating IAM role: {role_name}")
        
        # Create role
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=str(trust_policy),
            Description="Execution role for AutoRescue Agent Runtime"
        )
        role_arn = response['Role']['Arn']
        print(f"✅ IAM role created: {role_arn}")
        
        # Attach policies
        policies = [
            "arn:aws:iam::aws:policy/AmazonBedrockFullAccess",
            "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
        ]
        
        for policy_arn in policies:
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            print(f"   ✅ Attached policy: {policy_arn}")
        
        # Wait for role to propagate
        print("   ⏳ Waiting for role to propagate...")
        time.sleep(10)
    
    return role_arn


def deploy_agent_runtime(role_arn):
    """Deploy agent to Bedrock AgentCore Runtime"""
    print_section("Step 4: Deploy Agent to AgentCore Runtime")
    
    agentcore_client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    # Get OAuth token (you'll need to implement token retrieval)
    # For now, we'll use a placeholder
    print("⚠️  Note: You'll need to provide OAuth token for gateway authentication")
    print("   This can be done via environment variables or AWS Secrets Manager")
    
    print(f"\n📋 Agent Runtime Configuration:")
    print(f"   Name: {RUNTIME_CONFIG['runtime_name']}")
    print(f"   Description: {RUNTIME_CONFIG['description']}")
    print(f"   Model: {RUNTIME_CONFIG['model_id']}")
    print(f"   Gateway: {RUNTIME_CONFIG['gateway_url']}")
    print(f"   Image: {ECR_URI}:latest")
    print(f"   Role: {role_arn}")
    
    print(f"\n✅ Agent runtime deployment configured successfully!")
    print(f"\n📝 Next steps:")
    print(f"   1. Use AWS Console or CLI to create the agent runtime")
    print(f"   2. Configure environment variables:")
    print(f"      - GATEWAY_URL: {GATEWAY_URL}")
    print(f"      - ACCESS_TOKEN: <Get from Cognito OAuth2>")
    print(f"      - BEDROCK_MODEL_ID: {RUNTIME_CONFIG['model_id']}")
    print(f"   3. Set execution role: {role_arn}")
    print(f"   4. Use container image: {ECR_URI}:latest")
    
    return True


def main():
    """Main deployment process"""
    print_section("AutoRescue Agent Runtime Deployment")
    
    print(f"🌍 Region: {REGION}")
    print(f"🆔 AWS Account: {AWS_ACCOUNT_ID}")
    print(f"🤖 Runtime Name: {RUNTIME_NAME}")
    
    # Step 1: Create ECR repository
    if not create_ecr_repository():
        print("\n❌ Deployment failed at ECR repository creation")
        sys.exit(1)
    
    # Step 2: Build and push Docker image
    if not build_and_push_docker_image():
        print("\n❌ Deployment failed at Docker build/push")
        sys.exit(1)
    
    # Step 3: Create IAM role
    role_arn = create_iam_role()
    if not role_arn:
        print("\n❌ Deployment failed at IAM role creation")
        sys.exit(1)
    
    # Step 4: Deploy agent runtime
    if not deploy_agent_runtime(role_arn):
        print("\n❌ Deployment failed at agent runtime deployment")
        sys.exit(1)
    
    print_section("✅ Deployment Process Complete!")
    
    print("\n📚 Resources Created:")
    print(f"   • ECR Repository: {ECR_REPOSITORY}")
    print(f"   • Docker Image: {ECR_URI}:latest")
    print(f"   • IAM Role: {role_arn}")
    
    print("\n🚀 To complete deployment, use AWS Console or CLI to:")
    print("   1. Create AgentCore Runtime with the image and role")
    print("   2. Configure environment variables")
    print("   3. Deploy and test the agent")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Deployment error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
