"""
AutoRescue Flight Assistant Agent using AWS Bedrock AgentCore Runtime with Strands
Provides flight search and disruption analysis capabilities
"""

import os
import json
import boto3
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import requests
from random import choice, randint
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

# Cognito Domain Configuration
COGNITO_DOMAIN = os.getenv("COGNITO_DOMAIN", "autorescue-1760631013.auth.us-east-1.amazoncognito.com")

# Secrets cache
_secrets_cache = {
    'cognito_credentials': None,
    'fetched_at': None
}

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")  # Allow override via env var


def _get_cognito_credentials() -> Dict[str, str]:
    """
    Fetch Cognito credentials from AWS Secrets Manager with caching
    """
    # Return cached credentials if recently fetched (within 1 hour)
    if _secrets_cache['cognito_credentials'] and _secrets_cache['fetched_at']:
        elapsed = datetime.now() - _secrets_cache['fetched_at']
        if elapsed.total_seconds() < 3600:
            return _secrets_cache['cognito_credentials']
    
    # Fetch from Secrets Manager
    secret_name = "autorescue/cognito/credentials"
    region_name = os.getenv('AWS_REGION', 'us-east-1')
    
    client = boto3.client('secretsmanager', region_name=region_name)
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        
        # Cache the credentials
        _secrets_cache['cognito_credentials'] = secret
        _secrets_cache['fetched_at'] = datetime.now()
        
        return secret
    except Exception as e:
        logger.error(f"Failed to fetch Cognito credentials: {e}")
        raise RuntimeError(f"Failed to fetch Cognito credentials from Secrets Manager: {str(e)}")

# Model Configuration
MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
)

# Custom Tools
@tool
def current_time() -> str:
    """Get the current date and time in ISO format."""
    return datetime.now().isoformat()


@tool
def random_flight_suggestion() -> dict:
    """Generate a random flight search suggestion.
    Returns a dict with origin (North America), destination (Europe), airline based on route, and departure_date within next 14 days.
    """
    # North America airports with country mapping
    north_america_airports = {
        "JFK": "US", "EWR": "US", "LAX": "US", "ORD": "US", "DFW": "US", 
        "MIA": "US", "ATL": "US", "SEA": "US", "BOS": "US", "IAD": "US",
        "YYZ": "CA", "YUL": "CA", "YVR": "CA"
    }
    
    # Europe airports with country mapping
    europe_airports = {
        "LHR": "GB", "LGW": "GB", "MAN": "GB",  # UK
        "CDG": "FR", "ORY": "FR",  # France
        "AMS": "NL",  # Netherlands
        "FRA": "FR", "MUC": "DE",  # Germany
        "MAD": "ES", "BCN": "ES",  # Spain
        "DUB": "IE",  # Ireland
        "CPH": "DK",  # Denmark
        "FCO": "IT", "MXP": "IT"  # Italy
    }
    
    # Major carriers by country/region
    carriers = {
        "US": ["AA", "DL", "UA"],  # American, Delta, United
        "CA": ["AC"],  # Air Canada
        "GB": ["BA", "VS"],  # British Airways, Virgin Atlantic
        "FR": ["AF"],  # Air France
        "NL": ["KL"],  # KLM
        "DE": ["LH"],  # Lufthansa
        "ES": ["IB"],  # Iberia
        "IE": ["EI"],  # Aer Lingus
        "DK": ["SK"],  # SAS Scandinavian
        "IT": ["AZ"]  # ITA Airways
    }
    
    # Select random airports
    origin = choice(list(north_america_airports.keys()))
    destination = choice(list(europe_airports.keys()))
    
    # Get countries
    origin_country = north_america_airports[origin]
    destination_country = europe_airports[destination]
    
    # Choose airline from either origin or destination country
    available_carriers = carriers.get(origin_country, []) + carriers.get(destination_country, [])
    
    # If no carriers found (shouldn't happen), use default major transatlantic carriers
    if not available_carriers:
        available_carriers = ["AA", "BA", "DL", "AF", "AC"]
    
    airline = choice(available_carriers)
    days_ahead = randint(2, 14)  # Avoid same-day, start at 2 days out
    departure_date = (datetime.utcnow() + timedelta(days=days_ahead)).date().isoformat()
    
    return {
        "origin": origin,
        "destination": destination,
        "preferredAirline": airline,
        "departureDate": departure_date,
        "passengers": 1,
        "note": f"Sample transatlantic route with {airline} carrier based on origin/destination countries."
    }


