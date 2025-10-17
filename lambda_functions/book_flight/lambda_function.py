"""
AWS Lambda function for Flight Create Orders API (Flight Booking)
Handles booking flights using Amadeus Flight Create Orders API after pricing confirmation
"""

import json
import os
import sys
import traceback
from typing import Dict, Any, List
import requests
import boto3

def get_amadeus_credentials() -> Dict[str, str]:
    """
    Retrieve Amadeus API credentials from AWS Secrets Manager
    
    Returns:
        dict: Dictionary containing client_id and client_secret
        
    Raises:
        Exception: If credentials cannot be retrieved
    """
    secret_name = "autorescue/amadeus/credentials"
    region_name = "us-east-1"
    
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(get_secret_value_response['SecretString'])
        return secret
    except Exception as e:
        raise Exception(f"Failed to retrieve Amadeus credentials: {str(e)}")

def get_amadeus_access_token() -> str:
    """
    Get access token from Amadeus API using client credentials
    
    Returns:
        str: Access token for Amadeus API
        
    Raises:
        Exception: If token retrieval fails
    """
    credentials = get_amadeus_credentials()
    
    # Amadeus token endpoint
    token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    
    payload = {
        'grant_type': 'client_credentials',
        'client_id': credentials['client_id'],
        'client_secret': credentials['client_secret']
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        response = requests.post(token_url, data=payload, headers=headers)
        response.raise_for_status()
        
        token_data = response.json()
        return token_data['access_token']
        
    except Exception as e:
        raise Exception(f"Failed to get Amadeus access token: {str(e)}")

def validate_booking_request(booking_data: Dict[str, Any]) -> bool:
    """
    Validate the flight booking request data
    
    Args:
        booking_data: Flight booking request data
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = ['flightOffers', 'travelers']
    
    for field in required_fields:
        if field not in booking_data:
            return False
    
    # Validate flight offers
    if not isinstance(booking_data['flightOffers'], list) or len(booking_data['flightOffers']) == 0:
        return False
    
    # Validate travelers
    if not isinstance(booking_data['travelers'], list) or len(booking_data['travelers']) == 0:
        return False
    
    # Basic traveler validation
    for traveler in booking_data['travelers']:
        if not all(key in traveler for key in ['id', 'name']):
            return False
        if not all(key in traveler['name'] for key in ['firstName', 'lastName']):
            return False
    
    return True

def book_flight(booking_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Book a flight using Amadeus Flight Create Orders API
    
    Args:
        booking_data: Flight booking request data containing flight offers, travelers, etc.
        
    Returns:
        dict: Booking confirmation with flight order details
        
    Raises:
        Exception: If booking fails
    """
    # Get access token
    access_token = get_amadeus_access_token()
    
    # Amadeus Flight Create Orders API endpoint
    booking_url = "https://test.api.amadeus.com/v1/booking/flight-orders"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/vnd.amadeus+json'
    }
    
    # Prepare the booking payload
    booking_payload = {
        "data": {
            "type": "flight-order",
            "flightOffers": booking_data['flightOffers'],
            "travelers": booking_data['travelers']
        }
    }
    
    # Add optional fields if provided
    optional_fields = ['contacts', 'remarks', 'ticketingAgreement', 'formOfPayments']
    for field in optional_fields:
        if field in booking_data:
            booking_payload['data'][field] = booking_data[field]
    
    try:
        print(f"Booking flight with payload: {json.dumps(booking_payload, indent=2)}")
        
        response = requests.post(booking_url, json=booking_payload, headers=headers)
        
        print(f"Amadeus API Response Status: {response.status_code}")
        print(f"Amadeus API Response: {response.text}")
        
        if response.status_code == 201:
            # Successful booking
            booking_result = response.json()
            return {
                "success": True,
                "message": "Flight booked successfully",
                "booking_reference": booking_result['data'].get('id', 'Unknown'),
                "flight_order": booking_result['data'],
                "booking_details": {
                    "confirmation_number": booking_result['data'].get('id'),
                    "travelers": len(booking_data['travelers']),
                    "flight_offers": len(booking_data['flightOffers']),
                    "status": "CONFIRMED"
                }
            }
        else:
            # Booking failed
            error_response = response.json() if response.content else {}
            error_message = "Unknown error"
            
            if 'errors' in error_response:
                errors = error_response['errors']
                if errors and len(errors) > 0:
                    error_message = errors[0].get('detail', errors[0].get('title', 'Unknown error'))
            
            return {
                "success": False,
                "error": f"Booking failed: {error_message}",
                "status_code": response.status_code,
                "error_details": error_response
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Network error during booking: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error during booking: {str(e)}"
        }

def lambda_handler(event, context):
    """
    AWS Lambda handler for flight booking
    
    Args:
        event: Lambda event containing booking request data
        context: Lambda context
        
    Returns:
        dict: HTTP response with booking results
    """
    try:
        print(f"Received event: {json.dumps(event, indent=2)}")
        
        # Extract booking data from event
        if 'body' in event:
            # HTTP request from API Gateway
            if isinstance(event['body'], str):
                booking_data = json.loads(event['body'])
            else:
                booking_data = event['body']
        else:
            # Direct invocation
            booking_data = event
        
        # Validate request
        if not validate_booking_request(booking_data):
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "success": False,
                    "error": "Invalid booking request. Required fields: flightOffers, travelers"
                })
            }
        
        # Book the flight
        result = book_flight(booking_data)
        
        status_code = 201 if result.get('success') else 400
        
        return {
            "statusCode": status_code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result, indent=2, default=str)
        }
        
    except Exception as e:
        print(f"Lambda error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "success": False,
                "error": f"Internal server error: {str(e)}"
            })
        }

# For local testing
if __name__ == "__main__":
    # Test data
    test_event = {
        "flightOffers": [
            {
                "type": "flight-offer",
                "id": "1",
                "source": "GDS",
                "instantTicketingRequired": False,
                "nonHomogeneous": False,
                "oneWay": False,
                "lastTicketingDate": "2025-12-15",
                "numberOfBookableSeats": 4,
                "itineraries": [
                    {
                        "duration": "PT6H30M",
                        "segments": [
                            {
                                "departure": {
                                    "iataCode": "JFK",
                                    "terminal": "4",
                                    "at": "2025-12-15T08:00:00"
                                },
                                "arrival": {
                                    "iataCode": "LAX",
                                    "terminal": "B", 
                                    "at": "2025-12-15T11:30:00"
                                },
                                "carrierCode": "AA",
                                "number": "123"
                            }
                        ]
                    }
                ],
                "price": {
                    "currency": "USD",
                    "total": "350.00",
                    "base": "300.00"
                },
                "validatingAirlineCodes": ["AA"],
                "travelerPricings": [
                    {
                        "travelerId": "1",
                        "fareOption": "STANDARD",
                        "travelerType": "ADULT",
                        "price": {
                            "currency": "USD",
                            "total": "350.00"
                        }
                    }
                ]
            }
        ],
        "travelers": [
            {
                "id": "1",
                "dateOfBirth": "1990-01-01",
                "name": {
                    "firstName": "JOHN",
                    "lastName": "DOE"
                },
                "gender": "MALE",
                "contact": {
                    "emailAddress": "john.doe@test.com",
                    "phones": [
                        {
                            "deviceType": "MOBILE",
                            "countryCallingCode": "1",
                            "number": "1234567890"
                        }
                    ]
                }
            }
        ]
    }
    
    # Test the function
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))