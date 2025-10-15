#!/usr/bin/env python3
"""
AutoRescue AgentCore Gateway - Complete Setup
Creates AgentCore Gateway with Lambda targets and Cognito OAuth2 authentication
"""
import boto3
import json
import time
import sys

# Configuration
GATEWAY_NAME = "autorescue-gateway"
ROLE_NAME = "autorescue-agentcore-gateway-role"
REGION = "us-east-1"

def create_iam_role_if_needed():
    """Create IAM role for the AgentCore gateway if it doesn't exist"""
    print("🔐 Setting up IAM role...")
    
    iam_client = boto3.client('iam')
    
    # Check if role exists
    try:
        role_response = iam_client.get_role(RoleName=ROLE_NAME)
        print(f"   ✅ Using existing IAM role")
        return role_response['Role']['Arn']
    except iam_client.exceptions.NoSuchEntityException:
        pass
    
    # Trust policy for AgentCore
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock-agentcore.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Create role
    role_response = iam_client.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description="Role for AutoRescue AgentCore Gateway to invoke Lambda functions",
    )
    
    # Attach policy to invoke Lambda functions
    lambda_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "lambda:InvokeFunction"
                ],
                "Resource": [
                    f"arn:aws:lambda:{REGION}:*:function:AutoRescue-*"
                ]
            }
        ]
    }
    
    iam_client.put_role_policy(
        RoleName=ROLE_NAME,
        PolicyName='InvokeLambdaPolicy',
        PolicyDocument=json.dumps(lambda_policy)
    )
    
    print(f"   ✅ Created IAM role: {ROLE_NAME}")
    print(f"   ⏳ Waiting 10 seconds for role propagation...")
    time.sleep(10)
    
    return role_response['Role']['Arn']

def setup_cognito_oauth():
    """Set up complete Cognito OAuth2 configuration"""
    print("🔐 Setting up Cognito OAuth2...")
    
    cognito_client = boto3.client('cognito-idp', region_name=REGION)
    
    # Check if we already have configuration
    try:
        with open('.cognito_oauth_config', 'r') as f:
            oauth_config = json.load(f)
        print(f"   ✅ Using existing Cognito configuration")
        print(f"   🆔 User Pool: {oauth_config['user_pool_id']}")
        print(f"   🌐 Domain: {oauth_config['domain']}")
        return oauth_config
    except FileNotFoundError:
        pass
    
    # Create new User Pool
    pool_name = f"autorescue-pool-{int(time.time())}"
    print(f"   🆔 Creating User Pool: {pool_name}")
    
    try:
        pool_response = cognito_client.create_user_pool(
            PoolName=pool_name,
            Policies={
                'PasswordPolicy': {
                    'MinimumLength': 8,
                    'RequireUppercase': False,
                    'RequireLowercase': False,
                    'RequireNumbers': False,
                    'RequireSymbols': False
                }
            },
            AutoVerifiedAttributes=['email']
        )
        
        user_pool_id = pool_response['UserPool']['Id']
        print(f"      ✅ User Pool created: {user_pool_id}")
        
        # Create User Pool Domain
        domain_name = f"autorescue-{int(time.time())}"
        cognito_client.create_user_pool_domain(
            Domain=domain_name,
            UserPoolId=user_pool_id
        )
        print(f"      ✅ Domain created: {domain_name}.auth.{REGION}.amazoncognito.com")
        
        # Create Resource Server with scopes
        cognito_client.create_resource_server(
            UserPoolId=user_pool_id,
            Identifier='autorescue-api',
            Name='AutoRescue API Resource Server',
            Scopes=[
                {'ScopeName': 'flights.read', 'ScopeDescription': 'Read flight information'},
                {'ScopeName': 'flights.search', 'ScopeDescription': 'Search for flights'},
                {'ScopeName': 'disruptions.analyze', 'ScopeDescription': 'Analyze flight disruptions'}
            ]
        )
        print(f"      ✅ Resource Server created with scopes")
        
        # Create User Pool Client
        client_response = cognito_client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName=f"{pool_name}-client",
            GenerateSecret=True,
            ExplicitAuthFlows=['ALLOW_ADMIN_USER_PASSWORD_AUTH', 'ALLOW_USER_PASSWORD_AUTH', 'ALLOW_REFRESH_TOKEN_AUTH'],
            SupportedIdentityProviders=['COGNITO'],
            AllowedOAuthFlows=['client_credentials'],
            AllowedOAuthScopes=['autorescue-api/flights.read', 'autorescue-api/flights.search', 'autorescue-api/disruptions.analyze'],
            AllowedOAuthFlowsUserPoolClient=True
        )
        
        client_id = client_response['UserPoolClient']['ClientId']
        client_secret = client_response['UserPoolClient']['ClientSecret']
        print(f"      ✅ Client created: {client_id}")
        
        # Save configuration
        oauth_config = {
            "client_id": client_id,
            "client_secret": client_secret,
            "user_pool_id": user_pool_id,
            "domain": f"{domain_name}.auth.{REGION}.amazoncognito.com",
            "token_url": f"https://{domain_name}.auth.{REGION}.amazoncognito.com/oauth2/token",
            "scopes": ["autorescue-api/flights.read", "autorescue-api/flights.search", "autorescue-api/disruptions.analyze"]
        }
        
        with open('.cognito_oauth_config', 'w') as f:
            json.dump(oauth_config, f, indent=2)
        
        with open('.cognito_client_info', 'w') as f:
            f.write(f"{client_id}\n{client_secret}")
            
        with open('.cognito_user_pool_id', 'w') as f:
            f.write(user_pool_id)
        
        return oauth_config
        
    except Exception as e:
        print(f"   ❌ Failed to setup Cognito: {e}")
        raise

