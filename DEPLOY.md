# AutoRescue Deployment Guide

Complete guide to deploy the AutoRescue Flight Assistant using AWS Bedrock AgentCore Gateway with Lambda-backed tools.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture](#architecture)
4. [Deployment Steps](#deployment-steps)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)
7. [Cleanup](#cleanup)

---

## Overview

AutoRescue is an AI-powered flight booking and cancellation assistant built with:
- **AWS Bedrock AgentCore Gateway** - Routes tool calls with OAuth 2.0 authentication
- **AWS Lambda Functions** - Independent, scalable tool implementations
- **Amazon Cognito** - OAuth 2.0 authentication provider
- **Amadeus Flight API** - Real-time flight data
- **Claude 3.5 Sonnet** - Foundation model (when agent runtime is configured)

---

## Prerequisites

### Required

1. **AWS Account** with administrator access
2. **AWS CLI** configured with credentials
   ```bash
   aws configure
   ```
3. **Python 3.12+** installed
4. **Amadeus API Credentials** 
   - Stored in AWS Secrets Manager: `autorescue/amadeus/credentials`
   - See `SECURITY_REMEDIATION.md` for credential setup

### Verify Prerequisites

```bash
# Check AWS CLI
aws --version

# Check Python
python3 --version

# Check AWS credentials
aws sts get-caller-identity
```

---

## Architecture

```
Customer Request
      ↓
AgentCore Runtime (Claude 3.5 Sonnet)
      ↓
AgentCore Gateway (OAuth 2.0 via Cognito)
      ↓
Gateway Targets → AWS Lambda Functions
      ├─ SearchFlights
      └─ AnalyzeDisruption
      ↓
Amadeus Flight API
```

**Key Components:**
- **2 Lambda Functions**: Independent tools for flight operations
- **AgentCore Gateway**: Routes tool invocations with authentication
- **Cognito OAuth 2.0**: Secures gateway access
- **Lambda Targets**: Connect gateway to Lambda functions

---

## Deployment Steps

### Step 1: Setup Python Environment

```bash
# Navigate to project directory
cd /path/to/AutoRescue

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install boto3 requests python-dotenv
```

### Step 2: Deploy Lambda Functions

This creates both Lambda functions with Amadeus API integration.

```bash
# Make script executable
chmod +x scripts/deploy_lambdas.sh

# Deploy
./scripts/deploy_lambdas.sh
```

**What this creates:**
- ✅ IAM Role: `AutoRescueLambdaExecutionRole`
- ✅ Lambda: `AutoRescue-SearchFlights`
- ✅ Lambda: `AutoRescue-AnalyzeDisruption`
- ✅ Environment variables configured with Amadeus credentials

**Expected Output:**
```
=== AutoRescue Lambda Functions Deployment ===
✓ Created IAM role: AutoRescueLambdaExecutionRole
✓ Created function: AutoRescue-SearchFlights
✓ Created function: AutoRescue-AnalyzeDisruption
=== Deployment Complete ===
```

### Step 3: Test Lambda Functions

```bash
# Test both functions
./scripts/test_lambdas.sh
```

**Expected Output:**
- Flight search results from JFK to LAX
- Disruption analysis with alternative flight recommendations

### Step 4: Create AgentCore Gateway with Cognito

This creates the complete AgentCore Gateway setup with OAuth 2.0 authentication.

```bash
# Activate virtual environment
source venv/bin/activate

# Run gateway creation script
python scripts/create_agentcore_gateway.py
```

**What this creates:**
- ✅ IAM Role: `autorescue-agentcore-gateway-role`
- ✅ Cognito User Pool with OAuth 2.0 client credentials flow
- ✅ Cognito Domain for token endpoint
- ✅ Resource Server with scopes:
  - `autorescue-api/flights.read`
  - `autorescue-api/flights.search`
  - `autorescue-api/disruptions.analyze`
- ✅ AgentCore Gateway: `autorescue-gateway`

**Expected Output:**
```
🚀 AutoRescue AgentCore Gateway - Complete Setup
✅ Created IAM role: autorescue-agentcore-gateway-role
✅ User Pool created: us-east-1_XXXXXXXXX
✅ Domain created: autorescue-XXXXXXXXXX.auth.us-east-1.amazoncognito.com
✅ Client created: XXXXXXXXXXXXXXXXXX
✅ Gateway created: autorescue-gateway-XXXXX
✅ Gateway is ready!

🎉 SUCCESS! AutoRescue AgentCore Gateway is ready!
Gateway URL: https://autorescue-gateway-XXXXX.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp
Client ID: XXXXXXXXXXXXXXXXXX
Token URL: https://autorescue-XXXXXXXXXX.auth.us-east-1.amazoncognito.com/oauth2/token
```

**Files Created:**
- `gateway_info.json` - Gateway configuration
- `.cognito_oauth_config` - OAuth configuration
- `.cognito_client_info` - Client ID and secret
- `.cognito_user_pool_id` - User pool ID

### Step 5: Add Lambda Targets to Gateway (AWS Console)

⚠️ **Important**: The Lambda targets need to be added manually via AWS Console.

1. **Open AWS Console**:
   - Go to: https://console.aws.amazon.com/bedrock-agentcore/
   - Region: **us-east-1**
   - Click on **Gateways** in left sidebar

2. **Select Your Gateway**:
   - Click on `autorescue-gateway`

3. **Add Target 1: Search Flights**:
   - Click **"Add Target"**
   - **Name**: `search-flights-target`
   - **Description**: `Search for flight offers`
   - **Target Type**: Select Lambda/Custom
   - **Lambda ARN**: `arn:aws:lambda:us-east-1:YOUR_ACCOUNT:function:AutoRescue-SearchFlights`
   - **OpenAPI Schema**: Upload this schema:

   ```json
   {
     "openapi": "3.0.0",
     "info": {
       "title": "Search Flights API",
       "version": "1.0.0"
     },
     "paths": {
       "/search-flights": {
         "post": {
           "operationId": "searchFlights",
           "summary": "Search for flights",
           "requestBody": {
             "required": true,
             "content": {
               "application/json": {
                 "schema": {
                   "type": "object",
                   "required": ["origin", "destination", "departure_date"],
                   "properties": {
                     "origin": {
                       "type": "string",
                       "description": "IATA airport code (e.g., JFK)"
                     },
                     "destination": {
                       "type": "string",
                       "description": "IATA airport code (e.g., LAX)"
                     },
                     "departure_date": {
                       "type": "string",
                       "description": "Date in YYYY-MM-DD format"
                     },
                     "adults": {
                       "type": "integer",
                       "default": 1
                     },
                     "max_results": {
                       "type": "integer",
                       "default": 5
                     }
                   }
                 }
               }
             }
           },
           "responses": {
             "200": {
               "description": "Flight search results"
             }
           }
         }
       }
     }
   }
   ```

4. **Add Target 2: Analyze Disruption**:
   - Click **"Add Target"**
   - **Name**: `analyze-disruption-target`
   - **Description**: `Analyze flight disruptions`
   - **Target Type**: Select Lambda/Custom
   - **Lambda ARN**: `arn:aws:lambda:us-east-1:YOUR_ACCOUNT:function:AutoRescue-AnalyzeDisruption`
   - **OpenAPI Schema**: Upload this schema:

   ```json
   {
     "openapi": "3.0.0",
     "info": {
       "title": "Analyze Disruption API",
       "version": "1.0.0"
     },
     "paths": {
       "/analyze-disruption": {
         "post": {
           "operationId": "analyzeDisruption",
           "summary": "Analyze flight disruption",
           "requestBody": {
             "required": true,
             "content": {
               "application/json": {
                 "schema": {
                   "type": "object",
                   "required": ["original_flight", "origin", "destination", "original_date"],
                   "properties": {
                     "original_flight": {
                       "type": "string",
                       "description": "Flight number (e.g., AA123)"
                     },
                     "origin": {
                       "type": "string",
                       "description": "IATA airport code"
                     },
                     "destination": {
                       "type": "string",
                       "description": "IATA airport code"
                     },
                     "original_date": {
                       "type": "string",
                       "description": "Date in YYYY-MM-DD format"
                     },
                     "disruption_reason": {
                       "type": "string",
                       "default": "cancellation"
                     }
                   }
                 }
               }
             }
           },
           "responses": {
             "200": {
               "description": "Disruption analysis"
             }
           }
         }
       }
     }
   }
   ```

5. **Wait for Targets to be Ready**:
   - Status should change from "Creating" to "Ready"
   - This usually takes 1-2 minutes per target

---

## Testing

### Test 1: Get OAuth2 Token

```bash
# Read client secret
CLIENT_SECRET=$(cat .cognito_client_info | tail -1)

# Read client ID and token URL from config
CLIENT_ID=$(cat .cognito_oauth_config | python3 -c "import sys, json; print(json.load(sys.stdin)['client_id'])")
TOKEN_URL=$(cat .cognito_oauth_config | python3 -c "import sys, json; print(json.load(sys.stdin)['token_url'])")

# Get access token
curl -X POST "$TOKEN_URL" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "grant_type=client_credentials&client_id=$CLIENT_ID&client_secret=$CLIENT_SECRET&scope=autorescue-api/flights.search"
```

**Expected Output:**
```json
{
  "access_token": "eyJraWQiOiJ...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

### Test 2: Test Gateway Endpoint

```bash
# Get access token
ACCESS_TOKEN=$(curl -s -X POST "$TOKEN_URL" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "grant_type=client_credentials&client_id=$CLIENT_ID&client_secret=$CLIENT_SECRET&scope=autorescue-api/flights.search" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Get gateway URL
GATEWAY_URL=$(cat gateway_info.json | python3 -c "import sys, json; print(json.load(sys.stdin)['gateway']['mcpUrl'])")

# Test search flights
curl -X POST "$GATEWAY_URL/search-flights" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "origin": "JFK",
    "destination": "LAX",
    "departure_date": "2025-12-15",
    "adults": 1,
    "max_results": 3
  }'
```

### Test 3: Direct Lambda Test

```bash
# Test Lambda directly (bypass gateway)
./scripts/test_lambdas.sh
```

---

## Troubleshooting

### Issue: Lambda Functions Not Found

**Error**: `Lambda functions not found`

**Solution**:
```bash
# Check if Lambda functions exist
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `AutoRescue`)].FunctionName'

# Redeploy if missing
./scripts/deploy_lambdas.sh
```

### Issue: Gateway Creation Failed

**Error**: Gateway status is "FAILED"

**Solution**:
1. Check IAM role permissions
2. Verify Cognito user pool exists
3. Check CloudWatch logs for details

### Issue: Target Creation Failed

**Error**: `Credential provider configurations is not defined`

**Solution**: Add targets manually via AWS Console (see Step 5 above)

### Issue: OAuth Token Request Failed

**Error**: `401 Unauthorized` when requesting token

**Solution**:
```bash
# Verify client credentials
cat .cognito_client_info

# Check token URL
cat .cognito_oauth_config | python3 -c "import sys, json; print(json.load(sys.stdin)['token_url'])"

# Ensure you're using the correct scope
# Scope should be one of:
# - autorescue-api/flights.read
# - autorescue-api/flights.search
# - autorescue-api/disruptions.analyze
```

### Issue: Amadeus API Returns 401

**Error**: `401 Unauthorized from Amadeus API`

**Solution**:
```bash
# WARNING: Credentials are now fetched from AWS Secrets Manager at runtime
# Lambda functions no longer need these environment variables
# See SECURITY_REMEDIATION.md for credential management
```

### View Logs

```bash
# Lambda logs
aws logs tail /aws/lambda/AutoRescue-SearchFlights --follow
aws logs tail /aws/lambda/AutoRescue-AnalyzeDisruption --follow

# Check Lambda function configuration
aws lambda get-function --function-name AutoRescue-SearchFlights
```

---

## Cleanup

### Remove All Resources

```bash
# 1. Delete Lambda functions
aws lambda delete-function --function-name AutoRescue-SearchFlights
aws lambda delete-function --function-name AutoRescue-AnalyzeDisruption

# 2. Delete IAM role
aws iam delete-role-policy --role-name AutoRescueLambdaExecutionRole --policy-name InvokeLambdaPolicy
aws iam detach-role-policy --role-name AutoRescueLambdaExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam detach-role-policy --role-name AutoRescueLambdaExecutionRole --policy-arn arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess
aws iam delete-role --role-name AutoRescueLambdaExecutionRole

# 3. Delete Gateway (via console or API)
# Get gateway ID from gateway_info.json
GATEWAY_ID=$(cat gateway_info.json | python3 -c "import sys, json; print(json.load(sys.stdin)['gateway']['id'])")
# Note: Use AWS Console to delete gateway as CLI command may not be available

# 4. Delete Cognito User Pool
USER_POOL_ID=$(cat .cognito_user_pool_id)
aws cognito-idp delete-user-pool --user-pool-id $USER_POOL_ID

# 5. Delete Gateway IAM role
aws iam delete-role-policy --role-name autorescue-agentcore-gateway-role --policy-name InvokeLambdaPolicy
aws iam delete-role --role-name autorescue-agentcore-gateway-role

# 6. Clean up local files
rm -f gateway_info.json .cognito_* gateway.config
```

---

## Project Structure

After deployment, your project will look like:

```
AutoRescue/
├── README.md                          # Project overview
├── DEPLOY.md                          # This file
├── DEPENDENCIES.md                    # Dependency information
├── main.py                            # Agent entry point (for runtime)
├── requirements.txt                   # Python dependencies
├── venv/                              # Virtual environment
│
├── lambda_functions/                  # Lambda function source code
│   ├── search_flights/
│   │   ├── lambda_function.py         # Search flights implementation
│   │   └── requirements.txt           # Lambda dependencies
│   └── analyze_disruption/
│       ├── lambda_function.py         # Disruption analysis implementation
│       └── requirements.txt           # Lambda dependencies
│
├── scripts/                           # Deployment scripts
│   ├── create_agentcore_gateway.py    # Gateway setup script
│   ├── deploy_lambdas.sh              # Lambda deployment
│   └── test_lambdas.sh                # Lambda testing
│
└── gateway_info.json                  # Generated: Gateway configuration
└── .cognito_oauth_config              # Generated: OAuth configuration
└── .cognito_client_info               # Generated: Client credentials
└── .cognito_user_pool_id              # Generated: User pool ID
```

---

## Summary

**Deployment Checklist:**
- [x] Step 1: Setup Python environment
- [x] Step 2: Deploy Lambda functions
- [x] Step 3: Test Lambda functions
- [x] Step 4: Create AgentCore Gateway with Cognito
- [ ] Step 5: Add Lambda targets via AWS Console
- [ ] Step 6: Test OAuth2 authentication
- [ ] Step 7: Test end-to-end flow

**What You've Deployed:**
- ✅ 2 AWS Lambda Functions (tested and working)
- ✅ AgentCore Gateway with OAuth 2.0
- ✅ Cognito User Pool with client credentials flow
- ✅ IAM roles and permissions
- ⏳ Gateway targets (manual setup required)

**Next Steps:**
1. Add Lambda targets via AWS Console (Step 5)
2. Test OAuth2 token retrieval
3. Test gateway endpoints
4. Configure AgentCore Runtime (if needed)
5. Deploy to production

---

## Support

- **AWS Bedrock AgentCore**: https://docs.aws.amazon.com/bedrock/agentcore/
- **AWS Lambda**: https://docs.aws.amazon.com/lambda/
- **Amazon Cognito**: https://docs.aws.amazon.com/cognito/
- **Amadeus API**: https://developers.amadeus.com/

---

**Account**: Check with `aws sts get-caller-identity`  
**Region**: us-east-1  
**Last Updated**: October 15, 2025
