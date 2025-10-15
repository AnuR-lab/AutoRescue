# AutoRescue - Quick Deployment Guide

## 🚀 Quick Start

This guide walks you through deploying the AutoRescue Flight Assistant using AWS Bedrock AgentCore.

### Prerequisites Checklist

- [ ] AWS Account with Bedrock access
- [ ] AWS CLI installed and configured
- [ ] Python 3.12+ installed
- [ ] Amadeus API credentials (Client ID and Secret)
- [ ] Claude 3.5 Sonnet model access enabled in Bedrock

### Step-by-Step Deployment

#### 1. Install Dependencies

```bash
cd /Users/abhinaikumarchitrala/Documents/hackathon/AutoRescue

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r dev-requirements.txt
```

#### 2. Run Prerequisites Setup

```bash
# Make scripts executable
chmod +x scripts/prereq.sh
chmod +x scripts/list_ssm_parameters.sh
chmod +x scripts/cleanup.sh

# Run setup
./scripts/prereq.sh
```

**What this does:**
- Creates SSM parameters
- Sets up IAM role for AgentCore
- Stores Amadeus API credentials
- Displays next steps

#### 3. Create AgentCore Gateway

```bash
python scripts/agentcore_gateway.py create --name autorescue-gw
```

**Output:** Gateway configuration saved to `gateway.config`

#### 4. Setup Cognito Authentication

```bash
python scripts/cognito_credentials_provider.py create --name autorescue-gateways
```

**Output:** Cognito User Pool ID, App Client ID, Discovery URL

**Create a test user:**
```bash
# Get User Pool ID
USER_POOL_ID=$(aws ssm get-parameter --name /app/autorescue/agentcore/cognito_user_pool_id --query Parameter.Value --output text)

# Create user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username test@example.com \
  --user-attributes Name=email,Value=test@example.com \
  --temporary-password TempPass123!
```

#### 5. Create Memory Configuration

```bash
python scripts/agentcore_memory.py create --name autorescue
```

#### 6. List SSM Parameters

```bash
./scripts/list_ssm_parameters.sh
```

**Save these values - you'll need them in the next step!**

#### 7. Configure AgentCore Runtime

```bash
# Get the IAM role ARN
ROLE_ARN=$(aws ssm get-parameter --name /app/autorescue/agentcore/runtime_iam_role --query Parameter.Value --output text)

# Configure the agent
agentcore configure \
  --entrypoint main.py \
  -er $ROLE_ARN \
  --name autorescue-flight-assistant
```

**When prompted, enter:**
- **OAuth Discovery URL**: Get from `/app/autorescue/agentcore/cognito_discovery_url`
- **OAuth Client ID**: Get from `/app/autorescue/agentcore/web_client_id`

#### 8. Launch the Agent

```bash
# Remove any existing config
rm -f .agentcore.yaml

# Launch!
agentcore launch
```

**Success!** Your agent is now deployed on AWS Bedrock AgentCore Runtime.

#### 9. Test the Agent (Optional)

```bash
# Install agentcore CLI testing tools
agentcore test autorescue-flight-assistant -p "Find me flights from JFK to LAX on November 1st, 2025"
```

#### 10. Run Streamlit UI (Optional)

```bash
streamlit run app.py --server.port 8501 -- --agent=autorescue-flight-assistant
```

Access the UI at: `http://localhost:8501`

---

## 🧪 Testing the Agent

### Test Query Examples

1. **Simple Flight Search:**
   ```
   Find me flights from New York (JFK) to Los Angeles (LAX) on November 15, 2025
   ```

2. **Flight with Preferences:**
   ```
   I need a business class flight from Chicago (ORD) to Miami (MIA) on November 20, non-stop only
   ```

3. **Round Trip:**
   ```
   Book a round trip from Seattle (SEA) to Boston (BOS), leaving November 10 and returning November 17
   ```

4. **Flight Disruption:**
   ```
   My flight AA1234 from JFK to LAX on November 5th got cancelled. I need to analyze my options.
   ```

