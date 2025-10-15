"""
AWS Lambda Function: Analyze Flight Disruption
Standalone Lambda that analyzes flight disruptions and provides recommendations
Invoked by AgentCore Gateway
"""
import os
import json
import boto3
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List


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


def _search_alternative_flights(
    origin: str,
    destination: str,
    original_date: str,
    days_range: int = 3
) -> List[Dict[str, Any]]:
    """
    Search for alternative flights around the original date
    """
    try:
        access_token = _get_amadeus_token()
        original_dt = datetime.strptime(original_date, "%Y-%m-%d")
        
        all_alternatives = []
        
        # Search for flights on original date and ±days_range
        for day_offset in range(-days_range, days_range + 1):
            search_date = (original_dt + timedelta(days=day_offset)).strftime("%Y-%m-%d")
            
            url = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            params = {
                "originLocationCode": origin.upper(),
                "destinationLocationCode": destination.upper(),
                "departureDate": search_date,
                "adults": "1",
                "max": "3",
                "currencyCode": "USD"
            }
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                
                for offer in data.get('data', [])[:3]:
                    flight_info = {
                        "date": search_date,
                        "date_offset_days": day_offset,
                        "price": {
                            "total": offer['price']['total'],
                            "currency": offer['price']['currency']
                        },
                        "duration": offer['itineraries'][0]['duration'],
                        "segments": []
                    }
                    
                    for segment in offer['itineraries'][0]['segments']:
                        flight_info['segments'].append({
                            "departure": segment['departure']['iataCode'],
                            "arrival": segment['arrival']['iataCode'],
                            "departure_time": segment['departure']['at'],
                            "arrival_time": segment['arrival']['at'],
                            "carrier": segment['carrierCode'],
                            "flight_number": segment['number']
                        })
                    
                    all_alternatives.append(flight_info)
        
        # Sort by date offset (prefer same day, then closest days)
        all_alternatives.sort(key=lambda x: (abs(x['date_offset_days']), float(x['price']['total'])))
        
        return all_alternatives[:10]  # Return top 10 alternatives
        
    except Exception as e:
        print(f"Error searching alternatives: {str(e)}")
        return []


def analyze_disruption(
    original_flight: str,
    origin: str,
    destination: str,
    original_date: str,
    disruption_reason: str = "cancellation"
) -> Dict[str, Any]:
    """
    Analyze flight disruption and provide rebooking recommendations
    
    Args:
        original_flight: Original flight number (e.g., 'AA123')
        origin: IATA code of origin airport (e.g., 'JFK')
        destination: IATA code of destination airport (e.g., 'LAX')
        original_date: Original departure date in YYYY-MM-DD format
        disruption_reason: Reason for disruption (default: 'cancellation')
    
    Returns:
        Dictionary containing disruption analysis and recommendations
    """
    try:
        # Search for alternative flights
        alternatives = _search_alternative_flights(
            origin=origin,
            destination=destination,
            original_date=original_date,
            days_range=3
        )
        
        if not alternatives:
            return {
                "success": False,
                "message": "Unable to find alternative flights",
                "original_flight": original_flight,
                "disruption_reason": disruption_reason,
                "recommendations": []
            }
        
        # Categorize recommendations
        same_day = [f for f in alternatives if f['date_offset_days'] == 0]
        next_day = [f for f in alternatives if f['date_offset_days'] == 1]
        other_days = [f for f in alternatives if abs(f['date_offset_days']) > 1]
        
        # Generate recommendations
        recommendations = []
        
        if same_day:
            recommendations.append({
                "category": "Same Day Alternatives",
                "priority": "HIGH",
                "count": len(same_day),
                "flights": same_day[:3],
                "note": "Book quickly - same-day flights fill up fast"
            })
        
        if next_day:
            recommendations.append({
                "category": "Next Day Options",
                "priority": "MEDIUM",
                "count": len(next_day),
                "flights": next_day[:3],
                "note": "Good availability for next-day travel"
            })
        
        if other_days:
            recommendations.append({
                "category": "Alternative Dates",
                "priority": "LOW",
                "count": len(other_days),
                "flights": other_days[:4],
                "note": "More flexible dates with better pricing"
            })
        
        # Calculate price range
        all_prices = [float(f['price']['total']) for f in alternatives]
        price_range = {
            "min": min(all_prices),
            "max": max(all_prices),
            "currency": "USD"
        }
        
        return {
            "success": True,
            "message": f"Found {len(alternatives)} alternative flights for disrupted flight {original_flight}",
            "original_flight": original_flight,
            "origin": origin.upper(),
            "destination": destination.upper(),
            "original_date": original_date,
            "disruption_reason": disruption_reason,
            "total_alternatives": len(alternatives),
            "price_range": price_range,
            "recommendations": recommendations
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Analysis error: {str(e)}",
            "original_flight": original_flight,
            "disruption_reason": disruption_reason,
            "recommendations": []
        }


def lambda_handler(event, context):
    """
    AWS Lambda handler
    Expected event format from AgentCore Gateway:
    {
        "original_flight": "AA123",
        "origin": "JFK",
        "destination": "LAX",
        "original_date": "2025-12-15",
        "disruption_reason": "cancellation"
    }
    """
    try:
        # Parse input parameters
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        # Extract parameters
        original_flight = body.get('original_flight')
        origin = body.get('origin')
        destination = body.get('destination')
        original_date = body.get('original_date')
        disruption_reason = body.get('disruption_reason', 'cancellation')
        
        # Validate required parameters
        if not all([original_flight, origin, destination, original_date]):
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "success": False,
                    "error": "Missing required parameters: original_flight, origin, destination, original_date"
                })
            }
        
        # Call analysis function
        result = analyze_disruption(
            original_flight=original_flight,
            origin=origin,
            destination=destination,
            original_date=original_date,
            disruption_reason=disruption_reason
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
