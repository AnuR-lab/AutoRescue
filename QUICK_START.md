# 🚀 AutoRescue - Quick Start Guide

## ⚡ Start the App (One Command)

```bash
cd /Users/abhinaikumarchitrala/Documents/hackathon/AutoRescue && \
assume SBPOC11AdministratorAccess && \
uv run streamlit run app.py
```

**Or use the helper script:**
```bash
./scripts/start_ui.sh
```

---

## 🌐 Access URLs

- **Local:** http://localhost:8501
- **Network:** http://192.168.4.177:8501

---

## 🔐 Login Credentials

| Username | Password |
|----------|----------|
| `admin` | `admin123` |
| `demo` | `demo123` |

---

## 💬 Example Queries to Try

### Flight Search
```
Search for flights from Chicago ORD to Seattle SEA on December 10, 2025
```

### Disruption Handling
```
My flight from JFK to LAX today got cancelled. I need to find alternatives for the next 3 days.
```

### Price Comparison
```
Find me the cheapest flights from NYC to Miami next week
```

### Multi-City
```
I need flights from Boston to San Francisco with a return on December 20th
```

---

## 🛑 Stop the App

```bash
# Press Ctrl+C in the terminal
# Or force kill:
pkill -f streamlit
```

---

## ⚠️ Troubleshooting

### "Unable to locate credentials" Error

**Fix:**
```bash
# Stop app
pkill -f streamlit

# Re-assume role
assume SBPOC11AdministratorAccess

# Restart
uv run streamlit run app.py
```

### Credentials Expired (after 1 hour)

**Fix:** Same as above - stop, re-assume, restart

### Port Already in Use

**Fix:**
```bash
# Kill existing Streamlit
pkill -f streamlit

# Wait 2 seconds
sleep 2

# Restart
uv run streamlit run app.py
```

---

## 📊 System Architecture

```
User → Streamlit UI → AWS Bedrock AgentCore → Lambda Functions → Amadeus API
                           ↓
                    Secrets Manager
                    (credentials)
```

---

## 🎯 What's Working

✅ Streamlit UI running  
✅ AWS credentials configured  
✅ Secrets Manager integration  
✅ Agent Runtime deployed  
✅ Lambda functions operational  
✅ Amadeus API connected  
✅ CloudWatch logging active  

---

## 📝 Useful Commands

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check Lambda functions
aws lambda list-functions --query 'Functions[?contains(FunctionName, `AutoRescue`)].FunctionName'

# View Lambda logs
aws logs tail /aws/lambda/AutoRescue-SearchFlights --follow

# Test Lambda directly
aws lambda invoke --function-name AutoRescue-SearchFlights \
  --payload '{"origin":"JFK","destination":"LAX","departure_date":"2025-12-15","adults":1}' \
  response.json && cat response.json

# Deploy Lambda updates
./scripts/deploy_sam.sh
```

---

## 📚 Documentation

- `AWS_CREDENTIALS_FIX.md` - Credentials setup guide
- `LAMBDA_WORKING.md` - Lambda deployment status
- `SECRETS_MANAGER_FIX.md` - Secrets Manager integration
- `UV_SETUP.md` - UV package manager guide
- `UV_QUICK_REF.md` - UV quick reference

---

**Status:** 🟢 READY TO USE

**Access Now:** http://localhost:8501
