#!/bin/bash
#
# Test Lambda Functions
#

set -e

AWS_REGION="${AWS_REGION:-us-east-1}"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Testing AutoRescue Lambda Functions ===${NC}"
echo ""

# Test 1: Search Flights
echo -e "${YELLOW}Test 1: Search Flights (JFK → LAX)${NC}"
echo "Invoking AutoRescue-SearchFlights..."

cat > /tmp/search-payload.json <<EOF
{
  "origin": "JFK",
  "destination": "LAX",
  "departure_date": "2025-12-15",
  "adults": 1,
  "max_results": 3
}
EOF

aws lambda invoke \
  --function-name AutoRescue-SearchFlights \
  --cli-binary-format raw-in-base64-out \
  --payload file:///tmp/search-payload.json \
  --region "$AWS_REGION" \
  /tmp/search-response.json

echo ""
echo "Response:"
cat /tmp/search-response.json | python3 -m json.tool
echo ""

# Test 2: Analyze Disruption
echo -e "${YELLOW}Test 2: Analyze Flight Disruption${NC}"
echo "Invoking AutoRescue-AnalyzeDisruption..."

cat > /tmp/disruption-payload.json <<EOF
{
  "original_flight": "AA123",
  "origin": "JFK",
  "destination": "LAX",
  "original_date": "2025-12-15",
  "disruption_reason": "cancellation"
}
EOF

aws lambda invoke \
  --function-name AutoRescue-AnalyzeDisruption \
  --cli-binary-format raw-in-base64-out \
  --payload file:///tmp/disruption-payload.json \
  --region "$AWS_REGION" \
  /tmp/disruption-response.json

echo ""
echo "Response:"
cat /tmp/disruption-response.json | python3 -m json.tool
echo ""

echo -e "${GREEN}=== Testing Complete ===${NC}"
