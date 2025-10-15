#!/usr/bin/env python3
"""
Test script for AutoRescue AgentCore Gateway
Tests OAuth2 authentication and MCP protocol tool invocation
"""

import requests
import json
import sys

# Cognito OAuth2 Configuration
CLIENT_ID = "5ptprke4sq904kc6kv067d4mjo"
CLIENT_SECRET = "1k7ajt3pg59q2ef1oa9g449jteomhik63qod7e9vpckl0flnnp0r"
TOKEN_URL = "https://autorescue-1760552868.auth.us-east-1.amazoncognito.com/oauth2/token"

# Gateway Configuration
GATEWAY_URL = "https://autorescue-gateway-7ildpiqiqm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def fetch_access_token(client_id, client_secret, token_url):
    """Fetch OAuth2 access token using client credentials flow"""
    print("🔐 Fetching OAuth2 access token from Cognito...")
    
    response = requests.post(
        token_url,
        data=f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}",
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get access token: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)
    
    token_data = response.json()
    print(f"✅ Access token obtained successfully")
    print(f"   Token Type: {token_data.get('token_type')}")
    print(f"   Expires In: {token_data.get('expires_in')} seconds")
    print(f"   Scope: {token_data.get('scope')}")
    
    return token_data['access_token']

def list_tools(gateway_url, access_token):
    """List available tools from the gateway using MCP protocol"""
    print("\n📋 Listing available tools...")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    payload = {
        "jsonrpc": "2.0",
        "id": "list-tools-request",
        "method": "tools/list"
    }
    
    response = requests.post(gateway_url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"❌ Failed to list tools: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    result = response.json()
    print(f"✅ Tools retrieved successfully\n")
    
    if 'result' in result and 'tools' in result['result']:
        tools = result['result']['tools']
        print(f"Found {len(tools)} tools:\n")
        
        for i, tool in enumerate(tools, 1):
            print(f"{i}. {tool['name']}")
            print(f"   Description: {tool.get('description', 'N/A')}")
            if 'inputSchema' in tool:
                schema = tool['inputSchema']
                required_params = schema.get('required', [])
                properties = schema.get('properties', {})
                
                print(f"   Required Parameters:")
                for param in required_params:
                    param_info = properties.get(param, {})
                    print(f"      - {param}: {param_info.get('type', 'unknown')} - {param_info.get('description', 'N/A')}")
                
                optional_params = [p for p in properties.keys() if p not in required_params]
                if optional_params:
                    print(f"   Optional Parameters:")
                    for param in optional_params:
                        param_info = properties.get(param, {})
                        print(f"      - {param}: {param_info.get('type', 'unknown')} - {param_info.get('description', 'N/A')}")
            print()
    
    return result

def call_tool(gateway_url, access_token, tool_name, arguments):
    """Call a specific tool with arguments using MCP protocol"""
    print(f"\n🔧 Calling tool: {tool_name}")
    print(f"   Arguments: {json.dumps(arguments, indent=6)}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    payload = {
        "jsonrpc": "2.0",
        "id": f"call-{tool_name}-request",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    response = requests.post(gateway_url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"❌ Failed to call tool: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    result = response.json()
    print(f"✅ Tool call successful\n")
    
    return result

def main():
    """Main test execution"""
    print_section("AutoRescue Gateway Test")
    
    print(f"🌐 Gateway URL: {GATEWAY_URL}")
    print(f"🔑 Client ID: {CLIENT_ID}")
    print(f"🔐 Token URL: {TOKEN_URL}")
    
    # Step 1: Get OAuth2 Access Token
    print_section("Step 1: OAuth2 Authentication")
    access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
    
    # Step 2: List Available Tools
    print_section("Step 2: List Available Tools")
    tools_result = list_tools(GATEWAY_URL, access_token)
    
    if not tools_result:
        print("❌ Failed to list tools. Exiting.")
        sys.exit(1)
    
    # Step 3: Test searchFlights tool
    print_section("Step 3: Test Search Flights Tool")
    search_result = call_tool(
        GATEWAY_URL,
        access_token,
        "search-flights___searchFlights",
        {
            "origin": "JFK",
            "destination": "LAX",
            "departure_date": "2025-11-15",
            "adults": 1,
            "max_results": 3
        }
    )
    
    if search_result:
        print("Search Flights Result:")
        print(json.dumps(search_result, indent=2))
    
    # Step 4: Test analyzeDisruption tool
    print_section("Step 4: Test Analyze Disruption Tool")
    disruption_result = call_tool(
        GATEWAY_URL,
        access_token,
        "analyze-disruption___analyzeDisruption",
        {
            "original_flight": "AA123",
            "origin": "JFK",
            "destination": "LAX",
            "original_date": "2025-11-15",
            "disruption_reason": "mechanical issue"
        }
    )
    
    if disruption_result:
        print("Analyze Disruption Result:")
        print(json.dumps(disruption_result, indent=2))
    
    print_section("✅ All Tests Completed Successfully!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
