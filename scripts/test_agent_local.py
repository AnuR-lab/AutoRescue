#!/usr/bin/env python3
"""
Local test script for AutoRescue Agent
Tests the agent locally before deploying to AgentCore Runtime
"""

import sys
import os

# Add agent_runtime to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent_runtime'))

import requests
import json
from autorescue_agent import AutoRescueAgent

# Configuration
# WARNING: Do not hardcode credentials! Use environment variables or AWS Secrets Manager
CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "YOUR_COGNITO_CLIENT_ID_HERE")
CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET", "YOUR_COGNITO_CLIENT_SECRET_HERE")
TOKEN_URL = "https://autorescue-1760552868.auth.us-east-1.amazoncognito.com/oauth2/token"
GATEWAY_URL = "https://autorescue-gateway-7ildpiqiqm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"


def get_access_token():
    """Get OAuth2 access token from Cognito"""
    print("🔐 Fetching OAuth2 access token...")
    
    response = requests.post(
        TOKEN_URL,
        data=f"grant_type=client_credentials&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}",
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get access token: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)
    
    token_data = response.json()
    print(f"✅ Access token obtained")
    print(f"   Token type: {token_data.get('token_type')}")
    print(f"   Expires in: {token_data.get('expires_in')} seconds")
    
    return token_data['access_token']


def test_flight_search(agent):
    """Test flight search functionality"""
    print("\n" + "="*60)
    print("TEST 1: Flight Search (JFK → LAX)")
    print("="*60)
    
    query = "I need to find flights from JFK to LAX on November 15, 2025. I'm looking for 2 passengers."
    print(f"\n💬 User: {query}")
    
    print("\n🤖 Agent:")
    response = agent.invoke(query)
    print(response)
    
    return response


def test_disruption_analysis(agent):
    """Test disruption analysis functionality"""
    print("\n" + "="*60)
    print("TEST 2: Disruption Analysis")
    print("="*60)
    
    query = "My flight AA123 from JFK to LAX on November 15, 2025 was just canceled due to a mechanical issue. Can you help me find alternatives?"
    print(f"\n💬 User: {query}")
    
    print("\n🤖 Agent:")
    response = agent.invoke(query)
    print(response)
    
    return response


def test_general_conversation(agent):
    """Test general conversation"""
    print("\n" + "="*60)
    print("TEST 3: General Conversation")
    print("="*60)
    
    query = "What can you help me with?"
    print(f"\n💬 User: {query}")
    
    print("\n🤖 Agent:")
    response = agent.invoke(query)
    print(response)
    
    return response


def main():
    """Run all tests"""
    print("="*60)
    print("  AutoRescue Agent - Local Testing")
    print("="*60)
    
    # Get access token
    access_token = get_access_token()
    
    # Initialize agent
    print("\n🚀 Initializing AutoRescue Agent...")
    print(f"   Gateway: {GATEWAY_URL}")
    print(f"   Model: us.anthropic.claude-3-5-sonnet-20241022-v2:0")
    
    try:
        agent = AutoRescueAgent(bearer_token=access_token)
        print("✅ Agent initialized successfully")
        print(f"   Tools loaded: {len(agent.tools)}")
        print(f"   Tool names: {[tool.name if hasattr(tool, 'name') else str(tool) for tool in agent.tools[:5]]}")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Run tests
    try:
        # Test 1: Flight Search
        test_flight_search(agent)
        
        # Test 2: Disruption Analysis
        test_disruption_analysis(agent)
        
        # Test 3: General Conversation
        test_general_conversation(agent)
        
        print("\n" + "="*60)
        print("  ✅ All Tests Completed Successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        sys.exit(1)
