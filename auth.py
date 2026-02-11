"""
Authentication Module for Smart Microgrid Manager Pro
Handles user authentication, session management, and role-based access control.
"""

import streamlit as st
import pandas as pd
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import json
import os
import re

# Import branding for logo display
from branding import COMPANY_BRANDING, SVG_LOGO_SMALL

# Database file for users
USER_DB_FILE = "users.json"

# Security Settings
SESSION_TIMEOUT_MINUTES = 30
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = True


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((password + salt).encode())
    return f"{salt}:{hash_obj.hexdigest()}"


def calculate_password_strength(password: str) -> Dict:
    """
    Calculate password strength score and provide feedback.
    
    Returns:
        Dict with 'score' (0-5), 'strength' label, and 'feedback' list
    """
    score = 0
    feedback = []
    requirements_met = []
    
    # Length check
    if len(password) >= PASSWORD_MIN_LENGTH:
        score += 1
        requirements_met.append("✓ At least 8 characters")
    else:
        feedback.append(f"❌ Password should be at least {PASSWORD_MIN_LENGTH} characters")
    
    # Uppercase check
    if PASSWORD_REQUIRE_UPPERCASE:
        if any(c.isupper() for c in password):
            score += 1
            requirements_met.append("✓ Contains uppercase letter")
        else:
            feedback.append("❌ Add uppercase letters (A-Z)")
    
    # Lowercase check
    if PASSWORD_REQUIRE_LOWERCASE:
        if any(c.islower() for c in password):
            score += 1
            requirements_met.append("✓ Contains lowercase letter")
        else:
            feedback.append("❌ Add lowercase letters (a-z)")
    
    # Digit check
    if PASSWORD_REQUIRE_DIGIT:
        if any(c.isdigit() for c in password):
            score += 1
            requirements_met.append("✓ Contains number")
        else:
            feedback.append("❌ Add numbers (0-9)")
    
    # Special character check
    special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    if PASSWORD_REQUIRE_SPECIAL:
        if any(c in special_chars for c in password):
            score += 1
            requirements_met.append("✓ Contains special character")
        else:
            feedback.append(f"❌ Add special characters ({special_chars})")
    
    # Bonus: Check for common patterns
    common_patterns = ['password', '123456', 'qwerty', 'admin', 'microgrid']
    for pattern in common_patterns:
        if pattern.lower() in password.lower():
            score = max(0, score - 1)
            feedback.append(f"⚠️ Avoid common patterns like '{pattern}'")
            break
    
    # Determine strength label
    if score <= 1:
        strength = "Very Weak"
        color = "#e74c3c"
    elif score == 2:
        strength = "Weak"
        color = "#e67e22"
    elif score == 3:
        strength = "Fair"
        color = "#f1c40f"
    elif score == 4:
        strength = "Strong"
        color = "#27ae60"
    else:
        strength = "Very Strong"
        color = "#2ecc71"
    
    return {
        'score': score,
        'max_score': 5,
        'strength': strength,
        'color': color,
        'feedback': feedback,
        'requirements_met': requirements_met
    }


def get_password_strength_html(password: str) -> str:
    """Get HTML representation of password strength indicator."""
    if not password:
        return """
        <div class="password-strength">
            <p style="color: #666; font-size: 12px;">Enter a password to see strength</p>
        </div>
        """
    
    strength = calculate_password_strength(password)
    score_pct = (strength['score'] / strength['max_score']) * 100
    
    # Build requirements list
    requirements_html = "<ul style='margin: 5px 0; padding-left: 20px; font-size: 11px; color: #666;'>"
    for req in strength['requirements_met']:
        requirements_html += f"<li>{req}</li>"
    requirements_html += "</ul>"
    
    return f"""
    <div class="password-strength" style="margin-top: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-size: 12px; font-weight: 600;">Strength:</span>
            <span style="font-size: 12px; color: {strength['color']}; font-weight: 600;">{strength['strength']}</span>
        </div>
        <div style="background: #e0e0e0; border-radius: 4px; height: 8px; overflow: hidden;">
            <div style="background: {strength['color']}; height: 100%; width: {score_pct}%; transition: width 0.3s;"></div>
        </div>
        {requirements_html}
    </div>
    """