def get_lambda_arn(lambda_client, function_name):
    """Get Lambda function ARN"""
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        return response['Configuration']['FunctionArn']
    except Exception as e:
        print(f"   ❌ Lambda function {function_name} not found: {e}")
        return None

def create_gateway(client, role_arn, oauth_config):
    """Create the AgentCore Gateway with Cognito authentication"""
    print("🚪 Creating AgentCore Gateway...")
    
    user_pool_id = oauth_config['user_pool_id']
    client_id = oauth_config['client_id']
    
    auth_config = {
        "customJWTAuthorizer": {
            "allowedClients": [client_id],
            "discoveryUrl": f"https://cognito-idp.{REGION}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
        }
    }
    
    try:
        response = client.create_gateway(
            name=GATEWAY_NAME,
            description="AutoRescue AgentCore Gateway with Lambda targets",
            roleArn=role_arn,
            protocolType='MCP',
            authorizerType='CUSTOM_JWT',
            authorizerConfiguration=auth_config
        )
        
        gateway_id = response['gatewayId']
        print(f"   ✅ Gateway created: {gateway_id}")
        
        # Wait for gateway to be ready
        print(f"   ⏳ Waiting for gateway to be ready...")
        for i in range(30):
            try:
                status_response = client.get_gateway(gatewayIdentifier=gateway_id)
                status = status_response.get('status', 'UNKNOWN')
                
                if status == 'READY':
                    print(f"   ✅ Gateway is ready!")
                    break
                elif status == 'FAILED':
                    print(f"   ❌ Gateway creation failed!")
                    return None
                else:
                    print(f"   ⏳ Status: {status} (attempt {i+1}/30)")
                    time.sleep(10)
                    
            except Exception:
                print(f"   ⏳ Checking status... (attempt {i+1}/30)")
                time.sleep(10)
        
        return gateway_id
        
    except Exception as e:
        print(f"   ❌ Failed to create gateway: {e}")
        import traceback
        traceback.print_exc()
        raise

