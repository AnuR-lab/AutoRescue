"""
Test script for the random_flight_suggestion tool in Agent Runtime
"""
import json
import boto3
import sys
import os
import uuid

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(__file__))

from secrets_manager import get_agent_runtime_arn


def test_random_flight_suggestion():
    """Test the agent runtime's random_flight_suggestion tool"""
    try:
        # Get agent runtime ARN
        arn = get_agent_runtime_arn()
        print(f'Agent Runtime ARN: {arn[:50]}...')
        print('=' * 70)
        
        # Initialize Bedrock AgentCore client
        client = boto3.client('bedrock-agentcore', region_name='us-east-1')
        
        # Create a session ID
        session_id = str(uuid.uuid4()) + 'extra_chars_to_meet_33_char_min'
        
        # Test the random_flight_suggestion tool
        print('\nTesting random_flight_suggestion tool...\n')
        
        payload = json.dumps({'prompt': 'Generate a random flight suggestion'})
        
        response = client.invoke_agent_runtime(
            agentRuntimeArn=arn,
            runtimeSessionId=session_id,
            payload=payload,
            qualifier='DEFAULT'
        )
        
        response_body = response['response'].read()
        response_data = json.loads(response_body)
        
        print('Raw Response:')
        print('-' * 70)
        print(json.dumps(response_data, indent=2))
        print('-' * 70)
        
        if 'response' in response_data:
            raw_text = response_data['response']
            print('\nAgent Response Text:')
            print('-' * 70)
            print(raw_text)
            print('-' * 70)
            
            # Try to parse JSON from response
            print('\nAttempting JSON parsing...')
            start = raw_text.find('{')
            end = raw_text.rfind('}')
            
            if start != -1 and end != -1 and end > start:
                json_str = raw_text[start:end+1]
                print(f'Found JSON block: {json_str}')
                
                try:
                    parsed = json.loads(json_str)
                    print('\n✅ JSON parsing successful!')
                    print(f'Parsed data: {json.dumps(parsed, indent=2)}')
                    
                    # Check required keys
                    required_keys = ['origin', 'destination', 'preferredAirline', 'departureDate']
                    missing = [k for k in required_keys if k not in parsed]
                    
                    if missing:
                        print(f'\n❌ Missing keys: {missing}')
                    else:
                        print(f'\n✅ All required keys present!')
                        print(f'   Origin: {parsed["origin"]}')
                        print(f'   Destination: {parsed["destination"]}')
                        print(f'   Airline: {parsed["preferredAirline"]}')
                        print(f'   Date: {parsed["departureDate"]}')
                        print(f'   Passengers: {parsed.get("passengers", "N/A")}')
                except json.JSONDecodeError as e:
                    print(f'\n❌ JSON parsing failed: {e}')
            else:
                print('❌ No JSON block found in response')
                
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_random_flight_suggestion()
