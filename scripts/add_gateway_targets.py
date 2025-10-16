#!/usr/bin/env python3
"""
Add Lambda targets to existing AutoRescue AgentCore Gateway
"""

import boto3
import json
import sys
import time
import os

# Configuration
REGION = 'us-east-1'
GATEWAY_ID = 'autorescue-gateway-7ildpiqiqm'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
MCP_TOOLS_DIR = os.path.join(PROJECT_DIR, 'mcp_tools')

def load_mcp_tool(tool_name):
    """Load MCP tool specification from JSON file"""
    tool_file = os.path.join(MCP_TOOLS_DIR, f"{tool_name}.json")
    with open(tool_file, 'r') as f:
        return json.load(f)

def get_lambda_arn(lambda_client, function_name):
    """Get Lambda function ARN"""
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        return response['Configuration']['FunctionArn']
    except Exception as e:
        print(f"   ❌ Error getting Lambda ARN for {function_name}: {e}")
        return None

def verify_gateway(client, gateway_id):
    """Verify gateway exists and is ready"""
    try:
        print(f"🔍 Verifying gateway '{gateway_id}'...")
        
        response = client.get_gateway(gatewayIdentifier=gateway_id)
        status = response.get('status')
        name = response.get('name')
        
        print(f"   ✅ Found gateway: {name} (Status: {status})")
        
        if status != 'READY':
            print(f"   ⚠️ Gateway is not READY (current status: {status})")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error verifying gateway: {e}")
        return False

