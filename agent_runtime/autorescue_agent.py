"""
AutoRescue Flight Assistant Agent using AWS Bedrock AgentCore Runtime with Strands
Provides flight search and disruption analysis capabilities
"""

import os
import logging
from typing import List, Optional
from datetime import datetime
import requests
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AutoRescue")

# Initialize BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# Gateway Configuration from environment variables
GATEWAY_URL = os.getenv(
    "GATEWAY_URL",
    "https://autorescue-gateway-7ildpiqiqm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
)

# Cognito OAuth2 Configuration
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "5ptprke4sq904kc6kv067d4mjo")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET", "1k7ajt3pg59q2ef1oa9g449jteomhik63qod7e9vpckl0flnnp0r")
COGNITO_DOMAIN = os.getenv("COGNITO_DOMAIN", "autorescue-1760552868.auth.us-east-1.amazoncognito.com")

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")  # Allow override via env var

# Model Configuration
MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
)

# Custom Tools
@tool
def current_time() -> str:
    """Get the current date and time in ISO format."""
    return datetime.now().isoformat()


def fetch_oauth_token() -> str:
    """
    Fetch OAuth2 access token from Cognito using client credentials
    
    Returns:
        str: Access token
        
    Raises:
        Exception: If token fetch fails
    """
    token_url = f"https://{COGNITO_DOMAIN}/oauth2/token"
    
    try:
        logger.info("Fetching OAuth2 token from Cognito...")
        response = requests.post(
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=f"grant_type=client_credentials&client_id={COGNITO_CLIENT_ID}&client_secret={COGNITO_CLIENT_SECRET}",
            timeout=10
        )
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise ValueError("No access_token in response")
        
        logger.info(f"OAuth2 token obtained (expires in {token_data.get('expires_in', 'unknown')} seconds)")
        return access_token
        
    except Exception as e:
        logger.error(f"Failed to fetch OAuth2 token: {e}")
        raise


# System Prompt
SYSTEM_PROMPT = """You are AutoRescue, an AI-powered flight booking and disruption management assistant.
Your role is to help travelers with:

1. **Flight Search**: Find available flights between airports on specific dates
2. **Disruption Analysis**: When flights are canceled or delayed, find alternative options

## Guidelines

- Always be professional, empathetic, and helpful
- When searching for flights, ask for all required information:
  * Origin airport (3-letter IATA code like JFK)
  * Destination airport (3-letter IATA code like LAX)
  * Departure date (YYYY-MM-DD format)
  * Number of passengers (default to 1 if not specified)
  
- When handling disruptions:
  * Express empathy for the inconvenience
  * Prioritize same-day alternatives
  * Clearly categorize options (same-day, next-day, alternative dates)
  * Explain price differences and flight durations
  
- Present information clearly with:
  * Flight numbers and carriers
  * Departure and arrival times
  * Flight duration
  * Prices in USD
  
- If you don't have information, politely explain and offer to search again
- Never make assumptions about dates, airports, or passenger counts
- Always confirm important details with the user

## Tool Usage

You have access to these tools:
- **search-flights___searchFlights**: Search for available flights
- **analyze-disruption___analyzeDisruption**: Analyze flight cancellations and find alternatives
- **current_time**: Get current date and time for reference

Use these tools to provide accurate, real-time flight information.
"""


