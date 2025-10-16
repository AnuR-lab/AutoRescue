# Lambda Function Test Payloads

This directory contains test JSON payloads for testing Lambda functions directly using AWS CLI.

## Test Files

### 1. Search Flights Lambda

**File:** `test-search-flights.json`
**Lambda:** `AutoRescue-SearchFlights`
**Description:** Search for flights from JFK to LAX on October 20, 2025

```bash
aws lambda invoke \
  --function-name AutoRescue-SearchFlights \
  --region us-east-1 \
  --cli-binary-format raw-in-base64-out \
  --payload file://test-search-flights.json \
  /tmp/search-response.json && cat /tmp/search-response.json | jq .
```

**Parameters:**

- `origin`: "JFK" (John F. Kennedy International Airport)
- `destination`: "LAX" (Los Angeles International Airport)
- `departure_date`: "2025-10-20"
- `adults`: 1
- `max_results`: 5

---

**File:** `test-search-flights-multi.json`
**Lambda:** `AutoRescue-SearchFlights`
**Description:** Search for flights from SFO to ORD on November 15, 2025 for 2 adults

```bash
aws lambda invoke \
  --function-name AutoRescue-SearchFlights \
  --region us-east-1 \
  --cli-binary-format raw-in-base64-out \
  --payload file://test-search-flights-multi.json \
  /tmp/search-response.json && cat /tmp/search-response.json | jq .
```

**Parameters:**

- `origin`: "SFO" (San Francisco International Airport)
- `destination`: "ORD" (Chicago O'Hare International Airport)
- `departure_date`: "2025-11-15"
- `adults`: 2
- `max_results`: 3

---

### 2. Offer Price Lambda

**File:** `test-offer-wrapped.json`
**Lambda:** `AutoRescue-OfferPrice`
**Description:** Get pricing details for a selected flight offer

```bash
aws lambda invoke \
  --function-name AutoRescue-OfferPrice \
  --region us-east-1 \
  --cli-binary-format raw-in-base64-out \
  --payload file://test-offer-wrapped.json \
  /tmp/offer-response.json && cat /tmp/offer-response.json | jq .
```

**Note:** The payload contains a complete flight offer object from the search results.

---

### 3. Analyze Disruption Lambda

**File:** `test-analyze-disruption.json` (to be created)
**Lambda:** `AutoRescue-AnalyzeDisruption`
**Description:** Analyze flight disruption and suggest alternatives

```bash
aws lambda invoke \
  --function-name AutoRescue-AnalyzeDisruption \
  --region us-east-1 \
  --cli-binary-format raw-in-base64-out \
  --payload file://test-analyze-disruption.json \
  /tmp/disruption-response.json && cat /tmp/disruption-response.json | jq .
```

---

## Payload Format

All Lambda functions expect the payload in API Gateway format:

```json
{
  "body": "{\"parameter1\": \"value1\", \"parameter2\": \"value2\"}"
}
```

The `body` field should contain a JSON string (escaped) with the actual parameters.

---

## Common Airport Codes

- **JFK**: John F. Kennedy International Airport (New York)
- **LAX**: Los Angeles International Airport
- **SFO**: San Francisco International Airport
- **ORD**: Chicago O'Hare International Airport
- **ATL**: Hartsfield-Jackson Atlanta International Airport
- **DFW**: Dallas/Fort Worth International Airport
- **DEN**: Denver International Airport
- **LAS**: Las Vegas Harry Reid International Airport
- **SEA**: Seattle-Tacoma International Airport
- **MIA**: Miami International Airport

---

## Testing Workflow

### Step 1: Search for flights

```bash
aws lambda invoke \
  --function-name AutoRescue-SearchFlights \
  --region us-east-1 \
  --cli-binary-format raw-in-base64-out \
  --payload file://test-search-flights.json \
  /tmp/search-response.json

# View results
cat /tmp/search-response.json | jq '.body | fromjson | .flights'
```

### Step 2: Select a flight and get pricing

Copy one of the flight offers from the search results to `test-offer-wrapped.json` and invoke:

```bash
aws lambda invoke \
  --function-name AutoRescue-OfferPrice \
  --region us-east-1 \
  --cli-binary-format raw-in-base64-out \
  --payload file://test-offer-wrapped.json \
  /tmp/offer-response.json
```

### Step 3: Analyze disruption (if needed)

```bash
aws lambda invoke \
  --function-name AutoRescue-AnalyzeDisruption \
  --region us-east-1 \
  --cli-binary-format raw-in-base64-out \
  --payload file://test-analyze-disruption.json \
  /tmp/disruption-response.json
```

---

## Troubleshooting

### Error: "ExpiredToken"

Your AWS credentials have expired. Refresh them:

```bash
aws sso login
# or
aws sts get-caller-identity  # to check current credentials
```

### Error: "Missing required parameters"

Check that your payload has all required fields:

- **search_flights**: origin, destination, departure_date
- **offer_price**: flight_offer
- **analyze_disruption**: flightNumber, date

### Error: "Invalid JSON"

Make sure the `body` field contains properly escaped JSON string.

---

## Notes

- All Lambda functions are deployed in `us-east-1` region
- The Amadeus API credentials are stored in AWS Secrets Manager: `autorescue/amadeus/credentials`
- Lambda functions cache credentials and tokens for performance
- Use `--cli-binary-format raw-in-base64-out` to avoid base64 encoding issues