def create_iam_credential_provider(client, gateway_id):
    """Create IAM role credential provider for Lambda invocation"""
    print("\n🔐 Creating IAM credential provider for Lambda invocation...")
    
    try:
        response = client.create_credential_provider_configuration(
            gatewayIdentifier=gateway_id,
            name="lambda-iam-auth",
            description="IAM role authentication for Lambda invocation",
            authType="IAM_ROLE",
            iamRoleConfiguration={}  # Use gateway's IAM role
        )
        
        provider_id = response['id']
        print(f"   ✅ Credential provider created: {provider_id}")
        return provider_id
        
    except client.exceptions.ConflictException:
        print(f"   ⚠️ Credential provider 'lambda-iam-auth' already exists")
        # Try to get existing provider
        try:
            response = client.list_credential_provider_configurations(gatewayIdentifier=gateway_id)
            for provider in response.get('credentialProviderConfigurations', []):
                if provider.get('name') == 'lambda-iam-auth':
                    provider_id = provider.get('id')
                    print(f"   ✅ Using existing provider: {provider_id}")
                    return provider_id
        except Exception as list_error:
            print(f"   ❌ Error listing providers: {list_error}")
        return None
        
    except Exception as e:
        print(f"   ❌ Failed to create credential provider: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_search_flights_target(client, gateway_id, lambda_arn):
    """Create the Search Flights Lambda target"""
    print("\n🎯 Creating Search Flights target...")
    
    # Load MCP tool definition from JSON file
    mcp_tool = load_mcp_tool('search_flights')
    
    # Create target configuration for Lambda
    # toolSchema.inlinePayload expects an array of MCP tool definitions
    target_config = {
        "mcp": {
            "lambda": {
                "lambdaArn": lambda_arn,
                "toolSchema": {
                    "inlinePayload": [mcp_tool]
                }
            }
        }
    }
    
    # For Lambda targets, use GATEWAY_IAM_ROLE credential provider type
    # This uses the gateway's IAM role to invoke the Lambda function
    credential_configs = [
        {
            "credentialProviderType": "GATEWAY_IAM_ROLE"
        }
    ]
    
    try:
        response = client.create_gateway_target(
            gatewayIdentifier=gateway_id,
            name="search-flights",
            description="Search flights Lambda target",
            targetConfiguration=target_config,
            credentialProviderConfigurations=credential_configs
        )
        
        target_id = response['targetId']
        print(f"   ✅ Target created: {target_id}")
        
        # Wait for target to be ready
        print(f"   ⏳ Waiting for target to be ready...")
        for i in range(20):
            try:
                status_response = client.get_gateway_target(
                    gatewayIdentifier=gateway_id,
                    targetId=target_id
                )
                status = status_response.get('status', 'UNKNOWN')
                
                if status == 'READY':
                    print(f"   ✅ Target is READY!")
                    return target_id
                elif status == 'FAILED':
                    failure_reasons = status_response.get('failureReasons', ['Unknown'])
                    print(f"   ❌ Target FAILED: {failure_reasons}")
                    return None
                else:
                    print(f"   ⏳ Status: {status} (attempt {i+1}/20)")
                    time.sleep(10)
            except Exception as check_error:
                print(f"   ⏳ Checking... (attempt {i+1}/20)")
                time.sleep(10)
        
        print(f"   ⚠️ Timeout waiting for target to be ready")
        return target_id
        
    except client.exceptions.ConflictException:
        print(f"   ⚠️ Target 'search-flights' already exists")
        # Try to get existing target
        try:
            response = client.list_gateway_targets(gatewayIdentifier=gateway_id)
            for target in response.get('targets', []):
                if target.get('name') == 'search-flights':
                    target_id = target.get('id')
                    print(f"   ✅ Using existing target: {target_id}")
                    return target_id
        except:
            pass
        return "EXISTING"  # Special value to indicate target exists
        
    except Exception as e:
        print(f"   ❌ Failed to create target: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_offer_price_target(client, gateway_id, lambda_arn):
    """Create the Offer Price Lambda target"""
    print("\n🎯 Creating Offer Price target...")
    
    # Load MCP tool definition from JSON file
    mcp_tool = load_mcp_tool('offer_price')
    
    # Create target configuration for Lambda
    # toolSchema.inlinePayload expects an array of MCP tool definitions
    target_config = {
        "mcp": {
            "lambda": {
                "lambdaArn": lambda_arn,
                "toolSchema": {
                    "inlinePayload": [mcp_tool]
                }
            }
        }
    }
    
    # For Lambda targets, use GATEWAY_IAM_ROLE credential provider type
    # This uses the gateway's IAM role to invoke the Lambda function
    credential_configs = [
        {
            "credentialProviderType": "GATEWAY_IAM_ROLE"
        }
    ]
    
    try:
        response = client.create_gateway_target(
            gatewayIdentifier=gateway_id,
            name="offer-price",
            description="Price flight offer Lambda target",
            targetConfiguration=target_config,
            credentialProviderConfigurations=credential_configs
        )
        
        target_id = response['targetId']
        print(f"   ✅ Target created: {target_id}")
        
        # Wait for target to be ready
        print(f"   ⏳ Waiting for target to be ready...")
        for i in range(20):
            try:
                status_response = client.get_gateway_target(
                    gatewayIdentifier=gateway_id,
                    targetId=target_id
                )
                status = status_response.get('status', 'UNKNOWN')
                
                if status == 'READY':
                    print(f"   ✅ Target is READY!")
                    return target_id
                elif status == 'FAILED':
                    failure_reasons = status_response.get('failureReasons', ['Unknown'])
                    print(f"   ❌ Target FAILED: {failure_reasons}")
                    return None
                else:
                    print(f"   ⏳ Status: {status} (attempt {i+1}/20)")
                    time.sleep(10)
            except Exception as check_error:
                print(f"   ⏳ Checking... (attempt {i+1}/20)")
                time.sleep(10)
        
        print(f"   ⚠️ Timeout waiting for target to be ready")
        return target_id
        
    except client.exceptions.ConflictException:
        print(f"   ⚠️ Target 'offer-price' already exists")
        # Try to get existing target
        try:
            response = client.list_gateway_targets(gatewayIdentifier=gateway_id)
            for target in response.get('targets', []):
                if target.get('name') == 'offer-price':
                    target_id = target.get('id')
                    print(f"   ✅ Using existing target: {target_id}")
                    return target_id
        except:
            pass
        return "EXISTING"  # Special value to indicate target exists
        
    except Exception as e:
        print(f"   ❌ Failed to create target: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function"""
    print("🚀 Adding Lambda Targets to AutoRescue Gateway")
    print("=" * 60)
    
    try:
        # Setup clients
        client = boto3.client('bedrock-agentcore-control', region_name=REGION)
        lambda_client = boto3.client('lambda', region_name=REGION)
        
        # Verify gateway exists
        if not verify_gateway(client, GATEWAY_ID):
            return 1
        
        # Get Lambda ARNs
        print("\n📋 Checking Lambda functions...")
        search_flights_arn = get_lambda_arn(lambda_client, 'AutoRescue-SearchFlights')
        offer_price_arn = get_lambda_arn(lambda_client, 'AutoRescue-OfferPrice')
        
        if not search_flights_arn or not offer_price_arn:
            print("\n❌ Lambda functions not found! Please deploy them first:")
            print("   Run: ./scripts/deploy_sam.sh")
            return 1
        
        print(f"   ✅ SearchFlights: {search_flights_arn}")
        print(f"   ✅ OfferPrice: {offer_price_arn}")
        
        # Create targets with inline IAM role credential configuration
        search_target_id = create_search_flights_target(client, GATEWAY_ID, search_flights_arn)
        offer_price_target_id = create_offer_price_target(client, GATEWAY_ID, offer_price_arn)
        
        # Summary
        print("\n" + "=" * 60)
        # If targets exist or were created, consider it success
        search_ok = search_target_id is not None and search_target_id != False
        price_ok = offer_price_target_id is not None and offer_price_target_id != False
        
        if search_ok and price_ok:
            print("🎉 SUCCESS! Both targets are available in gateway")
            print("=" * 60)
            print(f"Gateway ID: {GATEWAY_ID}")
            print(f"Search Flights Target: {search_target_id if search_target_id != 'EXISTING' else 'existing'}")
            print(f"Offer Price Target: {offer_price_target_id if offer_price_target_id != 'EXISTING' else 'existing'}")
            print("\n✅ Your AutoRescue gateway is ready to use!")
            print(f"Gateway URL: https://{GATEWAY_ID}.gateway.bedrock-agentcore.{REGION}.amazonaws.com/mcp")
            return 0
        else:
            print("⚠️ Some targets may have failed to create")
            print(f"   Search Flights: {search_target_id}")
            print(f"   Offer Price: {offer_price_target_id}")
            print("=" * 60)
            return 1
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
