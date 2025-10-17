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
            st.session_state.suggestion_used = False  # Reset suggestion flag
            st.session_state.random_suggestion = None  # Clear suggestion
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
        st.session_state.suggestion_used = False  # Track if suggestion has been used
        # Fetch a random flight suggestion from agent runtime
        try:
            with st.spinner("Loading passenger itinerary..."):
                suggestion_response = call_agent_runtime("Generate a random flight suggestion")
            suggestion = None
            if isinstance(suggestion_response, dict):
                # Attempt to parse JSON block from response if present
                raw_text = suggestion_response.get("response", "")
                # Heuristic: find first JSON-like brace section
                start = raw_text.find("{")
                end = raw_text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    try:
                        suggestion = json.loads(raw_text[start:end+1])
                    except Exception:
                        suggestion = None
            if suggestion and all(k in suggestion for k in ["origin", "destination", "departureDate"]):
                st.session_state.random_suggestion = suggestion
                # Add a disruption notification message
                airline = suggestion.get('preferredAirline', 'Airline')
                today = datetime.utcnow().date().isoformat()
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            f"📧 **Message from {airline}:**\n\n"
                            f"Dear {st.session_state.username},\n\n"
                            f"We sincerely apologize to inform you that your flight **{airline} {suggestion['origin']} ➜ {suggestion['destination']}** "
                            f"scheduled for **{suggestion['departureDate']}** has been cancelled due to unforeseen circumstances.\n\n"
                            f"**Would you like to reschedule this itinerary?**\n\n"
                            f"Please provide your preferred date of travel below to search for available alternatives on the same route and airline."
                        ),
                    }
                )
            else:
                # Fallback: generate suggestion locally if agent didn't return structured JSON
                from random import choice, randint
                from datetime import datetime, timedelta
                north_america_airports = ["JFK", "EWR", "LAX", "ORD", "DFW", "MIA", "ATL", "YYZ", "YUL", "SEA"]
                europe_airports = ["LHR", "LGW", "CDG", "AMS", "FRA", "MAD", "BCN", "MUC", "DUB", "CPH"]
                airlines = ["AA", "BA", "DL", "LA", "AF"]
                fallback = {
                    "origin": choice(north_america_airports),
                    "destination": choice(europe_airports),
                    "preferredAirline": choice(airlines),
                    "departureDate": (datetime.utcnow() + timedelta(days=randint(2,14))).date().isoformat(),
                    "passengers": 1,
                    "note": "Locally generated suggestion (agent unavailable)."
                }
                st.session_state.random_suggestion = fallback
                # Add a disruption notification message for fallback
                airline = fallback.get('preferredAirline', 'Airline')
                today = datetime.utcnow().date().isoformat()
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            f"📧 **Message from {airline}:**\n\n"
                            f"Dear {st.session_state.username},\n\n"
                            f"We sincerely apologize to inform you that your flight **{airline} {fallback['origin']} ➜ {fallback['destination']}** "
                            f"scheduled for **{fallback['departureDate']}** has been cancelled due to unforeseen circumstances.\n\n"
                            f"**Would you like to reschedule this itinerary?**\n\n"
                            f"Please provide your preferred date of travel below to search for available alternatives on the same route and airline."
                        ),
                    }
                )
        except Exception as e:
            st.session_state.random_suggestion = None
            st.warning(f"Could not generate sample itinerary: {e}")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # If we have a random suggestion and it hasn't been used yet, show a helper panel
    if st.session_state.get("random_suggestion") and not st.session_state.get("suggestion_used", False):
        sugg = st.session_state.random_suggestion
        with st.container(border=True):
            st.subheader("✈️ Cancelled Flight - Reschedule Options")
            st.caption("⚠️ Original route and airline are locked. Please select a new departure date.")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.text_input("Origin", sugg["origin"], key="sugg_origin", disabled=True, 
                            help="Route is locked from cancelled booking")
            with col2:
                st.text_input("Destination", sugg["destination"], key="sugg_destination", disabled=True,
                            help="Route is locked from cancelled booking")
            with col3:
                date = st.text_input("Departure Date", sugg["departureDate"], key="sugg_date",
                                   help="Select your preferred new departure date")
            with col4:
                st.text_input("Airline", sugg.get("preferredAirline", ""), key="sugg_airline", disabled=True,
                            help="Airline is locked from cancelled booking")
            
            # Custom CSS for blue button and disabled inputs styling
            st.markdown("""
                <style>
                div[data-testid="stButton"] button[kind="primary"] {
                    background-color: #0066CC !important;
                    border-color: #0066CC !important;
                }
                div[data-testid="stButton"] button[kind="primary"]:hover {
                    background-color: #0052A3 !important;
                    border-color: #0052A3 !important;
                }
                /* Style for disabled inputs to show they're locked */
                input[disabled] {
                    background-color: #f0f0f0 !important;
                    color: #666 !important;
                    cursor: not-allowed !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            if st.button("🔍 Find Alternative Flights", use_container_width=True, type="primary"):
                # Mark suggestion as used
                st.session_state.suggestion_used = True
                
                # Use LOCKED values from original suggestion
                origin = sugg["origin"]
                destination = sugg["destination"]
                airline = sugg.get("preferredAirline", "")
                
                # Formulate a disruption handling prompt with locked parameters
                prompt = (
                    f"IMPORTANT: The passenger's cancelled flight had these FIXED parameters that CANNOT be changed:\n"
                    f"- Origin: {origin} (LOCKED)\n"
                    f"- Destination: {destination} (LOCKED)\n"
                    f"- Airline: {airline} (LOCKED)\n\n"
                    f"The passenger wants to reschedule to: {date}\n\n"
                    f"Please search for flights from {origin} to {destination} on {date} for 1 passenger with carrier {airline}. "
                    f"Use the carrier parameter to filter results."
                )
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(f"Find flights from **{origin}** to **{destination}** on **{date}** with **{airline}**")
                with st.chat_message("assistant"):
                    with st.spinner("Searching flights..."):
                        response_data = call_agent_runtime(prompt)
                        if "error" in response_data:
                            error_msg = response_data.get("response", "An error occurred.")
                            st.error(error_msg)
                            response_text = error_msg
                        else:
                            response_text = response_data.get("response", "No response from agent.")
                            st.markdown(response_text)
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                st.rerun()

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
