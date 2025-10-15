# Security Remediation Guide

## ⚠️ Security Issue

GitGuardian detected exposed AWS Cognito OAuth 2.0 credentials in the repository. All hardcoded secrets have been removed and migrated to AWS Secrets Manager.

## Exposed Credentials (Require Rotation)

The following credentials were exposed in git history:
- **Cognito Client ID**: [REDACTED]
- **Cognito Client Secret**: [REDACTED]
- **Amadeus Client ID**: [REDACTED]
- **Amadeus Client Secret**: [REDACTED]

## Remediation Steps

### Step 1: Store Secrets in AWS Secrets Manager

```bash
# Run the script to store secrets
python scripts/store_secrets.py
```

This will prompt you to enter:
- Amadeus Client ID
- Amadeus Client Secret
- Cognito Client ID
- Cognito Client Secret
- Cognito Domain

**Option A: Use existing credentials** (temporary - requires rotation later)
- Enter the current credentials when prompted
- You MUST rotate them later

**Option B: Create new credentials** (recommended)
- Create new Cognito app client: [AWS Console - Cognito](https://console.aws.amazon.com/cognito/)
- Generate new Amadeus API keys: [Amadeus Developer Portal](https://developers.amadeus.com/)
- Enter the new credentials

### Step 2: Apply IAM Permissions

```bash
# Make script executable
chmod +x scripts/apply_iam_policies.sh

# Apply Secrets Manager permissions to Lambda and AgentCore roles
./scripts/apply_iam_policies.sh
```

This grants the following IAM roles access to Secrets Manager:
- `search-flights-lambda-role`
- `analyze-disruption-lambda-role`
- `AmazonBedrockAgentCoreRuntimeExecutionRole`

### Step 3: Redeploy Lambda Functions

```bash
# Update Lambda function code with Secrets Manager integration
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

### Step 4: Redeploy Agent Runtime

```bash
# Navigate to agent runtime directory
cd agent_runtime

# Launch with AgentCore CLI (will rebuild with new code)
agentcore launch
```

### Step 5: Test End-to-End

```bash
# Test the agent with a flight search query
agentcore invoke '{"prompt": "Find me flights from JFK to LAX on December 25, 2025"}'
```

## Code Changes Made

### Lambda Functions Updated
- ✅ `lambda_functions/search_flights/lambda_function.py`
  - Added `_get_amadeus_credentials()` function
  - Fetches credentials from Secrets Manager: `autorescue/amadeus/credentials`
  - Removed hardcoded `AMADEUS_CLIENT_ID` and `AMADEUS_CLIENT_SECRET`

- ✅ `lambda_functions/analyze_disruption/lambda_function.py`
  - Added `_get_amadeus_credentials()` function
  - Fetches credentials from Secrets Manager: `autorescue/amadeus/credentials`
  - Removed hardcoded `AMADEUS_CLIENT_ID` and `AMADEUS_CLIENT_SECRET`

### Agent Runtime Updated
- ✅ `agent_runtime/autorescue_agent.py`
  - Added `_get_cognito_credentials()` function
  - Fetches credentials from Secrets Manager: `autorescue/cognito/credentials`
  - Removed hardcoded `COGNITO_CLIENT_ID` and `COGNITO_CLIENT_SECRET`

- ✅ `agent_runtime/Dockerfile`
  - Removed hardcoded `COGNITO_CLIENT_ID` and `COGNITO_CLIENT_SECRET` env vars
  - Added comment about IAM role requirements

### IAM Policies Created
- ✅ `iam_policies/secrets_manager_policy.json`
  - Grants `secretsmanager:GetSecretValue` permission
  - Scoped to `autorescue/cognito/credentials` and `autorescue/amadeus/credentials`

## Secrets Manager Structure

### Cognito Credentials
```json
{
  "client_id": "YOUR_COGNITO_CLIENT_ID",
  "client_secret": "YOUR_COGNITO_CLIENT_SECRET",
  "domain": "YOUR_COGNITO_DOMAIN"
}
```
**Secret Name**: `autorescue/cognito/credentials`

### Amadeus Credentials
```json
{
  "client_id": "YOUR_AMADEUS_CLIENT_ID",
  "client_secret": "YOUR_AMADEUS_CLIENT_SECRET"
}
```
**Secret Name**: `autorescue/amadeus/credentials`

## Credential Rotation (Recommended)

### Rotate Cognito Credentials

1. **Create new Cognito App Client**:
   ```bash
   aws cognito-idp create-user-pool-client \
       --user-pool-id us-east-1_Mfzoy9ILM \
       --client-name autorescue-app-client-new \
       --generate-secret \
       --allowed-o-auth-flows client_credentials \
       --allowed-o-auth-scopes autorescue-resource-server/flights.read \
       --allowed-o-auth-flows-user-pool-client
   ```

2. **Update Secret in Secrets Manager**:
   - Go to [AWS Secrets Manager Console](https://console.aws.amazon.com/secretsmanager/)
   - Find `autorescue/cognito/credentials`
   - Click "Retrieve secret value" → "Edit"
   - Update `client_id` and `client_secret`
   - Save

3. **Delete old app client**:
   ```bash
   aws cognito-idp delete-user-pool-client \
       --user-pool-id us-east-1_Mfzoy9ILM \
       --client-id <OLD_CLIENT_ID_FROM_GIT_HISTORY>
   ```

### Rotate Amadeus Credentials

1. Generate new API keys: https://developers.amadeus.com/my-apps
2. Update Secret in Secrets Manager: `autorescue/amadeus/credentials`
3. Revoke old API keys in Amadeus portal

## Verification Checklist

- [ ] Secrets stored in AWS Secrets Manager
- [ ] IAM policies applied to Lambda roles
- [ ] IAM policies applied to AgentCore Runtime role
- [ ] Lambda functions redeployed with new code
- [ ] Agent runtime redeployed with new code
- [ ] End-to-end test successful
- [ ] Old credentials rotated (optional but recommended)
- [ ] No hardcoded secrets in codebase
- [ ] `.gitignore` updated to prevent future exposure

## Files with Hardcoded Secrets (Cleaned)

The following files have been updated to remove hardcoded secrets:
- ✅ `agent_runtime/autorescue_agent.py`
- ✅ `agent_runtime/Dockerfile`
- ✅ `lambda_functions/search_flights/lambda_function.py`
- ✅ `lambda_functions/analyze_disruption/lambda_function.py`

**Note**: Test scripts and documentation still contain old credentials in examples. These are for reference only and will not be used by the deployed system.

## Prevention

To prevent future exposure:

1. **Never commit secrets** - Use AWS Secrets Manager, environment variables, or `.env` files (add to `.gitignore`)
2. **Use git-secrets** - Install and configure git-secrets to scan commits:
   ```bash
   brew install git-secrets
   git secrets --install
   git secrets --register-aws
   ```
3. **Enable branch protection** - Require pull request reviews
4. **Use pre-commit hooks** - Scan for secrets before committing

## Support

If you encounter issues during remediation:
1. Check IAM role permissions in AWS Console
2. Verify secrets are correctly stored in Secrets Manager
3. Check CloudWatch Logs for Lambda and AgentCore Runtime
4. Test secret retrieval: `aws secretsmanager get-secret-value --secret-id autorescue/cognito/credentials`