### Testing with Python

```python
import boto3

bedrock_agent = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

# You'll need the agent ID and alias ID from deployment
response = bedrock_agent.invoke_agent(
    agentId='YOUR_AGENT_ID',
    agentAliasId='YOUR_ALIAS_ID',
    sessionId='test-session-1',
    inputText='Find flights from JFK to LAX on November 15'
)
```

---

## 📋 Available MCP Tools

### 1. `search_flights_tool`

Search for flights on specific dates.

**Parameters:**
- `origin`: Airport code (e.g., "JFK")
- `destination`: Airport code (e.g., "LAX")
- `departure_date`: YYYY-MM-DD format
- `return_date`: Optional, for round trips
- `adults`: Number of passengers (default: 1)
- `children`: Number of children (default: 0)
- `travel_class`: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
- `non_stop`: Boolean for non-stop only
- `max_results`: Max results (default: 10)

### 2. `analyze_flight_disruption_tool`

Analyze flight cancellations and get rebooking recommendations.

**Parameters:**
- `original_flight_info`: JSON string with flight details
  ```json
  {
    "origin": "JFK",
    "destination": "LAX",
    "date": "2025-11-15",
    "flight_number": "AA1234"
  }
  ```
- `user_preferences`: Text describing user needs

---

## 🔧 Troubleshooting

### Issue: "No module named 'agentcore'"

**Solution:**
```bash
pip install agentcore boto3 requests
```

### Issue: "Access denied to Bedrock model"

**Solution:**
1. Go to AWS Bedrock Console
2. Click "Model access"
3. Request access to Claude 3.5 Sonnet
4. Wait for approval (usually instant)

### Issue: "Invalid Amadeus credentials"

**Solution:**
1. Verify credentials at [Amadeus Developer Portal](https://developers.amadeus.com/)
2. Update SSM parameters:
```bash
aws ssm put-parameter --name /app/autorescue/amadeus/client_id --value "YOUR_CLIENT_ID" --overwrite
aws ssm put-parameter --name /app/autorescue/amadeus/client_secret --value "YOUR_CLIENT_SECRET" --overwrite
```

### Issue: "Cognito user pool not found"

**Solution:**
Re-run the Cognito setup:
```bash
python scripts/cognito_credentials_provider.py create --name autorescue-gateways
```

---

## 🧹 Cleanup

To remove all resources:

```bash
./scripts/cleanup.sh
```

This will delete:
- Cognito User Pool
- AgentCore Gateway configuration
- Memory settings
- SSM parameters
- IAM roles
- Local config files

---

## 📊 Cost Estimate

**Monthly costs (approximate):**
- Bedrock Claude 3.5 Sonnet: $3-$15 per 1M tokens
- Lambda: ~$0 (within free tier for most usage)
- Cognito: ~$0 (first 50,000 MAUs free)
- SSM Parameters: $0 (standard parameters are free)
- **Amadeus API**: Check your plan limits

**Typical usage:** ~$5-20/month for moderate use

---

## 🆘 Getting Help

- **GitHub Issues**: https://github.com/AnuR-lab/AutoRescue/issues
- **AWS Bedrock Docs**: https://docs.aws.amazon.com/bedrock/
- **Amadeus API Docs**: https://developers.amadeus.com/

---

## ✅ Deployment Checklist

- [ ] Prerequisites installed (AWS CLI, Python 3.12+)
- [ ] AWS account with Bedrock access configured
- [ ] Amadeus API credentials obtained
- [ ] Virtual environment created and activated
- [ ] Dependencies installed
- [ ] Prerequisites setup completed (`./scripts/prereq.sh`)
- [ ] Gateway created
- [ ] Cognito provider configured
- [ ] Test user created in Cognito
- [ ] Memory configured
- [ ] Agent configured with `agentcore configure`
- [ ] Agent launched with `agentcore launch`
- [ ] Agent tested with sample queries
- [ ] (Optional) Streamlit UI running

**All done? You're ready to handle flight disruptions like a pro! ✈️**
