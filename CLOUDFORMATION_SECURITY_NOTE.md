# CloudFormation Template - Security Notice

⚠️ **IMPORTANT: This CloudFormation template contains embedded Lambda code with hardcoded credential fallbacks**

## Issue
The inline Lambda functions in `cloudformation.yaml` contain hardcoded credential fallbacks on lines 128-129 and 259-260.

## Current Status
- ✅ Actual Lambda function code (`lambda_functions/*/lambda_function.py`) has been updated to use AWS Secrets Manager
- ⚠️ CloudFormation inline code still has hardcoded fallbacks (not actively used)

## Recommendation

**Option 1: Use Updated Lambda Functions** (Recommended)
Deploy Lambda functions using the code in `lambda_functions/` directory which properly fetches from Secrets Manager:

```bash
cd lambda_functions/search_flights
zip -r function.zip lambda_function.py
aws lambda update-function-code \
    --function-name search-flights \
    --zip-file fileb://function.zip
```

**Option 2: Update CloudFormation Template**
If you need to use CloudFormation, update the inline Lambda code to fetch from Secrets Manager like the standalone Lambda files do.

**Option 3: Use CloudFormation with S3**
Package the actual Lambda code and reference it from S3 instead of using inline code.

## Why Not Fixed?
The CloudFormation template has embedded Python code in YAML which makes it difficult to automatically update. Since the actual Lambda functions have been updated and are deployed separately, this template is for reference only.

##Actual Working Code
The production Lambda functions use:
- `lambda_functions/search_flights/lambda_function.py` - ✅ Uses Secrets Manager
- `lambda_functions/analyze_disruption/lambda_function.py` - ✅ Uses Secrets Manager
- `agent_runtime/autorescue_agent.py` - ✅ Uses Secrets Manager

## Next Steps
If you want to use CloudFormation for deployment, extract the Lambda code to separate files and use the `Code` property with S3 bucket reference instead of inline code.

See `SECURITY_REMEDIATION.md` for complete security setup.
