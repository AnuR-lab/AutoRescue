#!/usr/bin/env python3
"""
Test script for the offer_price Lambda function through AgentCore Gateway
Tests the priceFlightOffer tool via MCP protocol
"""

import os
import json
import boto3
import requests
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Gateway Configuration
GATEWAY_URL = "https://autorescue-gateway-7ildpiqiqm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
COGNITO_DOMAIN = "autorescue-1760631013.auth.us-east-1.amazoncognito.com"

def get_cognito_credentials():
    """Fetch Cognito credentials from AWS Secrets Manager"""
    secret_name = "autorescue/cognito/credentials"
    region_name = 'us-east-1'
    
    client = boto3.client('secretsmanager', region_name=region_name)
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        logger.error(f"Failed to fetch Cognito credentials: {e}")
        raise

def get_oauth_token():
    """Get OAuth2 token from Cognito"""
    credentials = get_cognito_credentials()
    token_url = f"https://{COGNITO_DOMAIN}/oauth2/token"
    
    logger.info("Fetching OAuth2 token...")
    response = requests.post(
        token_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f"grant_type=client_credentials&client_id={credentials['client_id']}&client_secret={credentials['client_secret']}",
        timeout=10
    )
    response.raise_for_status()
    
    token_data = response.json()
    return token_data.get("access_token")

def test_gateway_connection(access_token):
    """Test basic gateway connection"""
    logger.info("Testing gateway connection...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Test with a simple list tools request
    test_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        response = requests.post(GATEWAY_URL, headers=headers, json=test_payload, timeout=30)
        logger.info(f"Gateway response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            tools = data.get("result", {}).get("tools", [])
            logger.info(f"Available tools: {[tool.get('name') for tool in tools]}")
            return True
        else:
            logger.error(f"Gateway connection failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Gateway connection error: {e}")
        return False

def test_offer_price_tool(access_token):
    """Test the priceFlightOffer tool with sample data"""
    logger.info("Testing priceFlightOffer tool...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Load flight offer data from file
    try:
        with open('test_offer_price_payload.json', 'r') as f:
            sample_flight_offer = json.load(f)
        logger.info("Loaded flight offer data from test_offer_price_payload.json")
    except Exception as e:
        logger.error(f"Failed to load payload file: {e}")
        return False
    
    # MCP tool call payload
    tool_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "offer-price___priceFlightOffer",
            "arguments": {
                "flight_offer": sample_flight_offer
            }
        }
    }
    
    try:
        logger.info("Sending priceFlightOffer request...")
        response = requests.post(GATEWAY_URL, headers=headers, json=tool_payload, timeout=60)
        logger.info(f"Tool response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("Tool call successful!")
            
            if "result" in data:
                result = data["result"]
                if "content" in result:
                    for content_item in result["content"]:
                        if content_item.get("type") == "text":
                            logger.info(f"Response: {content_item.get('text', '')[:200]}...")
                        else:
                            logger.info(f"Content type: {content_item.get('type')}")
                else:
                    logger.info(f"Raw result: {json.dumps(result, indent=2)[:500]}...")
            else:
                logger.info(f"Full response: {json.dumps(data, indent=2)[:500]}...")
                
            return True
        else:
            logger.error(f"Tool call failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Tool call error: {e}")
        return False

def main():
    """Main test function"""
    logger.info("Starting offer_price gateway test...")
    
    try:
        # Get OAuth token
        access_token = get_oauth_token()
        if not access_token:
            logger.error("Failed to get access token")
            return False
        
        logger.info("Successfully obtained access token")
        
        # Test gateway connection
        if not test_gateway_connection(access_token):
            logger.error("Gateway connection test failed")
            return False
        
        # Test the offer_price tool
        if not test_offer_price_tool(access_token):
            logger.error("offer_price tool test failed")
            return False
        
        logger.info("✅ All tests passed! offer_price target is working through gateway")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)