"""
Amadeus Flight API - MCP Tools Implementation
Model Context Protocol tools for flight operations
"""
import os
import requests
import json
from typing import Annotated, Optional
from datetime import datetime, timedelta
from agentcore import tool
from agentcore.types import ToolInput


# Amadeus API Configuration
AMADEUS_BASE_URL = "https://test.api.amadeus.com"
AMADEUS_CLIENT_ID = os.getenv('AMADEUS_CLIENT_ID', 'EAiOKtslVsY8vTxyT17QoXqdvyl9s67z')
AMADEUS_CLIENT_SECRET = os.getenv('AMADEUS_CLIENT_SECRET', 'leeAu7flsoGFTmYp')

# Token cache
_token_cache = {
    'access_token': None,
    'expiry': None
}


def _get_amadeus_token() -> str:
    """
    Internal function to get Amadeus OAuth2 token
    Implements token caching to minimize auth requests
    """
    now = datetime.now()
    
    # Return cached token if still valid
    if _token_cache['access_token'] and _token_cache['expiry'] and now < _token_cache['expiry']:
        return _token_cache['access_token']
    
    # Request new token
    url = f"{AMADEUS_BASE_URL}/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_CLIENT_ID,
        "client_secret": AMADEUS_CLIENT_SECRET
    }
    
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    
    token_data = response.json()
    _token_cache['access_token'] = token_data['access_token']
    _token_cache['expiry'] = now + timedelta(seconds=token_data.get('expires_in', 1799) - 60)
    
    return _token_cache['access_token']





@tool
def search_flights_tool(
    origin: Annotated[str, ToolInput(description="Three-letter IATA airport code for departure")],
    destination: Annotated[str, ToolInput(description="Three-letter IATA airport code for arrival")],
    departure_date: Annotated[str, ToolInput(description="Departure date in YYYY-MM-DD format")],
    return_date: Annotated[Optional[str], ToolInput(description="Optional return date in YYYY-MM-DD format for round trips")] = None,
    adults: Annotated[int, ToolInput(description="Number of adult passengers")] = 1,
    children: Annotated[int, ToolInput(description="Number of children passengers")] = 0,
    travel_class: Annotated[Optional[str], ToolInput(description="Cabin class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, or FIRST")] = None,
    non_stop: Annotated[bool, ToolInput(description="If true, only show non-stop flights")] = False,
    max_results: Annotated[int, ToolInput(description="Maximum number of results to return")] = 10
) -> str:
    """
    Search for flight offers for a specific date or date range.
    Use this for targeted searches when the user knows their travel dates.
    
    Returns JSON string with available flight offers including prices, schedules, and aircraft details.
    """
    token = _get_amadeus_token()
    
    url = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"
    headers = {"Authorization": f"Bearer {token}"}
    
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "adults": adults,
        "max": max_results,
        "currencyCode": "USD"
    }
    
    if return_date:
        params["returnDate"] = return_date
    if children > 0:
        params["children"] = children
    if travel_class:
        params["travelClass"] = travel_class
    if non_stop:
        params["nonStop"] = "true"
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    data = response.json()
    
    return json.dumps({
        'search_criteria': {
            'origin': origin,
            'destination': destination,
            'departure_date': departure_date,
            'return_date': return_date,
            'passengers': {'adults': adults, 'children': children},
            'travel_class': travel_class or 'Any',
            'non_stop_only': non_stop
        },
        'results': data
    }, indent=2)





@tool
def analyze_flight_disruption_tool(
    original_flight_info: Annotated[str, ToolInput(description="JSON string with original flight details: {origin, destination, date, flight_number}")],
    user_preferences: Annotated[str, ToolInput(description="User preferences for rebooking (e.g., time constraints, cabin class, budget, flexibility)")] = "No specific preferences"
) -> str:
    """
    Analyze a flight cancellation or disruption and provide intelligent rebooking recommendations.
    This tool coordinates the multi-day search to find the best alternatives.
    
    Returns analysis and recommendation summary. Use search_multi_day_flights_tool to get actual flight options.
    """
    try:
        flight_data = json.loads(original_flight_info)
        origin = flight_data.get('origin')
        destination = flight_data.get('destination')
        original_date = flight_data.get('date')
        flight_number = flight_data.get('flight_number', 'Unknown')
        
        analysis = {
            'disruption_details': {
                'original_flight': flight_number,
                'route': f"{origin} → {destination}",
                'original_date': original_date,
                'disruption_type': 'cancellation'
            },
            'user_preferences': user_preferences,
            'recommendations': {
                'next_steps': [
                    f"Search for alternative flights from {origin} to {destination} for the next 3 days",
                    "Compare prices and schedules",
                    "Consider flexibility with departure times",
                    "Check if airlines offer rebooking credits or refunds"
                ],
                'search_strategy': {
                    'primary': 'Use search_multi_day_flights_tool for comprehensive 3-day options',
                    'flexible_dates': 'Best if user can travel on alternate dates',
                    'priority': 'Focus on earliest available flights with reasonable prices'
                }
            },
            'automated_search_query': {
                'tool': 'search_multi_day_flights_tool',
                'parameters': {
                    'origin': origin,
                    'destination': destination,
                    'days_ahead': 3,
                    'adults': 1
                }
            }
        }
        
        return json.dumps(analysis, indent=2)
        
    except Exception as e:
        return json.dumps({
            'error': f"Failed to analyze disruption: {str(e)}",
            'recommendation': "Please provide flight details in JSON format with origin, destination, and date"
        }, indent=2)


# Export tools for use in main.py
__all__ = [
    'search_flights_tool',
    'analyze_flight_disruption_tool'
]
