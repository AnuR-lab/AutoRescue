# AutoRescue ✈️

> AI-powered Flight Booking and Cancellation Assistant using AWS Bedrock AgentCore

AutoRescue is an intelligent flight management assistant that helps travelers handle flight cancellations, rebookings, and travel disruptions with ease. Built on AWS Bedrock AgentCore with Lambda-backed tools for seamless Amadeus API integration.

## 🌟 Features

- **Real-time Flight Search** - Search flights for specific dates and routes
- **Smart Disruption Analysis** - Automated alternative flight recommendations
- **Real-time Pricing** - Live flight prices from Amadeus API
- **Secure Authentication** - OAuth 2.0 via Amazon Cognito
- **Scalable Architecture** - Independent Lambda functions for each tool

## 🏗️ Architecture

```
Customer → AgentCore Runtime → AgentCore Gateway → AWS Lambda → Amadeus API
              (Claude)             (OAuth 2.0)      (2 Tools)
```

**Components:**
- **AgentCore Gateway** - Routes tool calls with authentication
- **Lambda Functions** - `SearchFlights` + `AnalyzeDisruption`
- **Amazon Cognito** - OAuth 2.0 authentication
- **Amadeus Flight API** - Real-time flight data

## 🚀 Quick Start

See **[DEPLOY.md](DEPLOY.md)** for complete deployment instructions.

```bash
# 1. Deploy Lambda functions
./scripts/deploy_lambdas.sh

# 2. Create AgentCore Gateway
python scripts/create_agentcore_gateway.py

# 3. Add Lambda targets via AWS Console
# See DEPLOY.md Step 5 for details
```

## 📋 Prerequisites

- AWS Account with administrator access
- AWS CLI configured
- Python 3.12+
- Amadeus API credentials (included in Lambda code)

## 📁 Project Structure

```
AutoRescue/
├── README.md                     # This file
├── DEPLOY.md                     # Complete deployment guide
├── DEPENDENCIES.md               # Dependency information
├── main.py                       # Agent entry point
├── requirements.txt              # Python dependencies
│
├── lambda_functions/             # Lambda function source
│   ├── search_flights/
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   └── analyze_disruption/
│       ├── lambda_function.py
│       └── requirements.txt
│
└── scripts/                      # Deployment automation
    ├── create_agentcore_gateway.py
    ├── deploy_lambdas.sh
    └── test_lambdas.sh
```

## 📚 Documentation

- **[DEPLOY.md](DEPLOY.md)** - Complete deployment guide
- **[DEPENDENCIES.md](DEPENDENCIES.md)** - Dependency management

## 🛠️ Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test Lambda functions locally
./scripts/test_lambdas.sh
```

## 🧪 Testing

```bash
# Test Lambda functions
./scripts/test_lambdas.sh

# Test OAuth2 token
# See DEPLOY.md for detailed testing instructions
```

## 🔧 Troubleshooting

See **[DEPLOY.md - Troubleshooting](DEPLOY.md#troubleshooting)** for common issues and solutions.

## 📞 Support

- [AWS Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/agentcore/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Amadeus API Documentation](https://developers.amadeus.com/)

## 📄 License

This project is for demonstration purposes.

---

**For complete deployment instructions, see [DEPLOY.md](DEPLOY.md)**

## 🚀 Deployment

### Step 1: Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r dev-requirements.txt
```

### Step 2: Setup Infrastructure

```bash
# Make scripts executable
chmod +x scripts/prereq.sh
chmod +x scripts/list_ssm_parameters.sh
chmod +x scripts/cleanup.sh

# Run prerequisites setup
./scripts/prereq.sh
```

This will:
- Create SSM parameters for configuration
- Set up IAM roles for AgentCore runtime
- Store Amadeus API credentials securely

### Step 3: Create AgentCore Gateway

```bash
python scripts/agentcore_gateway.py create --name autorescue-gw
```

### Step 4: Setup Cognito Identity Provider

```bash
python scripts/cognito_credentials_provider.py create --name autorescue-gateways
```

This creates:
- Cognito User Pool
- App Client for web authentication
- OAuth discovery URL

**Create a test user:**
```bash
# Get User Pool ID from SSM
USER_POOL_ID=$(aws ssm get-parameter --name /app/autorescue/agentcore/cognito_user_pool_id --query Parameter.Value --output text)

# Create test user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username test@example.com \
  --user-attributes Name=email,Value=test@example.com \
  --temporary-password TempPass123!
```

### Step 5: Create Memory

```bash
python scripts/agentcore_memory.py create --name autorescue
```

### Step 6: Configure Agent Runtime

```bash
# List SSM parameters to get required values
./scripts/list_ssm_parameters.sh

# Configure AgentCore
agentcore configure \
  --entrypoint main.py \
  -er <RUNTIME_IAM_ROLE_ARN> \
  --name autorescue-flight-assistant
```

Fill in the prompts with values from SSM:
- **Role**: Value of `/app/autorescue/agentcore/runtime_iam_role`
- **OAuth Discovery URL**: Value of `/app/autorescue/agentcore/cognito_discovery_url`
- **OAuth Client ID**: Value of `/app/autorescue/agentcore/web_client_id`

### Step 7: Launch Agent

```bash
# Remove existing config (if any)
rm -f .agentcore.yaml

# Launch agent
agentcore launch
```

### Step 8: Run Streamlit UI (Optional)

```bash
# Run on port 8501
streamlit run app.py --server.port 8501 -- --agent=autorescue-flight-assistant
```

## 💬 Sample Queries

Try these queries with the agent:

1. **Flight Cancellation Rebooking**:
   ```
   My flight from JFK to LAX today got cancelled. I need to find alternatives for the next 3 days.
   ```

