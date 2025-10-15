"""
AWS Lambda Function: Search Flights
Standalone Lambda that calls Amadeus Flight Offers Search API
Invoked by AgentCore Gateway
"""
import os
import json
import boto3
import requests
from datetime import datetime, timedelta
from typing import Dict, Any


# Amadeus API Configuration
AMADEUS_BASE_URL = "https://test.api.amadeus.com"

# Secrets cache (Lambda container reuse)
_secrets_cache = {
    'amadeus_credentials': None,
    'fetched_at': None
}

# Token cache (Lambda container reuse)
_token_cache = {
    'access_token': None,
    'expiry': None
}


def _get_amadeus_credentials() -> Dict[str, str]:
    """
    Fetch Amadeus credentials from AWS Secrets Manager with caching
    """
    # Return cached credentials if recently fetched (within 1 hour)
    if _secrets_cache['amadeus_credentials'] and _secrets_cache['fetched_at']:
        elapsed = datetime.now() - _secrets_cache['fetched_at']
        if elapsed.total_seconds() < 3600:
            return _secrets_cache['amadeus_credentials']
    
    # Fetch from Secrets Manager
    secret_name = "autorescue/amadeus/credentials"
    region_name = os.getenv('AWS_REGION', 'us-east-1')
    
    client = boto3.client('secretsmanager', region_name=region_name)
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        
        # Cache the credentials
        _secrets_cache['amadeus_credentials'] = secret
        _secrets_cache['fetched_at'] = datetime.now()
        
        return secret
    except Exception as e:
        raise RuntimeError(f"Failed to fetch Amadeus credentials from Secrets Manager: {str(e)}")


def _get_amadeus_token() -> str:
    """
    Get Amadeus OAuth2 token with caching
    """
    now = datetime.now()
    
    # Return cached token if still valid
    if _token_cache['access_token'] and _token_cache['expiry'] and now < _token_cache['expiry']:
        return _token_cache['access_token']
    
    # Get credentials from Secrets Manager
    credentials = _get_amadeus_credentials()
    
    # Request new token
    url = f"{AMADEUS_BASE_URL}/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": credentials['client_id'],
        "client_secret": credentials['client_secret']
    }
    
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    
    token_data = response.json()
    _token_cache['access_token'] = token_data['access_token']
    # Amadeus tokens expire in 1799 seconds, cache for 25 minutes to be safe
    _token_cache['expiry'] = now + timedelta(seconds=1500)
    
    return _token_cache['access_token']


def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    adults: int = 1,
    max_results: int = 5
) -> Dict[str, Any]:
    """
    Search for flight offers using Amadeus API
    
    Args:
        origin: IATA code of origin airport (e.g., 'JFK')
        destination: IATA code of destination airport (e.g., 'LAX')
        departure_date: Departure date in YYYY-MM-DD format
        adults: Number of adult passengers (default: 1)
        max_results: Maximum number of results to return (default: 5)
    
    Returns:
        Dictionary containing flight offers and metadata
    """
    try:
        # Get access token
        access_token = _get_amadeus_token()
        
        # Prepare API request
        url = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        params = {
            "originLocationCode": origin.upper(),
            "destinationLocationCode": destination.upper(),
            "departureDate": departure_date,
            "adults": str(adults),
            "max": str(max_results),
            "currencyCode": "USD"
        }
        
        # Make API call
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Format response
        if 'data' not in data or len(data['data']) == 0:
            return {
                "success": False,
                "message": f"No flights found from {origin} to {destination} on {departure_date}",
                "flight_count": 0,
                "flights": []
            }
        
        # Extract and format flight offers
        flights = []
        for offer in data['data'][:max_results]:
            flight_info = {
                "id": offer['id'],
                "price": {
                    "total": offer['price']['total'],
                    "currency": offer['price']['currency']
                },
                "itineraries": []
            }
            
            for itinerary in offer['itineraries']:
                segments = []
                for segment in itinerary['segments']:
                    segments.append({
                        "departure": {
                            "iataCode": segment['departure']['iataCode'],
                            "at": segment['departure']['at']
                        },
                        "arrival": {
                            "iataCode": segment['arrival']['iataCode'],
                            "at": segment['arrival']['at']
                        },
                        "carrierCode": segment['carrierCode'],
                        "number": segment['number'],
                        "duration": segment['duration']
                    })
                
                flight_info['itineraries'].append({
                    "duration": itinerary['duration'],
                    "segments": segments
                })
            
            flights.append(flight_info)
        
        return {
            "success": True,
            "message": f"Found {len(flights)} flights from {origin} to {destination}",
            "flight_count": len(flights),
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure_date": departure_date,
            "flights": flights
        }
        
    except requests.exceptions.HTTPError as e:
        return {
            "success": False,
            "error": f"Amadeus API error: {str(e)}",
            "flight_count": 0,
            "flights": []
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "flight_count": 0,
            "flights": []
        }


def lambda_handler(event, context):
    """
    AWS Lambda handler
    Expected event format from AgentCore Gateway:
    {
        "origin": "JFK",
        "destination": "LAX",
        "departure_date": "2025-12-15",
        "adults": 1,
        "max_results": 5
    }
    """
    try:
        # Parse input parameters
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        # Extract parameters
        origin = body.get('origin')
        destination = body.get('destination')
        departure_date = body.get('departure_date')
        adults = body.get('adults', 1)
        max_results = body.get('max_results', 5)
        
        # Validate required parameters
        if not all([origin, destination, departure_date]):
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "success": False,
                    "error": "Missing required parameters: origin, destination, departure_date"
                })
            }
        
        # Call search function
        result = search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            adults=adults,
            max_results=max_results
        )
        
        # Return response
        return {
            "statusCode": 200 if result.get("success") else 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(result)
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "error": f"Lambda error: {str(e)}"
            })
        }
