#!/usr/bin/env python3
"""
Deploy updated AutoRescue Agent to AgentCore Runtime via CodeBuild
"""

import boto3
import os
import sys
import time
import zipfile
from pathlib import Path

# Configuration
REGION = "us-east-1"
PROJECT_NAME = "bedrock-agentcore-autorescue_agent-builder"
SOURCE_BUCKET = "bedrock-agentcore-codebuild-sources-905418267822-us-east-1"
SOURCE_KEY = "autorescue_agent/source.zip"
AGENT_DIR = "agent_runtime"

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def create_source_zip():
    """Create a zip file of the agent source code"""
    print("📦 Creating source archive...")
    
    zip_path = "/tmp/autorescue_agent_source.zip"
    agent_path = Path(AGENT_DIR)
    
    # Files to include
    files_to_include = [
        "autorescue_agent.py",
        "requirements.txt",
        "Dockerfile"
    ]
    
    # Check if .bedrock_agentcore.yaml exists
    config_file = agent_path / ".bedrock_agentcore.yaml"
    if config_file.exists():
        files_to_include.append(".bedrock_agentcore.yaml")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_name in files_to_include:
            file_path = agent_path / file_name
            if file_path.exists():
                zipf.write(file_path, file_name)
                print(f"   ✅ Added: {file_name}")
            else:
                print(f"   ⚠️  Skipped (not found): {file_name}")
    
    print(f"   ✅ Source archive created: {zip_path}")
    return zip_path

def upload_to_s3(zip_path):
    """Upload source zip to S3"""
    print(f"\n☁️  Uploading to S3...")
    print(f"   Bucket: {SOURCE_BUCKET}")
    print(f"   Key: {SOURCE_KEY}")
    
    s3_client = boto3.client('s3', region_name=REGION)
    
    try:
        s3_client.upload_file(
            zip_path,
            SOURCE_BUCKET,
            SOURCE_KEY
        )
        print(f"   ✅ Source uploaded successfully")
        return True
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        return False

def trigger_build():
    """Trigger CodeBuild to rebuild and deploy the agent"""
    print(f"\n🚀 Triggering CodeBuild...")
    print(f"   Project: {PROJECT_NAME}")
    
    codebuild_client = boto3.client('codebuild', region_name=REGION)
    
    try:
        response = codebuild_client.start_build(
            projectName=PROJECT_NAME
        )
        
        build_id = response['build']['id']
        build_number = response['build']['buildNumber']
        
        print(f"   ✅ Build started successfully")
        print(f"   Build ID: {build_id}")
        print(f"   Build Number: {build_number}")
        
        return build_id
    except Exception as e:
        print(f"   ❌ Failed to start build: {e}")
        return None

def wait_for_build(build_id):
    """Wait for build to complete"""
    print(f"\n⏳ Waiting for build to complete...")
    print(f"   You can also check status in AWS Console")
    print(f"   https://console.aws.amazon.com/codesuite/codebuild/projects/{PROJECT_NAME}/history")
    
    codebuild_client = boto3.client('codebuild', region_name=REGION)
    
    last_phase = None
    
    while True:
        try:
            response = codebuild_client.batch_get_builds(ids=[build_id])
            build = response['builds'][0]
            
            status = build['buildStatus']
            current_phase = build.get('currentPhase', 'UNKNOWN')
            
            # Print phase changes
            if current_phase != last_phase:
                print(f"   📍 Phase: {current_phase}")
                last_phase = current_phase
            
            if status == 'SUCCEEDED':
                print(f"\n   ✅ Build completed successfully!")
                return True
            elif status == 'FAILED':
                print(f"\n   ❌ Build failed!")
                return False
            elif status in ['FAULT', 'TIMED_OUT', 'STOPPED']:
                print(f"\n   ❌ Build ended with status: {status}")
                return False
            
            # Still in progress
            time.sleep(10)
            
        except KeyboardInterrupt:
            print(f"\n\n   ⚠️  Monitoring interrupted. Build is still running.")
            print(f"   Check status at: https://console.aws.amazon.com/codesuite/codebuild/projects/{PROJECT_NAME}/history")
            return None
        except Exception as e:
            print(f"\n   ❌ Error checking build status: {e}")
            return None

def main():
    """Main deployment process"""
    print_section("AutoRescue Agent Runtime Deployment")
    
    print("This will:")
    print("  1. Package the updated agent code")
    print("  2. Upload to S3")
    print("  3. Trigger CodeBuild to rebuild and deploy")
    print("  4. Wait for deployment to complete")
    
    response = input("\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("Deployment cancelled")
        sys.exit(0)
    
    # Step 1: Create source zip
    print_section("Step 1: Package Agent Code")
    zip_path = create_source_zip()
    
    # Step 2: Upload to S3
    print_section("Step 2: Upload to S3")
    if not upload_to_s3(zip_path):
        print("\n❌ Deployment failed at S3 upload")
        sys.exit(1)
    
    # Step 3: Trigger build
    print_section("Step 3: Trigger CodeBuild")
    build_id = trigger_build()
    if not build_id:
        print("\n❌ Deployment failed to start build")
        sys.exit(1)
    
    # Step 4: Wait for build
    print_section("Step 4: Monitor Build Progress")
    result = wait_for_build(build_id)
    
    # Cleanup
    os.remove(zip_path)
    
    if result:
        print_section("✅ Deployment Complete!")
        print("\n🎉 Agent runtime updated successfully!")
        print("\nThe updated agent with pricing workflow is now live.")
        print("\nAgent ARN: arn:aws:bedrock-agentcore:us-east-1:905418267822:runtime/autorescue_agent-KyZlYU4Lgs")
    elif result is False:
        print_section("❌ Deployment Failed")
        print("\nCheck the CodeBuild logs for details:")
        print(f"https://console.aws.amazon.com/codesuite/codebuild/projects/{PROJECT_NAME}/history")
        sys.exit(1)
    else:
        print_section("⚠️  Deployment Status Unknown")
        print("\nThe build was started but monitoring was interrupted.")
        print(f"Check build status at: https://console.aws.amazon.com/codesuite/codebuild/projects/{PROJECT_NAME}/history")

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
