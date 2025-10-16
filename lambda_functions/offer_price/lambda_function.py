"""
Lambda function for Amadeus Flight Offer Pricing API
Validates and gets the final price for a selected flight offer
"""

import json
import logging
import os
from datetime import datetime, timedelta

import boto3
import requests

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Amadeus API Configuration
AMADEUS_BASE_URL = os.environ.get("AMADEUS_BASE_URL", "https://test.api.amadeus.com")

# AWS Clients
secretsmanager = boto3.client('secretsmanager')

# Cache for credentials and tokens (in-memory, reused across warm Lambda invocations)
_secrets_cache = {}
_token_cache = {"access_token": None, "expires_at": None}


def get_amadeus_credentials():
    """
    Retrieve Amadeus credentials from AWS Secrets Manager with caching
    """
    cache_key = 'amadeus_credentials'
    current_time = datetime.now()
    
    # Check cache (1 hour TTL)
    if cache_key in _secrets_cache:
        cached_data, cached_time = _secrets_cache[cache_key]
        if (current_time - cached_time).seconds < 3600:
            return cached_data
    
    # Fetch from Secrets Manager
    try:
        response = secretsmanager.get_secret_value(
            SecretId='autorescue/amadeus/credentials'
        )
        credentials = json.loads(response['SecretString'])
        
        # Cache the credentials
        _secrets_cache[cache_key] = (credentials, current_time)
        
        return credentials
    except Exception as e:
        logger.error(f"Error fetching credentials from Secrets Manager: {str(e)}")
        raise


def get_amadeus_token():
    """
    Get Amadeus OAuth2 token with caching
    Token is cached and reused until it expires
    """
    global _token_cache

    # Check if we have a valid cached token
    if _token_cache["access_token"] and _token_cache["expires_at"]:
        if datetime.now() < _token_cache["expires_at"]:
            logger.info("Using cached Amadeus access token")
            return _token_cache["access_token"]

    # Get new token
    logger.info("Fetching new Amadeus access token")
    credentials = get_amadeus_credentials()
    
    url = f"{AMADEUS_BASE_URL}/v1/security/oauth2/token"

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    data = {
        "grant_type": "client_credentials",
        "client_id": credentials['client_id'],
        "client_secret": credentials['client_secret'],
    }

    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status()

        token_data = response.json()
        access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 1799)  # Default ~30 minutes

        # Cache the token with expiration (subtract 60 seconds for safety margin)
        _token_cache["access_token"] = access_token
        _token_cache["expires_at"] = datetime.now() + timedelta(seconds=expires_in - 60)

        logger.info(
            f"Successfully obtained Amadeus token, expires in {expires_in} seconds"
        )
        return access_token

    except Exception as e:
        logger.error(f"Error getting Amadeus token: {str(e)}")
        raise


def price_flight_offer(flight_offer_data):
    """
    Price a flight offer using Amadeus Flight Offers Pricing API

    Args:
        flight_offer_data: The complete flight offer object to price (from search results)
                          MUST include all mandatory fields: travelerPricings, segment IDs, 
                          validatingAirlineCodes

    Returns:
        dict: Pricing details with final price, taxes, fees, and booking information
    """
    try:
        # Get access token
        access_token = get_amadeus_token()

        # Amadeus Flight Offers Pricing API endpoint
        url = f"{AMADEUS_BASE_URL}/v1/shopping/flight-offers/pricing"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-HTTP-Method-Override": "GET",
        }

        # Validate mandatory fields
        if not flight_offer_data.get("travelerPricings"):
            raise ValueError("Missing required field: travelerPricings. The complete flight offer object must be provided.")
        
        if not flight_offer_data.get("validatingAirlineCodes"):
            raise ValueError("Missing required field: validatingAirlineCodes. The complete flight offer object must be provided.")
        
        # Check for segment IDs
        for itinerary in flight_offer_data.get("itineraries", []):
            for segment in itinerary.get("segments", []):
                if "id" not in segment:
                    raise ValueError("Missing required field: segment ID. The complete flight offer object with all segment IDs must be provided.")

        # Prepare the pricing request payload
        payload = {
            "data": {
                "type": "flight-offers-pricing",
                "flightOffers": [flight_offer_data],
            }
        }

        logger.info(
            f"Pricing flight offer ID: {flight_offer_data.get('id', 'unknown')}"
        )
        
        # Log the actual request details
        logger.info(f"[AMADEUS API REQUEST]")
        logger.info(f"URL: {url}")
        logger.info(f"Headers: {json.dumps({k: v for k, v in headers.items() if k != 'Authorization'})}")
        logger.info(f"Authorization: Bearer {access_token[:20]}...")  # Only log first 20 chars of token
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")

        # Make the API request
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        # Log response details
        logger.info(f"[AMADEUS API RESPONSE]")
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        
        response.raise_for_status()

        pricing_data = response.json()
        logger.info(f"Response Body: {json.dumps(pricing_data, indent=2)}")

        logger.info("Successfully priced flight offer")
        return pricing_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Amadeus Pricing API: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response Status Code: {e.response.status_code}")
            logger.error(f"Response Headers: {dict(e.response.headers)}")
            logger.error(f"Response Body: {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in price_flight_offer: {str(e)}")
        raise


