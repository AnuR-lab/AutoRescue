# 🚀 Quick Deployment Guide - Secure AutoRescue

## Current Status
✅ Secrets created in AWS Secrets Manager  
✅ IAM permissions applied  
✅ Code updated to use Secrets Manager  
⏳ Agent redeployment in progress  

## What's Happening Now

The `deploy_simplified.sh` script is waiting for you to confirm the agent name.

**Action Required**: Press Enter in the terminal to accept "autorescue_agent" as the agent name.

## After Deployment Completes

### Test the Agent
```bash
cd agent_runtime
source ../venv/bin/activate

# Simple test
agentcore invoke '{"prompt": "What time is it?"}'

# Flight search test (full end-to-end)
agentcore invoke '{"prompt": "Find flights from JFK to LAX on December 25, 2025"}'
```

### Expected Behavior
The agent should:
1. Fetch Cognito credentials from AWS Secrets Manager
2. Authenticate with Cognito using those credentials
3. Call the gateway with OAuth token
4. Return flight search results

### If You See Errors

**Error: Failed to fetch Cognito credentials**
```bash
# Verify secret exists
aws secretsmanager get-secret-value \
    --secret-id autorescue/cognito/credentials \
    --region us-east-1
```

**Error: Access Denied**
```bash
# Check IAM policy
aws iam get-role-policy \
    --role-name AmazonBedrockAgentCoreSDKRuntime-us-east-1-c76824e496 \
    --policy-name AutoRescueSecretsManagerAccess
```

**Check Logs**
```bash
# View CloudWatch logs
aws logs tail /aws/bedrock-agentcore/runtimes/autorescue_agent-KyZlYU4Lgs-DEFAULT \
    --log-stream-name-prefix "2025/10/15/[runtime-logs]" \
    --follow
```

## Next Steps (After Agent Works)

### 1. Deploy Lambda Functions (Optional)
Since Lambdas were created by script, update them:

```bash
cd lambda_functions/search_flights
zip -r function.zip lambda_function.py
aws lambda update-function-code \
    --function-name search-flights \
    --zip-file fileb://function.zip

cd ../analyze_disruption
zip -r function.zip lambda_function.py
aws lambda update-function-code \
    --function-name analyze-disruption \
    --zip-file fileb://function.zip
```

Then add IAM policy to Lambda roles:
```bash
# Get Lambda role names
aws lambda get-function --function-name search-flights --query 'Configuration.Role'
aws lambda get-function --function-name analyze-disruption --query 'Configuration.Role'

# Apply policy to each role
aws iam put-role-policy \
    --role-name <ROLE_NAME> \
    --policy-name AutoRescueSecretsManagerAccess \
    --policy-document file://iam_policies/secrets_manager_policy.json
```

### 2. Rotate Exposed Credentials (Recommended)

See `SECURITY_REMEDIATION.md` for detailed rotation steps.

### 3. Commit Changes

Once everything is working:
```bash
git add .
git commit -m "Security: Migrate all credentials to AWS Secrets Manager

- Store Cognito and Amadeus credentials in AWS Secrets Manager
- Update Lambda and agent code to fetch credentials at runtime
- Remove all hardcoded secrets from codebase
- Add IAM policies for Secrets Manager access
- Enhance .gitignore to prevent future exposure

Fixes GitGuardian security alert."

git push origin main
```

## Files Changed (Summary)

**Modified**:
- `agent_runtime/autorescue_agent.py` - Fetch Cognito creds from Secrets Manager
- `agent_runtime/Dockerfile` - Remove hardcoded env vars
- `lambda_functions/*/lambda_function.py` - Fetch Amadeus creds from Secrets Manager
- `.gitignore` - Enhanced secret patterns

**New**:
- `scripts/create_secrets.sh` - Create secrets
- `scripts/apply_iam_policies.sh` - Apply IAM permissions
- `scripts/deploy_secure.sh` - Secure deployment
- `iam_policies/secrets_manager_policy.json` - IAM policy
- `SECURITY_REMEDIATION.md` - Full remediation guide
- `SECURITY_REMEDIATION_SUMMARY.md` - This summary
- `.env.example` - Safe template

## Resources

- **Secrets Manager Console**: https://console.aws.amazon.com/secretsmanager/home?region=us-east-1
- **CloudWatch Logs**: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups
- **IAM Console**: https://console.aws.amazon.com/iam/
- **GenAI Dashboard**: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#gen-ai-observability/agent-core

## Support

Questions? Check:
1. `SECURITY_REMEDIATION.md` - Detailed guide
2. `SECURITY_REMEDIATION_SUMMARY.md` - What we did
3. CloudWatch Logs - Runtime errors
4. AWS Secrets Manager - Verify secrets exist

---

**Ready to Continue?**

Press Enter in the terminal to complete the agent deployment! 🚀
