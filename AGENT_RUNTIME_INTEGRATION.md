# Agent Runtime Integration Guide

## Overview

The AutoRescue Streamlit app now integrates directly with the AWS Bedrock Agent Runtime, combining the user session handoff logic with direct agent runtime calls.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Streamlit UI (home.py)                                     │
│  - User authentication                                       │
│  - Chat interface                                            │
│  - Session management                                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent Runtime Client (call_agent_runtime)                  │
│  - Load configuration from .env or Secrets Manager          │
│  - Maintain session ID for conversation continuity          │
│  - Call invoke_agent_runtime API                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  AWS Bedrock AgentCore Runtime                              │
│  - Process user prompts                                      │
│  - Execute tools (search flights, analyze disruptions)      │
│  - Return structured responses                               │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. **Direct Agent Runtime Calls**

- Uses `boto3` client to invoke the agent runtime
- No intermediate gateway needed
- Direct AWS API integration

### 2. **Session Management**

- Unique session ID per user login
- Maintains conversation context across messages
- Clear chat resets the session

### 3. **Handoff Support**

- Detects when agent needs more information
- Displays interactive forms for user input
- Continues conversation seamlessly
- Supports both soft and hard handoffs

### 4. **Secrets Management**

- Automatically retrieves `AGENT_RUNTIME_ARN` from AWS Secrets Manager
- Falls back to `.env` for local development
- No hardcoded credentials

## Code Structure

### `init_agent_runtime()`

Initializes the agent runtime configuration on first run:

- Loads environment variables
- Retrieves ARN from Secrets Manager if needed
- Creates boto3 client
- Generates unique session ID

### `call_agent_runtime(user_prompt: str) -> dict`

Makes API call to agent runtime:

```python
payload = json.dumps({"prompt": user_prompt})
response = client.invoke_agent_runtime(
    agentRuntimeArn=AGENT_RUNTIME_ARN,
    runtimeSessionId=session_id,
    payload=payload,
    qualifier="DEFAULT"
)
```

### Handoff Logic

Inspired by `chat.py`, implements:

1. **Pending handoff detection**: Checks for keywords or explicit handoff signals
2. **Interactive forms**: Shows text area for user input
3. **Conversation continuation**: Maintains context through session ID
4. **Breakout support**: Can exit handoff loop when needed

## Usage

### 1. Start the App

```bash
uv run streamlit run app.py
```

### 2. Login

- Username: `admin`, `demo`, or `user`
- Password: See authentication credentials

### 3. Chat with Agent

```
User: "Search for flights from JFK to LAX on 2025-10-20"
Agent: [Searches flights and displays results]

User: "My flight was cancelled, help me find alternatives"
Agent: [Analyzes disruption and suggests options]
```

### 4. Handoff Example

```
User: "I need special assistance"
Agent: "I need more information. What type of assistance do you require?"
[Interactive form appears]
User: [Provides details]
Agent: [Continues helping with context]
```

## Configuration

### Environment Variables (.env)

```bash
# Optional - will use Secrets Manager if not set
AGENT_RUNTIME_ARN=arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:runtime/NAME

# Required
AWS_REGION=us-east-1
```

### AWS Secrets Manager

The app automatically retrieves the ARN from:

```
Secret Name: autorescue/agent-runtime-arn
Secret Key: AGENT_RUNTIME_ARN
```

## Session State Management

| State Variable               | Purpose                                             |
| ---------------------------- | --------------------------------------------------- |
| `agent_runtime_config`       | Stores client, ARN, region, session_id              |
| `messages`                   | Chat history (user/assistant messages)              |
| `pending_handoff`            | Active handoff state with message and breakout flag |
| `handoff_triggered_this_run` | Prevents duplicate handoff processing               |
| `username`                   | Current logged-in user                              |
| `authenticated`              | Authentication status                               |

## Key Differences from chat.py

| Aspect             | chat.py (Original)                  | home.py (New)                 |
| ------------------ | ----------------------------------- | ----------------------------- |
| **Agent Backend**  | Strands Agent with MCP              | AWS Bedrock AgentCore Runtime |
| **API Calls**      | Gateway via MCP client              | Direct `invoke_agent_runtime` |
| **Streaming**      | Async streaming with `stream_async` | Synchronous response          |
| **Tools**          | Custom `@tool` decorators           | Built-in agent runtime tools  |
| **Authentication** | Optional MCP gateway auth           | Streamlit + AWS credentials   |
| **Session**        | Strands conversation history        | Runtime session ID            |

## Benefits of This Approach

✅ **Simpler Architecture**: Direct AWS API calls, no gateway layer  
✅ **Better Integration**: Uses existing Streamlit authentication  
✅ **Conversation Context**: Session ID maintains context  
✅ **Secrets Security**: Automatic Secrets Manager integration  
✅ **Error Handling**: Graceful fallbacks and user-friendly errors  
✅ **Scalability**: Leverages AWS infrastructure

## Testing

### 1. Test Agent Response

```
User: "Search for flights from SFO to NYC on 2025-11-01"
Expected: Flight search results with prices and times
```

### 2. Test Handoff

```
User: "I need help but I'm not sure what information you need"
Expected: Agent asks clarifying questions via handoff form
```

### 3. Test Session Continuity

```
User: "Search flights from LAX to JFK"
Agent: [Shows results]
User: "What about the next day?"
Expected: Agent remembers context (LAX to JFK)
```

### 4. Test Clear Chat

- Click "Clear Chat" button
- Verify new session ID is generated
- Verify conversation history is cleared

## Troubleshooting

### Issue: "Unable to initialize agent runtime"

**Cause:** AGENT_RUNTIME_ARN not found  
**Solution:**

```bash
# Check if secret exists
python3 scripts/manage_secrets.py get autorescue/agent-runtime-arn

# Or set in .env
echo "AGENT_RUNTIME_ARN=arn:aws:..." >> .env
```

### Issue: "Error: The security token is expired"

**Cause:** AWS credentials expired  
**Solution:**

```bash
aws sso login
```

### Issue: Handoff not triggering

**Cause:** Response doesn't contain handoff keywords  
**Solution:** Customize detection logic in `show_home_page()`:

```python
if "handoff" in response_text.lower() or "need more information" in response_text.lower():
    st.session_state.pending_handoff = {...}
```

## Future Enhancements

### Streaming Support

Add async streaming like chat.py:

```python
async def stream_agent_response(prompt):
    # Implement streaming via EventStream
    pass
```

### Enhanced Handoff Detection

Parse agent response for explicit handoff signals:

```python
if response_data.get("handoff_requested"):
    st.session_state.pending_handoff = {...}
```

### Multi-Modal Support

Add support for images, files, etc.:

```python
payload = json.dumps({
    "prompt": prompt,
    "attachments": [...]
})
```

## Related Files

- `src/home.py` - Main chat interface
- `scripts/runtime_test.py` - Runtime testing script
- `scripts/secrets_manager.py` - Secrets retrieval utility
- `src/auth.py` - Authentication logic
- `src/login.py` - Login page

## References

- [AWS Bedrock AgentCore Runtime API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_Operations_Amazon_Bedrock_Runtime.html)
- [Streamlit Session State](https://docs.streamlit.io/library/api-reference/session-state)
- [Original chat.py](Downloads/chat.py) - Reference implementation
