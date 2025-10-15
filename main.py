"""
AutoRescue Flight Assistant - Main Entry Point
AWS Bedrock AgentCore with MCP Tools
"""
import os
from agentcore import Agent
from amadeus_mcp_tools import (
    search_flights_tool,
    analyze_flight_disruption_tool
)


# Initialize the AutoRescue Flight Assistant Agent
agent = Agent(
    name="AutoRescue Flight Assistant",
    instructions="""You are AutoRescue Flight Assistant, an intelligent AI agent specialized in helping 
    travelers with flight bookings, cancellations, and travel disruptions.
    
    Your capabilities include:
    1. **Flight Search**: Search for flights for specific dates and routes
    2. **Disruption Analysis**: Analyze flight cancellations and provide rebooking recommendations
    
    When a user mentions a flight cancellation or needs to rebook:
    1. Use the analyze_flight_disruption tool to understand their situation
    2. Use the search_flights tool to find alternative flights
    3. Present options sorted by price and convenience
    4. Highlight the best recommendations based on user preferences
    
    Always be helpful, professional, and provide clear options with:
    - Price information in USD
    - Flight times and duration
    - Airline and flight numbers
    - Number of stops
    
    Use the MCP tools available to you to fetch real-time flight data from Amadeus API.""",
    model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",  # Bedrock model ID
    tools=[
        search_flights_tool,
        analyze_flight_disruption_tool
    ]
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
