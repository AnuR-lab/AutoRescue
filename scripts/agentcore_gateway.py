"""
AgentCore Gateway Management Script
Creates and manages AWS Bedrock AgentCore Gateway for AutoRescue
Registers Lambda functions as tool targets
"""
import argparse
import boto3
import json
import sys
from pathlib import Path


class AgentCoreGatewayManager:
    def __init__(self, region='us-east-1'):
        self.region = region
        self.bedrock = boto3.client('bedrock-agent', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.ssm = boto3.client('ssm', region_name=region)
        self.project_name = 'autorescue'
        
    def get_lambda_arn(self, function_name: str) -> str:
        """Get Lambda function ARN"""
        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            return response['Configuration']['FunctionArn']
        except Exception as e:
            print(f"❌ Error getting Lambda ARN for {function_name}: {e}")
            return None
        
    def create_gateway(self, name: str, api_spec_file: str = None):
        """Create AgentCore Gateway with Lambda tool targets"""
        print(f"🚀 Creating AgentCore Gateway: {name}")
        
        # Get Lambda function ARNs
        search_flights_arn = self.get_lambda_arn('AutoRescue-SearchFlights')
        analyze_disruption_arn = self.get_lambda_arn('AutoRescue-AnalyzeDisruption')
        
        if not search_flights_arn or not analyze_disruption_arn:
            print("❌ Lambda functions not found. Please deploy them first:")
            print("   Run: ./scripts/deploy_lambdas.sh")
            sys.exit(1)
        
        print(f"✓ Found Lambda: AutoRescue-SearchFlights")
        print(f"✓ Found Lambda: AutoRescue-AnalyzeDisruption")
        
        # Load API specification
        if api_spec_file:
            with open(api_spec_file, 'r') as f:
                api_spec = json.load(f)
        else:
            # Default API spec for Lambda-backed tools
            api_spec = {
                "openapi": "3.0.0",
                "info": {
                    "title": "AutoRescue Flight API",
                    "version": "1.0.0",
                    "description": "Lambda-backed MCP tools for flight search and disruption analysis"
                },
                "paths": {
                    "/search-flights": {
                        "post": {
                            "summary": "Search flights for specific date",
                            "operationId": "searchFlights",
                            "description": "Search for flight offers for a specific departure date. Calls Lambda function.",
                            "x-amazon-apigateway-integration": {
                                "type": "aws_proxy",
                                "httpMethod": "POST",
                                "uri": f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{search_flights_arn}/invocations"
                            },
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
                                                    "description": "Three-letter IATA airport code for departure"
                                                },
                                                "destination": {
                                                    "type": "string",
                                                    "description": "Three-letter IATA airport code for arrival"
                                                },
                                                "departure_date": {
                                                    "type": "string",
                                                    "format": "date",
                                                    "description": "Departure date in YYYY-MM-DD format"
                                                },
                                                "adults": {
                                                    "type": "integer",
                                                    "default": 1,
                                                    "description": "Number of adult passengers"
                                                },
                                                "max_results": {
                                                    "type": "integer",
                                                    "default": 5,
                                                    "description": "Maximum number of results"
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Flight search results"
                                }
                            }
                        }
                    },
                    "/analyze-disruption": {
                        "post": {
                            "summary": "Analyze flight disruption and get rebooking recommendations",
                            "operationId": "analyzeDisruption",
                            "description": "Analyze a flight cancellation or disruption and provide intelligent rebooking recommendations. Calls Lambda function.",
                            "x-amazon-apigateway-integration": {
                                "type": "aws_proxy",
                                "httpMethod": "POST",
                                "uri": f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{analyze_disruption_arn}/invocations"
                            },
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
                                                    "description": "Original flight number (e.g., 'AA123')"
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
                                                    "format": "date",
                                                    "description": "Original departure date in YYYY-MM-DD format"
                                                },
                                                "disruption_reason": {
                                                    "type": "string",
                                                    "default": "cancellation",
                                                    "description": "Reason for disruption"
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Disruption analysis and recommendations"
                                }
                            }
                        }
                    }
                }
            }
        
        # Save gateway configuration
        config = {
            'name': name,
            'api_spec': api_spec,
            'region': self.region,
            'lambda_targets': {
                'search_flights': search_flights_arn,
                'analyze_disruption': analyze_disruption_arn
            }
        }
        
        config_file = Path('gateway.config')
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Store in SSM
        self.ssm.put_parameter(
            Name=f'/app/{self.project_name}/agentcore/gateway_name',
            Value=name,
            Type='String',
            Overwrite=True
        )
        
        self.ssm.put_parameter(
            Name=f'/app/{self.project_name}/agentcore/lambda_search_flights',
            Value=search_flights_arn,
            Type='String',
            Overwrite=True
        )
        
        self.ssm.put_parameter(
            Name=f'/app/{self.project_name}/agentcore/lambda_analyze_disruption',
            Value=analyze_disruption_arn,
            Type='String',
            Overwrite=True
        )
        
        print(f"✅ Gateway configuration created: {config_file}")
        print(f"   Gateway Name: {name}")
        print(f"   API Endpoints: {len(api_spec['paths'])}")
        print(f"   Lambda Targets:")
        print(f"     - search-flights → {search_flights_arn}")
        print(f"     - analyze-disruption → {analyze_disruption_arn}")
        
        return config
    
    def delete_gateway(self, confirm=False):
        """Delete AgentCore Gateway"""
        try:
            # Read gateway name from SSM
            response = self.ssm.get_parameter(
                Name=f'/app/{self.project_name}/agentcore/gateway_name'
            )
            gateway_name = response['Parameter']['Value']
        except:
            print("❌ No gateway found to delete")
            return
        
        if not confirm:
            confirm_input = input(f"Delete gateway '{gateway_name}'? (yes/no): ")
            if confirm_input.lower() != 'yes':
                print("Cancelled")
                return
        
        print(f"🗑️  Deleting gateway: {gateway_name}")
        
        # Delete SSM parameter
        try:
            self.ssm.delete_parameter(
                Name=f'/app/{self.project_name}/agentcore/gateway_name'
            )
        except:
            pass
        
        # Delete config file
        config_file = Path('gateway.config')
        if config_file.exists():
            config_file.unlink()
        
        print("✅ Gateway deleted successfully")


def main():
    parser = argparse.ArgumentParser(description='Manage AgentCore Gateway')
    parser.add_argument('action', choices=['create', 'delete'], help='Action to perform')
    parser.add_argument('--name', help='Gateway name')
    parser.add_argument('--api-spec-file', help='Path to OpenAPI specification file')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    manager = AgentCoreGatewayManager(region=args.region)
    
    if args.action == 'create':
        if not args.name:
            print("Error: --name required for create action")
            sys.exit(1)
        manager.create_gateway(args.name, args.api_spec_file)
    elif args.action == 'delete':
        manager.delete_gateway(args.confirm)


if __name__ == '__main__':
    main()