def create_search_flights_target(client, gateway_id, lambda_arn):
    """Create the Search Flights Lambda target"""
    print("🎯 Creating Search Flights target...")
    
    # OpenAPI spec for search flights
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Search Flights API",
            "version": "1.0.0",
            "description": "Search for flight offers"
        },
        "servers": [
            {
                "url": lambda_arn,
                "description": "Search Flights Lambda"
            }
        ],
        "paths": {
            "/search-flights": {
                "post": {
                    "summary": "Search for flights",
                    "description": "Search for flight offers for a specific route and date",
                    "operationId": "searchFlights",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["origin", "destination", "departure_date"],
                                    "properties": {
                                        "origin": {
                                            "type": "string",
                                            "description": "Three-letter IATA airport code for departure (e.g., JFK)"
                                        },
                                        "destination": {
                                            "type": "string",
                                            "description": "Three-letter IATA airport code for arrival (e.g., LAX)"
                                        },
                                        "departure_date": {
                                            "type": "string",
                                            "description": "Departure date in YYYY-MM-DD format"
                                        },
                                        "adults": {
                                            "type": "integer",
                                            "description": "Number of adult passengers",
                                            "default": 1
                                        },
                                        "max_results": {
                                            "type": "integer",
                                            "description": "Maximum number of flight results",
                                            "default": 5
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Successful flight search"
                        }
                    }
                }
            }
        }
    }
    
    # Create target configuration
    target_config = {
        "mcp": {
            "openApiSchema": {
                "inlinePayload": json.dumps(openapi_spec)
            }
        }
    }
    
    try:
        response = client.create_gateway_target(
            gatewayIdentifier=gateway_id,
            name="search-flights-target",
            description="Search flights Lambda target",
            targetConfiguration=target_config
        )
        
        target_id = response['targetId']
        print(f"   ✅ Target created: {target_id}")
        
        # Wait for target to be ready
        print(f"   ⏳ Waiting for target to be ready...")
        for i in range(12):
            try:
                status_response = client.get_gateway_target(
                    gatewayIdentifier=gateway_id,
                    targetId=target_id
                )
                status = status_response.get('status', 'UNKNOWN')
                
                if status == 'READY':
                    print(f"   ✅ Target is ready!")
                    break
                elif status == 'FAILED':
                    print(f"   ❌ Target failed!")
                    break
                else:
                    print(f"   ⏳ Status: {status} (attempt {i+1}/12)")
                    time.sleep(10)
            except Exception:
                print(f"   ⏳ Checking status... (attempt {i+1}/12)")
                time.sleep(10)
        
        return target_id
        
    except Exception as e:
        print(f"   ❌ Failed to create target: {e}")
        import traceback
        traceback.print_exc()
        raise

def create_analyze_disruption_target(client, gateway_id, lambda_arn):
    """Create the Analyze Disruption Lambda target"""
    print("🎯 Creating Analyze Disruption target...")
    
    # OpenAPI spec for analyze disruption
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Analyze Disruption API",
            "version": "1.0.0",
            "description": "Analyze flight disruptions"
        },
        "servers": [
            {
                "url": lambda_arn,
                "description": "Analyze Disruption Lambda"
            }
        ],
        "paths": {
            "/analyze-disruption": {
                "post": {
                    "summary": "Analyze flight disruption",
                    "description": "Analyze a flight cancellation and provide rebooking recommendations",
                    "operationId": "analyzeDisruption",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["original_flight", "origin", "destination", "original_date"],
                                    "properties": {
                                        "original_flight": {
                                            "type": "string",
                                            "description": "Original flight number (e.g., AA123)"
                                        },
                                        "origin": {
                                            "type": "string",
                                            "description": "Three-letter IATA airport code for departure"
                                        },
                                        "destination": {
                                            "type": "string",
                                            "description": "Three-letter IATA airport code for arrival"
                                        },
                                        "original_date": {
                                            "type": "string",
                                            "description": "Original departure date in YYYY-MM-DD format"
                                        },
                                        "disruption_reason": {
                                            "type": "string",
                                            "description": "Reason for disruption",
                                            "default": "cancellation"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Disruption analysis with recommendations"
                        }
                    }
                }
            }
        }
    }
    
    # Create target configuration
    target_config = {
        "mcp": {
            "openApiSchema": {
                "inlinePayload": json.dumps(openapi_spec)
            }
        }
    }
    
    try:
        response = client.create_gateway_target(
            gatewayIdentifier=gateway_id,
            name="analyze-disruption-target",
            description="Analyze disruption Lambda target",
            targetConfiguration=target_config
        )
        
        target_id = response['targetId']
        print(f"   ✅ Target created: {target_id}")
        
        # Wait for target to be ready
        print(f"   ⏳ Waiting for target to be ready...")
        for i in range(12):
            try:
                status_response = client.get_gateway_target(
                    gatewayIdentifier=gateway_id,
                    targetId=target_id
                )
                status = status_response.get('status', 'UNKNOWN')
                
                if status == 'READY':
                    print(f"   ✅ Target is ready!")
                    break
                elif status == 'FAILED':
                    print(f"   ❌ Target failed!")
                    break
                else:
                    print(f"   ⏳ Status: {status} (attempt {i+1}/12)")
                    time.sleep(10)
            except Exception:
                print(f"   ⏳ Checking status... (attempt {i+1}/12)")
                time.sleep(10)
        
        return target_id
        
    except Exception as e:
        print(f"   ❌ Failed to create target: {e}")
        import traceback
        traceback.print_exc()
        raise