class AutoRescueAgent:
    """AutoRescue Flight Assistant Agent"""
    
    def __init__(
        self,
        bearer_token: str,
        model_id: str = MODEL_ID,
        system_prompt: str = SYSTEM_PROMPT,
        additional_tools: Optional[List[callable]] = None
    ):
        """
        Initialize AutoRescue Agent
        
        Args:
            bearer_token: OAuth2 bearer token for gateway authentication
            model_id: Bedrock model ID to use
            system_prompt: System prompt for the agent
            additional_tools: Additional tools to add to the agent
        """
        self.model_id = model_id
        self.system_prompt = system_prompt
        
        # Initialize Bedrock Model
        logger.info(f"Initializing Bedrock model: {self.model_id}")
        self.model = BedrockModel(model_id=self.model_id)
        
        # Initialize MCP Gateway Client
        logger.info(f"Connecting to gateway: {GATEWAY_URL}")
        try:
            self.gateway_client = MCPClient(
                lambda: streamablehttp_client(
                    GATEWAY_URL,
                    headers={"Authorization": f"Bearer {bearer_token}"}
                )
            )
            self.gateway_client.start()
            logger.info("Gateway client started successfully")
        except Exception as e:
            logger.error(f"Failed to initialize gateway client: {str(e)}")
            raise RuntimeError(f"Error initializing AutoRescue agent: {str(e)}")
        
        # Collect all tools
        self.tools = [
            current_time,  # Built-in time tool
        ] + self.gateway_client.list_tools_sync()  # Gateway MCP tools
        
        if additional_tools:
            self.tools.extend(additional_tools)
        
        logger.info(f"Loaded {len(self.tools)} tools")
        
        # Create the Strands Agent
        self.agent = Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            tools=self.tools,
        )
        
        logger.info("AutoRescue agent initialized successfully")
    
    def invoke(self, user_query: str) -> str:
        """
        Invoke the agent with a user query
        
        Args:
            user_query: The user's question or request
            
        Returns:
            The agent's response as a string
        """
        try:
            logger.info(f"Processing query: {user_query[:100]}...")
            response = self.agent(user_query)
            result = response.message["content"][0]["text"]
            logger.info(f"Response generated: {len(result)} characters")
            return result
        except Exception as e:
            error_msg = f"Error invoking agent: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def stream(self, user_query: str):
        """
        Stream the agent's response
        
        Args:
            user_query: The user's question or request
            
        Yields:
            Response chunks from the agent
        """
        try:
            logger.info(f"Streaming query: {user_query[:100]}...")
            async for event in self.agent.stream_async(user_query):
                yield event
        except Exception as e:
            error_msg = f"Error streaming agent response: {str(e)}"
            logger.error(error_msg)
            yield {"error": error_msg}


# Global agent instance (initialized on first request)
_agent_instance: Optional[AutoRescueAgent] = None


def get_agent_instance(bearer_token: str) -> AutoRescueAgent:
    """
    Get or create the agent instance
    
    Args:
        bearer_token: OAuth2 bearer token for gateway authentication
        
    Returns:
        AutoRescueAgent instance
    """
    global _agent_instance
    
    if _agent_instance is None:
        logger.info("Creating new AutoRescue agent instance")
        _agent_instance = AutoRescueAgent(bearer_token=bearer_token)
    
    return _agent_instance


@app.entrypoint
def invoke(payload: dict, context=None):
    """
    AgentCore Runtime entrypoint function
    
    Args:
        payload: Request payload containing:
            - prompt: User's message/question
            - bearer_token: (Optional) OAuth2 token for gateway authentication
        context: Runtime context information
        
    Returns:
        Agent's response dictionary
    """
    try:
        # Extract user message
        user_message = payload.get("prompt")
        if not user_message:
            return {"error": "Missing 'prompt' field in payload"}
        
        # Get bearer token - try payload first, then env var, then fetch dynamically
        bearer_token = payload.get("bearer_token") or ACCESS_TOKEN
        
        if not bearer_token:
            logger.info("No bearer token provided, fetching from Cognito...")
            try:
                bearer_token = fetch_oauth_token()
            except Exception as e:
                return {"error": f"Failed to obtain OAuth2 token: {str(e)}"}
        
        logger.info(f"Request received: {user_message[:100]}...")
        
        # Get agent instance
        agent = get_agent_instance(bearer_token)
        
        # Return synchronous response
        response_text = agent.invoke(user_message)
        return {
            "response": response_text,
            "model": MODEL_ID,
            "gateway": GATEWAY_URL
        }
    
    except Exception as e:
        error_msg = f"Error in entrypoint: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"error": error_msg}


if __name__ == "__main__":
    # Run the AgentCore Runtime app
    logger.info("Starting AutoRescue Agent Runtime...")
    app.run()
