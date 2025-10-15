# 🔐 AWS Credentials Issue - RESOLVED

## ✅ Problem Fixed

**Error:** "I apologize, but I encountered an error: Unable to locate credentials"

**Root Cause:** Streamlit app was started without AWS credentials in the environment.

---

## 🛠️ Solution

The Streamlit app needs AWS credentials to call the Bedrock AgentCore service. You have two options:

### Option 1: Use the Start Script (Recommended)

```bash
# First, assume AWS role
assume SBPOC11AdministratorAccess

# Then start Streamlit with the helper script
./scripts/start_ui.sh
```

### Option 2: Manual Start (One Command)

```bash
# Assume role and start Streamlit in one command
cd /Users/abhinaikumarchitrala/Documents/hackathon/AutoRescue
assume SBPOC11AdministratorAccess && uv run streamlit run app.py
```

---

## 📋 How It Works

### The Flow

1. **Assume AWS Role** → Sets AWS credentials in environment variables
   ```bash
   assume SBPOC11AdministratorAccess
   ```

2. **Environment Variables Set:**
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_SESSION_TOKEN`
   - `AWS_REGION`

3. **Streamlit Inherits Credentials** → boto3 client can access AWS services

4. **Agent Calls Work** → Bedrock AgentCore invocations succeed!

---

## 🔍 Verification

### Check if Credentials are Active

```bash
# This should show your account info
aws sts get-caller-identity
```

**Expected Output:**
```json
{
    "UserId": "AROA...",
    "Account": "905418267822",
    "Arn": "arn:aws:sts::905418267822:assumed-role/..."
}
```

### Check Credential Expiry

The `assume` command shows:
```
[✔] [SBPOC11AdministratorAccess](us-east-1) session credentials will expire in 1 hour
```

**Note:** You need to re-run `assume` after 1 hour and restart Streamlit.

---

## 🎯 Complete Startup Sequence

### Quick Start (Copy-Paste)

```bash
# Step 1: Navigate to project
cd /Users/abhinaikumarchitrala/Documents/hackathon/AutoRescue

# Step 2: Assume AWS role (valid for 1 hour)
assume SBPOC11AdministratorAccess

# Step 3: Start Streamlit with UV
uv run streamlit run app.py
```

### Or Use the Helper Script

```bash
# The script checks for credentials and starts Streamlit
./scripts/start_ui.sh
```

---

## 🚨 Common Issues

### Issue 1: "Unable to locate credentials"

**Cause:** AWS credentials not set or expired

**Fix:**
```bash
# Re-assume the role
assume SBPOC11AdministratorAccess

# Restart Streamlit
pkill -f streamlit
uv run streamlit run app.py
```

### Issue 2: Credentials Expired (after 1 hour)

**Symptoms:**
- Agent responds with credential errors
- AWS API calls fail

**Fix:**
```bash
# Stop Streamlit
pkill -f streamlit

# Re-assume role
assume SBPOC11AdministratorAccess

# Restart Streamlit
uv run streamlit run app.py
```

### Issue 3: Streamlit Started Without Credentials

**Symptoms:**
- Started Streamlit before running `assume`
- Credentials added later don't work

**Fix:**
```bash
# Must restart Streamlit to inherit new environment variables
pkill -f streamlit
assume SBPOC11AdministratorAccess && uv run streamlit run app.py
```

---

## 🎨 Better Solution: Create an Alias

Add this to your `~/.zshrc`:

```bash
# AutoRescue Streamlit Launcher
alias autorescue='cd /Users/abhinaikumarchitrala/Documents/hackathon/AutoRescue && assume SBPOC11AdministratorAccess && uv run streamlit run app.py'
```

Then reload:
```bash
source ~/.zshrc
```

Now you can start the app with just:
```bash
autorescue
```

---

## 📊 What's Happening Behind the Scenes

### When You Run `assume`

```bash
assume SBPOC11AdministratorAccess
```

This sets temporary environment variables:
```bash
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="abc123..."
export AWS_SESSION_TOKEN="IQoJb3JpZ2..."
export AWS_REGION="us-east-1"
```

### When Streamlit Starts

```python
# In src/home.py
client = boto3.client("bedrock-agentcore", region_name=AWS_REGION)
```

boto3 automatically finds credentials from environment variables.

### When You Make a Request

```python
response = config["client"].invoke_agent_runtime(
    agentRuntimeArn=config["arn"],
    runtimeSessionId=config["session_id"],
    payload=payload,
    qualifier="DEFAULT",
)
```

AWS authenticates using the session credentials.

---

## ✅ Current Status

**Streamlit is now running with credentials at:**
- 🌐 **Local:** http://localhost:8501
- 🌐 **Network:** http://192.168.4.177:8501

**AWS Account:** 905418267822  
**Region:** us-east-1  
**Credentials:** Valid for 1 hour

---

## 📝 Best Practices

1. **Always assume role before starting Streamlit**
   ```bash
   assume SBPOC11AdministratorAccess && uv run streamlit run app.py
   ```

2. **Check credentials before long sessions**
   ```bash
   aws sts get-caller-identity
   ```

3. **Set a reminder to refresh after 1 hour**
   - Credentials expire after 1 hour
   - Must stop Streamlit, re-assume, and restart

4. **Use the helper script**
   ```bash
   ./scripts/start_ui.sh
   ```
   - Automatically checks for credentials
   - Shows helpful error messages

---

## 🎉 Success!

Your Streamlit app should now work correctly. Try asking:

- "Search for flights from Chicago ORD to Seattle SEA on December 10, 2025"
- "My flight from JFK to LAX today got cancelled. I need alternatives for the next 3 days."
- "Find me the cheapest flights from NYC to Miami next week"

The agent will now be able to call the Lambda functions and return real flight data!

---

## 📚 Related Documentation

- `LAMBDA_WORKING.md` - Lambda deployment status
- `SECRETS_MANAGER_FIX.md` - Secrets Manager integration
- `UV_SETUP.md` - UV package manager guide
- `scripts/start_ui.sh` - Helper script to start Streamlit

---

**Status:** 🟢 **FULLY OPERATIONAL WITH CREDENTIALS**

**Next Step:** Refresh your browser at http://localhost:8501 and try asking the agent a question!
