import streamlit as st
from datetime import datetime

def show_home_page():
    """Display the main chatbot interface"""
    
    # Sidebar
    with st.sidebar:
        st.title("✈️ Auto Rescue Advisor")
        st.markdown(f"**Logged in as:** {st.session_state.username}")
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.messages = []
            st.rerun()
        
        st.markdown("---")
        st.markdown("### About")
        st.info("""
        This AI chatbot helps you:
        - Get auto rescue recommendations
        """)
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    # Main chat interface
    st.title("🤖 Auto Rescue Advisor Chatbot")
    st.markdown("Ask me anything about Auto Rescue !")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Hello {st.session_state.username}! 👋 I'm your Auto Rescue Advisor. How can I help you today?"
        })
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response (placeholder for your teammate's chatbot logic)
        with st.chat_message("assistant"):
            response = get_chatbot_response(prompt)
            st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

def get_chatbot_response(user_input):
    """
    Placeholder function for chatbot logic.
    Your teammate can replace this with their AI model.
    """
    
    # Simple response logic (replace with actual AI model)
    user_input_lower = user_input.lower()
    
    if "Rescue" in user_input_lower:
        return "🛋️ I can help you find Auto Rescue information! Please tell me:\n- Which airport are you traveling from?\n- What's your travel class?"
    else:
        return f"I understand you're asking about: '{user_input}'\n\n🤖 **[Your teammate's AI model will respond here]**\n\nThis is a placeholder response. The actual chatbot logic will be integrated by your team."