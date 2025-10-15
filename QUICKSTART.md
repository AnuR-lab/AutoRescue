# AutoRescue Quick Start Guide

## 🚀 Lambda-Based Architecture

Your AutoRescue project now uses **AWS Lambda functions as separate tool targets**, matching the AWS Bedrock AgentCore Gateway architecture.

## 📁 Project Structure

```
AutoRescue/
├── lambda_functions/              # AWS Lambda functions (NEW)
│   ├── search_flights/           # Search flights tool
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   └── analyze_disruption/       # Analyze disruption tool
│       ├── lambda_function.py
│       └── requirements.txt
│
├── scripts/
│   ├── deploy_lambdas.sh         # Deploy Lambda functions (NEW)
│   ├── agentcore_gateway.py      # Create gateway with Lambda targets (UPDATED)
│   ├── cognito_credentials_provider.py
│   ├── agentcore_memory.py
│   └── prereq.sh
│
├── main.py                       # Agent entry point (UPDATED)
├── README.md                     # Main documentation (UPDATED)
├── LAMBDA_DEPLOYMENT.md          # Lambda deployment guide (NEW)
└── LAMBDA_REFACTORING.md         # Refactoring summary (NEW)
```

## 🔧 Deployment Steps

### 1. Deploy Lambda Functions
```bash
./scripts/deploy_lambdas.sh
```

This creates:
- `AutoRescue-SearchFlights` Lambda function
- `AutoRescue-AnalyzeDisruption` Lambda function
- IAM role: `AutoRescueLambdaExecutionRole`

### 2. Create AgentCore Gateway
```bash
python scripts/agentcore_gateway.py create --name autorescue-gw
```

This:
- Discovers deployed Lambda functions
- Creates OpenAPI spec with Lambda integrations
- Stores configuration in SSM Parameter Store

### 3. Setup Cognito (OAuth 2.0)
```bash
python scripts/cognito_credentials_provider.py create --name autorescue-gateways
```

### 4. Create Memory Store
```bash
python scripts/agentcore_memory.py create --name autorescue
```

### 5. Configure & Launch Agent
```bash
# Get Lambda role ARN
ROLE_ARN=$(aws iam get-role --role-name AutoRescueLambdaExecutionRole --query 'Role.Arn' --output text)

# Configure agent
agentcore configure \
  --entrypoint main.py \
  --execution-role $ROLE_ARN \
  --name autorescue-flight-assistant \
  --model us.anthropic.claude-3-5-sonnet-20241022-v2:0

# Launch agent
agentcore launch
```

## 🧪 Testing

### Test Lambda Functions Directly

```bash
# Test Search Flights
aws lambda invoke \
  --function-name AutoRescue-SearchFlights \
  --payload '{"origin":"JFK","destination":"LAX","departure_date":"2025-12-15","adults":1,"max_results":5}' \
  --region us-east-1 \
  response.json

cat response.json | jq

# Test Analyze Disruption
aws lambda invoke \
  --function-name AutoRescue-AnalyzeDisruption \
  --payload '{"original_flight":"AA123","origin":"JFK","destination":"LAX","original_date":"2025-12-15","disruption_reason":"cancellation"}' \
  --region us-east-1 \
  response.json

cat response.json | jq
```

### Test via AgentCore

```bash
agentcore test --query "Find flights from JFK to LAX on December 15"
agentcore test --query "My flight AA123 from JFK to LAX on Dec 15 was cancelled, help me rebook"
```

## 📊 Monitoring

### View Lambda Logs
```bash
# Search Flights logs
aws logs tail /aws/lambda/AutoRescue-SearchFlights --follow

# Analyze Disruption logs
aws logs tail /aws/lambda/AutoRescue-AnalyzeDisruption --follow
```

### Check Lambda Metrics
```bash
# List Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `AutoRescue`)].[FunctionName,Runtime,LastModified]' --output table

# Get function configuration
aws lambda get-function --function-name AutoRescue-SearchFlights
```

## 🔄 Update Lambda Functions

```bash
# Simply re-run the deployment script
./scripts/deploy_lambdas.sh
```

This will update both Lambda functions with any code changes.

## 🗑️ Cleanup

```bash
# Delete Lambda functions
aws lambda delete-function --function-name AutoRescue-SearchFlights
aws lambda delete-function --function-name AutoRescue-AnalyzeDisruption

# Delete gateway
python scripts/agentcore_gateway.py delete --confirm

# Delete Cognito
python scripts/cognito_credentials_provider.py delete --confirm

# Delete memory
python scripts/agentcore_memory.py delete --confirm

# Delete IAM role
aws iam detach-role-policy --role-name AutoRescueLambdaExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam detach-role-policy --role-name AutoRescueLambdaExecutionRole --policy-arn arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess
aws iam delete-role --role-name AutoRescueLambdaExecutionRole
```

## 🎯 Key Benefits

✅ **Independent Scaling**: Each tool scales separately based on demand
✅ **Security Isolation**: Each Lambda has its own IAM permissions
✅ **Easy Testing**: Test each Lambda function independently
✅ **Cost Effective**: Pay only for what you use (Lambda free tier: 1M requests/month)
✅ **Production Ready**: Follows AWS best practices and architecture patterns

## 📚 Documentation

- **Deployment Guide**: `LAMBDA_DEPLOYMENT.md` - Comprehensive deployment instructions
- **Refactoring Summary**: `LAMBDA_REFACTORING.md` - What changed and why
- **Main README**: `README.md` - Project overview and architecture
- **Project Structure**: `PROJECT_STRUCTURE.md` - File organization
- **Dependencies**: `DEPENDENCIES.md` - Package management

## 🆘 Troubleshooting

### Lambda Not Found
```bash
./scripts/deploy_lambdas.sh
```

### Amadeus API 401 Error
```bash
aws lambda update-function-configuration \
  --function-name AutoRescue-SearchFlights \
  --environment "Variables={AMADEUS_CLIENT_ID=your_id,AMADEUS_CLIENT_SECRET=your_secret}"
```

### Timeout Issues
```bash
aws lambda update-function-configuration \
  --function-name AutoRescue-SearchFlights \
  --timeout 60
```

## 🌐 Architecture

```
┌─────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────┐
│Customer │────>│ AgentCore Runtime│────>│ AgentCore Gateway│────>│  AWS Lambda      │────>│ Amadeus  │
│         │<────│    (Agent)       │<────│   (OAuth 2.0)    │<────│   Functions      │<────│   API    │
└─────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘     └──────────┘
                         │                         │                       │
                         │                         │                       ├─ SearchFlights
                         │                         │                       └─ AnalyzeDisruption
                         │                         │
                         ├─ Claude 3.5 Sonnet      ├─ Amazon Cognito
                         └─ Memory Store           └─ Lambda Integration
```

## 💡 Next Steps

1. **Deploy to AWS**: Follow the deployment steps above
2. **Test Thoroughly**: Use both Lambda direct invocation and AgentCore testing
3. **Monitor Performance**: Check CloudWatch logs and metrics
4. **Optimize**: Adjust Lambda memory/timeout based on actual usage
5. **Enhance**: Add more tools as Lambda functions as needed

## 📞 Support

- AWS Documentation: https://docs.aws.amazon.com/lambda/
- Amadeus API: https://developers.amadeus.com/
- AgentCore: https://docs.aws.amazon.com/bedrock/agentcore/

---

**Status**: ✅ Ready for deployment
**Architecture**: ✅ Matches AWS best practices
**Documentation**: ✅ Complete
