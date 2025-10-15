import hashlib
import json
import os

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_credentials(username, password):
    """
    Verify username and password against stored credentials.
    For demo purposes, using hardcoded credentials.
    In production, use a database or secure credential store.
    """
    
    # Demo credentials (username: hashed_password)
    VALID_USERS = {
        "admin": hash_password("admin123"),
        "demo": hash_password("demo123"),
        "user": hash_password("password123")
    }
    
    # Check if username exists
    if username not in VALID_USERS:
        return False
    
    # Verify password
    hashed_input = hash_password(password)
    return hashed_input == VALID_USERS[username]

def load_users_from_file(filepath="users.json"):
    """
    Load users from a JSON file (optional enhancement).
    File format: {"username": "hashed_password", ...}
    """
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading users: {e}")
    return {}

def save_user(username, password, filepath="users.json"):
    """
    Save a new user to the JSON file (optional enhancement).
    """
    try:
        users = load_users_from_file(filepath)
        users[username] = hash_password(password)
        
        with open(filepath, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving user: {e}")
        return False