def format_pricing_response(pricing_data):
    """
    Format the pricing response into a user-friendly structure

    Args:
        pricing_data: Raw response from Amadeus Pricing API

    Returns:
        dict: Formatted pricing information
    """
    try:
        if "data" not in pricing_data or "flightOffers" not in pricing_data["data"]:
            return {
                "error": "Invalid pricing response structure",
                "raw_data": pricing_data,
            }

        flight_offers = pricing_data["data"]["flightOffers"]

        if not flight_offers:
            return {"error": "No flight offers in pricing response"}

        # Get the first (and typically only) priced offer
        priced_offer = flight_offers[0]

        # Extract price information
        price = priced_offer.get("price", {})

        # Extract itinerary information
        itineraries = priced_offer.get("itineraries", [])

        # Extract traveler pricing
        traveler_pricings = priced_offer.get("travelerPricings", [])

        # Format the response
        formatted_response = {
            "offer_id": priced_offer.get("id"),
            "pricing": {
                "currency": price.get("currency", "USD"),
                "total": price.get("total", "0.00"),
                "base": price.get("base", "0.00"),
                "fees": price.get("fees", []),
                "grand_total": price.get("grandTotal", price.get("total", "0.00")),
                "taxes": [tax for tax in price.get("taxes", [])],
            },
            "booking_info": {
                "instant_ticketing_required": priced_offer.get(
                    "instantTicketingRequired", False
                ),
                "last_ticketing_date": priced_offer.get("lastTicketingDate"),
                "last_ticketing_datetime": priced_offer.get("lastTicketingDateTime"),
                "number_of_bookable_seats": priced_offer.get(
                    "numberOfBookableSeats", 0
                ),
                "validating_airline_codes": priced_offer.get(
                    "validatingAirlineCodes", []
                ),
            },
            "itineraries": [
                {
                    "duration": itinerary.get("duration"),
                    "segments": [
                        {
                            "departure": seg.get("departure"),
                            "arrival": seg.get("arrival"),
                            "carrier_code": seg.get("carrierCode"),
                            "flight_number": seg.get("number"),
                            "aircraft": seg.get("aircraft", {}).get("code"),
                            "cabin": (
                                next(
                                    (
                                        fare.get("cabin")
                                        for fare in traveler_pricings[0].get(
                                            "fareDetailsBySegment", []
                                        )
                                        if fare.get("segmentId") == seg.get("id")
                                    ),
                                    "ECONOMY",
                                )
                                if traveler_pricings
                                else "ECONOMY"
                            ),
                        }
                        for seg in itinerary.get("segments", [])
                    ],
                }
                for itinerary in itineraries
            ],
            "travelers": [
                {
                    "traveler_id": tp.get("travelerId"),
                    "traveler_type": tp.get("travelerType", "ADULT"),
                    "fare_option": tp.get("fareOption", "STANDARD"),
                    "price": tp.get("price", {}),
                    "fare_details": tp.get("fareDetailsBySegment", []),
                }
                for tp in traveler_pricings
            ],
            "pricing_options": priced_offer.get("pricingOptions", {}),
            "raw_offer": priced_offer,  # Include full offer for booking if needed
        }

        return formatted_response

    except Exception as e:
        logger.error(f"Error formatting pricing response: {str(e)}")
        return {
            "error": f"Error formatting response: {str(e)}",
            "raw_data": pricing_data,
        }


def lambda_handler(event, context):
    """
    Lambda handler for flight offer pricing

    Expected input:
    {
        "flight_offer": { ... }  # The flight offer object from search results
    }

    Returns:
    {
        "statusCode": 200,
        "body": { ... pricing details ... }
    }
    """
    logger.info(f"[LAMBDA INPUT] Received event: {json.dumps(event, indent=2)}")

    try:
        # Parse input
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", event)

        logger.info(f"[LAMBDA INPUT] Parsed body: {json.dumps(body, indent=2)}")

        # Check if it's a flight offer wrapped in "flight_offer" key or direct flight offer
        if "flight_offer" in body:
            # Legacy format with wrapper
            flight_offer = body.get("flight_offer")
            logger.info("[LAMBDA INPUT] Using legacy format with 'flight_offer' wrapper")
        elif "type" in body or "id" in body:
            # Direct flight offer object
            flight_offer = body
            logger.info("[LAMBDA INPUT] Using direct flight offer format")
        else:
            # Neither format found
            flight_offer = None
            logger.error("[LAMBDA INPUT] No valid flight offer format found")

        logger.info(f"[LAMBDA INPUT] Final flight_offer: {json.dumps(flight_offer, indent=2) if flight_offer else 'None'}")

        if not flight_offer:
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "error": "Missing required parameter: flight_offer",
                        "message": "Please provide a flight offer object to price",
                    }
                ),
            }

        # Ensure the flight offer has the required structure
        if "type" not in flight_offer:
            flight_offer["type"] = "flight-offer"

        # Call Amadeus Pricing API
        logger.info("Calling Amadeus Flight Offers Pricing API")
        pricing_data = price_flight_offer(flight_offer)

        # Format the response
        formatted_response = format_pricing_response(pricing_data)

        # Return success response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(formatted_response, default=str),
        }

    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {"error": str(e), "message": "Failed to price flight offer"}
            ),
        }