def save_gateway_info(gateway_id, targets, oauth_config, lambda_arns):
    """Save complete gateway information"""
    print("💾 Saving gateway information...")
    
    gateway_info = {
        "created": time.strftime('%Y-%m-%dT%H:%M:%S'),
        "gateway": {
            "id": gateway_id,
            "name": GATEWAY_NAME,
            "mcpUrl": f"https://{gateway_id}.gateway.bedrock-agentcore.{REGION}.amazonaws.com/mcp"
        },
        "targets": targets,
        "lambda_functions": lambda_arns,
        "oauth": {
            "client_id": oauth_config['client_id'],
            "user_pool_id": oauth_config['user_pool_id'],
            "token_url": oauth_config['token_url'],
            "scopes": oauth_config['scopes']
        }
    }
    
    with open('gateway_info.json', 'w') as f:
        json.dump(gateway_info, f, indent=2)
    
    # Store in SSM
    ssm = boto3.client('ssm', region_name=REGION)
    ssm.put_parameter(
        Name='/app/autorescue/agentcore/gateway_id',
        Value=gateway_id,
        Type='String',
        Overwrite=True
    )
    
    print("   ✅ Gateway info saved to gateway_info.json")
    return gateway_info

def main():
    """Main function to create complete AutoRescue AgentCore Gateway"""
    print("🚀 AutoRescue AgentCore Gateway - Complete Setup")
    print("=" * 60)
    
    try:
        # Setup IAM role
        role_arn = create_iam_role_if_needed()
        
        # Setup Cognito OAuth2
        oauth_config = setup_cognito_oauth()
        
        # Setup AgentCore client
        client = boto3.client('bedrock-agentcore-control', region_name=REGION)
        
        # Get Lambda ARNs
        lambda_client = boto3.client('lambda', region_name=REGION)
        
        print("\n📋 Checking Lambda functions...")
        search_flights_arn = get_lambda_arn(lambda_client, 'AutoRescue-SearchFlights')
        analyze_disruption_arn = get_lambda_arn(lambda_client, 'AutoRescue-AnalyzeDisruption')
        
        if not search_flights_arn or not analyze_disruption_arn:
            print("\n❌ Lambda functions not found! Please deploy them first:")
            print("   Run: ./scripts/deploy_lambdas.sh")
            return 1
        
        print(f"   ✅ SearchFlights: {search_flights_arn}")
        print(f"   ✅ AnalyzeDisruption: {analyze_disruption_arn}")
        
        lambda_arns = {
            'search_flights': search_flights_arn,
            'analyze_disruption': analyze_disruption_arn
        }
        
        # Create gateway
        print()
        gateway_id = create_gateway(client, role_arn, oauth_config)
        if not gateway_id:
            return 1
        
        # Create targets
        print()
        search_target_id = create_search_flights_target(client, gateway_id, search_flights_arn)
        
        print()
        disruption_target_id = create_analyze_disruption_target(client, gateway_id, analyze_disruption_arn)
        
        targets = {
            'search_flights': {
                'id': search_target_id,
                'name': 'search-flights-target',
                'lambda_arn': search_flights_arn
            },
            'analyze_disruption': {
                'id': disruption_target_id,
                'name': 'analyze-disruption-target',
                'lambda_arn': analyze_disruption_arn
            }
        }
        
        # Save info
        print()
        gateway_info = save_gateway_info(gateway_id, targets, oauth_config, lambda_arns)
        
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! AutoRescue AgentCore Gateway is ready!")
        print("=" * 60)
        print(f"Gateway URL: {gateway_info['gateway']['mcpUrl']}")
        print(f"Gateway ID: {gateway_id}")
        print(f"Client ID: {oauth_config['client_id']}")
        print(f"Token URL: {oauth_config['token_url']}")
        print(f"Scopes: {', '.join(oauth_config['scopes'])}")
        print("\n✅ Gateway configuration saved to gateway_info.json")
        print("✅ OAuth config saved to .cognito_oauth_config")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
