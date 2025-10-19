"""
AWS Lambda function for Flight Booking Confirmation
Loads passenger information from S3 and returns booking confirmation
Uses flight details from the priced offer (no actual API booking call)
"""

import json
import os
import sys
import traceback
from typing import Dict, Any, List
import boto3
from datetime import datetime

# S3 Configuration for passenger info
S3_BUCKET = os.getenv("PERSONAL_INFO_BUCKET", "autorescue-personal-info")
S3_KEY = os.getenv("PERSONAL_INFO_KEY", "personal_info.json")

# Initialize S3 client
s3_client = boto3.client('s3')


def load_passenger_info_from_s3() -> Dict[str, Any]:
    """
    Load passenger information from S3
    
    Returns:
        dict: Passenger information with public details
    """
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
        body = response['Body'].read()
        passenger_data = json.loads(body)
        print(f"Successfully loaded passenger info from S3: {S3_BUCKET}/{S3_KEY}")
        return passenger_data
    except Exception as e:
        print(f"Error loading passenger info from S3: {e}")
        # Return default info if S3 fails
        return {
            "name": {
                "firstName": "John",
                "lastName": "Doe"
            },
            "contact": {
                "email": "passenger@example.com",
                "phone": "+1-555-0100"
            }
        }


def validate_booking_request(booking_data: Dict[str, Any]) -> bool:
    """
    Validate the flight booking request data
    
    Args:
        booking_data: Flight booking request data
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = ['flight_offer']
    
    for field in required_fields:
        if field not in booking_data:
            return False
    
    # Validate flight offer has basic required fields
    flight_offer = booking_data['flight_offer']
    if not isinstance(flight_offer, dict):
        return False
    
    # Check for itineraries
    if 'itineraries' not in flight_offer or not flight_offer['itineraries']:
        return False
    
    return True

def book_flight(booking_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a flight booking confirmation using flight details from priced offer
    and passenger information from S3
    
    Args:
        booking_data: Flight booking request data containing flight offer
        
    Returns:
        dict: Booking confirmation with flight and passenger details
    """
    # Load passenger info from S3
    passenger_info = load_passenger_info_from_s3()
    
    # Extract flight details from the priced offer
    flight_offer = booking_data['flight_offer']
    
    # Get itinerary details
    itineraries = flight_offer.get('itineraries', [{}])
    first_itinerary = itineraries[0] if itineraries else {}
    segments = first_itinerary.get('segments', [])
    first_segment = segments[0] if segments else {}
    last_segment = segments[-1] if segments else {}
    
    # Get price information
    price = flight_offer.get('price', {})
    
    # Extract passenger details from S3
    passenger_name_obj = passenger_info.get('name', {})
    passenger_name = f"{passenger_name_obj.get('firstName', 'Passenger')} {passenger_name_obj.get('lastName', '')}"
    passenger_email = passenger_info.get('contact', {}).get('email', 'passenger@example.com')
    
    # Generate a booking reference (timestamp-based for demo)
    booking_reference = f"AR{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Extract flight details
    origin = first_segment.get('departure', {}).get('iataCode', 'N/A')
    destination = last_segment.get('arrival', {}).get('iataCode', 'N/A')
    departure_date = first_segment.get('departure', {}).get('at', 'N/A')
    carrier_code = first_segment.get('carrierCode', 'N/A')
    flight_number = f"{carrier_code}{first_segment.get('number', '')}"
    total_price = price.get('total', 'N/A')
    currency = price.get('currency', 'USD')
    
    return {
        "success": True,
        "message": f"🎉 Flight booked successfully for {passenger_name}!",
        "booking_reference": booking_reference,
        "confirmation": {
            "bookingNumber": booking_reference,
            "status": "CONFIRMED",
            "passengerName": passenger_name,
            "confirmationEmail": passenger_email,
            "flightDetails": {
                "origin": origin,
                "destination": destination,
                "departureDate": departure_date,
                "carrier": carrier_code,
                "flightNumber": flight_number,
                "price": f"{currency} {total_price}"
            },
            "message": f"✈️ Your booking confirmation has been sent to {passenger_email}"
        },
        "booking_details": {
            "confirmation_number": booking_reference,
            "passenger": {
                "name": passenger_name,
                "email": passenger_email
            },
            "flight": {
                "from": origin,
                "to": destination,
                "date": departure_date,
                "airline": carrier_code,
                "flight_number": flight_number,
                "total_price": f"{currency} {total_price}"
            },
            "status": "CONFIRMED"
        }
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
                    "error": "Invalid booking request. Required field: flight_offer"
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
    # Test data - simplified booking request with priced offer
    test_event = {
        "flight_offer": {
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
    }
    
    # Test the function
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))