def fetch_oauth_token() -> str:
    """
    Fetch OAuth2 access token from Cognito using client credentials
    
    Returns:
        str: Access token
        
    Raises:
        Exception: If token fetch fails
    """
    # Get credentials from Secrets Manager
    credentials = _get_cognito_credentials()
    
    token_url = f"https://{COGNITO_DOMAIN}/oauth2/token"
    
    try:
        logger.info("Fetching OAuth2 token from Cognito...")
        response = requests.post(
            token_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=f"grant_type=client_credentials&client_id={credentials['client_id']}&client_secret={credentials['client_secret']}",
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
2. **Flight Pricing**: Get final pricing and booking details for selected flights

## Complete Booking Workflow

When a user wants to book a flight, follow this exact sequence:

1. **Search for Flights** - Use `searchFlights` tool to find available options
2. **Present Options** - Show the user flight details (times, duration, price)
3. **User Selects** - Wait for user to select their preferred flight option
4. **Price the Offer** - Use `priceFlightOffer` tool with the COMPLETE flight offer object to get final pricing
5. **Present Final Details** - Show validated pricing, taxes, fees, and booking requirements
6. **Collect Booking Information** - When user confirms booking, collect required details:
    - Traveler information (name, date of birth, gender, contact details)
    - Travel documents (passport/ID information)
    - Contact information for booking confirmation
7. **Complete Booking** - Use `bookFlight` tool to finalize the reservation and receive booking confirmation

## CRITICAL: Disruption/Cancellation Handling Rules

When handling CANCELLED or DISRUPTED flights, the following parameters are **LOCKED and CANNOT be changed**:
- **Origin airport**: Must remain the same as the cancelled flight
- **Destination airport**: Must remain the same as the cancelled flight  
- **Airline/Carrier**: Must remain the same as the cancelled flight

The ONLY parameter that can be changed is:
- **Departure date**: The passenger can choose a new date

**When you see a prompt indicating "LOCKED" parameters or cancelled flight rebooking:**
1. Extract the locked origin, destination, and carrier from the prompt
2. ONLY ask the user about their preferred NEW departure date if not provided
3. When calling searchFlights, ALWAYS include the carrier parameter with the locked airline code
4. Do NOT offer to change origin, destination, or airline
5. Present results as rebooking options for the SAME route and airline

## Guidelines

- Always be professional, empathetic, and helpful
- When searching for flights, ask for all required information:
  * Origin airport (3-letter IATA code like JFK)
  * Destination airport (3-letter IATA code like LAX)
  * Departure date (YYYY-MM-DD format)
  * Number of passengers (default to 1 if not specified)
  * Carrier/Airline code (when rebooking cancelled flights - this is MANDATORY)
  
- When pricing a selected flight:
  * CRITICAL: Pass the ENTIRE flight offer object from search results to priceFlightOffer
  * Do not modify or summarize the flight offer object
  * The pricing validates availability and provides final price with all taxes and fees
  * Present booking requirements (passport, ID, contact info, etc.)
  * Highlight the ticketing deadline clearly
  
- When handling disruptions:
  * Express empathy for the inconvenience
  * Prioritize same-day alternatives
  * Clearly categorize options (same-day, next-day, alternative dates)
  * Explain price differences and flight durations
  
- Present information clearly with:
  * Flight numbers and carriers
  * Departure and arrival times
  * Flight duration
  * Prices in USD with tax breakdown
  * Number of seats available
  
- If you don't have information, politely explain and offer to search again.
- If no flights could be found for the user's request, ask the user to contact the customer service desk for further assistance.
- Never make assumptions about dates, airports, or passenger counts
- Always confirm important details with the user

## Flight Selection and Pricing Workflow

**IMPORTANT**: When a user expresses interest in booking or selecting a specific flight offer from search results:

1. **Identify Selection**: Look for phrases like:
    - "I want to book flight X"
    - "Please select option 2"
    - "I'll take the morning flight"
    - "Book the cheapest option"
    - "I want the [specific flight details]"

2. **Extract Flight Offer**: From the previous search results, identify the flight that matches the user's selection.
    - Each flight in search results has two parts:
      * "summary": Human-readable info (carrier, times, price, stops)
      * "amadeus_offer": Complete Amadeus flight offer object
    - Use the "summary" to understand which flight the user wants
    - Use the "amadeus_offer" for the pricing API call

3. **Call offer-price___priceFlightOffer**: Automatically call this tool with the complete Amadeus offer to get:
    - Final pricing with all taxes and fees
    - Booking conditions and requirements
    - Seat availability confirmation
    - Payment and ticketing deadlines
    
    **CRITICAL**: Pass the ENTIRE "amadeus_offer" object from the selected flight. 
    Do NOT use the "summary" object for pricing - it's only for display.
    The "amadeus_offer" includes all required fields:
    - type, id, source, instantTicketingRequired, nonHomogeneous, oneWay
    - lastTicketingDate, numberOfBookableSeats
    - itineraries (complete with all segments and their IDs)
    - price (with currency, total, base, fees, grandTotal)
    - pricingOptions, validatingAirlineCodes
    - travelerPricings (complete array with all fare details)

4. **Present Results**: Show the user:
    - Final total price (may differ from search price)
    - All included services and fees
    - Booking conditions
    - Next steps for completing the booking

## Tool Usage

You have access to these tools:
- **search-flights___searchFlights**: Search for available flights
  - Parameters: origin, destination, departure_date, adults, max_results, **carrier** (airline code filter)
  - **IMPORTANT**: Always use the carrier parameter when rebooking cancelled flights to filter by the specific airline
- **offer-price___priceFlightOffer**: Get final pricing for a selected flight offer (use when user selects a specific flight)
- **current_time**: Get current date and time for reference
- **random-flight-suggestion___random_flight_suggestion**: Generate a sample transatlantic flight search (random North America origin, random Europe destination, one of major airlines AA/BA/DL/LA/AF, and a date within the next 14 days). Use this at session start if the user hasn't provided search criteria to inspire them.

**Flow Example (Normal Booking)**:
1. User: "Find flights from JFK to LAX on 2025-11-01"
2. Agent: Calls search-flights___searchFlights → Shows options
3. User: "I want to book option 2"
4. Agent: Calls offer-price___priceFlightOffer with the selected flight offer → Shows final pricing and booking details

**Flow Example (Cancelled Flight Rebooking)**:
1. User: "My AA flight from JFK to LHR on 2025-10-25 was cancelled. Find alternatives for 2025-10-27"
2. Agent: Calls search-flights___searchFlights(origin="JFK", destination="LHR", departure_date="2025-10-27", carrier="AA") → Shows AA flights only
3. User: "I want option 1"
4. Agent: Calls offer-price___priceFlightOffer → Shows final pricing for rebooking

Use these tools to provide accurate, real-time flight information and seamless booking assistance.
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
        if not GATEWAY_URL:
            raise ValueError("GATEWAY_URL environment variable is not set!")
        
        logger.info(f"Connecting to gateway: {GATEWAY_URL}")
        logger.info(f"Bearer token present: {bool(bearer_token)}")
        logger.info(f"Bearer token length: {len(bearer_token) if bearer_token else 0}")
        
        try:
            self.gateway_client = MCPClient(
                lambda: streamablehttp_client(
                    GATEWAY_URL,
                    headers={"Authorization": f"Bearer {bearer_token}"}
                )
            )
            logger.info("MCPClient created, starting connection...")
            self.gateway_client.start()
            logger.info("Gateway client started successfully")
        except Exception as e:
            logger.error(f"Failed to initialize gateway client: {str(e)}", exc_info=True)
            logger.error(f"GATEWAY_URL was: {GATEWAY_URL}")
            raise RuntimeError(f"Error initializing AutoRescue agent: {str(e)}")
        
        # Collect all tools
        self.tools = [
            current_time,  # Built-in time tool
            random_flight_suggestion,  # Random flight suggestion tool
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
            
            # Check if this looks like a flight selection or booking query
            selection_keywords = [
                "book", "select", "choose", "i want", "i'll take", 
                "option", "flight", "cheapest", "morning", "afternoon", 
                "evening", "direct", "shortest", "fastest"
            ]
            
            booking_keywords = [
                "confirm booking", "finalize", "complete booking", "book it",
                "proceed with booking", "make reservation", "reserve"
            ]
            
            query_lower = user_query.lower()
            is_selection_query = any(keyword in query_lower for keyword in selection_keywords)
            is_booking_query = any(keyword in query_lower for keyword in booking_keywords)
            
            if is_selection_query:
                logger.info("Detected potential flight selection query")
            if is_booking_query:
                logger.info("Detected potential booking completion query")
            
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
        
        logger.info(f"Bearer token from payload: {bool(payload.get('bearer_token'))}")
        logger.info(f"Bearer token from env: {bool(ACCESS_TOKEN)}")
        
        if not bearer_token:
            logger.info("No bearer token provided, fetching from Cognito...")
            try:
                bearer_token = fetch_oauth_token()
                logger.info("Successfully fetched OAuth token from Cognito")
            except Exception as e:
                error_msg = f"Failed to obtain OAuth2 token: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return {"error": error_msg}
        
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
