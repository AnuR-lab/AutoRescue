#!/usr/bin/env python3
"""
Test script for AutoRescue Agent Runtime with offer_price workflow
"""

import sys
import json
import logging

# Add the agent_runtime directory to the path
sys.path.append('agent_runtime')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agent_workflow():
    """Test the complete flight search and selection workflow"""
    
    print("🧪 Testing AutoRescue Agent Runtime Workflow")
    print("=" * 50)
    
    try:
        # Import after adding to path
        from autorescue_agent import AutoRescueAgent, fetch_oauth_token
        
        # Get OAuth token
        print("🔐 Getting OAuth token...")
        bearer_token = fetch_oauth_token()
        print("✅ OAuth token obtained")
        
        # Create agent instance
        print("🤖 Creating agent instance...")
        agent = AutoRescueAgent(bearer_token=bearer_token)
        print("✅ Agent created successfully")
        
        # Test 1: Flight search
        print("\n📋 Test 1: Flight Search")
        search_query = "Find flights from JFK to LAX on 2025-11-01"
        print(f"Query: {search_query}")
        
        search_response = agent.invoke(search_query)
        print("Search Response:")
        print("-" * 30)
        print(search_response[:500] + "..." if len(search_response) > 500 else search_response)
        
        # Test 2: Flight selection (simulate user selecting a flight)
        print("\n📋 Test 2: Flight Selection")
        selection_query = "I want to book the cheapest option from the search results"
        print(f"Query: {selection_query}")
        
        selection_response = agent.invoke(selection_query)
        print("Selection Response:")
        print("-" * 30)
        print(selection_response[:500] + "..." if len(selection_response) > 500 else selection_response)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_tools():
    """Test that the agent can access both tools"""
    
    print("\n🔧 Testing Agent Tools Access")
    print("=" * 30)
    
    try:
        from autorescue_agent import AutoRescueAgent, fetch_oauth_token
        
        bearer_token = fetch_oauth_token()
        agent = AutoRescueAgent(bearer_token=bearer_token)
        
        print(f"Available tools: {len(agent.tools)}")
        for i, tool in enumerate(agent.tools, 1):
            tool_name = getattr(tool, 'name', str(tool))
            print(f"  {i}. {tool_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tools test failed: {e}")
        return False

def main():
    """Main test function"""
    
    success = True
    
    # Test tools access
    if not test_agent_tools():
        success = False
    
    # Test workflow
    if not test_agent_workflow():
        success = False
    
    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())