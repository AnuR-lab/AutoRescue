import json
import os
import sys
import uuid
from datetime import datetime

import boto3
import streamlit as st
from dotenv import load_dotenv

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts"))

try:
    from secrets_manager import get_agent_runtime_arn
    SECRETS_MANAGER_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ secrets_manager module not available: {e}")
    st.info("Will try to use AGENT_RUNTIME_ARN from environment variable only.")
    get_agent_runtime_arn = None
    SECRETS_MANAGER_AVAILABLE = False
except Exception as e:
    st.error(f"Error importing secrets_manager: {e}")
    get_agent_runtime_arn = None
    SECRETS_MANAGER_AVAILABLE = False


def init_agent_runtime():
    """Initialize the agent runtime configuration"""
    if "agent_runtime_config" not in st.session_state:
        # Load environment variables
        load_dotenv()

        AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
        AGENT_RUNTIME_ARN = os.getenv("AGENT_RUNTIME_ARN")

        # Try to get ARN from environment or Secrets Manager
        if not AGENT_RUNTIME_ARN:
            if SECRETS_MANAGER_AVAILABLE and get_agent_runtime_arn:
                try:
                    with st.spinner("Fetching Agent Runtime ARN from AWS Secrets Manager..."):
                        AGENT_RUNTIME_ARN = get_agent_runtime_arn(region_name=AWS_REGION)
                    st.success("✓ Agent Runtime ARN retrieved from Secrets Manager")
                except Exception as e:
                    st.error(f"❌ Failed to retrieve agent runtime ARN from Secrets Manager: {str(e)}")
                    with st.expander("📋 Configuration Instructions"):
                        st.markdown("""
                        **Option 1: Set Environment Variable**
                        ```bash
                        export AGENT_RUNTIME_ARN="your-agent-runtime-arn"
                        ```
                        
                        **Option 2: Create .env file**
                        ```
                        AGENT_RUNTIME_ARN=your-agent-runtime-arn
                        AWS_REGION=us-east-1
                        ```
                        
                        **Option 3: Store in AWS Secrets Manager**
                        ```bash
                        python scripts/store_secrets.py
                        ```
                        """)
                    return None
            else:
                st.error("❌ AGENT_RUNTIME_ARN not configured. Please check your environment.")
                with st.expander("📋 How to configure"):
                    st.markdown("""
                    The Agent Runtime ARN is required to communicate with AWS Bedrock AgentCore.
                    
                    **For Local Development:**
                    Create a `.env` file in the project root:
                    ```
                    AGENT_RUNTIME_ARN=arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:runtime/NAME
                    AWS_REGION=us-east-1
                    ```
                    
                    **For Server Deployment:**
                    Store the ARN in AWS Secrets Manager:
                    ```bash
                    python scripts/store_secrets.py
                    ```
                    
                    Or set as environment variable:
                    ```bash
                    export AGENT_RUNTIME_ARN="your-arn-here"
                    ```
                    """)
                return None

        if not AGENT_RUNTIME_ARN:
            st.error("AGENT_RUNTIME_ARN not configured. Please check your environment.")
            return None

        # Initialize boto3 client
        client = boto3.client("bedrock-agentcore", region_name=AWS_REGION)

        st.session_state.agent_runtime_config = {
            "client": client,
            "arn": AGENT_RUNTIME_ARN,
            "region": AWS_REGION,
            "session_id": str(uuid.uuid4()) + "extra_chars_to_meet_33_char_min",
        }

    return st.session_state.agent_runtime_config


def call_agent_runtime(user_prompt: str) -> dict:
    """
    Call the AWS Bedrock Agent Runtime with the user's prompt

    Args:
        user_prompt: The user's question or request

    Returns:
        dict: Agent response containing 'response', 'model', 'gateway' keys
    """
    config = st.session_state.agent_runtime_config

    try:
        payload = json.dumps({"prompt": user_prompt})

        response = config["client"].invoke_agent_runtime(
            agentRuntimeArn=config["arn"],
            runtimeSessionId=config["session_id"],
            payload=payload,
            qualifier="DEFAULT",
        )

        response_body = response["response"].read()
        response_data = json.loads(response_body)

        return response_data

    except Exception as e:
        return {
            "error": str(e),
            "response": f"I apologize, but I encountered an error: {str(e)}",
        }


