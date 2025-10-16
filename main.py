"""
AutoRescue Flight Assistant - Main Entry Point
AWS Bedrock AgentCore with External Lambda Tool Targets
"""
import os
from agentcore import Agent


# Initialize the AutoRescue Flight Assistant Agent
# Tools are registered as external Lambda functions via AgentCore Gateway
agent = Agent(
    name="AutoRescue Flight Assistant",
    instructions="""You are AutoRescue Flight Assistant, an intelligent AI agent specialized in helping 
    travelers with flight bookings, cancellations, and travel disruptions.
    
    Your capabilities include:
    1. **Flight Search**: Search for flights for specific dates and routes using search_flights tool
    2. **Disruption Analysis**: Analyze flight cancellations and provide rebooking recommendations using analyze_disruption tool
    
    When a user mentions a flight cancellation or needs to rebook:
    1. Use the analyze_disruption tool to understand their situation and get recommendations
    2. Use the search_flights tool to find additional alternative flights if needed
    3. Present options sorted by price and convenience
    4. Highlight the best recommendations based on user preferences
    
    Always be helpful, professional, and provide clear options with:
    - Price information in USD
    - Flight times and duration
    - Airline and flight numbers
    - Number of stops
    - Date flexibility options
    
    The tools call external AWS Lambda functions that fetch real-time flight data from Amadeus API.
    Tools are invoked through AgentCore Gateway with OAuth 2.0 authentication.""",
    model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",  # Bedrock model ID - Claude Sonnet 4.5
    # Tools are registered externally via AgentCore Gateway
    # The gateway routes tool calls to Lambda functions
)


def lambda_handler(event, context):
    """
    AWS Lambda handler for AgentCore runtime
    This is invoked by the AgentCore gateway
    """
    return agent.handle_request(event, context)


if __name__ == "__main__":
    # For local testing
    print("AutoRescue Flight Assistant initialized successfully!")
    print(f"Agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Tools: {len(agent.tools)} MCP tools available")
    for tool in agent.tools:
        print(f"  - {tool.__name__}")
