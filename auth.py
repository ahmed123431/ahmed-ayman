"""
Authentication and Role-Based Access Control (RBAC) for Mall RCM System.
"""
import streamlit as st
from database import get_connection, hash_password

def authenticate_user(username, password):
    """Verify username and password against database."""
    conn = get_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password)
    cursor.execute("""
        SELECT id, username, full_name, email, role, department
        FROM users
        WHERE username = ? AND password_hash = ?
    """, (username.strip(), pwd_hash))
    user = cursor.fetchone()
    conn.close()
    if user:
        return dict(user)
    return None

def login_ui():
    """Render a modern login interface in Streamlit."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, #1E293B, #0F172A); padding: 30px; border-radius: 12px; border: 1px solid #334155; margin-top: 40px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
                <div style="text-align: center; margin-bottom: 20px;">
                    <span style="font-size: 45px;">🏢 ⚙️</span>
                    <h2 style="color: #F8FAFC; margin: 10px 0 5px 0; font-family: 'Segoe UI', Tahoma, sans-serif;">RCM SYSTEM</h2>
                    <p style="color: #94A3B8; font-size: 14px; margin: 0;">Reliability Centered Maintenance & Operations Portal</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.form("login_form", clear_on_submit=False):
            st.markdown("### Sign In to Portal")
            username = st.text_input("Username", placeholder="e.g. admin, engineer1, tech1, tenant_zara")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Log In", use_container_width=True, type="primary")

            if submit:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state['user'] = user
                        st.success(f"Welcome back, {user['full_name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please verify username and password.")

        # Quick demo credential hints for ease of testing
        with st.expander("🔑 Quick Demo Credentials (Click to view)"):
            st.markdown("""
            | Role | Username | Password | Access Level |
            | :--- | :--- | :--- | :--- |
            | **Mall Operations Director** | `admin` | `admin123` | Full Admin & Budget Access |
            | **Chief MEP Engineer** | `engineer1` | `eng123` | FMEA, Asset Strategy, RCM Config |
            | **Senior HVAC Tech** | `tech1` | `tech123` | Work Orders, Checklists & Execution |
            | **Tenant Representative** | `tenant_zara` | `tenant123` | Issue Reporting & Status Tracking |
            """)

def logout():
    """Clear session and log out."""
    if 'user' in st.session_state:
        del st.session_state['user']
    st.rerun()

def get_current_user():
    """Return currently authenticated user or None."""
    return st.session_state.get('user', None)

def require_role(allowed_roles):
    """Check if current user has one of the allowed roles."""
    user = get_current_user()
    if not user or user.get('role') not in allowed_roles:
        st.error("⚠️ Access Denied: Your account role does not have permission to view this section.")
        st.stop()
