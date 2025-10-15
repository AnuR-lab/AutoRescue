"""
AgentCore Gateway Management Script
Creates and manages AWS Bedrock AgentCore Gateway for AutoRescue
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
        self.ssm = boto3.client('ssm', region_name=region)
        self.project_name = 'autorescue'
        
    def create_gateway(self, name: str, api_spec_file: str = None):
        """Create AgentCore Gateway"""
        print(f"🚀 Creating AgentCore Gateway: {name}")
        
        # Load API specification
        if api_spec_file:
            with open(api_spec_file, 'r') as f:
                api_spec = json.load(f)
        else:
            # Default API spec for Amadeus integration
            api_spec = {
                "openapi": "3.0.0",
                "info": {
                    "title": "AutoRescue Flight API",
                    "version": "1.0.0",
                    "description": "MCP tools for flight search and disruption analysis"
                },
                "paths": {
                    "/search-flights": {
                        "post": {
                            "summary": "Search flights for specific date",
                            "operationId": "searchFlights",
                            "description": "Search for flight offers for a specific departure date",
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
                                                "return_date": {
                                                    "type": "string",
                                                    "format": "date",
                                                    "description": "Optional return date for round trips"
                                                },
                                                "adults": {
                                                    "type": "integer",
                                                    "default": 1,
                                                    "description": "Number of adult passengers"
                                                },
                                                "children": {
                                                    "type": "integer",
                                                    "default": 0,
                                                    "description": "Number of children passengers"
                                                },
                                                "travel_class": {
                                                    "type": "string",
                                                    "enum": ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"],
                                                    "description": "Cabin class preference"
                                                },
                                                "non_stop": {
                                                    "type": "boolean",
                                                    "default": False,
                                                    "description": "Only show non-stop flights"
                                                },
                                                "max_results": {
                                                    "type": "integer",
                                                    "default": 10,
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
                    "/analyze-flight-disruption": {
                        "post": {
                            "summary": "Analyze flight disruption and get rebooking recommendations",
                            "operationId": "analyzeFlightDisruption",
                            "description": "Analyze a flight cancellation or disruption and provide intelligent rebooking recommendations",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["original_flight_info"],
                                            "properties": {
                                                "original_flight_info": {
                                                    "type": "string",
                                                    "description": "JSON string with original flight details (origin, destination, date, flight_number)"
                                                },
                                                "user_preferences": {
                                                    "type": "string",
                                                    "default": "No specific preferences",
                                                    "description": "User preferences for rebooking (time constraints, cabin class, budget)"
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
            'region': self.region
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
        
        print(f"✅ Gateway configuration created: {config_file}")
        print(f"   Gateway Name: {name}")
        print(f"   API Endpoints: {len(api_spec['paths'])}")
        
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
