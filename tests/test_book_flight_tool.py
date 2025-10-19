#!/usr/bin/env python3
"""
Test script for the book_flight @tool in agent runtime
Tests the native tool that loads passenger info from S3
"""

import sys
import os
import json

# Add agent_runtime and src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent_runtime'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import the book_flight tool
from autorescue_agent import book_flight

# Sample priced offer from priceFlightOffer tool
test_flight_offer = {
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

def main():
    """Test the book_flight tool"""
    print("=" * 70)
    print("Testing book_flight @tool (Agent Runtime)")
    print("=" * 70)
    
    print("\n📋 Test Flight Offer:")
    print(f"Route: {test_flight_offer['itineraries'][0]['segments'][0]['departure']['iataCode']} → "
          f"{test_flight_offer['itineraries'][0]['segments'][0]['arrival']['iataCode']}")
    print(f"Price: {test_flight_offer['price']['currency']} {test_flight_offer['price']['total']}")
    print(f"Carrier: {test_flight_offer['validatingAirlineCodes'][0]}")
    
    print("\n🔄 Calling book_flight tool...")
    print("   (This will attempt to load passenger info from S3)")
    
    try:
        # Call the tool with flight_offer parameter
        result_json = book_flight(flight_offer=test_flight_offer)
        
        print("\n✅ Tool Response (JSON string):")
        print(result_json)
        
        # Parse the JSON response
        result = json.loads(result_json)
        
        if result.get('success'):
            print("\n" + "=" * 70)
            print("✅ BOOKING SUCCESSFUL!")
            print("=" * 70)
            conf = result['confirmation']
            print(f"Booking Reference: {result['booking_reference']}")
            print(f"Passenger: {conf['passengerName']}")
            print(f"Email: {conf['confirmationEmail']}")
            print(f"Status: {conf['status']}")
            print(f"\nFlight Details:")
            print(f"  Route: {conf['flightDetails']['origin']} → {conf['flightDetails']['destination']}")
            print(f"  Flight: {conf['flightDetails']['flightNumber']}")
            print(f"  Date: {conf['flightDetails']['departureDate']}")
            print(f"  Price: {conf['flightDetails']['price']}")
            print(f"\n{conf['message']}")
            print("=" * 70)
        else:
            print("\n❌ BOOKING FAILED!")
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