2. **Multi-Day Search**:
   ```
   Show me flight options from New York (JFK) to Los Angeles (LAX) for the next 3 days in economy class.
   ```

3. **Best Price Discovery**:
   ```
   What are the cheapest flights from Miami (MIA) to San Francisco (SFO) this week?
   ```

4. **Specific Date Search**:
   ```
   Find me business class flights from Chicago (ORD) to Boston (BOS) on November 15, 2025.
   ```

5. **Round Trip**:
   ```
   I need a round trip from Seattle (SEA) to Denver (DEN), departing October 20 and returning October 25.
   ```

## 🛠️ MCP Tools

The agent uses these MCP tools for flight operations:

### 1. `search_multi_day_flights_tool`
Search flights from today up to N days ahead. Essential for handling cancellations.

**Parameters:**
- `origin` (str): IATA airport code (e.g., "JFK")
- `destination` (str): IATA airport code (e.g., "LAX")
- `days_ahead` (int): Number of days to search (default: 3)
- `adults` (int): Number of passengers (default: 1)
- `travel_class` (str): ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST

### 2. `search_flights_tool`
Search flights for a specific date or date range.

**Parameters:**
- `origin`, `destination`: Airport codes
- `departure_date` (str): YYYY-MM-DD format
- `return_date` (str, optional): For round trips
- `non_stop` (bool): Non-stop flights only
- `max_results` (int): Maximum results

### 3. `get_cheapest_flights_tool`
Find the cheapest options across multiple days.

**Parameters:**
- `origin`, `destination`: Airport codes
- `days_ahead` (int): Search period (default: 7)

### 4. `analyze_flight_disruption_tool`
Analyze cancellations and provide rebooking strategies.

**Parameters:**
- `original_flight_info` (JSON): Original flight details
- `user_preferences` (str): Rebooking preferences

## 📁 Project Structure

```
AutoRescue/
├── main.py                          # AgentCore entrypoint
├── amadeus_mcp_tools.py            # MCP tools for Amadeus API
├── app.py                          # Streamlit UI
├── src/
│   ├── home.py                     # Chatbot interface
│   ├── login.py                    # Authentication
│   └── auth.py                     # Auth utilities
├── scripts/
│   ├── prereq.sh                   # Prerequisites setup
│   ├── agentcore_gateway.py        # Gateway management
│   ├── cognito_credentials_provider.py  # Cognito setup
│   ├── agentcore_memory.py         # Memory management
│   ├── list_ssm_parameters.sh      # List config
│   └── cleanup.sh                  # Resource cleanup
├── pyproject.toml                  # Project dependencies
├── dev-requirements.txt            # Development dependencies
└── README.md                       # This file
```

## 🔧 Configuration

All configuration is stored in AWS Systems Manager Parameter Store:

```
/app/autorescue/
├── project/name
├── project/region
├── amadeus/api_base_url
├── amadeus/client_id
├── amadeus/client_secret
├── agentcore/runtime_iam_role
├── agentcore/cognito_user_pool_id
├── agentcore/cognito_domain
├── agentcore/web_client_id
├── agentcore/cognito_discovery_url
├── agentcore/gateway_name
└── agentcore/memory_name
```

## 🧪 Testing

### Test MCP Tools Locally

```python
from amadeus_mcp_tools import search_multi_day_flights_tool

# Test multi-day search
result = search_multi_day_flights_tool(
    origin="JFK",
    destination="LAX",
    days_ahead=3,
    adults=1,
    travel_class="ECONOMY"
)
print(result)
```

### Test Deployed Agent

```bash
# Using agentcore CLI
agentcore test autorescue-flight-assistant -p "Find flights from JFK to LAX for next 3 days"
```

## 🔒 Security

- **API Credentials**: Stored in AWS Systems Manager Parameter Store
- **Authentication**: Cognito-based OAuth 2.0
- **IAM Roles**: Least privilege access for Lambda execution
- **Encryption**: All data encrypted at rest and in transit
- **VPC**: Optional VPC deployment for enhanced security

## 💰 Cost Estimation

- **Claude 3.5 Sonnet**: ~$3/$15 per 1M tokens (input/output)
- **Lambda Invocations**: First 1M free, then $0.20 per 1M
- **Cognito**: 50,000 MAUs free tier
- **SSM Parameters**: Standard parameters are free
- **Amadeus API**: Check your plan limits

## 🧹 Cleanup

To remove all resources:

```bash
./scripts/cleanup.sh
```

This will delete:
- Cognito User Pool
- AgentCore Gateway
- Memory configuration
- SSM parameters
- IAM roles
- Local config files

## 📚 Resources

- [AWS Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [AWS Bedrock AgentCore Samples](https://github.com/awslabs/amazon-bedrock-agentcore-samples)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Amadeus Flight API Documentation](https://developers.amadeus.com/self-service/category/flights)
- [Strands Framework](https://strandsagents.com/latest/documentation/)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/AnuR-lab/AutoRescue/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AnuR-lab/AutoRescue/discussions)
- **Documentation**: Check individual script comments and docstrings

## 🎯 Roadmap

- [ ] Support for multi-city flights
- [ ] Hotel and car rental integration
- [ ] SMS/Email notifications for flight changes
- [ ] Integration with airline loyalty programs
- [ ] Mobile app support
- [ ] Advanced price prediction using ML
- [ ] Support for additional airlines APIs

## 👏 Acknowledgments

- AWS Bedrock Team for AgentCore framework
- Anthropic for Claude 3.5 Sonnet
- Amadeus for flight data API
- AWS Labs for AgentCore samples

---

Built with ❤️ by the AutoRescue Team
