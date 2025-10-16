# AutoRescue Flight Pricing Workflow

**Status**: ✅ Fully Implemented  
**Date**: October 16, 2025  
**Commit**: 691697b

---

## Overview

AutoRescue now supports a complete 6-step flight booking workflow with validated pricing before booking.

## Complete Workflow

```
1. Search for Flights
   ↓
2. Present Flight Options to User
   ↓
3. User Selects Preferred Flight
   ↓
4. Price the Selected Offer (Validates & Gets Final Price)
   ↓
5. Present Final Pricing Details
   ↓
6. Proceed to Booking (if user confirms)
```

---

## Implementation Details

### 1. Lambda Function: `AutoRescue-OfferPrice`

**Location**: `lambda_functions/offer_price/lambda_function.py`  
**Runtime**: Python 3.13  
**Timeout**: 30 seconds  
**Memory**: 256 MB

**Functionality**:
- Validates flight offers with Amadeus Pricing API
- Gets final price with all taxes and fees
- Returns booking requirements and ticketing deadline
- Handles multiple input formats (direct, wrapped, API Gateway)

**API Endpoint**: POST `/v1/shopping/flight-offers/pricing`  
**Required Header**: `X-HTTP-Method-Override: GET`

**Input Format**:
```json
{
  "flight_offer": {
    "type": "flight-offer",
    "id": "...",
    "source": "GDS",
    "itineraries": [...],
    "price": {...},
    "travelerPricings": [...]
  }
}
```

**Output Format**:
```json
{
  "offer_id": "...",
  "pricing": {
    "currency": "USD",
    "total": "350.00",
    "base": "300.00",
    "taxes": [...],
    "grand_total": "350.00"
  },
  "booking_info": {
    "instant_ticketing_required": false,
    "last_ticketing_date": "2025-12-20",
    "number_of_bookable_seats": 9,
    "validating_airline_codes": ["AA"]
  },
  "itineraries": [...],
  "travelers": [...],
  "raw_offer": {...}
}
```

---

### 2. MCP Tool Definition

**Location**: `mcp_tools/offer_price.json`

```json
{
  "name": "priceFlightOffer",
  "description": "Get the final price and booking details for a selected flight offer...",
  "inputSchema": {
    "type": "object",
    "properties": {
      "flight_offer": {
        "type": "object",
        "description": "The complete flight offer object from search results..."
      }
    },
    "required": ["flight_offer"]
  }
}
```

---

### 3. Gateway Target

**Gateway ID**: `autorescue-gateway-7ildpiqiqm`  
**Target Name**: `offer-price-target`  
**Tool Name**: `offer-price___priceFlightOffer`  
**Lambda ARN**: `arn:aws:lambda:us-east-1:905418267822:function:AutoRescue-OfferPrice`  
**Status**: ✅ DEPLOYED

**OpenAPI Spec**: Automatically generated from MCP tool definition

---

### 4. Agent Integration

**Location**: `agent_runtime/autorescue_agent.py`

**System Prompt Updates**:
- Added "Flight Pricing" as core capability
- Documented 6-step booking workflow
- Emphasized passing complete flight offer object
- Highlighted booking requirements presentation
- Added pricing validation before booking confirmation

**Key Instructions for Agent**:
```
When pricing a selected flight:
* CRITICAL: Pass the ENTIRE flight offer object from search results
* Do not modify or summarize the flight offer object
* The pricing validates availability and provides final price
* Present booking requirements (passport, ID, contact info)
* Highlight the ticketing deadline clearly
```

**Available Tools**:
1. `search-flights___searchFlights` - Search for flights
2. `offer-price___priceFlightOffer` - Price selected flight ✨ NEW
3. `analyze-disruption___analyzeDisruption` - Handle disruptions
4. `current_time` - Get current date/time

---

## User Experience Flow

### Example Conversation:

**User**: "I need a flight from JFK to LAX on December 25th"

**Agent**: 
1. Uses `searchFlights` tool
2. Presents 5 flight options with:
   - Flight numbers and carriers
   - Departure/arrival times
   - Duration
   - Initial price estimate
   - Available seats

**User**: "I'll take option 2, the 10am American Airlines flight"

**Agent**:
1. Uses `priceFlightOffer` with complete flight offer object
2. Presents validated final pricing:
   - Base fare: $300.00
   - Taxes: $50.00
   - **Total: $350.00**
3. Shows booking requirements:
   - Passport required
   - Book by: December 20th, 2025
   - 9 seats available
4. Asks for confirmation

**User**: "Yes, book it"

**Agent**: Proceeds to booking with validated offer

---

## Key Benefits

✅ **Price Validation**: Ensures price hasn't changed between search and booking  
✅ **Availability Check**: Confirms seats are still available  
✅ **Transparency**: Shows complete tax and fee breakdown  
✅ **Requirements**: Alerts user to booking prerequisites  
✅ **Deadlines**: Highlights ticketing deadlines clearly  
✅ **Trust**: User confirms final price before committing  

---

## Testing

### Lambda Function Test

```bash
# Note: Requires REAL flight offer from Amadeus search
# Manually crafted offers will fail with "No fare applicable"

aws lambda invoke \
  --function-name AutoRescue-OfferPrice \
  --payload file://real_flight_offer.json \
  response.json
```

### Agent Test

```bash
# Test tool availability
uv run python scripts/test_pricing_tool.py

# Test end-to-end workflow
uv run python scripts/test_agent_local.py
```

---

## Important Notes

1. **Real Offers Only**: The Amadeus Pricing API only works with real, recent flight offers from their search API. Manually crafted offers will be rejected.

2. **Time Sensitivity**: Flight offers have limited validity. Price them promptly after search.

3. **Complete Object**: Always pass the ENTIRE flight offer object to `priceFlightOffer`. Missing fields will cause validation errors.

4. **Network Requirements**: Requires access to:
   - Amadeus API (test.api.amadeus.com)
   - AWS Secrets Manager (for credentials)
   - AgentCore Gateway (for tool invocation)

---

## Files Modified/Created

**Modified**:
- `agent_runtime/autorescue_agent.py` - Updated system prompt with pricing workflow

**Created**:
- `lambda_functions/offer_price/lambda_function.py` - Pricing Lambda function
- `mcp_tools/offer_price.json` - MCP tool definition
- `scripts/test_pricing_tool.py` - Tool availability test
- `PRICING_WORKFLOW.md` - This documentation

**Deployed**:
- Lambda function: `AutoRescue-OfferPrice` (Python 3.13)
- Gateway target: `offer-price-target` (Status: READY)

---

## Next Steps

1. ✅ Search flights workflow - WORKING
2. ✅ Price selected offer workflow - IMPLEMENTED
3. 🔄 Booking API integration - NEXT
4. 🔄 Payment processing - FUTURE
5. 🔄 Confirmation & ticketing - FUTURE

---

**Deployment Date**: October 16, 2025  
**Last Updated**: October 16, 2025  
**Commit**: 691697b
