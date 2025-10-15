# Lambda Functions with Enhanced Logging - Ready to Deploy

## ✅ What Was Done

### 1. Enhanced Lambda Functions with Comprehensive Logging
Both Lambda functions now have detailed logging for debugging:

#### **SearchFlights Lambda** (`lambda_functions/search_flights/lambda_function.py`)
- ✅ Logs incoming event and request ID
- ✅ Logs parsed body and parameters
- ✅ Logs missing parameters with details
- ✅ Logs API call progress
- ✅ Logs success/error responses
- ✅ Logs full stack trace on exceptions
- ✅ Supports both `departure_date` and `departureDate` parameters

#### **AnalyzeDisruption Lambda** (`lambda_functions/analyze_disruption/lambda_function.py`)
- ✅ Logs incoming event and request ID
- ✅ Logs parsed body and parameters
- ✅ Logs missing parameters with details
- ✅ Logs API call progress
- ✅ Logs success/error responses
- ✅ Logs full stack trace on exceptions
- ✅ Supports multiple parameter aliases (flightNumber/original_flight, date/original_date)

### 2. Created Update Script
**File:** `scripts/update_lambdas.sh`

**Features:**
- ✅ Validates AWS credentials
- ✅ Packages Lambda functions as ZIP files
- ✅ Updates both Lambda functions
- ✅ Shows version numbers
- ✅ Provides helpful commands

---

## 🚀 How to Deploy

### Step 1: Assume AWS Role
```bash
cd /Users/abhinaikumarchitrala/Documents/hackathon/AutoRescue
assume
```

### Step 2: Run Update Script
```bash
./scripts/update_lambdas.sh
```

The script will:
1. Validate AWS credentials
2. Package both Lambda functions
3. Update AutoRescue-SearchFlights
4. Update AutoRescue-AnalyzeDisruption
5. Show version numbers
6. Clean up temporary files

---

## 📊 Expected Output

```
╔════════════════════════════════════════════════════════════╗
║    AutoRescue Lambda Functions Deployment                 ║
╔════════════════════════════════════════════════════════════╗

[0/4] Validating AWS credentials...
✅ AWS Account: 905418267822

[1/4] Packaging SearchFlights Lambda...
✅ Package created: search_flights/lambda_package.zip

[2/4] Packaging AnalyzeDisruption Lambda...
✅ Package created: analyze_disruption/lambda_package.zip

[3/4] Updating AutoRescue-SearchFlights Lambda...
✅ Updated SearchFlights Lambda (Version: X)

[4/4] Updating AutoRescue-AnalyzeDisruption Lambda...
✅ Updated AnalyzeDisruption Lambda (Version: Y)

╔════════════════════════════════════════════════════════════╗
║           🎉 Lambda Functions Updated! 🎉                  ║
╔════════════════════════════════════════════════════════════╗
```

---

## 🔍 Testing with Enhanced Logs

### Test Agent
```bash
cd agent_runtime
source ../venv/bin/activate
agentcore invoke '{"prompt": "Search for flights from Boston to Miami on December 1, 2025"}'
```

### View Lambda Logs (Real-time)
```bash
# SearchFlights logs
aws logs tail /aws/lambda/AutoRescue-SearchFlights --follow --region us-east-1

# AnalyzeDisruption logs
aws logs tail /aws/lambda/AutoRescue-AnalyzeDisruption --follow --region us-east-1
```

### Example Log Output
```
[SEARCH_FLIGHTS] ===== NEW REQUEST =====
[SEARCH_FLIGHTS] Request ID: abc-123-def
[SEARCH_FLIGHTS] Function ARN: arn:aws:lambda:us-east-1:...
[SEARCH_FLIGHTS] Received event: {"body": "..."}
[SEARCH_FLIGHTS] Parsed body: {"origin": "BOS", ...}
[SEARCH_FLIGHTS] Parameters - Origin: BOS, Destination: MIA, Date: 2025-12-01, Adults: 1
[SEARCH_FLIGHTS] Calling search_flights()...
[SEARCH_FLIGHTS][CREDENTIALS] Checking for cached credentials...
[SEARCH_FLIGHTS][CREDENTIALS] Using cached credentials (age: 150s)
[SEARCH_FLIGHTS][TOKEN] Getting Amadeus access token...
[SEARCH_FLIGHTS] Search completed. Success: True, Flight count: 5
[SEARCH_FLIGHTS] Returning success response
```

---

## 📋 Key Improvements

### Parameter Flexibility
Both functions now support multiple parameter names:
- `departure_date` OR `departureDate`
- `original_flight` OR `flightNumber`
- `original_date` OR `date`

This ensures compatibility with different calling patterns from the agent.

### Error Tracking
- Full request/response logging
- Stack traces on exceptions
- Parameter validation with detailed error messages
- API call progress tracking

### Performance Monitoring
- Request IDs for correlation
- Timestamp tracking
- Cache hit/miss logging
- API response time visibility

---

## 🎯 What This Solves

Previously, Lambda logs showed:
```
START RequestId: abc-123
END RequestId: abc-123
REPORT RequestId: abc-123  Duration: 1.53 ms  Billed Duration: 2 ms
```

Now you'll see:
```
[SEARCH_FLIGHTS] ===== NEW REQUEST =====
[SEARCH_FLIGHTS] Request ID: abc-123
[SEARCH_FLIGHTS] Received event: {"body": "{\"origin\":\"BOS\"..."}
[SEARCH_FLIGHTS] Parsed body: {"origin": "BOS", "destination": "MIA", ...}
[SEARCH_FLIGHTS] Parameters - Origin: BOS, Destination: MIA, Date: 2025-12-01, Adults: 1
[SEARCH_FLIGHTS] Calling search_flights()...
[SEARCH_FLIGHTS] Search completed. Success: True, Flight count: 5
[SEARCH_FLIGHTS] Returning success response
```

This makes it **much easier to debug** what's happening!

---

## 🔗 File Locations

- **Lambda Functions:**
  - `lambda_functions/search_flights/lambda_function.py`
  - `lambda_functions/analyze_disruption/lambda_function.py`

- **Deployment Script:**
  - `scripts/update_lambdas.sh`

- **CloudFormation Templates:**
  - `cloudformation-lambdas-only.yaml` (inline code version - backup)
  - Future: Will create version with file references

---

## ⏭️ Next Steps

### Immediate
1. **Run `assume` to get AWS credentials**
2. **Run `./scripts/update_lambdas.sh` to deploy updated Lambdas**
3. **Test agent** with a flight search query
4. **Check logs** to see detailed debugging information

### Optional
- Create CloudFormation template that references Lambda ZIP files instead of inline code
- Add CloudWatch metric filters for errors
- Set up CloudWatch alarms for Lambda failures
- Add distributed tracing with AWS X-Ray

---

## 💾 Git Status

**Committed:**
- ✅ Enhanced Lambda functions with logging
- ✅ Update deployment script
- ✅ Pushed to GitHub (commit: 55ada28)

**Files Changed:**
- `lambda_functions/search_flights/lambda_function.py`
- `lambda_functions/analyze_disruption/lambda_function.py`
- `scripts/update_lambdas.sh`

---

## 🎉 Ready to Deploy!

Just run:
```bash
assume                          # Get AWS credentials
./scripts/update_lambdas.sh    # Deploy updated Lambdas
```

Then test with the agent and you'll see detailed logs! 🚀