def validate_password_requirements(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password against all requirements.
    
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
    
    if PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    
    if PASSWORD_REQUIRE_SPECIAL:
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        if not any(c in special_chars for c in password):
            errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors


# Session Management Functions
def init_session_state():
    """Initialize session state for authentication with security features."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = None
    if "role" not in st.session_state:
        st.session_state["role"] = None
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "show_admin" not in st.session_state:
        st.session_state["show_admin"] = False
    if "last_activity" not in st.session_state:
        st.session_state["last_activity"] = datetime.now()
    if "login_attempts" not in st.session_state:
        st.session_state["login_attempts"] = 0
    if "account_locked" not in st.session_state:
        st.session_state["account_locked"] = False
    if "lockout_end_time" not in st.session_state:
        st.session_state["lockout_end_time"] = None


def check_session_timeout() -> bool:
    """
    Check if the current session has timed out.
    
    Returns:
        True if session is valid, False if timed out
    """
    if not st.session_state.get("authenticated", False):
        return False
    
    if "last_activity" not in st.session_state:
        return False
    
    last_activity = st.session_state.last_activity
    timeout = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    
    if datetime.now() - last_activity > timeout:
        # Session has timed out
        logout(reason="Session timed out due to inactivity")
        return False
    
    return True


def update_activity():
    """Update the last activity timestamp."""
    st.session_state.last_activity = datetime.now()


def increment_login_attempts():
    """Increment failed login attempts counter."""
    st.session_state["login_attempts"] = st.session_state.get("login_attempts", 0) + 1


def reset_login_attempts():
    """Reset login attempts counter on successful login."""
    st.session_state["login_attempts"] = 0
    st.session_state["account_locked"] = False
    st.session_state["lockout_end_time"] = None


def check_account_locked(username: str) -> Tuple[bool, Optional[str]]:
    """
    Check if an account is locked due to too many failed attempts.
    
    Returns:
        Tuple of (is_locked, reason_if_locked)
    """
    users = load_users()
    username_lower = username.lower()
    
    if username_lower in users:
        user = users[username_lower]
        lockout_info = user.get("lockout_info", {})
        
        if lockout_info.get("is_locked", False):
            lockout_end = lockout_info.get("lockout_end")
            if lockout_end:
                lockout_end_time = datetime.fromisoformat(lockout_end)
                if datetime.now() < lockout_end_time:
                    remaining = (lockout_end_time - datetime.now()).seconds // 60
                    return True, f"Account locked. Try again in {remaining} minutes."
                else:
                    # Lockout period has expired, unlock the account
                    unlock_account(username)
    
    return False, None


def lock_account(username: str, duration_minutes: int = LOCKOUT_DURATION_MINUTES) -> bool:
    """
    Lock an account due to too many failed login attempts.
    
    Args:
        username: The username to lock
        duration_minutes: How long to lock the account for
        
    Returns:
        True if successfully locked, False otherwise
    """
    users = load_users()
    username_lower = username.lower()
    
    if username_lower in users:
        lockout_end = datetime.now() + timedelta(minutes=duration_minutes)
        users[username_lower]["lockout_info"] = {
            "is_locked": True,
            "lockout_start": datetime.now().isoformat(),
            "lockout_end": lockout_end.isoformat(),
            "reason": "Too many failed login attempts"
        }
        save_users(users)
        return True
    
    return False


def unlock_account(username: str) -> bool:
    """
    Unlock a previously locked account.
    
    Args:
        username: The username to unlock
        
    Returns:
        True if successfully unlocked, False otherwise
    """
    users = load_users()
    username_lower = username.lower()
    
    if username_lower in users:
        users[username_lower].pop("lockout_info", None)
        save_users(users)
        return True
    
    return False


def track_login_attempt(username: str, success: bool, ip_address: str = None):
    """
    Track a login attempt for security monitoring.
    
    Args:
        username: The username that attempted login
        success: Whether the login was successful
        ip_address: The IP address of the request
    """
    if success:
        # Reset attempts on successful login
        users = load_users()
        username_lower = username.lower()
        if username_lower in users:
            users[username_lower]["failed_attempts"] = 0
            users[username_lower]["last_failed_attempt"] = None
            save_users(users)
        reset_login_attempts()
    else:
        # Increment failed attempts
        increment_login_attempts()
        users = load_users()
        username_lower = username.lower()
        if username_lower in users:
            if "failed_attempts" not in users[username_lower]:
                users[username_lower]["failed_attempts"] = 0
            users[username_lower]["failed_attempts"] = users[username_lower].get("failed_attempts", 0) + 1
            users[username_lower]["last_failed_attempt"] = datetime.now().isoformat()
            
            # Check if should lock
            if users[username_lower]["failed_attempts"] >= MAX_LOGIN_ATTEMPTS:
                lock_account(username)
                users[username_lower]["failed_attempts"] = 0  # Reset counter after lock
                st.session_state["account_locked"] = True
                lockout_end = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                st.session_state["lockout_end_time"] = lockout_end
            
            save_users(users)


def get_failed_attempts(username: str) -> int:
    """Get the number of failed login attempts for a user."""
    users = load_users()
    username_lower = username.lower()
    
    if username_lower in users:
        return users[username_lower].get("failed_attempts", 0)
    
    return 0


# Session Activity History Functions
def record_session_activity(username: str, action: str, details: str = ""):
    """
    Record a session activity event.
    
    Args:
        username: The username
        action: The action performed
        details: Additional details about the action
    """
    users = load_users()
    username_lower = username.lower()
    
    if username_lower in users:
        if "activity_history" not in users[username_lower]:
            users[username_lower]["activity_history"] = []
        
        activity = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        }
        
        # Keep only last 100 activities
        users[username_lower]["activity_history"] = (
            [activity] + users[username_lower]["activity_history"]
        )[:100]
        
        save_users(users)


def get_session_activity(username: str, limit: int = 50) -> List[Dict]:
    """
    Get session activity history for a user.
    
    Args:
        username: The username
        limit: Maximum number of activities to return
        
    Returns:
        List of activity dictionaries
    """
    users = load_users()
    username_lower = username.lower()
    
    if username_lower in users:
        return users[username_lower].get("activity_history", [])[:limit]
    
    return []


# Profile Management Functions
def update_user_profile(username: str, profile_data: Dict) -> Tuple[bool, str]:
    """
    Update user profile information.
    
    Args:
        username: The username
        profile_data: Dictionary containing profile fields to update
        
    Returns:
        Tuple of (success, message)
    """
    users = load_users()
    username_lower = username.lower()
    
    if username_lower not in users:
        return False, "User not found"
    
    # Allowed fields to update
    allowed_fields = ['phone', 'company', 'address', 'timezone', 'preferred_units', 
                      'notification_email', 'daily_summary', 'language']
    
    for field, value in profile_data.items():
        if field in allowed_fields:
            users[username_lower][field] = value
    
    users[username_lower]['updated_at'] = datetime.now().isoformat()
    save_users(users)
    
    return True, "Profile updated successfully"


def get_user_profile(username: str) -> Dict:
    """
    Get user profile information.
    
    Args:
        username: The username
        
    Returns:
        Dictionary containing profile information
    """
    users = load_users()
    username_lower = username.lower()
    
    if username_lower in users:
        user = users[username_lower]
        return {
            'username': user.get('username', ''),
            'email': user.get('email', ''),
            'role': user.get('role', ''),
            'phone': user.get('phone', ''),
            'company': user.get('company', ''),
            'address': user.get('address', ''),
            'timezone': user.get('timezone', 'UTC'),
            'preferred_units': user.get('preferred_units', 'metric'),
            'notification_email': user.get('notification_email', user.get('email', '')),
            'daily_summary': user.get('daily_summary', True),
            'language': user.get('language', 'English'),
            'created_at': user.get('created_at', ''),
            'last_login': user.get('last_login', ''),
            'activity_count': len(user.get('activity_history', []))
        }
    
    return {}


def change_password(username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
    """
    Change user password with old password verification.
    
    Args:
        username: The username
        old_password: The current password
        new_password: The new password
        
    Returns:
        Tuple of (success, message)
    """
    users = load_users()
    username_lower = username.lower()
    
    if username_lower not in users:
        return False, "User not found"
    
    user = users[username_lower]
    
    # Verify old password
    if not verify_password(old_password, user['password']):
        return False, "Current password is incorrect"
    
    # Validate new password
    is_valid, errors = validate_password_requirements(new_password)
    if not is_valid:
        return False, "Password does not meet requirements: " + "; ".join(errors)
    
    # Check if new password is same as old
    if verify_password(new_password, user['password']):
        return False, "New password cannot be the same as the old password"
    
    # Update password
    users[username_lower]['password'] = hash_password(new_password)
    users[username_lower]['password_changed_at'] = datetime.now().isoformat()
    save_users(users)
    
    # Record activity
    record_session_activity(username, 'password_change', 'Password changed successfully')
    
    return True, "Password changed successfully"


def get_account_stats(username: str) -> Dict:
    """
    Get account statistics for a user.
    
    Args:
        username: The username
        
    Returns:
        Dictionary containing account statistics
    """
    users = load_users()
    username_lower = username.lower()
    
    if username_lower not in users:
        return {}
    
    user = users[username_lower]
    
    return {
        'username': user.get('username', ''),
        'email': user.get('email', ''),
        'role': user.get('role', ''),
        'created_at': user.get('created_at', ''),
        'last_login': user.get('last_login', ''),
        'total_logins': user.get('total_logins', 1),
        'failed_attempts': user.get('failed_attempts', 0),
        'last_failed_attempt': user.get('last_failed_attempt', ''),
        'password_changed_at': user.get('password_changed_at', ''),
        'activity_count': len(user.get('activity_history', [])),
        'sessions_count': len(user.get('sessions', [])),
        'is_locked': user.get('lockout_info', {}).get('is_locked', False) if user.get('lockout_info') else False
    }


# Default admin credentials (defined after hash_password)
DEFAULT_ADMIN = {
    "username": "admin",
    "password": hash_password("microgrid"),
    "role": "admin",
    "email": "admin@microgrid.com",
    "created_at": datetime.now().isoformat(),
    "last_login": None,
    "is_active": True
}

DEFAULT_USER = {
    "username": "user",
    "password": hash_password("user123"),
    "role": "user",
    "email": "user@microgrid.com",
    "created_at": datetime.now().isoformat(),
    "last_login": None,
    "is_active": True
}


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        salt, hash_value = stored_hash.split(":")
        hash_obj = hashlib.sha256((password + salt).encode())
        return hash_obj.hexdigest() == hash_value
    except:
        return False


def load_users() -> Dict:
    """Load users from JSON file."""
    if not os.path.exists(USER_DB_FILE):
        # Create default users
        users = {
            "admin": DEFAULT_ADMIN.copy(),
            "user": DEFAULT_USER.copy()
        }
        save_users(users)
        return users
    
    try:
        with open(USER_DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}


def save_users(users: Dict):
    """Save users to JSON file."""
    with open(USER_DB_FILE, 'w') as f:
        json.dump(users, f, indent=4)


def create_user(username: str, password: str, role: str = "user", 
                email: str = "") -> tuple[bool, str]:
    """Create a new user."""
    users = load_users()
    
    if username.lower() in users:
        return False, "Username already exists"
    
    users[username.lower()] = {
        "username": username,
        "password": hash_password(password),
        "role": role,
        "email": email,
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "is_active": True
    }
    
    save_users(users)
    return True, "User created successfully"


def authenticate(username: str, password: str) -> Optional[Dict]:
    """Authenticate a user and return user info if successful."""
    users = load_users()
    
    username_lower = username.lower()
    if username_lower in users:
        user = users[username_lower]
        if user.get("is_active", True):
            if verify_password(password, user["password"]):
                # Update last login
                user["last_login"] = datetime.now().isoformat()
                save_users(users)
                return user
    
    return None


def get_user_info(username: str) -> Optional[Dict]:
    """Get user information."""
    users = load_users()
    username_lower = username.lower()
    if username_lower in users:
        return users[username_lower]
    return None


def update_user_password(username: str, new_password: str) -> bool:
    """Update user password."""
    users = load_users()
    username_lower = username.lower()
    
    if username_lower in users:
        users[username_lower]["password"] = hash_password(new_password)
        save_users(users)
        return True
    return False


def delete_user(username: str) -> bool:
    """Delete a user (cannot delete admin)."""
    users = load_users()
    username_lower = username.lower()
    
    if username_lower in users and users[username_lower]["role"] != "admin":
        del users[username_lower]
        save_users(users)
        return True
    return False


def list_users() -> List[Dict]:
    """List all users (admin only)."""
    users = load_users()
    return [
        {
            "username": v["username"],
            "role": v["role"],
            "email": v.get("email", ""),
            "created_at": v.get("created_at", ""),
            "last_login": v.get("last_login", ""),
            "is_active": v.get("is_active", True)
        }
        for k, v in users.items()
    ]


def is_admin(username: str) -> bool:
    """Check if user is admin."""
    users = load_users()
    username_lower = username.lower()
    return username_lower in users and users[username_lower]["role"] == "admin"


def login_page():
    """Display login page with Sign In and Sign Up options with enhanced security."""
    # Custom CSS for login page with branding colors
    st.markdown(f"""
    <style>
    .login-container {{
        background: linear-gradient(135deg, #1A365D 0%, #2D4A77 100%);
        font-family: 'Segoe UI', Arial, sans-serif;
        min-height: 100vh;
        margin: 0;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .login-box {{
        background: #fff;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(44, 62, 80, 0.15);
        padding: 40px 32px 32px 32px;
        width: 450px;
        max-width: 95vw;
        text-align: center;
    }}
    .login-box h2 {{
        margin: 16px 0 8px 0;
        color: #1A365D;
        font-size: 24px;
        font-weight: 700;
    }}
    .login-tagline {{
        color: #48BB78;
        font-size: 14px;
        margin: 0 0 24px 0;
    }}
    .stTextInput label {{
        display: block;
        margin-bottom: 8px;
        color: #1A365D;
        font-weight: 500;
        text-align: left;
    }}
    .stButton button {{
        width: 100%;
        padding: 12px;
        background: linear-gradient(135deg, #1A365D 0%, #2D4A77 100%);
        color: #fff;
        border: none;
        border-radius: 8px;
        font-size: 1.1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    .stButton button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(26, 54, 93, 0.3);
    }}
    .security-badge {{
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        background: #e8f5e9;
        border-radius: 20px;
        font-size: 11px;
        color: #2e7d32;
        margin: 4px;
    }}
    .login-attempts-warning {{
        background: #fff3e0;
        border: 1px solid #ff9800;
        border-radius: 8px;
        padding: 12px;
        margin: 10px 0;
        font-size: 13px;
        color: #e65100;
    }}
    .lockout-warning {{
        background: #ffebee;
        border: 1px solid #f44336;
        border-radius: 8px;
        padding: 12px;
        margin: 10px 0;
        font-size: 13px;
        color: #c62828;
    }}
    .brand-logo-container {{
        margin-bottom: 16px;
    }}
    .brand-logo-container svg {{
        width: 100px;
        height: 100px;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        # Logo and branding
        st.markdown(f'''
        <div class="brand-logo-container">
            {SVG_LOGO_SMALL}
        </div>
        <h2>{COMPANY_BRANDING['company_name']}</h2>
        <p class="login-tagline">{COMPANY_BRANDING['tagline']}</p>
        ''', unsafe_allow_html=True)
        
        # Security badges
        st.markdown("""
        <div style="margin-bottom: 16px;">
            <span class="security-badge">🔒 Secure Login</span>
            <span class="security-badge">🔑 Password Protected</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Tab selection for Sign In or Sign Up
        tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Sign Up"])
        
        with tab1:
            # Check for account lockout
            username_input = st.text_input("Username", key="login_username")
            
            # Check if account is locked
            is_locked, lockout_reason = check_account_locked(username_input)
            
            if is_locked:
                st.markdown(f"""
                <div class="lockout-warning">
                    <strong>⚠️ Account Locked</strong><br>
                    {lockout_reason}
                </div>
                """, unsafe_allow_html=True)
                
                # Show countdown if available
                if st.session_state.get("lockout_end_time"):
                    remaining = (st.session_state["lockout_end_time"] - datetime.now()).seconds // 60
                    st.info(f"Time remaining: {remaining} minutes")
            
            password_input = st.text_input("Password", type="password", key="login_password")
            
            # Show remaining attempts
            if username_input and not is_locked:
                attempts = get_failed_attempts(username_input)
                remaining_attempts = MAX_LOGIN_ATTEMPTS - attempts
                if remaining_attempts <= 2:
                    st.markdown(f"""
                    <div class="login-attempts-warning">
                        ⚠️ <strong>Warning:</strong> {remaining_attempts} attempt(s) remaining before lockout
                    </div>
                    """, unsafe_allow_html=True)
            
            with st.form("login_form"):
                submit = st.form_submit_button("Sign In", use_container_width=True)
                
                if submit:
                    if is_locked:
                        st.error("Account is locked. Please try again later.")
                    elif username_input and password_input:
                        user = authenticate(username_input, password_input)
                        if user:
                            # Track successful login
                            track_login_attempt(username_input, True)
                            record_session_activity(username_input, 'login', 'Successful login')
                            
                            st.session_state["authenticated"] = True
                            st.session_state["username"] = user["username"]
                            st.session_state["role"] = user["role"]
                            st.session_state["user"] = user
                            st.session_state["last_activity"] = datetime.now()
                            st.rerun()
                        else:
                            # Track failed login
                            track_login_attempt(username_input, False)
                            record_session_activity(username_input, 'login_failed', f'Failed login attempt for {username_input}')
                            
                            attempts = get_failed_attempts(username_input)
                            remaining = MAX_LOGIN_ATTEMPTS - attempts
                            
                            if remaining <= 0:
                                st.error("Account locked due to too many failed attempts.")
                            else:
                                st.error(f"Invalid username or password. {remaining} attempts remaining.")
                    else:
                        st.error("Please enter username and password")
            
            st.markdown("---")
            st.info("Default credentials:")
            st.markdown("- **Admin:** admin / microgrid")
            st.markdown("- **User:** user / user123")
        
        with tab2:
            st.markdown("### Create New Account")
            
            with st.form("signup_form"):
                new_username = st.text_input("Choose Username", key="signup_username")
                new_email = st.text_input("Email Address", key="signup_email", type="default")
                new_password = st.text_input("Choose Password", type="password", key="signup_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
                
                # Password strength indicator (live)
                password_strength_html = get_password_strength_html(new_password)
                st.markdown(password_strength_html, unsafe_allow_html=True)
                
                signup_submit = st.form_submit_button("Create Account", use_container_width=True)
                
                if signup_submit:
                    if not new_username or not new_password or not new_email:
                        st.error("All fields are required")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_username) < 3:
                        st.error("Username must be at least 3 characters")
                    else:
                        # Validate password strength
                        strength = calculate_password_strength(new_password)
                        if strength['score'] < 3:
                            st.error("Password is too weak. Please choose a stronger password.")
                        else:
                            success, msg = create_user(new_username, new_password, "user", new_email)
                            if success:
                                st.success(f"✅ Account created successfully!")
                                st.info("Please sign in with your new credentials.")
                            else:
                                st.error(msg)
            
            # Password requirements help
            with st.expander("📋 Password Requirements", expanded=True):
                st.markdown("""
                **Strong Password Guidelines:**
                - Minimum 8 characters
                - At least one uppercase letter (A-Z)
                - At least one lowercase letter (a-z)
                - At least one number (0-9)
                - At least one special character (!@#$...)
                - Avoid common patterns
                """)
        
        st.markdown('</div>', unsafe_allow_html=True)


def logout():
    """Log out the current user with activity tracking."""
    username = st.session_state.get("username")
    
    # Record logout activity
    if username:
        record_session_activity(username, 'logout', 'User logged out')
    
    # Clear session state
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.session_state["role"] = None
    st.session_state["user"] = None
    st.session_state["show_profile"] = False
    st.session_state["show_admin"] = False
    
    st.rerun()


def require_auth(func):
    """Decorator to require authentication."""
    def wrapper(*args, **kwargs):
        if not st.session_state.get("authenticated", False):
            login_page()
            return
        
        if st.session_state.get("role") == "admin":
            func(*args, **kwargs)
        else:
            st.error("Admin access required")
    
    return wrapper


def show_user_menu():
    """Show user menu in sidebar with enhanced features."""
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"**👤 User:** {st.session_state.get('username', 'Guest')}")
        st.markdown(f"**📋 Role:** {st.session_state.get('role', 'N/A')}")
        
        # Session timeout indicator
        if st.session_state.get("authenticated", False):
            last_activity = st.session_state.get("last_activity", datetime.now())
            timeout = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
            time_remaining = timeout - (datetime.now() - last_activity)
            minutes_left = max(0, time_remaining.seconds // 60)
            
            if minutes_left < 5:
                st.warning(f"⏰ Session expires in {minutes_left} min")
            else:
                st.info(f"⏱️ Session: {minutes_left} min remaining")
        
        # Profile button
        if st.button("👤 Profile", use_container_width=True):
            st.session_state["show_profile"] = True
        
        # Admin panel link (only for admins)
        if st.session_state.get("role") == "admin":
            if st.button("⚙️ Admin Panel", use_container_width=True):
                st.session_state["show_admin"] = True
        
        if st.button("🚪 Logout", use_container_width=True):
            logout()


def show_profile_page():
    """Display the user profile management page."""
    st.title("👤 User Profile Management")
    
    username = st.session_state.get("username")
    if not username:
        st.error("Please log in to view your profile.")
        return
    
    # Get current profile data
    profile = get_user_profile(username)
    stats = get_account_stats(username)
    activity = get_session_activity(username, limit=20)
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Profile Info", "🔑 Change Password", "📊 Account Stats", "📋 Activity Log"])
    
    with tab1:
        st.subheader("Edit Profile Information")
        
        with st.form("profile_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                phone = st.text_input("Phone Number", value=profile.get('phone', ''))
                company = st.text_input("Company/Organization", value=profile.get('company', ''))
                timezone = st.selectbox(
                    "Timezone",
                    ["UTC", "America/New_York", "America/Los_Angeles", "Europe/London", 
                     "Europe/Paris", "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata"],
                    index=["UTC", "America/New_York", "America/Los_Angeles", "Europe/London",
                          "Europe/Paris", "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata"].index(profile.get('timezone', 'UTC'))
                )
            
            with col2:
                address = st.text_area("Address", value=profile.get('address', ''))
                preferred_units = st.selectbox(
                    "Preferred Units",
                    ["metric", "imperial"],
                    index=0 if profile.get('preferred_units', 'metric') == 'metric' else 1
                )
                language = st.selectbox(
                    "Language",
                    ["English", "Hindi", "Spanish", "French", "German", "Chinese"],
                    index=["English", "Hindi", "Spanish", "French", "German", "Chinese"].index(profile.get('language', 'English'))
                )
            
            notification_email = st.text_input("Notification Email", value=profile.get('notification_email', profile.get('email', '')))
            daily_summary = st.checkbox("Receive Daily Summary Emails", value=profile.get('daily_summary', True))
            
            submit = st.form_submit_button("💾 Save Changes")
            
            if submit:
                profile_data = {
                    'phone': phone,
                    'company': company,
                    'address': address,
                    'timezone': timezone,
                    'preferred_units': preferred_units,
                    'language': language,
                    'notification_email': notification_email,
                    'daily_summary': daily_summary
                }
                
                success, msg = update_user_profile(username, profile_data)
                if success:
                    st.success(msg)
                    record_session_activity(username, 'profile_update', 'Profile information updated')
                else:
                    st.error(msg)
    
    with tab2:
        st.subheader("Change Password")
        
        with st.form("password_change_form"):
            old_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_new_password = st.text_input("Confirm New Password", type="password")
            
            # Show password strength for new password
            if new_password:
                st.markdown("**New Password Strength:**")
                st.markdown(get_password_strength_html(new_password), unsafe_allow_html=True)
            
            submit = st.form_submit_button("🔐 Change Password")
            
            if submit:
                if not old_password:
                    st.error("Please enter your current password")
                elif new_password != confirm_new_password:
                    st.error("New passwords do not match")
                elif old_password == new_password:
                    st.error("New password must be different from current password")
                else:
                    success, msg = change_password(username, old_password, new_password)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
        
        # Password requirements reminder
        with st.expander("📋 Password Requirements"):
            st.markdown("""
            **Your new password must:**
            - Be at least 8 characters long
            - Contain at least one uppercase letter
            - Contain at least one lowercase letter  
            - Contain at least one number
            - Contain at least one special character (!@#$...)
            - Not be the same as your current password
            """)
    
    with tab3:
        st.subheader("Account Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Logins", stats.get('total_logins', 1))
        
        with col2:
            st.metric("Failed Attempts", stats.get('failed_attempts', 0))
        
        with col3:
            last_login = stats.get('last_login', 'Never')
            if last_login:
                try:
                    last_login_dt = datetime.fromisoformat(last_login)
                    last_login = last_login_dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            st.metric("Last Login", last_login)
        
        # Additional stats
        st.markdown("### Account Details")
        
        details_cols = st.columns(2)
        
        with details_cols[0]:
            st.markdown(f"**Username:** {stats.get('username', '')}")
            st.markdown(f"**Email:** {stats.get('email', '')}")
            st.markdown(f"**Role:** {stats.get('role', '')}")
        
        with details_cols[1]:
            created = stats.get('created_at', 'Unknown')
            if created:
                try:
                    created_dt = datetime.fromisoformat(created)
                    created = created_dt.strftime("%Y-%m-%d")
                except:
                    pass
            st.markdown(f"**Account Created:** {created}")
            st.markdown(f"**Activities Tracked:** {stats.get('activity_count', 0)}")
            st.markdown(f"**Password Changed:** {stats.get('password_changed_at', 'Never')}")
        
        # Session security info
        st.markdown("### 🔒 Security Info")
        
        security_cols = st.columns(3)
        
        with security_cols[0]:
            is_locked = stats.get('is_locked', False)
            if is_locked:
                st.error("⚠️ Account is LOCKED")
            else:
                st.success("✓ Account is active")
        
        with security_cols[1]:
            session_timeout = SESSION_TIMEOUT_MINUTES
            st.info(f"⏱️ Timeout: {session_timeout} min")
        
        with security_cols[2]:
            max_attempts = MAX_LOGIN_ATTEMPTS
            st.info(f"🔐 Lock after: {max_attempts} attempts")
    
    with tab4:
        st.subheader("Activity Log")
        
        if activity:
            # Display activity in a table
            activity_data = []
            for item in activity:
                timestamp = item.get('timestamp', '')
                if timestamp:
                    try:
                        ts = datetime.fromisoformat(timestamp)
                        timestamp = ts.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                
                action = item.get('action', '')
                details = item.get('details', '')
                
                # Format action
                action_icons = {
                    'login': '🔓',
                    'login_failed': '❌',
                    'logout': '🔒',
                    'password_change': '🔑',
                    'profile_update': '📝',
                    'report_generated': '📄',
                    'scenario_saved': '💾'
                }
                icon = action_icons.get(action, '📌')
                
                activity_data.append({
                    'Time': timestamp,
                    'Action': f"{icon} {action.replace('_', ' ').title()}",
                    'Details': details
                })
            
            activity_df = pd.DataFrame(activity_data)
            st.dataframe(activity_df, use_container_width=True)
        else:
            st.info("No activity recorded yet.")
    
    # Back button
    if st.button("← Back to Dashboard"):
        st.session_state["show_profile"] = False
        st.rerun()


def show_admin_panel():
    """Show admin panel for user management with enhanced features."""
    st.title("👥 User Management")
    
    with st.expander("Create New User", expanded=False):
        with st.form("create_user"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            new_email = st.text_input("Email")
            new_role = st.selectbox("Role", ["user", "admin"])
            
            # Show password strength for admin-created users
            if new_password:
                st.markdown("**Password Strength:**")
                st.markdown(get_password_strength_html(new_password), unsafe_allow_html=True)
            
            create_submit = st.form_submit_button("Create User")
            
            if create_submit:
                if new_username and new_password:
                    # Validate password
                    strength = calculate_password_strength(new_password)
                    if strength['score'] < 3:
                        st.error("Password is too weak. Please choose a stronger password.")
                    else:
                        success, msg = create_user(new_username, new_password, new_role, new_email)
                        if success:
                            st.success(msg)
                            record_session_activity(st.session_state.get("username", "admin"), 
                                                   'admin_user_created', f'Created user: {new_username}')
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    st.error("Username and password are required")
    
    with st.expander("Manage Users", expanded=True):
        users = list_users()
        if users:
            df = pd.DataFrame(users)
            st.dataframe(df, use_container_width=True)
            
            # Security info for admin
            st.markdown("### 🔒 Security Dashboard")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_users = len(users)
                st.metric("Total Users", total_users)
            
            with col2:
                active_users = sum(1 for u in users if u.get('is_active', True))
                st.metric("Active Users", active_users)
            
            with col3:
                admin_count = sum(1 for u in users if u.get('role') == 'admin')
                st.metric("Admins", admin_count)
            
            with col4:
                locked_users = sum(1 for u in users if u.get('lockout_info', {}).get('is_locked', False))
                st.metric("Locked", locked_users)
            
            # Delete user section
            st.subheader("Delete User")
            user_options = [u["username"] for u in users if u["username"] != "admin"]
            user_to_delete = st.selectbox("Select user to delete", user_options)
            
            col_del, col_confirm = st.columns([1, 1])
            
            with col_del:
                if st.button("🗑️ Delete User", type="primary"):
                    st.session_state["confirm_delete"] = True
            
            if st.session_state.get("confirm_delete"):
                with col_confirm:
                    if st.button("⚠️ Confirm Delete"):
                        if delete_user(user_to_delete):
                            st.success(f"User {user_to_delete} deleted")
                            record_session_activity(st.session_state.get("username", "admin"),
                                                   'admin_user_deleted', f'Deleted user: {user_to_delete}')
                            st.session_state["confirm_delete"] = False
                            st.rerun()
                        else:
                            st.error("Cannot delete user")
            
            # Reset password section
            st.markdown("---")
            st.subheader("Reset User Password")
            
            with st.form("reset_password"):
                reset_user = st.selectbox("Select User", user_options)
                new_pass = st.text_input("New Password", type="password")
                
                if new_pass:
                    st.markdown(get_password_strength_html(new_pass), unsafe_allow_html=True)
                
                if st.form_submit_button("🔑 Reset Password"):
                    if new_pass:
                        strength = calculate_password_strength(new_pass)
                        if strength['score'] < 3:
                            st.error("Password is too weak.")
                        else:
                            if update_user_password(reset_user, new_pass):
                                st.success(f"Password reset for {reset_user}")
                                record_session_activity(st.session_state.get("username", "admin"),
                                                       'admin_password_reset', f'Reset password for: {reset_user}')
                            else:
                                st.error("Failed to reset password")
        else:
            st.info("No users found")

