#!/usr/bin/env python3
"""
Test AutoRescue AgentCore Gateway - Comprehensive Gateway Testing
Tests both search-flights and offer-price tools via MCP protocol
"""

import json
import requests
import sys
import os
from datetime import datetime
import time

# Add agent_runtime to path for OAuth token functionality
sys.path.append('agent_runtime')

# Gateway Configuration
GATEWAY_URL = "https://autorescue-gateway-7ildpiqiqm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
REGION = "us-east-1"

def get_oauth_token():
    """Get OAuth token for gateway authentication"""
    try:
        from autorescue_agent import fetch_oauth_token
        return fetch_oauth_token()
    except Exception as e:
        print(f"❌ Failed to get OAuth token: {e}")
        return None

def test_gateway_connectivity(token):
    """Test basic gateway connectivity"""
    print("🔗 Testing Gateway Connectivity...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test basic MCP initialization
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "AutoRescue-Test",
                "version": "1.0.0"
            }
        }
    }
    
    try:
        response = requests.post(GATEWAY_URL, json=init_payload, headers=headers, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Gateway connectivity successful")
            print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
            return True
        else:
            print(f"   ❌ Gateway connectivity failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Gateway connectivity error: {e}")
        return False

def test_list_tools(token):
    """Test listing available tools"""
    print("\n🔧 Testing Tool Listing...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    list_tools_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        response = requests.post(GATEWAY_URL, json=list_tools_payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            tools = result.get('result', {}).get('tools', [])
            
            print(f"   ✅ Found {len(tools)} tools:")
            for i, tool in enumerate(tools, 1):
                print(f"   {i}. {tool.get('name', 'Unknown')}")
                print(f"      Description: {tool.get('description', 'N/A')}")
            
            return tools
        else:
            print(f"   ❌ Tool listing failed: {response.text}")
            return []
            
    except Exception as e:
        print(f"   ❌ Tool listing error: {e}")
        return []

def test_search_flights_tool(token):
    """Test the search-flights tool"""
    print("\n✈️ Testing Search Flights Tool...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test flight search
    search_payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "search-flights___searchFlights",
            "arguments": {
                "originLocationCode": "JFK",
                "destinationLocationCode": "LAX", 
                "departureDate": "2025-12-15",
                "adults": 1,
                "max": 5
            }
        }
    }
    
    try:
        print("   🔍 Searching flights JFK → LAX on 2025-12-15...")
        response = requests.post(GATEWAY_URL, json=search_payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'result' in result:
                print("   ✅ Flight search successful")
                
                # Parse and display results
                content = result['result'].get('content', [])
                if content and len(content) > 0:
                    text_content = content[0].get('text', '')
                    print(f"   📋 Results preview: {text_content[:200]}...")
                    
                    # Try to extract flight count
                    if 'flight' in text_content.lower():
                        print("   ✅ Flight data detected in response")
                    else:
                        print("   ⚠️  No flight data detected")
                        
                return True
            else:
                print(f"   ❌ Flight search failed: {result}")
                return False
                
        else:
            print(f"   ❌ Flight search HTTP error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Flight search error: {e}")
        return False

def test_offer_price_tool(token):
    """Test the offer-price tool"""
    print("\n💰 Testing Offer Price Tool...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Sample flight offer (this would normally come from search results)
    sample_offer = {
        "type": "flight-offer",
        "id": "1",
        "source": "GDS",
        "instantTicketingRequired": False,
        "nonHomogeneous": False,
        "oneWay": False,
        "lastTicketingDate": "2025-12-15",
        "numberOfBookableSeats": 4,
        "itineraries": [
            {
                "duration": "PT6H30M",
                "segments": [
                    {
                        "departure": {
                            "iataCode": "JFK",
                            "terminal": "4",
                            "at": "2025-12-15T08:00:00"
                        },
                        "arrival": {
                            "iataCode": "LAX",
                            "terminal": "B",
                            "at": "2025-12-15T11:30:00"
                        },
                        "carrierCode": "AA",
                        "number": "123",
                        "aircraft": {
                            "code": "321"
                        },
                        "operating": {
                            "carrierCode": "AA"
                        },
                        "duration": "PT6H30M",
                        "id": "1",
                        "numberOfStops": 0,
                        "blacklistedInEU": False
                    }
                ]
            }
        ],
        "price": {
            "currency": "USD",
            "total": "350.00",
            "base": "300.00",
            "fees": [
                {
                    "amount": "0.00",
                    "type": "SUPPLIER"
                }
            ],
            "grandTotal": "350.00"
        },
        "pricingOptions": {
            "fareType": ["PUBLISHED"],
            "includedCheckedBagsOnly": True
        },
        "validatingAirlineCodes": ["AA"],
        "travelerPricings": [
            {
                "travelerId": "1",
                "fareOption": "STANDARD",
                "travelerType": "ADULT",
                "price": {
                    "currency": "USD",
                    "total": "350.00",
                    "base": "300.00"
                }
            }
        ]
    }
    
    price_payload = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "offer-price___priceFlightOffer",
            "arguments": {
                "flightOffer": sample_offer
            }
        }
    }
    
    try:
        print("   💸 Pricing sample flight offer...")
        response = requests.post(GATEWAY_URL, json=price_payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'result' in result:
                print("   ✅ Offer pricing successful")
                
                # Parse and display results
                content = result['result'].get('content', [])
                if content and len(content) > 0:
                    text_content = content[0].get('text', '')
                    print(f"   📋 Pricing preview: {text_content[:200]}...")
                    
                    # Check for pricing keywords
                    pricing_keywords = ['price', 'total', 'fare', 'tax', 'fee']
                    found_keywords = [kw for kw in pricing_keywords if kw.lower() in text_content.lower()]
                    
                    if found_keywords:
                        print(f"   ✅ Pricing data detected: {found_keywords}")
                    else:
                        print("   ⚠️  No pricing data detected")
                        
                return True
            else:
                print(f"   ❌ Offer pricing failed: {result}")
                return False
                
        else:
            print(f"   ❌ Offer pricing HTTP error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Offer pricing error: {e}")
        return False

def main():
    """Main testing function"""
    print("🧪 AutoRescue AgentCore Gateway Testing")
    print("=" * 60)
    print(f"Gateway URL: {GATEWAY_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Get OAuth token
    print("🔐 Getting OAuth Token...")
    token = get_oauth_token()
    if not token:
        print("❌ Cannot proceed without OAuth token")
        return 1
    print("✅ OAuth token obtained")
    
    # Test results
    test_results = {
        "connectivity": False,
        "tools_list": False,
        "search_flights": False,
        "offer_price": False
    }
    
    # Run tests
    test_results["connectivity"] = test_gateway_connectivity(token)
    
    if test_results["connectivity"]:
        tools = test_list_tools(token)
        test_results["tools_list"] = len(tools) > 0
        
        test_results["search_flights"] = test_search_flights_tool(token)
        test_results["offer_price"] = test_offer_price_tool(token)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 GATEWAY TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All gateway tests passed! Gateway is fully functional.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())