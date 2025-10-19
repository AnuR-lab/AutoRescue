#!/usr/bin/env python3
"""
Test script for AutoRescue-SearchFlights Lambda function
"""
import json
import boto3
from datetime import datetime, timedelta

def test_search_flights():
    """Test the SearchFlights Lambda function"""
    
    # Initialize Lambda client
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Prepare test payload
    # Search for flights 7 days from now
    departure_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    test_payload = {
        'origin': 'JFK',
        'destination': 'LAX',
        'departure_date': departure_date,
        'adults': 1,
        'max_results': 3
    }
    
    print("🧪 Testing AutoRescue-SearchFlights Lambda")
    print("=" * 60)
    print(f"📋 Test Payload:")
    print(json.dumps(test_payload, indent=2))
    print("=" * 60)
    
    try:
        # Invoke Lambda function
        print("\n🚀 Invoking Lambda function...")
        response = lambda_client.invoke(
            FunctionName='AutoRescue-SearchFlights',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        # Parse response
        status_code = response['StatusCode']
        print(f"\n✅ Lambda invocation status: {status_code}")
        
        # Read response payload
        response_payload = json.loads(response['Payload'].read())
        
        print(f"\n📦 Lambda Response:")
        print("=" * 60)
        print(json.dumps(response_payload, indent=2))
        print("=" * 60)
        
        # Parse the actual response body
        if 'body' in response_payload:
            body = json.loads(response_payload['body'])
            
            if body.get('success'):
                print(f"\n✅ Flight search successful!")
                print(f"📊 Found {body.get('flight_count', 0)} flights")
                print(f"🛫 Route: {body.get('origin')} → {body.get('destination')}")
                print(f"📅 Date: {body.get('departure_date')}")
                
                if body.get('flights'):
                    print(f"\n💰 Flight Options:")
                    for i, flight in enumerate(body['flights'][:3], 1):
                        price = flight['price']
                        duration = flight['itineraries'][0]['duration'] if flight['itineraries'] else 'N/A'
                        print(f"  {i}. ${price['total']} {price['currency']} - Duration: {duration}")
                        
                        # Show segments
                        if flight['itineraries']:
                            for seg_idx, segment in enumerate(flight['itineraries'][0]['segments'], 1):
                                print(f"     Segment {seg_idx}: {segment['departure']['iataCode']} → {segment['arrival']['iataCode']}")
                                print(f"       {segment['carrierCode']}{segment['number']} - {segment['duration']}")
                
                return True
            else:
                print(f"\n❌ Flight search failed!")
                print(f"Error: {body.get('error', 'Unknown error')}")
                return False
        else:
            print(f"\n⚠️  Unexpected response format (no body)")
            return False
            
    except Exception as e:
        print(f"\n❌ Error testing Lambda: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_search_flights()
    exit(0 if success else 1)
