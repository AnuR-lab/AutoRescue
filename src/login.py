import streamlit as st
# from src.auth import verify_credentials 
from src.auth_s3 import verify_credentials, get_user_roles

def show_login_page():
    """Display login page with authentication"""

    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
        }
        .stButton>button {
            width: 100%;
            background-color: #FF4B4B;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("# ✈️ Auto Rescue Advisor")
        st.markdown("### Welcome Back!")
        st.markdown("---")

        if "login_attempts" not in st.session_state:
            st.session_state.login_attempts = 0

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")

            submit_button = st.form_submit_button("Login")

            if submit_button:
                if not username or not password:
                    st.warning("Please enter both username and password")
                else:
                    try:
                        if verify_credentials(username, password):
                            st.session_state.authenticated = True
                            st.session_state.username = username
                            st.session_state.roles = get_user_roles(username)
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.session_state.login_attempts += 1
                            st.error("Invalid username or password")
                    except Exception as e:
                        st.exception(e) 
                        st.error("Authentication service temporarily unavailable")

        st.markdown("---")
        st.caption("Contact an admin to create or reset your account.")
