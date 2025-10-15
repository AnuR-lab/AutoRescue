import streamlit as st
from src.login import show_login_page
from src.home import show_home_page

# Page configuration
st.set_page_config(
    page_title="Auto Rescue Advisor",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None

def main():
    """Main application logic with routing"""
    
    # Show login page if not authenticated
    if not st.session_state.authenticated:
        show_login_page()
    else:
        # Show home page if authenticated
        show_home_page()

if __name__ == "__main__":
    main()