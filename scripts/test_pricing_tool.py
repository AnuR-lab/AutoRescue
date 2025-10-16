#!/usr/bin/env python3
"""
Test script to verify priceFlightOffer tool is available in the agent
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent_runtime'))

from autorescue_agent import AutoRescueAgent, fetch_oauth_token

def test_tools_available():
    """Test that all tools including priceFlightOffer are available"""
    print("🧪 Testing AutoRescue Agent Tools")
    print("=" * 60)
    
    try:
        # Get OAuth token
        print("\n1️⃣ Fetching OAuth token...")
        bearer_token = fetch_oauth_token()
        print("   ✅ Token obtained")
        
        # Initialize agent
        print("\n2️⃣ Initializing agent...")
        agent = AutoRescueAgent(bearer_token=bearer_token)
        print("   ✅ Agent initialized")
        
        # List available tools
        print(f"\n3️⃣ Available tools ({len(agent.tools)} total):")
        print("   " + "-" * 56)
        
        tool_names = []
        for tool in agent.tools:
            if hasattr(tool, '__name__'):
                tool_name = tool.__name__
            elif hasattr(tool, 'name'):
                tool_name = tool.name
            else:
                tool_name = str(tool)
            
            tool_names.append(tool_name)
            print(f"   • {tool_name}")
        
        print("   " + "-" * 56)
        
        # Check for expected tools
        print("\n4️⃣ Verification:")
        expected_tools = [
            'current_time',
            'search-flights___searchFlights',
            'analyze-disruption___analyzeDisruption',
            'offer-price___priceFlightOffer'
        ]
        
        for expected in expected_tools:
            found = any(expected in str(t) for t in tool_names)
            status = "✅" if found else "❌"
            print(f"   {status} {expected}")
        
        # Test simple query
        print("\n5️⃣ Testing simple query...")
        response = agent.invoke("What tools do you have available?")
        print(f"   Response preview: {response[:200]}...")
        
        print("\n" + "=" * 60)
        print("🎉 Test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_tools_available())
