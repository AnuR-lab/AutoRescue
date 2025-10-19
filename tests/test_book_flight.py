#!/usr/bin/env python3
"""
Test script for simplified bookFlight Lambda function
Tests local execution with sample priced offer
"""

import sys
import os

# Add lambda function directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda_functions', 'book_flight'))

from lambda_function import lambda_handler
import json

# Sample priced offer from priceFlightOffer tool
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
                        "number": "123",
                        "aircraft": {"code": "32B"},
                        "duration": "PT6H30M"
                    }
                ]
            }
        ],
        "price": {
            "currency": "USD",
            "total": "350.00",
            "base": "300.00",
            "fees": [{"amount": "0.00", "type": "SUPPLIER"}],
            "grandTotal": "350.00"
        },
        "pricingOptions": {
            "fareType": ["PUBLISHED"],
            "includedCheckedBagsOnly": True
        },
        "validatingAirlineCodes": ["AA"],
        "travelerPricings": [
            {
                "travelerId": "1",
                "fareOption": "STANDARD",
                "travelerType": "ADULT",
                "price": {
                    "currency": "USD",
                    "total": "350.00",
                    "base": "300.00"
                },
                "fareDetailsBySegment": [
                    {
                        "segmentId": "1",
                        "cabin": "ECONOMY",
                        "fareBasis": "GSAVER",
                        "class": "G",
                        "includedCheckedBags": {"quantity": 0}
                    }
                ]
            }
        ]
    }
}

def main():
    """Test the bookFlight Lambda function"""
    print("=" * 70)
    print("Testing Simplified bookFlight Lambda Function")
    print("=" * 70)
    
    print("\n📋 Test Event:")
    print(json.dumps(test_event, indent=2))
    
    print("\n🔄 Calling Lambda handler...")
    
    try:
        result = lambda_handler(test_event, None)
        
        print("\n✅ Lambda Response:")
        print(f"Status Code: {result['statusCode']}")
        print(f"Headers: {result['headers']}")
        
        print("\n📦 Response Body:")
        body = json.loads(result['body'])
        print(json.dumps(body, indent=2))
        
        if body.get('success'):
            print("\n" + "=" * 70)
            print("✅ BOOKING SUCCESSFUL!")
            print("=" * 70)
            print(f"Booking Reference: {body['booking_reference']}")
            print(f"Passenger: {body['confirmation']['passengerName']}")
            print(f"Email: {body['confirmation']['confirmationEmail']}")
            print(f"Flight: {body['confirmation']['flightDetails']['flightNumber']}")
            print(f"Route: {body['confirmation']['flightDetails']['origin']} → "
                  f"{body['confirmation']['flightDetails']['destination']}")
            print(f"Price: {body['confirmation']['flightDetails']['price']}")
            print("=" * 70)
        else:
            print("\n❌ BOOKING FAILED!")
            print(f"Error: {body.get('error', 'Unknown error')}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
