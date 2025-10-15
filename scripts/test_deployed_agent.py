#!/usr/bin/env python3
"""
Test script for deployed AutoRescue Agent on AWS AgentCore Runtime
Invokes the agent with proper authentication
"""

import boto3
import json
import sys

# Configuration
AGENT_ARN = "arn:aws:bedrock-agentcore:us-east-1:905418267822:runtime/autorescue_agent-KyZlYU4Lgs"
REGION = "us-east-1"

def generate_session_id():
    """Generate a valid session ID (33+ characters)"""
    import uuid
    return str(uuid.uuid4()) + str(uuid.uuid4())[:5]

def invoke_agent(prompt, session_id=None):
    """Invoke the deployed agent"""
    client = boto3.client('bedrock-agentcore', region_name=REGION)
    
    if not session_id:
        session_id = generate_session_id()
    
    payload = json.dumps({"prompt": prompt}).encode('utf-8')
    
    print(f"🤖 Invoking agent...")
    print(f"   Session: {session_id}")
    print(f"   Prompt: {prompt}")
    print()
    
    try:
        response = client.invoke_agent_runtime(
            agentRuntimeArn=AGENT_ARN,
            runtimeSessionId=session_id,
            payload=payload
        )
        
        # Read the response
        response_body = response['response'].read()
        response_data = json.loads(response_body)
        
        print("✅ Response:")
        print(json.dumps(response_data, indent=2))
        return response_data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Main test function"""
    print("="*60)
    print("AutoRescue Agent - Production Testing")
    print("="*60)
    print()
    
    # Test 1: Simple time query
    print("TEST 1: Current Time")
    print("-" * 60)
    invoke_agent("What time is it?")
    print()
    
    # Test 2: Flight search
    print("TEST 2: Flight Search")
    print("-" * 60)
    invoke_agent("Find me flights from JFK to LAX on December 25, 2025")
    print()
    
    # Test 3: Disruption analysis
    print("TEST 3: Disruption Analysis")
    print("-" * 60)
    invoke_agent("My flight was just canceled. I was supposed to fly from New York to Los Angeles tomorrow morning. What are my options?")
    print()
    
    print("="*60)
    print("Testing Complete!")
    print("="*60)

if __name__ == "__main__":
    main()