def show_home_page():
    """Display the main chatbot interface"""

    # Initialize agent runtime
    config = init_agent_runtime()
    if not config:
        st.error("Unable to initialize agent runtime. Please check your configuration.")
        return

    # Initialize session state for handoff
    if "pending_handoff" not in st.session_state:
        st.session_state.pending_handoff = None
    if "handoff_triggered_this_run" not in st.session_state:
        st.session_state.handoff_triggered_this_run = False

    # Sidebar
    with st.sidebar:
        st.title("✈️ AutoRescue Assistant")
        st.markdown(f"**Logged in as:** {st.session_state.username}")
        st.markdown("---")

        # Session info
        st.markdown("### Session Info")
        st.code(f"Session ID: {config['session_id'][:20]}...")
        st.caption(f"Region: {config['region']}")

        st.markdown("---")

        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.messages = []
            st.session_state.pending_handoff = None
            st.session_state.agent_runtime_config = None
            st.rerun()

        st.markdown("---")
        st.markdown("### About")
        st.info(
            """
        This AI assistant helps you:
        - Search for available flights
        - Handle flight disruptions
        - Find alternative travel options
        - Get real-time flight information
        
        **Powered by AWS Bedrock AgentCore**
        """
        )

        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.pending_handoff = None
            # Generate new session ID for fresh conversation
            st.session_state.agent_runtime_config["session_id"] = (
                str(uuid.uuid4()) + "extra_chars_to_meet_33_char_min"
            )
            st.rerun()

    # Main chat interface
    st.title("🤖 AutoRescue Flight Assistant")
    st.markdown("Ask me about flights, disruptions, or travel alternatives!")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"Hello {st.session_state.username}! 👋 I'm your AutoRescue Flight Assistant. I can help you:\n\n- **Search for flights** between airports\n- **Handle disruptions** like cancellations or delays\n- **Find alternatives** when plans change\n\nHow can I assist you today?",
            }
        )

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ----- HANDOFF GATE (must be before chat_input) -----
    if st.session_state.pending_handoff:
        # Show the agent's request and a form for the human to answer
        with st.chat_message("assistant"):
            st.markdown(
                f"**Agent handoff:** {st.session_state.pending_handoff['message']}"
            )

        with st.form("handoff_form", clear_on_submit=True):
            user_reply = st.text_area(
                "Your input", placeholder="Type your answer…", height=120
            )
            submitted = st.form_submit_button("Send")

        if submitted and user_reply.strip():
            # Add user reply to messages
            st.session_state.messages.append({"role": "user", "content": user_reply})

            # Clear the pending handoff
            breakout = bool(st.session_state.pending_handoff.get("breakout"))
            st.session_state.pending_handoff = None
            st.session_state.handoff_triggered_this_run = False

            # If breakout==True, stop here and return to normal chat
            if breakout:
                st.rerun()
            else:
                # For soft handoff, continue the conversation
                with st.chat_message("assistant"):
                    with st.spinner("Processing your response..."):
                        response_data = call_agent_runtime(user_reply)

                        if "error" in response_data:
                            response_text = response_data.get(
                                "response", "An error occurred."
                            )
                            st.error(response_text)
                        else:
                            response_text = response_data.get(
                                "response", "No response from agent."
                            )
                            st.markdown(response_text)

                        # Add to chat history
                        st.session_state.messages.append(
                            {"role": "assistant", "content": response_text}
                        )

                st.rerun()

        st.stop()  # Don't fall through to chat_input on this run

    # ----- NORMAL CHAT INPUT -----
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Call agent runtime and get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response_data = call_agent_runtime(prompt)

                if "error" in response_data:
                    error_msg = response_data.get("response", "An error occurred.")
                    st.error(error_msg)
                    response_text = error_msg
                else:
                    response_text = response_data.get(
                        "response", "No response from agent."
                    )

                    # Check if response indicates a handoff is needed
                    # (You can customize this logic based on your agent's response patterns)
                    if (
                        "handoff" in response_text.lower()
                        or "need more information" in response_text.lower()
                    ):
                        st.session_state.pending_handoff = {
                            "message": response_text,
                            "breakout": False,
                        }
                        st.session_state.handoff_triggered_this_run = True

                    st.markdown(response_text)

                    # Show metadata if available
                    if "model" in response_data:
                        with st.expander("Response Details"):
                            st.json(
                                {
                                    "model": response_data.get("model"),
                                    "gateway": response_data.get("gateway"),
                                }
                            )

        # Add assistant response to chat history
        st.session_state.messages.append(
            {"role": "assistant", "content": response_text}
        )

        # Rerun if handoff was triggered
        if st.session_state.handoff_triggered_this_run:
            st.rerun()
