# AutoRescue Project Structure - Cleaned Up ✨

## 📁 Current Project Structure

```
AutoRescue/
├── main.py                                  # AgentCore agent entry point (2 MCP tools)
├── amadeus_mcp_tools.py                     # MCP tools for Amadeus API
│   ├── search_flights_tool                  # Tool 1: Search flights
│   └── analyze_flight_disruption_tool       # Tool 2: Analyze disruptions
│
├── app.py                                   # Streamlit UI application
├── src/                                     # Streamlit UI modules
│   ├── __init__.py
│   ├── auth.py                              # Authentication utilities
│   ├── login.py                             # Login page
│   └── home.py                              # Chat interface
│
├── scripts/                                 # Deployment automation scripts
│   ├── prereq.sh                            # Setup prerequisites (SSM, IAM)
│   ├── list_ssm_parameters.sh               # List configuration values
│   ├── agentcore_gateway.py                 # Create/delete gateway
│   ├── cognito_credentials_provider.py      # Setup Cognito authentication
│   ├── agentcore_memory.py                  # Configure agent memory
│   └── cleanup.sh                           # Remove all resources
│
├── pyproject.toml                           # Project dependencies
├── dev-requirements.txt                     # Development dependencies
├── README.md                                # Main documentation
├── DEPLOYMENT.md                            # Step-by-step deployment guide
│
└── FlightOffersSearch_v2_Version_2.8_swagger_specification.json  # Amadeus API spec
```

## 🗑️ Cleaned Up (Removed)

- ❌ `bedrock_agent/` directory (old Strands framework approach)
  - `strands_agent.py`
  - `lambda_handler.py`
  - `deploy.py`
  - `bedrock_agent_cloudformation.yaml`
  - All related files
  
- ❌ Extra MCP tools:
  - `search_multi_day_flights_tool` (removed)
  - `get_cheapest_flights_tool` (removed)

## ✅ What Remains (Essential Only)

### Core Agent Files

**`main.py`** - AgentCore agent with 2 MCP tools
- `search_flights_tool`: Search flights for specific dates
- `analyze_flight_disruption_tool`: Analyze cancellations

**`amadeus_mcp_tools.py`** - MCP tool implementations
- OAuth2 token management
- Amadeus API integration
- JSON response formatting

### Deployment Scripts

All scripts in `scripts/` directory for automated setup:
1. **prereq.sh** - Initial setup (SSM, IAM roles)
2. **agentcore_gateway.py** - Gateway management
3. **cognito_credentials_provider.py** - Authentication setup
4. **agentcore_memory.py** - Memory configuration
5. **cleanup.sh** - Resource cleanup

### UI Components

Streamlit application in `app.py` and `src/` for user interface

### Documentation

- **README.md** - Complete project documentation
- **DEPLOYMENT.md** - Step-by-step deployment guide

## 🎯 Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                    (Streamlit App / API)                    │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   Amazon Cognito                            │
│                (Authentication & Authorization)              │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              AWS Bedrock AgentCore Gateway                   │
│                  (OAuth 2.0 + API Gateway)                   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│          AWS Bedrock AgentCore Runtime (Lambda)              │
│                                                              │
│    ┌────────────────────────────────────────────────┐      │
│    │  AutoRescue Flight Assistant Agent (main.py)   │      │
│    │  Model: Claude 3.5 Sonnet                      │      │
│    └────────────────┬───────────────────────────────┘      │
│                     │                                        │
│         ┌───────────┴───────────┐                           │
│         │                       │                           │
│    ┌────▼─────┐          ┌─────▼──────┐                    │
│    │  Tool 1  │          │   Tool 2   │                    │
│    │  Search  │          │  Analyze   │                    │
│    │ Flights  │          │ Disruption │                    │
│    └────┬─────┘          └─────┬──────┘                    │
│         │                      │                            │
└─────────┼──────────────────────┼────────────────────────────┘
          │                      │
          └──────────┬───────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │     Amadeus Flight API      │
        │   (OAuth2 + REST API)       │
        │                             │
        │  • Flight Search            │
        │  • Real-time Pricing        │
        │  • Availability Data        │
        └─────────────────────────────┘
```

## 🔑 Key Features (Simplified)

### 1. Two Essential MCP Tools

**Tool 1: `search_flights_tool`**
- Search flights for specific dates
- Support for round trips
- Travel class selection
- Non-stop filtering
- Multi-passenger support

**Tool 2: `analyze_flight_disruption_tool`**
- Analyze flight cancellations
- Provide rebooking strategies
- User preference integration
- Recommendation generation

### 2. AgentCore Integration

- **Gateway**: API endpoint with Cognito auth
- **Runtime**: Lambda-based execution
- **Memory**: Conversation context storage
- **Model**: Claude 3.5 Sonnet v2

### 3. Deployment Automation

- One-command prerequisite setup
- Automated infrastructure creation
- SSM parameter management
- Easy cleanup and teardown

## 📝 Next Steps

1. **Run Prerequisites Setup**
   ```bash
   ./scripts/prereq.sh
   ```

2. **Create Gateway**
   ```bash
   python scripts/agentcore_gateway.py create --name autorescue-gw
   ```

3. **Setup Cognito**
   ```bash
   python scripts/cognito_credentials_provider.py create --name autorescue-gateways
   ```

4. **Configure & Launch**
   ```bash
   agentcore configure --entrypoint main.py -er <ROLE_ARN> --name autorescue-flight-assistant
   agentcore launch
   ```

5. **Test**
   ```bash
   agentcore test autorescue-flight-assistant -p "Find flights from JFK to LAX on Nov 15"
   ```

## 🎉 Summary

- ✅ Simplified from 4 tools to 2 essential tools
- ✅ Removed old Strands framework code
- ✅ Clean AgentCore-based architecture
- ✅ Automated deployment scripts
- ✅ Comprehensive documentation
- ✅ Ready for deployment!

---

**Status**: Ready for deployment 🚀
**Last Updated**: October 15, 2025
**Architecture**: AWS Bedrock AgentCore + MCP Tools
