#!/usr/bin/env python3
"""
Quick corrected gateway test with proper parameter names
"""

import json
import requests
import sys
import os
from datetime import datetime

# Add agent_runtime to path for OAuth token functionality
sys.path.append('agent_runtime')

# Gateway Configuration
GATEWAY_URL = "https://autorescue-gateway-7ildpiqiqm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"

def get_oauth_token():
    """Get OAuth token for gateway authentication"""
    try:
        from autorescue_agent import fetch_oauth_token
        return fetch_oauth_token()
    except Exception as e:
        print(f"❌ Failed to get OAuth token: {e}")
        return None

def test_search_flights_corrected(token):
    """Test search-flights with correct parameters"""
    print("✈️ Testing Search Flights (Corrected Parameters)...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Corrected parameters based on MCP tool definition
    search_payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "search-flights___searchFlights",
            "arguments": {
                "origin": "JFK",
                "destination": "LAX", 
                "departure_date": "2025-12-15",
                "adults": 1,
                "max_results": 5
            }
        }
    }
    
    try:
        print("   🔍 Searching flights JFK → LAX on 2025-12-15...")
        response = requests.post(GATEWAY_URL, json=search_payload, headers=headers, timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Search request successful")
            
            # Display full result for debugging
            print("\n   📋 Full Response:")
            print(json.dumps(result, indent=2)[:1000] + "...")
            
            return True
        else:
            print(f"   ❌ Search failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Search error: {e}")
        return False

def main():
    """Quick corrected test"""
    print("🧪 AutoRescue Gateway - Corrected Parameter Test")
    print("=" * 60)
    
    # Get OAuth token
    token = get_oauth_token()
    if not token:
        print("❌ Cannot proceed without OAuth token")
        return 1
    
    print("✅ OAuth token obtained")
    
    # Test with corrected parameters
    success = test_search_flights_corrected(token)
    
    if success:
        print("\n🎉 Corrected test completed!")
    else:
        print("\n❌ Test failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())